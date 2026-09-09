"""Strict V2-044 public-CLI retest against an explicitly supplied frozen package.

Run with: python3 -B delivery_scope_retest.py <new-frozen-plugin-root>
All mutations use public CLI. Original q0-repairs evidence remains untouched.
"""
import hashlib
import json
import sys
import traceback
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'core'))
import acceptance_core as ac


class ScopedSession(ac.Session):
    add_tamper_task = False

    def submit(self, phase, operations):
        operations = [dict(op) for op in operations]
        for op in operations:
            if op.get('op') == 'create_check' and op.get('purpose') == 'release_readback':
                op['input_paths'] = ac.scope(self.prefix or '.')
        if phase == 'PLN' and self.add_tamper_task:
            task = self.task('tamper_after_prepare', self.dsn['count_design'], self.req['count_ac'],
                             self.prefix + 'count.py', phase='RLS')
            task.update(kind='deliver', description='Expected negative: mutate declared B input after delivery preparation',
                        completion_text='Actual post-prepare changed bytes retained for rejection evidence')
            operations.append(task)
        return super().submit(phase, operations)


def verify_archive(session, prepared, prefix):
    path = session.root / prepared['package_path']
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read('manifest.json'))
        code = [name for name in manifest['files'] if name.startswith('code/')]
        assert code and all(name.startswith('code/main/' + prefix) for name in code), code
    ac.save(session.case / 'strict-delivery-manifest.json', manifest)
    return {'code_files': code, 'package_path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def prepare_b_change(root, bindings, slug, tamper=False):
    session = ScopedSession(slug, root=root, bindings={key: bindings[key] for key in ['project_id', 'workspace_id']})
    session.context()
    session.new_change(slug)
    session.add_tamper_task = tamper
    session.plan(prefix='b/')
    actual = session.work(session.tasks['count_work'], check=session.dsn['count_test'])
    assert actual['outcome'] == 'pass'
    session.complete('IMP')
    assert session.check(session.dsn['count_test'])['outcome'] == 'pass'
    session.review()
    assert session.complete('VFY')['converged']
    prepared = session.ok('delivery.prepare', {**session.execution, 'usage': 'B-only deterministic fixture report and source.'})
    return session, prepared


def main():
    plugin = Path(sys.argv[1]).resolve()
    manifest = json.loads((plugin / 'install-manifest.json').read_text())
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((plugin / name).read_bytes()).hexdigest() == expected, name
    output = Path(__file__).resolve().parent / ('scoped-retest-' + manifest['package_digest'][:12])
    assert not output.exists(), 'Use a new package/evidence directory; preserve the previous run.'
    output.mkdir()
    ac.PLUGIN, ac.CLI, ac.BASE, ac.Session = plugin, plugin / 'scripts/sdlc.py', output, ScopedSession
    ac.save(output / 'verified-package.json', manifest)
    result = {'source_head': manifest['source_head'], 'package_digest': manifest['package_digest'],
              'kind': 'deterministic public-CLI retest', 'status': 'running'}
    try:
        baseline = ac.two_projects()
        root = output / 'v2-044-shared-attempt3/product'
        packages = {}
        for label, prefix in [('a', 'a/'), ('b', 'b/')]:
            s = ScopedSession('v2-044-' + label + '-attempt3', root=root)
            packages[label] = verify_archive(s, baseline[label + '_delivery']['prepared'], prefix)
        isolation = []
        for owner, other in [('a', 'b'), ('b', 'a')]:
            owner_session = ScopedSession('cross-read-'+owner, root=root, bindings=dict(baseline[owner]))
            wrong_revision = baseline[other+'_delivery']['readback']['delivery']['revision_id']
            denied = owner_session.send('check.evaluate', {'revision_id': wrong_revision})
            assert not denied['ok'] and denied['errors'][0]['code'] == 'REVISION_SCOPE', denied
            isolation.append({'owner':owner, 'other':other, 'rejected':denied})
        result['bidirectional_result_isolation'] = isolation
        result['two_project_baseline'] = baseline
        result['strict_packages'] = packages

        b, prepared = prepare_b_change(root, baseline['b'], 'b-unrelated-source-change')
        a = ScopedSession('a-independent-edit', root=root,
                          bindings={key: baseline['a'][key] for key in ['project_id', 'workspace_id']})
        a.context()
        a.new_change('a-independent-edit')
        a.plan(prefix='a/')
        a.work(a.tasks['count_work'], {'a/count.py': ac.COUNT_GOOD + '# Independent A-only edit after B prepared.\n'})
        a.complete('IMP')
        a.ok('run.cancel', {'reason': 'Independent A-only fixture mutation completed; no delivery requested for this helper change.'})
        executed = b.ok('delivery.execute', {'delivery_id': prepared['delivery_id'], 'lease_id': b.lease})
        assert executed['status'] == 'succeeded', executed
        b.complete('RLS')
        b.ok('delivery.get', {'delivery_id': prepared['delivery_id']})
        result['unrelated_a_change'] = {'delivery': executed, 'package': verify_archive(b, prepared, 'b/')}
        b.evidence()

        b, prepared = prepare_b_change(root, baseline['b'], 'b-relevant-source-change', tamper=True)
        b.work(b.tasks['tamper_after_prepare'], {'b/count.py': 'def count(values):\n    return 0\n'})
        rejected = b.send('delivery.execute', {'delivery_id': prepared['delivery_id'], 'lease_id': b.lease})
        assert not rejected['ok'] and rejected['errors'][0]['code'] == 'DELIVERY_SUBJECT_CHANGED', rejected
        assert not (root / prepared['package_path']).exists()
        b.ok('run.cancel', {'reason': 'Expected relevant-input mutation rejection retained; isolated negative fixture complete.'})
        b.evidence()
        result['relevant_b_change'] = rejected
        result['status'] = 'verified'
    except Exception as exc:
        result.update(status='failed', exception=str(exc), traceback=traceback.format_exc())
        print(result['traceback'], flush=True)
    ac.save(output / 'RESULT.json', result)
    print(json.dumps({'status': result['status'], 'output': str(output)}), flush=True)
    return int(result['status'] != 'verified')


if __name__ == '__main__':
    raise SystemExit(main())
