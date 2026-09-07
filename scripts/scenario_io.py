"""Shared test-side transport for independently authored real scenarios.

Not an installed Skill or domain implementation. Every phase executes its public
CLI in a separate process. Canonical state is read only via ArtifactStore APIs.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys


class ScenarioIO:
    def __init__(self, runtime, work, output, executor, boundary):
        self.runtime=Path(runtime).resolve(); self.work=Path(work).resolve()
        self.out=Path(output).resolve(); self.executor=executor; self.boundary=boundary
        self.out.mkdir(parents=True,exist_ok=True)
        sys.path.insert(0,str(self.runtime))
        from packages.sdlc_artifact_store import ArtifactStore
        self.store_class=ArtifactStore
        self.statefile=self.out/'checkpoint.json'
        self.state=json.loads(self.statefile.read_text()) if self.statefile.exists() else {
            'stages':{},'sequence':0,'pending':{},'source_sha':os.environ['SDLC_SOURCE_SHA']}
        assert self.state['source_sha']==os.environ['SDLC_SOURCE_SHA'], 'A replay may not silently change runtime source'

    def save(self):
        self.statefile.write_text(json.dumps(self.state,ensure_ascii=False,indent=2)+'\n')

    @staticmethod
    def reference(result):
        artifact=result.get('artifact'); assert artifact,result
        return artifact.get('reference') or f"{artifact['id']}@{artifact['revision']}"

    def read(self,reference):
        identity,revision=reference.split('@')
        return self.store_class.open_read_only(self.work).read_revision(identity,int(revision))

    def export(self,reference,label):
        stored=self.read(reference); d=self.out/'artifacts'/label; d.mkdir(parents=True,exist_ok=True)
        (d/'primary.md').write_bytes(stored.payload.primary_blob)
        (d/'manifest.json').write_bytes(stored.payload.manifest.raw_bytes)
        for member in stored.payload.members:
            p=d/'members'/member.canonical_name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(member.raw_bytes)
        (d/'identity.json').write_text(json.dumps({'reference':reference,'revision_state':stored.control.state,
            'status':stored.payload.artifact_status,'primary_sha256':stored.payload.primary_sha256},indent=2)+'\n')
        shutil.copytree(self.work/'.sdlc/authority',self.out/'authority',dirs_exist_ok=True)
        return stored

    def invoke(self,phase,operation,body,reference=None,inputs=(),binding=None):
        self.state['sequence']+=1;self.save();tag=f"{self.state['sequence']:03d}-{phase}-{operation}"
        base=self.runtime/f'skills/sdlc-{phase}/scripts'
        env=os.environ.copy();env['SDLC_EXECUTOR_TOKEN']=self.executor
        if phase in ('000-ctx','100-req'):
            request={'contract':'sdlc-ai-spec/runtime-invocation/v1','operation':operation,
                'project_root':str(self.work),'artifact_reference':reference,'inputs':body,
                'confirmations':[{'type':'write' if phase=='000-ctx' else 'artifact_store_write','approved':True}],
                'options':{'dry_run':False}}
            if phase=='000-ctx':
                request['confirmations'].append({'type':'project_boundary','value':self.boundary,'authority_reference':'EVD-001'})
                request['options']['prepare_confirmation']=True
                if body.get('final_confirmation'):
                    request['confirmations'].append(body['final_confirmation'])
                    request['inputs']={k:v for k,v in body.items() if k!='final_confirmation'}
            command=[sys.executable,'-B',str(base/('runtime_final.py' if phase=='100-req' else 'runtime.py'))]
        else:
            request={'inputs':body,'confirmations':[{'type':'artifact_store_write','approved':True}]} if phase in ('200-dsn','300-pln') else body
            command=[sys.executable,'-B',str(base/'runtime.py'),operation,'-p',str(self.work),'-f','json','-d','model','-w','auto']
            if reference:command+=['-r',reference]
            for item in inputs:command+=['-i',item]
            if binding:command+=['--binding',binding,'--owner',self.executor]
        directory=self.out/'calls';directory.mkdir(exist_ok=True)
        (directory/(tag+'.request.json')).write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
        proc=subprocess.run(command,input=json.dumps(request,ensure_ascii=False),text=True,capture_output=True,cwd=self.work,env=env,timeout=600)
        (directory/(tag+'.stdout')).write_text(proc.stdout);(directory/(tag+'.stderr')).write_text(proc.stderr)
        result=json.loads(proc.stdout)
        (directory/(tag+'.result.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(tag,json.dumps({k:result[k] for k in ('ok','artifact','gate','product_result','artifact_gate','errors') if k in result},ensure_ascii=False),flush=True)
        if result.get('artifact'):self.export(self.reference(result),phase.split('-')[1].upper()+'-'+str(self.state['sequence']))
        return result

    def review(self,reference,result):
        dest=self.out/'review.json'
        proc=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('review_artifact.py')),
            '--runtime',str(self.runtime),'--project',str(self.work),'--reference',reference,
            '--executor',self.executor,'--out',str(dest)],text=True,capture_output=True,timeout=90)
        assert proc.returncode==0,proc.stderr
        conf=json.loads(dest.read_text())
        def subject(value):
            if isinstance(value,dict):
                if isinstance(value.get('subject_digest'),str):return value['subject_digest']
                for item in value.values():
                    found=subject(item)
                    if found:return found
            if isinstance(value,list):
                for item in value:
                    found=subject(item)
                    if found:return found
        digest=subject(result)
        if digest:conf['subject_digest']=digest
        return conf

    def complete(self,phase,body,inputs=(),label=None,binding=None):
        label=label or phase.split('-')[1].upper()
        if label in self.state['stages']:
            self.export(self.state['stages'][label],label)
            return self.state['stages'][label]
        pending=self.state['pending'].get(label)
        r=self.invoke(phase,'revise' if pending else 'create',body,reference=pending,inputs=inputs,binding=binding)
        reference=self.reference(r);self.state['pending'][label]=reference;self.save()
        assert not r.get('errors') and r['gate']['result']!='fail',r
        if phase=='000-ctx':
            baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=self.work,text=True).strip()
            body['refresh']={'base_revision':self.read(reference).control.base_revision,
                'observed_at':self.state.setdefault('ctx_observed_at',datetime.now(timezone.utc).isoformat(timespec='seconds')),
                'observation_baseline':baseline,'refresh_reason':'Confirm complete observed project context',
                'effective_change_references':'None','evidence_references':'EVD-001'}
            self.save();r=self.invoke(phase,'revise',body,reference=reference)
            assert not r.get('errors') and r['gate']['result']!='fail',r
        conf=self.review(reference,r);approved=copy.deepcopy(body)
        if phase=='400-imp':approved['inputs']['final_confirmation']=conf
        else:approved['final_confirmation']=conf
        final=self.invoke(phase,'revise',approved,reference=reference,inputs=inputs,binding=binding)
        assert final['ok'] and final['artifact']['revision_state']=='frozen',final
        if phase=='400-imp':
            assert next(w for w in final['warnings'] if w['code']=='IMP_EXECUTION_STATE')['claim_state']=='completed'
        self.state['stages'][label]=reference;self.state['pending'].pop(label,None);self.save();self.export(reference,label)
        return reference

    def verify_and_close(self,plan,terminal,candidate,requirement):
        if 'VFY' not in self.state['stages']:
            pending=self.state['pending'].get('VFY')
            if not pending:
                r=self.invoke('500-vfy','create',{'persist':True,'run_automated':False,'candidate':candidate},inputs=[plan,terminal])
                assert r.get('ok'),r
                pending=self.reference(r);self.state['pending']['VFY']=pending;self.save()
            r=self.invoke('500-vfy','run',{'persist':True,'allow_commands':True,'finalize':False},reference=pending)
            assert r.get('ok') and r['product_result']=='pass',r
            sys.path.insert(0,str(self.runtime/'skills/sdlc-500-vfy/scripts'))
            from vfy_handler import VfyHandler
            from vfy_builder import confirmation_subject_digest
            actual=VfyHandler(self.work).check(reference=pending)['state']
            expected=VfyHandler(self.work).confirmation_requirements(actual)
            conf=self.review(pending,r);conf['subject_digest']=confirmation_subject_digest(actual)
            assert all(conf[k]==v for k,v in expected.items())
            r=self.invoke('500-vfy','run',{'persist':True,'allow_commands':True,'finalize':True,'confirmation':conf},reference=pending)
            assert r.get('ok') and r['artifact']['revision_state']=='frozen' and r['product_result']=='pass' and r['rls_ready'],r
            self.state['stages']['VFY']=pending;self.state['pending'].pop('VFY',None);self.save();self.export(pending,'VFY')
        proc=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('close_release.py')),
            '--runtime',str(self.runtime),'--work',str(self.work),'--output',str(self.out),
            '--vfy',self.state['stages']['VFY'],'--executor',self.executor],text=True,capture_output=True,timeout=300)
        (self.out/'rls-adapter.stdout').write_text(proc.stdout);(self.out/'rls-adapter.stderr').write_text(proc.stderr)
        assert proc.returncode==0,proc.stderr
        closed=json.loads((self.out/'rls-closed.json').read_text());reference=closed['reference']
        self.state['stages']['RLS']=reference;self.save();self.export(reference,'RLS')
        proc=subprocess.run([sys.executable,'-B',str(self.runtime/'skills/sdlc-status/scripts/runtime.py'),
            'inspect','-p',str(self.work),'-r',requirement,'-f','json','-w','deny'],text=True,capture_output=True,timeout=90)
        (self.out/'status.json').write_text(proc.stdout);(self.out/'status.stderr').write_text(proc.stderr)
        assert proc.returncode==0,proc.stderr
        status=json.loads(proc.stdout)
        assert status['ok'] and status['next_action']['code']=='LIFECYCLE_COMPLETE' and not status['projection']['blockers'],status
        print('LIFECYCLE_COMPLETE',reference,flush=True)
