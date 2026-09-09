"""V2-002/010 public-entry deterministic acceptance; not a business Agent run."""
import hashlib
import json
import subprocess
import sys
import traceback
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent / 'core'))
import acceptance_core as ac

PLUGIN = Path('/Users/shuaiw/Workspace/goedge.cloud/test-sdlc/.local-runs/sdlc-v2/installed/final-v1')
ac.CLI = PLUGIN / 'scripts/sdlc.py'
ac.BASE = BASE
PHASES = ['REQ', 'DSN', 'PLN', 'IMP', 'VFY', 'RLS']
SKILLS = dict(zip(PHASES, ['sdlc-100-req', 'sdlc-200-dsn', 'sdlc-300-pln', 'sdlc-400-imp', 'sdlc-500-vfy', 'sdlc-600-rls']))
BRIEF = '# Background reference\n\nEmpty input has size 0. Three elements have size 3.\nThis document is reference material, not a task producer or execution prerequisite.\n'


def dump(path, value):
    ac.save(path, value)


def load(mode):
    case = BASE / mode
    state = json.loads((case / 'state.json').read_text())
    s = ac.Session(mode, root=case / 'product', bindings=state['bindings'])
    s.index = len(list((case / 'requests').glob('*/request.json')))
    for key in ['req', 'dsn', 'tasks', 'rev', 'lease', 'source', 'target']:
        if key in state:
            setattr(s, key, state[key])
    return s, state


def keep(s, state):
    state['bindings'] = s.bindings
    for key in ['req', 'dsn', 'tasks', 'rev', 'lease', 'source', 'target']:
        if hasattr(s, key):
            state[key] = getattr(s, key)
    dump(s.case / 'state.json', state)


def setup(mode):
    case = BASE / mode
    assert not case.exists(), 'Preserve previous fixture; use a new evidence directory.'
    s = ac.Session(mode)
    (s.root / 'background.md').write_text(BRIEF)
    s.initialize()
    s.target = '.sdlc/exports/entry-source'
    created = s.send('change.create', {'slug': 'entry-source', 'context_id': s.ctx,
        'title': 'Count Sized input', 'summary': 'Exact count and background attachment',
        'goal': 'Return exact length without requiring iteration', 'in_scope': 'Local deterministic count fixture and report',
        'out_of_scope': 'External effects and unrelated product scenarios', 'delivery_mode': 'local',
        'delivery_target': s.target, 'original_text': 'Return len for every Sized input, including empty input and noniterable Sized input; use the supplied background reference only as a source.',
        'authorizations': s.auth(['edit_local', 'run_check', 'package_local']), 'actor_id': 'current-agent', 'review_mode': 'auto'})
    assert created['ok'], created
    s.bindings.update(change_id=created['data']['change_id'], run_id=created['run_id'])
    s.source = created['data']['source_id']
    state = {'mode': mode, 'next_phase': 'REQ', 'phase_history': [], 'created_change': s.bindings['change_id']}
    keep(s, state)
    return s, state


def stage(s, state, phase):
    assert state['next_phase'] == phase
    skill = PLUGIN / 'skills' / SKILLS[phase] / 'SKILL.md'
    content = skill.read_bytes()
    (s.case / ('loaded-' + phase + '-SKILL.md')).write_bytes(content)
    entered = s.ok('phase.prepare', {'phase': phase})
    assert entered['change']['change_id'] == state['created_change'] == s.bindings['change_id']
    rev = entered['content']['revision']
    if state['phase_history']:
        previous = state['phase_history'][-1]
        if phase in ['DSN', 'PLN']:
            assert rev['parent_id'] == previous['committed_revision_id']
        else:
            assert rev['state'] == 'committed' and rev['revision_id'] == s.rev
    record = {'phase': phase, 'entry_change_id': s.bindings['change_id'], 'entry_run_id': s.bindings['run_id'],
              'entry_revision_id': rev['revision_id'], 'entry_revision_state': rev['state'],
              'entry_parent_revision_id': rev['parent_id'], 'skill_sha256': hashlib.sha256(content).hexdigest(),
              'public_phase_schema_sha256': hashlib.sha256(json.dumps(entered['input_schema'], sort_keys=True).encode()).hexdigest()}
    if phase == 'REQ':
        asset = s.ok('asset.add', {'path': 'background.md', 'owner_type': 'source', 'owner_id': s.source,
            'purpose': 'Readable background source; no runtime prerequisite'}, expected_generation=entered['generation'])
        state['asset'] = asset
        s.req = s.submit('REQ', [
            {'op': 'create_requirement', 'client_key': 'req', 'kind': 'behavior', 'statement': 'Count Sized input without iteration', 'sources': [{'id': s.source}]},
            {'op': 'create_criterion', 'client_key': 'ac', 'condition_text': 'Empty/nonempty/noniterable Sized inputs',
             'expected_result': 'Exact len', 'requirements': [{'client_key': 'req'}]}])['ids']
        completed = s.complete('REQ')
    elif phase == 'DSN':
        links = entered['attachments']
        assert len(links) == 1 and links[0]['source_id'] == s.source
        sha = links[0]['sha256']
        asset_path = s.root / '.sdlc/assets' / sha[:2] / sha[2:4] / sha
        assert asset_path.read_text() == BRIEF
        state['source_readback'] = {'sha256': sha, 'bytes': len(asset_path.read_bytes()), 'source_id': s.source,
                                    'phase': 'DSN', 'text_equals_original': True}
        s.dsn = s.submit('DSN', [
            {'op': 'create_design', 'client_key': 'design', 'domain': 'components', 'title': 'Sized length',
             'decision': 'Call len directly', 'rationale': 'Noniterable Sized values remain supported',
             'alternatives': 'Iteration would violate the requirement', 'detail': 'Background is source only',
             'requirements': [{'id': s.req['req']}]},
            {'op': 'create_check', 'client_key': 'test', 'purpose': 'acceptance', 'method': 'test', 'executor': 'command',
             'description': 'Actual Sized assertions', 'expected_result': 'Three assertions pass', 'required': True,
             'argv': [str(ac.PYTHON), '-B', 'test_count.py'], 'input_paths': ac.scope('count.py') + ac.scope('test_count.py'),
             'criteria': [{'id': s.req['ac']}]},
            {'op': 'create_check', 'client_key': 'review', 'purpose': 'convergence', 'method': 'inspection', 'executor': 'agent',
             'description': 'Self review of all fixture scope', 'expected_result': 'No unresolved gap', 'required': True},
            {'op': 'create_check', 'client_key': 'readback', 'purpose': 'release_readback', 'method': 'test', 'executor': 'command',
             'description': 'Independent local report readback', 'expected_result': 'All archive digests agree', 'required': True,
             'argv': ['@runtime', 'delivery.readback']}])['ids']
        completed = s.complete('DSN')
    elif phase == 'PLN':
        s.tasks = s.submit('PLN', [s.task('work', s.dsn['design'], s.req['ac'], '.'),
            {'op': 'update_check', 'id': s.dsn['test'], 'task': {'client_key': 'work'}}])['ids']
        completed = s.complete('PLN')
        s.rev = completed['revision_id']
    elif phase == 'IMP':
        s.lease = s.ok('run.acquire')['lease_id']
        content = entered['content']
        assert content['task_dependencies'] == [] and content['preconditions'] == []
        assert len(content['requirement_sources']) == 1
        runnable = s.ok('task.next', {'revision_id': s.rev})['tasks']
        assert len(runnable) == 1 and runnable[0]['task']['task_id'] == s.tasks['work'] and runnable[0]['runnable']
        state['source_not_dependency'] = {'sources': content['sources'], 'source_links': content['requirement_sources'],
            'attachments': entered['attachments'], 'task_dependencies': content['task_dependencies'],
            'preconditions': content['preconditions'], 'task_next': runnable}
        s.work(s.tasks['work'], {'count.py': ac.COUNT_GOOD, 'test_count.py': ac.COUNT_TEST})
        completed = s.complete('IMP')
    elif phase == 'VFY':
        command = s.check(s.dsn['test'])
        assert (command['outcome'], command['exit_code']) == ('pass', 0)
        review = s.review()
        state['vfy_results'] = {'command': command, 'review': review}
        completed = s.complete('VFY')
        assert completed['converged']
    else:
        state['delivery'] = s.deliver()
        completed = state['delivery']['closed']
        exported = s.ok('workspace.export', {'change_id': s.bindings['change_id']}, run_id=None, change_id=None)
        state['export'] = exported
        with zipfile.ZipFile(exported['path']) as archive:
            assert archive.testzip() is None
            assets = [n for n in archive.namelist() if n.endswith(state['source_readback']['sha256'])]
            assert assets and any(archive.read(n).decode() == BRIEF for n in assets)
        final = s.ok('change.get')
        dump(s.case / 'final-content.json', final['content'])
        run = s.ok('run.get')
        assert run['run']['status'] == 'completed'
        assert {r['phase'] for r in run['steps']} >= set(PHASES)
        state['final_run'] = run
    record['committed_revision_id'] = completed.get('committed_revision_id', s.rev if hasattr(s, 'rev') else None)
    record['completion'] = completed
    state['phase_history'].append(record)
    state['next_phase'] = PHASES[PHASES.index(phase) + 1] if phase != 'RLS' else None
    keep(s, state)


def normalize(s, state):
    content = json.loads((s.case / 'final-content.json').read_text())
    ids = {s.source: 'source'}
    for key in ['req','dsn','tasks']:
        ids.update({value: key + ':' + name for name,value in state[key].items()})
    def walk(value):
        if isinstance(value, dict):
            return {key: walk(v) for key,v in value.items() if key not in ['revision_id', 'observed_at']}
        if isinstance(value, list):
            return sorted([walk(v) for v in value], key=lambda v: json.dumps(v,sort_keys=True))
        if isinstance(value, str):
            return ids.get(value,value)
        return value
    normalized = {k:walk(v) for k,v in content.items() if k != 'revision'}
    outcome = {'content': normalized, 'delivery_mode': state['delivery']['readback']['delivery']['mode'],
        'delivery_status': state['delivery']['delivered']['status'], 'target': s.target,
        'product_files': {name:hashlib.sha256((s.root/name).read_bytes()).hexdigest() for name in ['count.py','test_count.py']},
        'schema_by_phase': {r['phase']:r['public_phase_schema_sha256'] for r in state['phase_history']},
        'command_outcome': state['vfy_results']['command']['outcome'],
        'original_attachment_sha256':state['source_readback']['sha256']}
    dump(s.case/'normalized-result.json',outcome)
    return outcome


def main():
    if len(sys.argv) > 1:
        mode, phase = sys.argv[1:]
        s,state = load(mode)
        stage(s,state,phase)
        return 0
    manifest=json.loads((PLUGIN/'install-manifest.json').read_text())
    assert manifest['source_head']=='495177acf777251d378652e2a50e47a1b5c4c41a' and not manifest['source_dirty']
    assert manifest['package_digest']=='a3ecb85d9286fe61b80f98882da4e4f6b91ca33aa25616401d0b043967f9a310'
    for name,sha in manifest['files'].items(): assert hashlib.sha256((PLUGIN/name).read_bytes()).hexdigest()==sha
    dump(BASE/'verified-package.json',manifest)
    result={'status':'running','source_head':manifest['source_head'],'source_dirty':False,'package_digest':manifest['package_digest'],
            'kind':'deterministic public CLI entry equivalence and source dependency fixture; not a business/native Skill certification'}
    try:
        s,state=setup('continuous')
        for phase in PHASES: stage(s,state,phase)
        continuous=normalize(s,state)
        setup('staged')
        for phase in PHASES:
            proc=subprocess.run([str(ac.PYTHON),'-B',str(Path(__file__).resolve()),'staged',phase],capture_output=True,text=True)
            (BASE/'staged'/('driver-'+phase+'.stdout.log')).write_text(proc.stdout)
            (BASE/'staged'/('driver-'+phase+'.stderr.log')).write_text(proc.stderr)
            dump(BASE/'staged'/('driver-'+phase+'.json'),{'phase':phase,'exit_code':proc.returncode})
            assert proc.returncode==0,proc.stderr or proc.stdout
        s,state=load('staged')
        staged=normalize(s,state)
        assert continuous==staged
        result.update(status='verified',equivalent=True,normalization='Generated stable IDs mapped by public receipt client-key role; revision_id and observed_at excluded; content/relationships/criteria/methods/phases/delivery/file bytes compared.',
            phase_counts={'continuous':6,'staged':6},source_readback=state['source_readback'],source_does_not_generate_dependencies=True,
            comparison_sha256=hashlib.sha256(json.dumps(staged,sort_keys=True).encode()).hexdigest())
    except Exception as exc:
        result.update(status='failed',exception=str(exc),traceback=traceback.format_exc());print(result['traceback'])
    dump(BASE/'RESULT.json',result)
    print(json.dumps({'status':result['status']}),flush=True)
    return int(result['status']!='verified')


if __name__=='__main__': raise SystemExit(main())
