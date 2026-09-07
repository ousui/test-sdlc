"""Verify actual completed evidence and copy original readable projections."""
from pathlib import Path
import argparse,hashlib,json,re,shutil,sys
p=argparse.ArgumentParser()
for name in ('evidence','destination','run-id','runtime-sha'):p.add_argument('--'+name,required=True)
a=p.parse_args();assert not sys.flags.optimize
assert re.fullmatch(r'[0-9]+',a.run_id) and re.fullmatch(r'[0-9a-f]{40}',a.runtime_sha)
root=Path(a.evidence).resolve(strict=True);run=root/'run';dest=Path(a.destination)/('FANSITE-'+a.run_id)
assert not dest.exists(),'Never overwrite an archived execution'
load=lambda p:json.loads(p.read_text())
cp=load(run/'checkpoint.json');status=load(run/'status.json');closed=load(run/'rls-closed.json')
assert cp['source_sha']==a.runtime_sha==(root/'runtime-source.sha').read_text().strip()
assert not cp.get('pending') and status['ok'] and not status['errors']
assert status['effective_write_policy']=='deny' and status['next_action']['code']=='LIFECYCLE_COMPLETE'
projection=status['projection'];assert not projection['blockers']
assert len(projection['current_claims'])==3
assert all(c['completed'] and c['claim_state']=='completed' for c in projection['current_claims'])
rls=projection['rls_projection']
assert rls['revision_state']=='frozen' and rls['artifact_gate']=='pass'
assert rls['release_conclusion']=='success' and not rls['effect_uncertain'] and not rls['issue_references'] and rls['follow_up']=='none'
assert closed['artifact_gate']=='pass' and closed['release_conclusion']=='success'
phases=('CTX','REQ','DSN','PLN','IMP-1','IMP-2','IMP-3','VFY','RLS')
for phase in phases:
 d=run/'artifacts'/phase;identity=load(d/'identity.json')
 assert identity['reference']==cp['stages'][phase]
 assert identity['revision_state']=='frozen' and identity['status']=='ready'
 assert identity['primary_sha256']=='sha256:'+hashlib.sha256((d/'primary.md').read_bytes()).hexdigest()
 for m in load(d/'manifest.json')['local_members']:
  f=d/'members'/m['canonical_name'];f.resolve(strict=True).relative_to((d/'members').resolve())
  assert m['sha256']=='sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
source={p.relative_to(root/'product-source').as_posix():p.read_bytes() for p in (root/'product-source').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
snapshot=load(run/'artifacts/IMP-3/members/snapshots/result-res-001.json')
assert {v['path']:bytes.fromhex(v['content_hex']) for v in snapshot['entries']}==source,'Archive source differs from current terminal IMP'
state=load(run/'artifacts/VFY/members/vfy-state.json')
assert state['product_result']=='pass' and not state['early_stop'] and not state['returns'] and not state['exceptions']
assert len(state['targets'])==3 and len(state['target_conclusions'])==3
assert all(x['conclusion']=='pass' for x in state['target_conclusions'])
assert all(x['conclusion']=='pass' for x in state['fixed_conclusions'])
evidence=load(run/'artifacts/VFY/members/vfy-evidence-001.json');o=evidence['observed']
assert evidence['result']=='pass' and o['exit_code']==0 and not o['timed_out']
assert not o.get('output_limit_exceeded',False) and o.get('capture_policy_code',0)==0
assert o['containment']=='os-sandbox' and o['network']=='disabled'
assert o['source_before']==o['source_after']
expected=set(re.findall(r'^func\s+(Test\w+)\s*\(',source['site_test.go'].decode(),re.M))
log=o['stdout']+'\n'+o['stderr'];executed=re.findall(r'^--- PASS: (Test\w+) \(',log,re.M)
assert len(expected)==24 and len(executed)==len(set(executed))==24 and set(executed)==expected
assert '\nPASS\n' in log and '--- SKIP:' not in log and '--- FAIL:' not in log
assert o['argv']==['go','test','-count=1','-v','./...']
imp=load(run/'artifacts/IMP-3/members/evidence/evd-chk-001.json')
assert imp['result']=='pass' and imp['exit_code']==0
assert imp['command']==['go','test','./...']
assert re.search(r'^ok\s+example\.invalid/miriam-fansite\s+',imp['stdout'],re.M) and '(cached)' not in imp['stdout']
for name in ('main.go','server.go','store.go','web/index.html','web/app.js','web/style.css','README.md','SOURCE.md','CASE-TRACEABILITY.md','sample_media.py','vendor/modules.txt','vendor/golang.org/x/crypto/LICENSE'):
 assert name in source and source[name]
assert 'jQuery' not in source['web/app.js'].decode()
assert 'innerHTML' not in source['web/app.js'].decode()

def copy_tree(src,dst):
 for f in src.rglob('*'):
  assert not f.is_symlink(),'Symlink publication rejected'
  if f.is_file():
   rel=f.relative_to(src)
   if '__pycache__' in rel.parts or f.suffix=='.pyc':continue
   assert f.stat().st_size<4*1024*1024
   p=dst/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,p)
copy_tree(run,dest/'evidence');copy_tree(root/'product-source',dest/'source')
for name in ('runtime-source.sha','test-source.sha','runtime-files.json','environment.txt','replay.log'):shutil.copyfile(root/name,dest/name)
rows='\n'.join(f'| {ph} | `{cp["stages"][ph]}` | [完整正文](evidence/artifacts/{ph}/primary.md) |' for ph in phases)
(dest/'README.md').write_text(f'''# 杨千嬅非官方粉丝站：真实需求闭环

状态：**CLOSED — Runtime全流程与本地Sandbox范围**。

- 共同被测Runtime：`{a.runtime_sha}`。
- [实际执行](https://github.com/ousui/test-sdlc/actions/runs/{a.run_id})。
- 从空应用脚手架开始；三个有依赖IMP：账户/持久化→HTTP/页面/媒体/后台→测试和说明。
- 实际Go功能测试：**24项，零失败/错误/跳过**；IMP完成无缓存全包检查，VFY再以当前终态源码在OS沙箱逐项执行24项测试，三个VFO均pass。
- [最终网站源码](source/)、[运行说明](source/README.md)、[AC—测试追踪](source/CASE-TRACEABILITY.md)、[最终Status](evidence/status.json)、[RLS结果](evidence/rls-closed.json)。
- 实际工具版本见[环境](environment.txt)，语言下限Go1.23；HTML+原生JavaScript无远端依赖。

| 阶段 | 准确Artifact | 产物 |
|---|---|---|
{rows}

## 可用功能

公开主页、粉丝注册/登录/资料/注销、WAV音乐GET/HEAD/Range试听、发布相册和照片；管理员管理用户状态、主页、音乐与相册的创建/编辑/发布/下架/删除、照片上传和删除。服务端角色/会话/CSRF检查；禁用与重新启用不恢复旧会话；重启保留实体但要求重新登录。真实用例覆盖并发写入、故障一致性、非法输入、草稿直接URL和媒体关联。

运行 `python3 sample_media.py` 生成自产测试音和色块图片，经后台表单上传。没有艺人录音/照片、实际用户数据或源码内管理员凭据。管理员首次设置使用显式环境变量，见README。默认只监听127.0.0.1。

## 准确边界

此证明是AI依照Skill编写正常场景并经正式Runtime CLI顺序执行，不是原生Codex发现/安装或独立AI语义审查；客观合规由独立进程读回重算。UI主观体验不是门禁，功能测试使用真实HTTP Handler和临时本地文件，不冒称浏览器人工验收。

持久化是单进程原子JSON文件，非分布式数据库；媒体为1MiB以内WAV和PNG/JPEG，不构成生产安全或负载认证。RLS执行已有本地Sandbox版本状态，不等于网站生产部署。原始恢复包和源码bundle随该Actions附件保留30天，可读正文/成员/引用/源码及哈希在Git保留。
''')
manifest={f.relative_to(dest).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(dest.rglob('*')) if f.is_file()}
(dest/'SHA256SUMS.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(json.dumps({'case':'fansite','status':'CLOSED','tests':len(expected),'runtime_sha':a.runtime_sha,'output':str(dest)},ensure_ascii=False))
