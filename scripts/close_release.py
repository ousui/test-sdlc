"""Host orchestration of the real RLS CLI and separate artifact review.

The only release effect is the existing isolated Sandbox version contract.
This never asserts production deployment of the application.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile,uuid,shutil
p=argparse.ArgumentParser()
for name in ('runtime','work','output','vfy','executor'):p.add_argument('--'+name,required=True)
a=p.parse_args();runtime=Path(a.runtime).resolve();work=Path(a.work).resolve();out=Path(a.output).resolve()
sys.path[:0]=[str(runtime),str(runtime/'skills/sdlc-600-rls/scripts')]
from rls_service import RlsService
from rls_target import SandboxReleaseTarget
from rls_trusted_effect import TrustedEffectRecords
service=RlsService(work);checkpoint=out/'release-checkpoint.json'
state=json.loads(checkpoint.read_text()) if checkpoint.exists() else {'sequence':0,'sandbox_root':str(Path(tempfile.gettempdir())/('sdlc-release-'+uuid.uuid4().hex)),'target':'local-validation','release_reference':'admin-'+hashlib.sha256(a.vfy.encode()).hexdigest()[:16]}
def save():checkpoint.write_text(json.dumps(state,indent=2)+'\n')
save();target=SandboxReleaseTarget(state['sandbox_root'],state['target'])
def call(operation,body,inputs=(),reference=None):
 state['sequence']+=1;save();label=f'rls-{state["sequence"]:03d}-{operation}'
 command=[sys.executable,'-B',str(runtime/'skills/sdlc-600-rls/scripts/runtime.py'),operation,'-p',str(work),'-f','json','-w','auto']
 if reference:command+=['-r',reference]
 for value in inputs:command+=['-i',value]
 body={**body,'sandbox_root':state['sandbox_root'],'target':state['target']}
 (out/(label+'.request.json')).write_text(json.dumps(body,indent=2)+'\n')
 proc=subprocess.run(command,input=json.dumps(body),text=True,capture_output=True,cwd=work,timeout=120)
 (out/(label+'.stdout')).write_text(proc.stdout);(out/(label+'.stderr')).write_text(proc.stderr)
 result=json.loads(proc.stdout);assert result.get('ok'),result
 return result
if not state.get('reference'):
 result=call('create',{'release_reference':state['release_reference']},inputs=[a.vfy])
 state['reference']=result['artifact']['artifact']['reference'];save()
reference=state['reference'];actual,_=service.read(reference)
if actual['artifact']['revision_state']!='frozen':
 pending=[row['id'] for row in actual['release_items'] if row['result']=='pending']
 if pending:
  basis=work/'.sdlc/authority/work-authorization.md';assert basis.is_file()
  grant=TrustedEffectRecords(work).grant(actual,pending,authorizer_identity='web-realflow-isolated-host',approved=True)
  (out/'sandbox-host-authorization.json').write_text(json.dumps({'basis_sha256':hashlib.sha256(basis.read_bytes()).hexdigest(),'scope':'only this exact local Sandbox target and pending RLI set','grant':grant},indent=2)+'\n')
  call('execute',{'items':pending,'effect_authorization':grant},reference=reference)
 actual,_=service.read(reference)
 pending=[row['id'] for row in actual['confirmations'] if row['result']=='pending']
 if pending:call('confirm',{'items':pending},reference=reference)
 actual,_=service.read(reference)
 assert all(row['result']=='success' for row in actual['release_items']),actual
 assert all(row['result']=='pass' for row in actual['confirmations']),actual
 expected=service.confirmation_requirements(reference,target)
 executors={row['executor'] for row in actual['release_items']};assert len(executors)==1
 confpath=out/'release-review.json'
 proc=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('review_artifact.py')),'--runtime',str(runtime),'--project',str(work),'--reference',reference,'--executor',next(iter(executors)),'--out',str(confpath)],text=True,capture_output=True,timeout=60)
 assert proc.returncode==0,proc.stderr
 confirmation=json.loads(confpath.read_text())
 assert all(confirmation[k]==value for k,value in expected.items()),(confirmation,expected)
 call('finalize',{'final_confirmation':confirmation},reference=reference)
check=call('check',{},reference=reference)
actual,_=service.read(reference)
assert actual['artifact']['revision_state']=='frozen' and actual['artifact_gate']=='pass' and actual['release_conclusion']=='success',actual
snapshot=target.snapshot();assert snapshot['version']==state['release_reference']
(out/'sandbox-target-snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
shutil.copytree(target.root,out/'sandbox-target',dirs_exist_ok=True)
(out/'rls-closed.json').write_text(json.dumps({'reference':reference,'artifact_gate':actual['artifact_gate'],'release_conclusion':actual['release_conclusion'],'target_snapshot':snapshot,'scope':'local Sandbox contract; not deployment of the Flask application'},indent=2)+'\n')
print(json.dumps({'reference':reference,'gate':'pass','release_conclusion':'success'}))
