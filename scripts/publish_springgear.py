"""Archive only an independently verified, completed SpringGear experiment.

Original evidence bytes remain unchanged. This publisher cannot create Gate,
Claim, Method results or authority records, and does not declare production use.
"""
from pathlib import Path, PurePosixPath
import argparse,hashlib,json,re,shutil,sys,tarfile
p=argparse.ArgumentParser()
for name in ('evidence','destination','run-id','runtime-sha'):p.add_argument('--'+name,required=True)
a=p.parse_args();assert not sys.flags.optimize
assert re.fullmatch(r'[0-9]+',a.run_id) and re.fullmatch(r'[0-9a-f]{40}',a.runtime_sha)
root=Path(a.evidence).resolve(strict=True);run=root/'run';dest=Path(a.destination)/('SPRINGGEAR-'+a.run_id)
assert not dest.exists(),'Do not overwrite an archived execution'
load=lambda p:json.loads(p.read_text())
cp=load(run/'checkpoint.json');status=load(run/'status.json');closed=load(run/'rls-closed.json')
assert cp['source_sha']==a.runtime_sha==(root/'runtime-source.sha').read_text().strip()
assert (root/'upstream-source.sha').read_text().strip()=='e855096ff19dcdb303dc4250ba19c30acd743ac7'
assert not cp.get('pending') and status['ok'] and not status['errors']
assert status['effective_write_policy']=='deny' and status['next_action']['code']=='LIFECYCLE_COMPLETE'
projection=status['projection'];assert not projection['blockers']
claims=projection['current_claims'];assert len(claims)==2
assert all(c['completed'] and c['claim_state']=='completed' for c in claims)
rls=projection['rls_projection']
assert rls['revision_state']=='frozen' and rls['artifact_gate']=='pass'
assert rls['release_conclusion']=='success' and not rls['effect_uncertain'] and not rls['issue_references'] and rls['follow_up']=='none'
assert closed['artifact_gate']=='pass' and closed['release_conclusion']=='success'
phases=('CTX','REQ','DSN','PLN','IMP-1','IMP-2','VFY','RLS')
for phase in phases:
    directory=run/'artifacts'/phase;identity=load(directory/'identity.json')
    assert identity['reference']==cp['stages'][phase]
    assert identity['revision_state']=='frozen' and identity['status']=='ready'
    assert identity['primary_sha256']=='sha256:'+hashlib.sha256((directory/'primary.md').read_bytes()).hexdigest()
    for member in load(directory/'manifest.json')['local_members']:
        path=directory/'members'/member['canonical_name']
        path.resolve(strict=True).relative_to((directory/'members').resolve())
        assert member['sha256']=='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
actual_source={p.relative_to(root/'product-source').as_posix():p.read_bytes() for p in (root/'product-source').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
snapshot=load(run/'artifacts/IMP-2/members/snapshots/result-res-001.json')
assert {v['path']:bytes.fromhex(v['content_hex']) for v in snapshot['entries']}==actual_source,'Published product must match the terminal immutable IMP result'
# Compare the whole preserved upstream; only the declared migration files may differ.
baseline={}
with tarfile.open(root/'authored-inputs.tar.gz','r:gz') as archive:
    for item in archive:
        path=PurePosixPath(item.name)
        if item.isfile() and path.parts[:2]==('springgear-inputs','baseline'):
            assert '..' not in path.parts and item.size<4*1024*1024
            relative=PurePosixPath(*path.parts[2:]).as_posix();assert relative not in baseline
            baseline[relative]=archive.extractfile(item).read()
assert baseline and set(baseline)<=set(actual_source)
changed={name for name,body in baseline.items() if actual_source[name]!=body}
added=set(actual_source)-set(baseline)
assert changed=={'pom.xml','springgear-parent/pom.xml'}
assert added=={'springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java','JDK21-MIGRATION.md'}
assert all(actual_source[name]==body for name,body in baseline.items() if name.endswith('.java'))
state=load(run/'artifacts/VFY/members/vfy-state.json')
assert state['product_result']=='pass' and not state['early_stop'] and not state['returns'] and not state['open_items'] and not state['exceptions']
assert all(x['result']=='pass' for x in state['method_results'])
assert all(x['conclusion']=='pass' for x in state['fixed_conclusions'])
observed=load(run/'artifacts/VFY/members/vfy-evidence-001.json')['observed']
assert observed['exit_code']==0 and not observed['timed_out']
assert observed['containment']=='os-sandbox' and observed['network']=='disabled'
assert observed['source_before']==observed['source_after']
text=actual_source['springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java'].decode()
expected=set(re.findall(r'@Test\s+(?:public\s+)?void\s+(\w+)\s*\(',text))
log=observed['stdout']+'\n'+observed['stderr']
executed=re.findall(r'^SDLC_EXECUTED (\w+)\s*$',log,re.M)
assert len(expected)==10 and len(executed)==len(set(executed))==10 and set(executed)==expected
assert re.search(r'Tests run:\s*10, Failures:\s*0, Errors:\s*0, Skipped:\s*0',log) and 'BUILD SUCCESS' in log
# IMP must actually package the current reactor, not only VFY test it later.
imp_check=load(run/'artifacts/IMP-2/members/evidence/evd-chk-002.json')
assert imp_check['result']=='pass' and imp_check['exit_code']==0
assert imp_check['executed_command']==['mvn','-o','verify'] and 'BUILD SUCCESS' in imp_check['stdout']

def copy_tree(source,target):
    for path in source.rglob('*'):
        assert not path.is_symlink()
        if path.is_file():
            assert path.stat().st_size<4*1024*1024
            relative=path.relative_to(source)
            if '__pycache__' in relative.parts or path.suffix=='.pyc':continue
            out=target/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
copy_tree(run,dest/'evidence');copy_tree(root/'product-source',dest/'source')
for name in ('runtime-source.sha','test-source.sha','upstream-source.sha','runtime-files.json','environment.txt','replay.log','dependency-preparation.log','product.patch'):
    shutil.copyfile(root/name,dest/name)
(dest/'scope-diff.json').write_text(json.dumps({'upstream_sha':(root/'upstream-source.sha').read_text().strip(),'modified':sorted(changed),'added':sorted(added),'all_upstream_java_unchanged':True},indent=2)+'\n')
rows='\n'.join(f'| {ph} | `{cp["stages"][ph]}` | [完整正文](evidence/artifacts/{ph}/primary.md) |' for ph in phases)
(dest/'README.md').write_text(f'''# SpringGear JDK 21 真实需求闭环

状态：**CLOSED — Runtime 全流程与本地 Sandbox 范围**。

- 被测Runtime：`{a.runtime_sha}`。
- 原项目：`ousui/springgear@e855096ff19dcdb303dc4250ba19c30acd743ac7`，原许可证及公共Java源码保留。
- 实际运行：https://github.com/ousui/test-sdlc/actions/runs/{a.run_id}
- 两个有依赖的IMP完成：构建适配→测试与文档；正式VFY重新验证当前终态结果。
- JDK21、class major65、上下文和流水线行为：**10项实际JUnit测试通过，零失败/错误/跳过**。
- IMP中离线Maven verify成功；不是仅修改版本字符串，也不是只重复准备阶段的日志。
- [最终源码](source/)、[迁移说明](source/JDK21-MIGRATION.md)、[范围差异](scope-diff.json)、[最终Status](evidence/status.json)、[RLS结果](evidence/rls-closed.json)。

| 阶段 | 准确Artifact | 产物 |
|---|---|---|
{rows}

## 范围与证据边界

只验证原有build/parent/core/bom四模块；禁用历史扩展模块不算通过，不要求Java8二进制兼容，不迁移到Spring7，不操作SpringGear上游分支，不部署至Maven仓库或生产环境。

AI编写需求与候选实现，正式Runtime CLIs顺序执行并保留完整原始输入输出；不声称原生Codex发现/安装认证。客观合规确认由独立进程读回重算，不冒称独立AI语义审查。RLS只验证现有本地Sandbox版本契约，不等于实际安装或部署Java库。

原始恢复包和源bundle保留在此运行附件中30天。此目录保留完整可读产物、成员、确认依据、源码和哈希清单；固定输入可用于干净重放。
''')
manifest={p.relative_to(dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file()}
(dest/'SHA256SUMS.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(json.dumps({'case':'springgear-jdk21','status':'CLOSED','tests':len(expected),'runtime_sha':a.runtime_sha,'output':str(dest)}))
