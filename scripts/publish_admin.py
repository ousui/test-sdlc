"""Validate completed exported evidence before copying readable projections.

This is experiment delivery tooling, not an ArtifactStore or a PASS producer.
It does not modify original evidence, runtime source or formal state.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil

p = argparse.ArgumentParser()
p.add_argument('--evidence', required=True)
p.add_argument('--destination', required=True)
p.add_argument('--run-id', required=True)
p.add_argument('--runtime-sha', required=True)
a = p.parse_args()
assert re.fullmatch(r'[0-9]+', a.run_id)
assert re.fullmatch(r'[0-9a-f]{40}', a.runtime_sha)
source = Path(a.evidence).resolve(strict=True)
run = source / 'run'
dest = Path(a.destination) / ('ADMIN-' + a.run_id)
assert not dest.exists(), 'Never overwrite an archived run'
load = lambda f: json.loads(f.read_text())
checkpoint = load(run / 'checkpoint.json')
assert checkpoint['source_sha'] == a.runtime_sha == (source/'runtime-source.sha').read_text().strip()
assert not checkpoint.get('pending'), 'Pending phases are not closed'
phases = ('CTX','REQ','DSN','PLN','IMP-1','IMP-2','VFY','RLS')
assert set(phases) <= set(checkpoint['stages'])
status = load(run/'status.json')
assert status['ok'] and not status['errors'] and status['effective_write_policy'] == 'deny'
assert status['next_action']['code'] == 'LIFECYCLE_COMPLETE'
projection = status['projection']
assert not projection['blockers']
assert len(projection['current_claims']) == 2
assert all(c['completed'] and c['claim_state']=='completed' for c in projection['current_claims'])
rls = projection['rls_projection']
assert rls['revision_state']=='frozen' and rls['artifact_gate']=='pass'
assert rls['release_conclusion']=='success' and not rls['effect_uncertain']
assert not rls['issue_references'] and rls['follow_up']=='none'
closed = load(run/'rls-closed.json')
assert closed['artifact_gate']=='pass' and closed['release_conclusion']=='success'
for phase in phases:
    directory = run/'artifacts'/phase
    identity = load(directory/'identity.json')
    assert identity['reference']==checkpoint['stages'][phase]
    assert identity['revision_state']=='frozen' and identity['status']=='ready'
    assert identity['primary_sha256']=='sha256:'+hashlib.sha256((directory/'primary.md').read_bytes()).hexdigest()
    for member in load(directory/'manifest.json')['local_members']:
        path = directory/'members'/member['canonical_name']
        path.resolve(strict=True).relative_to((directory/'members').resolve())
        assert member['sha256']=='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
vfy = load(run/'artifacts/VFY/members/vfy-state.json')
assert vfy['product_result']=='pass' and not vfy['early_stop']
assert not vfy['returns'] and not vfy['open_items'] and not vfy['exceptions']
assert all(row['result']=='pass' for row in vfy['method_results'])
assert all(row['conclusion']=='pass' for row in vfy['fixed_conclusions'])
evidence = load(run/'artifacts/VFY/members/vfy-evidence-001.json')
observed = evidence['observed']
assert evidence['result']=='pass' and observed['exit_code']==0 and not observed['timed_out']
assert observed['containment']=='os-sandbox' and observed['network']=='disabled'
assert observed['source_before']==observed['source_after']
tree = ast.parse((source/'product-source/test_enabled.py').read_text())
expected = {n.name for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
log = observed['stdout']+'\n'+observed['stderr']
actual = re.findall(r'^(test_\w+) \([^\n]+\) \.\.\. ok$',log,re.M)
assert expected and len(actual)==len(set(actual)) and set(actual)==expected
assert re.search(rf'Ran {len(expected)} tests? in ',log) and '\nOK\n' in log
assert len(expected)==13, 'Do not silently remove the declared account scenarios'

def copy_tree(src, dst):
    for path in src.rglob('*'):
        assert not path.is_symlink(), 'Symlink publication is not permitted'
        rel = path.relative_to(src)
        if '__pycache__' in rel.parts or path.suffix in {'.pyc','.sqlite','.sqlite3','.db'}:
            continue
        if path.is_file():
            assert path.stat().st_size < 4*1024*1024
            target = dst/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)

# Publish original bytes, not a reconstructed or reformatted authority.
copy_tree(run,dest/'evidence')
copy_tree(source/'product-source',dest/'source')
for name in ('runtime-source.sha','test-source.sha','environment.txt','runtime-files.json','replay.log'):
    shutil.copyfile(source/name,dest/name)
rows = '\n'.join(f'| {phase} | `{checkpoint["stages"][phase]}` | [完整正文](evidence/artifacts/{phase}/primary.md) |' for phase in phases)
text = f'''# Admin 真实需求闭环\n\n状态：**CLOSED — Runtime 全流程与本地 Sandbox 范围**。\n\n- 被测源码：`{a.runtime_sha}`。\n- 执行记录：https://github.com/ousui/test-sdlc/actions/runs/{a.run_id}\n- 原始需求：既有轻量 Admin 的用户启用/禁用、后台筛选修改、即时会话撤销和旧库兼容。\n- 实际功能测试：{len(expected)} 项，零失败/错误/跳过；VFY 在 OS 隔离环境重新执行。\n- [最终源码](source/)、[完整状态](evidence/status.json)、[RLS 结果](evidence/rls-closed.json)、[原始调用与返回](evidence/calls/)。\n\n| 阶段 | 准确 Artifact | 产物 |\n|---|---|---|\n{rows}\n\n## 证据边界\n\nAI 按 Skill 编写的真实场景经过正式 Runtime CLIs 顺序重放；不是 Codex 原生 Discovery 认证。客观合规确认由独立进程读回和重算，不冒称独立 AI 或人工语义审查。业务判断依赖明确验收标准和真实功能测试。\n\nRLS 执行的是已支持的本地 Sandbox 版本状态转换；**不是 Flask 应用的生产部署或发布包安装证明**。上游示例的简化权限模型保留，本轮不宣称具备生产 RBAC。\n\n完整恢复包 `recovery.tar.gz` 随该 Actions 运行附件保留30天；本目录永久保留可读产物、成员、确认依据、代码和命令证据。新的 clean replay 可从仓库固定输入重建独立运行。\n'''
(dest/'README.md').write_text(text)
manifest = {path.relative_to(dest).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(dest.rglob('*')) if path.is_file()}
(dest/'SHA256SUMS.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(json.dumps({'case':'admin','runtime_sha':a.runtime_sha,'status':'CLOSED','functional_tests':len(expected),'output':str(dest)},ensure_ascii=False))
