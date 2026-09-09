"""Deterministic public-CLI acceptance fixtures; never an actual business Skill run.

All Store mutations and checks use the frozen installed CLI. SQL is read-only
and used only after a scenario has executed, to inventory its evidence.
"""
import hashlib
import json
import sqlite3
import subprocess
import sys
import traceback
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
PLUGIN = Path('/Users/shuaiw/Workspace/goedge.cloud/test-sdlc/.local-runs/sdlc-v2/installed/final-v1')
PYTHON = Path('/Users/shuaiw/.local/share/mise/installs/python/3.11.15/bin/python3')
CLI = PLUGIN / 'scripts/sdlc.py'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def scope(path='.', access='read'):
    return [{'resource': 'main', 'path': path, 'access': access}]


class Session:
    def __init__(self, case, root=None, bindings=None):
        self.case = BASE / case
        self.root = root or self.case / 'product'
        self.root.mkdir(parents=True, exist_ok=True)
        self.bindings = bindings or {}
        self.index = 0

    def send(self, command, payload=None, **extra):
        self.index += 1
        req = dict(api_version='2', command=command, payload=payload or {},
                   **self.bindings)
        req.update(extra)
        req = {k: v for k, v in req.items() if v is not None}
        trace = self.case / 'requests' / f'{self.index:03d}-{command}'
        save(trace / 'request.json', req)
        argv = [str(PYTHON), '-B', str(CLI), '--root', str(self.root), '--request', '-']
        p = subprocess.run(argv, input=json.dumps(req), text=True, capture_output=True)
        (trace / 'stdout.log').write_text(p.stdout)
        (trace / 'stderr.log').write_text(p.stderr)
        save(trace / 'process.json', {'argv': argv, 'exit_code': p.returncode})
        response = json.loads(p.stdout)
        save(trace / 'response.json', response)
        expected = 0 if response['ok'] else (2 if response['status'] in {'invalid_input', 'conflict'} else 3 if response['status'] in {'blocked', 'needs_input', 'needs_work', 'unknown'} else 4)
        assert p.returncode == expected, (command, p.returncode, response)
        print(self.case.name, self.index, command, response['status'], flush=True)
        return response

    def ok(self, command, payload=None, **extra):
        r = self.send(command, payload, **extra)
        assert r['ok'], r
        return r['data']

    def initialize(self):
        config = self.ok('workspace.init', {'name': self.case.name})['config']
        self.bindings = {key: config[key] for key in ['project_id', 'workspace_id']}
        self.context()

    def context(self):
        self.ctx = self.ok('context.commit', {'summary': 'Isolated deterministic acceptance fixture',
            'entries': [{'kind': 'resource', 'name': 'main', 'content': 'Disposable fixture only',
                         'settings': {'resource': 'main'}}]})['context_id']

    def new_change(self, slug, actions=('edit_local', 'run_check', 'package_local')):
        self.target = '.sdlc/exports/' + slug
        self.change_payload = {'slug': slug, 'context_id': self.ctx, 'title': slug,
            'summary': 'Deterministic acceptance: count sized values and preserve independent double',
            'goal': 'Meet exact checks without changing original criteria', 'in_scope': 'Disposable local fixture',
            'out_of_scope': 'Actual Q0/Q1/Q2 business execution and external writes', 'delivery_mode': 'local',
            'delivery_target': self.target, 'original_text': 'Count any sized input, including empty and noniterable sized values. Independently double integers.',
            'review_mode': 'auto', 'actor_id': 'current-agent',
            'authorizations': self.auth(actions)}
        r = self.send('change.create', self.change_payload)
        assert r['ok'], r
        self.bindings.update(change_id=r['data']['change_id'], run_id=r['run_id'])
        self.source = r['data']['source_id']

    def auth(self, actions):
        return [{'action': a, 'target': self.target if a == 'package_local' else 'main',
                 'issued_by': 'user', 'basis_text': 'Parent assignment authorizes isolated acceptance fixture local implementation, real checks, local packaging.'} for a in actions]

    def submit(self, phase, operations):
        p = self.ok('phase.prepare', {'phase': phase})
        return self.ok('phase.submit', {'phase': phase,
            'revision_id': p['content']['revision']['revision_id'], 'operations': operations}, expected_generation=p['generation'])

    def complete(self, phase):
        if phase in ('IMP', 'VFY', 'RLS'):
            return self.ok('phase.complete', {'phase': phase, **self.execution})
        p = self.ok('phase.prepare', {'phase': phase})
        return self.ok('phase.complete', {'phase': phase,
            'revision_id': p['content']['revision']['revision_id']}, expected_generation=p['generation'])

    def task(self, key, design, criterion, path, phase='IMP', write=True):
        return {'op': 'create_task', 'client_key': key, 'target_phase': phase,
            'kind': 'implement' if write else 'verify', 'title': key,
            'description': 'Perform the bounded ' + key + ' fixture work',
            'completion_text': 'Actual work and attempt saved', 'scope_paths': scope(path, 'write' if write else 'read'),
            'designs': [{'id': design}], 'criteria': [{'id': criterion}]}

    def plan(self, prefix='', verification_only=False, two=False):
        self.prefix = prefix
        reqs = ['count', 'double'] if two else ['count']
        ops = []
        for name in reqs:
            ops += [{'op': 'create_requirement', 'client_key': name, 'kind': 'behavior',
                'statement': 'Count any sized input without requiring iteration' if name == 'count' else 'Double integer value independently', 'sources': [{'id': self.source}]},
                {'op': 'create_criterion', 'client_key': name + '_ac', 'condition_text': 'Empty and noniterable sized input' if name == 'count' else 'Negative, zero and positive integers',
                 'expected_result': 'Exact length' if name == 'count' else 'Input multiplied by two', 'requirements': [{'client_key': name}]}]
        self.req = self.submit('REQ', ops)['ids']
        self.complete('REQ')
        ops = []
        for name in reqs:
            ops += [{'op': 'create_design', 'client_key': name + '_design', 'domain': 'components', 'title': name,
                'decision': 'Use len on Sized inputs' if name == 'count' else 'Use integer multiplication by two',
                'rationale': 'Preserve exact declared behavior', 'alternatives': 'Custom iteration violates the Sized interface' if name == 'count' else 'Repeated addition is unnecessary',
                'detail': 'Verify current bytes without product edits' if verification_only else 'Implement the explicit interface',
                'requirements': [{'id': self.req[name]}]},
                {'op': 'create_check', 'client_key': name + '_test', 'purpose': 'acceptance', 'method': 'test', 'executor': 'command',
                 'description': 'Actually execute ' + name + ' assertions', 'expected_result': 'All assertions pass',
                 'argv': [str(PYTHON), '-B', prefix + 'test_' + name + '.py'], 'required': True,
                 'input_paths': scope(prefix + name + '.py') + scope(prefix + 'test_' + name + '.py'),
                 'criteria': [{'id': self.req[name + '_ac']}]}]
        ops += [{'op': 'create_check', 'client_key': 'review', 'purpose': 'convergence', 'method': 'inspection', 'executor': 'agent',
                 'description': 'Inspect all fixture requirements, design decisions and implementation for missing or contradictory scope',
                 'expected_result': 'No unresolved fixture gap', 'required': True, 'input_paths': scope(prefix or '.')},
                {'op': 'create_check', 'client_key': 'readback', 'purpose': 'release_readback', 'method': 'test', 'executor': 'command',
                 'description': 'Independent local archive readback', 'expected_result': 'All archived digests match',
                 'argv': ['@runtime', 'delivery.readback'], 'required': True}]
        self.dsn = self.submit('DSN', ops)['ids']
        self.complete('DSN')
        ops = []
        for name in reqs:
            ops += [self.task(name + '_work', self.dsn[name + '_design'], self.req[name + '_ac'], prefix or '.', write=not verification_only),
                {'op': 'update_check', 'id': self.dsn[name + '_test'], 'task': {'client_key': name + '_work'}}]
        self.tasks = self.submit('PLN', ops)['ids']
        self.rev = self.complete('PLN')['revision_id']
        self.lease = self.ok('run.acquire')['lease_id']

    @property
    def execution(self):
        return {'revision_id': self.rev, 'lease_id': self.lease}

    def work(self, task, files=None, check=None):
        p = {**self.execution, 'task_id': task}
        step = self.ok('task.start', p)['step_id']
        if files:
            self.ok('task.write', {**p, 'step_id': step, 'files': [{'path': k, 'content': v} for k, v in files.items()]})
        result = self.check(check) if check else None
        self.ok('task.finish', {**p, 'step_id': step, 'summary': 'Performed and retained the actual bounded fixture work'})
        return result

    def check(self, check):
        return self.ok('check.run', {**self.execution, 'check_id': check})

    def review(self, findings=None):
        return self.ok('check.record_review', {**self.execution, 'check_id': self.dsn['review'],
            'status': 'fail' if findings else 'pass', 'observations': 'Deterministic fixture self review: actual command assertions are separate authoritative behavioral evidence.',
            'findings': findings or []})

    def deliver(self):
        prepared = self.ok('delivery.prepare', {**self.execution, 'usage': 'Read verification.json and run archived test scripts with recorded Python.'})
        delivered = self.ok('delivery.execute', {'delivery_id': prepared['delivery_id'], 'lease_id': self.lease})
        assert delivered['status'] == 'succeeded', delivered
        closed = self.complete('RLS')
        readback = self.ok('delivery.get', {'delivery_id': prepared['delivery_id']})
        package = self.root / prepared['package_path']
        with zipfile.ZipFile(package) as z:
            assert z.testzip() is None
            manifest = json.loads(z.read('manifest.json'))
            assert manifest['revision_id'] == self.rev
            save(self.case / 'delivery-manifest.json', manifest)
            (self.case / 'delivered-verification.json').write_bytes(z.read('verification.json'))
        return {'prepared': prepared, 'delivered': delivered, 'closed': closed, 'readback': readback,
                'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest()}

    def evidence(self):
        con = sqlite3.connect(f'file:{self.root / ".sdlc/store.sqlite3"}?mode=ro', uri=True)
        con.row_factory = sqlite3.Row
        result = {table: [dict(r) for r in con.execute('SELECT * FROM ' + table)]
                  for table in ['projects', 'workspaces', 'changes', 'runs', 'steps', 'check_results', 'findings', 'authorizations', 'deliveries']}
        result['foreign_key_check'] = [list(r) for r in con.execute('PRAGMA foreign_key_check')]
        con.close()
        save(self.case / 'post-execution-evidence.json', result)
        return result


COUNT_TEST = ('from count import count\nclass SizedOnly:\n    def __len__(self): return 7\n'
              'assert count([]) == 0\nassert count([1, 2]) == 2\nassert count(SizedOnly()) == 7\nprint("three real count assertions passed")\n')
COUNT_GOOD = 'def count(values):\n    return len(values)\n'
DOUBLE_GOOD = 'def double(value):\n    return value * 2\n'
DOUBLE_TEST = 'from double import double\nassert [double(x) for x in [-2, 0, 3]] == [-4, 0, 6]\nprint("three independent double cases passed")\n'


def verification_only():
    s = Session('v2-008-attempt2')
    (s.root / 'count.py').write_text(COUNT_GOOD)
    (s.root / 'test_count.py').write_text(COUNT_TEST)
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in s.root.glob('*.py')}
    s.initialize()
    s.new_change('verification-only', actions=('run_check', 'package_local'))
    s.plan(verification_only=True)
    imp = s.work(s.tasks['count_work'], check=s.dsn['count_test'])
    assert (imp['outcome'], imp['exit_code']) == ('pass', 0)
    s.complete('IMP')
    vfy = s.check(s.dsn['count_test'])
    assert vfy['result_id'] != imp['result_id'] and vfy['outcome'] == 'pass'
    s.review()
    assert s.complete('VFY')['converged']
    delivered = s.deliver()
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in s.root.glob('*.py')}
    assert before == after
    evidence = s.evidence()
    assert {r['phase'] for r in evidence['steps'] if r['change_id'] == s.bindings['change_id']} >= {'REQ', 'DSN', 'PLN', 'IMP', 'VFY', 'RLS'}
    assert not [a for a in evidence['authorizations'] if a['action'] == 'edit_local']
    return {'status': 'verified', 'before': before, 'after': after, 'imp_check': imp, 'vfy_check': vfy, 'delivery': delivered}


def missing_function():
    s = Session('v2-003')
    s.initialize()
    s.new_change('missing-function')
    s.plan()
    old_revision = s.rev
    s.work(s.tasks['count_work'], {'count.py': '# The defined count function is missing.\n', 'test_count.py': COUNT_TEST})
    s.complete('IMP')
    red = s.check(s.dsn['count_test'])
    assert red['outcome'] == 'fail' and red['exit_code'] != 0
    review = s.review([{'kind': 'missing', 'severity': 'blocking', 'return_phase': 'PLN',
        'description': 'The defined count function is absent; add an explicit implementation task.', 'issue_key': 'missing-count'}])
    finding = review['finding_ids'][0]
    returned = s.send('phase.complete', {'phase': 'VFY', **s.execution})
    assert returned['status'] == 'needs_work' and returned['next_actions'][0]['phase'] == 'PLN', returned
    s.ok('change.revise', {'phase': 'PLN', 'reason': 'Add the missing function implementation task identified by VFY.'})
    added = s.submit('PLN', [s.task('add_count', s.dsn['count_design'], s.req['count_ac'], 'count.py')])['ids']['add_count']
    s.rev = s.complete('PLN')['revision_id']
    assert s.rev != old_revision and added != s.tasks['count_work']
    s.work(added, {'count.py': COUNT_GOOD})
    s.complete('IMP')
    green = s.check(s.dsn['count_test'])
    assert green['outcome'] == 'pass'
    new_review = s.review()
    for fid, rid in [(red['finding_id'], green['result_id']), (finding, new_review['result_id'])]:
        s.ok('finding.address', {'finding_id': fid, 'lease_id': s.lease})
        s.ok('finding.resolve', {'finding_id': fid, 'result_id': rid, 'lease_id': s.lease})
    assert s.complete('VFY')['converged']
    s.evidence()
    return {'status': 'verified', 'returned': returned, 'old_revision': old_revision, 'new_revision': s.rev,
            'added_task': added, 'red': red, 'green': green, 'findings': s.ok('finding.list')}


def contradicts_design():
    s = Session('v2-004')
    s.initialize()
    s.new_change('contradicts-design')
    s.plan(two=True)
    old_revision = s.rev
    before = s.ok('phase.prepare')['content']
    s.work(s.tasks['count_work'], {'count.py': 'def count(values):\n    return sum(1 for item in values)\n', 'test_count.py': COUNT_TEST})
    s.work(s.tasks['double_work'], {'double.py': DOUBLE_GOOD, 'test_double.py': DOUBLE_TEST})
    s.complete('IMP')
    red = s.check(s.dsn['count_test'])
    unrelated_before = s.check(s.dsn['double_test'])
    assert red['outcome'] == 'fail' and unrelated_before['outcome'] == 'pass'
    reviewed = s.review([{'kind': 'contradicts', 'severity': 'blocking', 'return_phase': 'DSN',
        'description': 'Count iterates despite the explicit len decision; clarify Sized-only implementation details before repair.', 'issue_key': 'sized-design-contradiction'}])
    returned = s.send('phase.complete', {'phase': 'VFY', **s.execution})
    assert returned['status'] == 'needs_work' and returned['next_actions'][0]['phase'] == 'DSN', returned
    s.ok('change.revise', {'phase': 'DSN', 'reason': 'Clarify exact direct-len implementation for the existing Sized acceptance; retain unrelated doubling design.'})
    s.submit('DSN', [{'op': 'update_design', 'id': s.dsn['count_design'],
                      'detail': 'Call len(values) directly. A __len__-only object is supported and must not be iterated.'}])
    s.complete('DSN')
    s.rev = s.complete('PLN')['revision_id']
    after = s.ok('phase.prepare')['content']
    save(s.case / 'content-before.json', before)
    save(s.case / 'content-after.json', after)
    s.work(s.tasks['count_work'], {'count.py': COUNT_GOOD})
    s.complete('IMP')
    green = s.check(s.dsn['count_test'])
    unrelated_after = s.check(s.dsn['double_test'])
    assert green['outcome'] == unrelated_after['outcome'] == 'pass'
    new_review = s.review()
    for fid, rid in [(red['finding_id'], green['result_id']), (reviewed['finding_ids'][0], new_review['result_id'])]:
        s.ok('finding.address', {'finding_id': fid, 'lease_id': s.lease})
        s.ok('finding.resolve', {'finding_id': fid, 'result_id': rid, 'lease_id': s.lease})
    assert s.complete('VFY')['converged']
    evidence = s.evidence()
    results = {x['result_id']: x for x in evidence['check_results']}
    assert results[red['result_id']]['definition_digest'] != results[green['result_id']]['definition_digest']
    assert results[unrelated_before['result_id']]['definition_digest'] == results[unrelated_after['result_id']]['definition_digest']
    steps = [r for r in evidence['steps'] if r['step_key'] == 'task:' + s.tasks['double_work']]
    assert len(steps) == 1 and steps[0]['status'] == 'completed'
    assert (s.root / 'double.py').read_text() == DOUBLE_GOOD
    assert before['requirements'] == [{**r, 'revision_id': old_revision} for r in after['requirements']]
    return {'status': 'verified', 'returned': returned, 'old_revision': old_revision, 'new_revision': s.rev,
        'changed_check_fingerprints': [results[x['result_id']]['definition_digest'] for x in [red, green]],
        'unrelated_check_fingerprints': [results[x['result_id']]['definition_digest'] for x in [unrelated_before, unrelated_after]],
        'unrelated_original_step': steps[0], 'findings': s.ok('finding.list')}


def two_projects():
    a = Session('v2-044-a-attempt3', root=BASE / 'v2-044-shared-attempt3/product')
    a.initialize()
    project_a = dict(a.bindings)
    created = a.ok('project.create', {'name': 'Independent project B'})
    b = Session('v2-044-b-attempt3', root=a.root, bindings=created)
    b.context()
    a.new_change('project-a')
    b.new_change('project-b', actions=('edit_local', 'package_local'))
    a.plan(prefix='a/')
    a.work(a.tasks['count_work'], {'a/count.py': COUNT_GOOD, 'a/test_count.py': COUNT_TEST})
    a.complete('IMP')
    a_result = a.check(a.dsn['count_test'])
    assert a_result['outcome'] == 'pass'
    a.review()
    assert a.complete('VFY')['converged']
    a_delivered = a.deliver()
    b.plan(prefix='b/')
    b.work(b.tasks['count_work'], {'b/count.py': COUNT_GOOD, 'b/test_count.py': COUNT_TEST})
    b.complete('IMP')
    wrong_context_payload = dict(b.change_payload, slug='cross-context', context_id=a.ctx)
    cross_context = b.send('change.create', wrong_context_payload, change_id=None, run_id=None)
    assert cross_context['errors'][0]['code'] == 'CONTEXT_SCOPE', cross_context
    denied = b.send('check.run', {**b.execution, 'check_id': b.dsn['count_test']})
    assert denied['errors'][0]['code'] == 'AUTHORIZATION_REQUIRED', denied
    b.ok('authorization.grant', {'authorizations': b.auth(['run_check'])})
    cross_check = b.send('check.run', {**b.execution, 'check_id': a.dsn['count_test']})
    assert cross_check['errors'][0]['code'] == 'CHECK_SCOPE', cross_check
    cross_revision = b.send('check.run', {**b.execution, 'revision_id': a.rev, 'check_id': a.dsn['count_test']})
    assert not cross_revision['ok'], cross_revision
    b_result = b.check(b.dsn['count_test'])
    assert b_result['outcome'] == 'pass' and b_result['result_id'] != a_result['result_id']
    b.review()
    assert b.complete('VFY')['converged']
    b_delivered = b.deliver()
    evidence = b.evidence()
    assert len(evidence['projects']) == 2
    for s in (a, b):
        phases = {r['phase'] for r in evidence['steps'] if r['change_id'] == s.bindings['change_id']}
        assert phases >= {'REQ', 'DSN', 'PLN', 'IMP', 'VFY', 'RLS'}, phases
        for r in evidence['check_results']:
            if r['change_id'] == s.bindings['change_id']:
                assert r['project_id'] == s.bindings['project_id']
        for r in evidence['authorizations']:
            if r['change_id'] == s.bindings['change_id']:
                assert r['project_id'] == s.bindings['project_id'] and r['workspace_id'] == s.bindings['workspace_id']
    return {'status': 'verified', 'a': a.bindings, 'b': b.bindings, 'cross_context': cross_context,
        'cross_check': cross_check, 'cross_revision': cross_revision, 'authorization_denied': denied,
        'a_delivery': a_delivered, 'b_delivery': b_delivered}


def main():
    manifest = json.loads((PLUGIN / 'install-manifest.json').read_text())
    assert manifest['source_head'] == '495177acf777251d378652e2a50e47a1b5c4c41a' and not manifest['source_dirty']
    assert manifest['package_digest'] == 'a3ecb85d9286fe61b80f98882da4e4f6b91ca33aa25616401d0b043967f9a310'
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((PLUGIN / name).read_bytes()).hexdigest() == expected, name
    save(BASE / 'verified-package.json', manifest)
    cases = {'V2-003': missing_function, 'V2-004': contradicts_design, 'V2-008': verification_only, 'V2-044': two_projects}
    selected = sys.argv[1:] or list(cases)
    results = {}
    for key in selected:
        try:
            results[key] = cases[key]()
        except Exception as exc:
            results[key] = {'status': 'failed', 'exception': str(exc), 'traceback': traceback.format_exc()}
            print(results[key]['traceback'], flush=True)
        save(BASE / (key + '-result.json'), results[key])
    save(BASE / 'last-execution.json', {'source_head': manifest['source_head'], 'package_digest': manifest['package_digest'],
        'kind': 'deterministic acceptance fixture', 'results': results})
    print(json.dumps({k: v['status'] for k, v in results.items()}), flush=True)
    return int(any(v['status'] != 'verified' for v in results.values()))


if __name__ == '__main__':
    raise SystemExit(main())
