import hashlib,json,os,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
LAB=OUT.parents[1]
PACKAGE=Path('/Users/shuaiw/Workspace/goedge.cloud/test-sdlc/.local-runs/sdlc-v2/installed/final-v1')
CLI=PACKAGE/'scripts/sdlc.py'
PYTHON=Path('/Users/shuaiw/.local/share/mise/installs/python/3.11.15/bin/python3')

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def command(argv,cwd,label,evidence):
    p=subprocess.run(argv,cwd=cwd,text=True,capture_output=True)
    save(evidence/(label+'.json'),{'argv':[str(v) for v in argv],'cwd':str(cwd),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    assert p.returncode==0,(argv,p.stdout,p.stderr)
    return p.stdout

class Session:
    def __init__(self,root,evidence):
        self.root=Path(root);self.evidence=Path(evidence);self.evidence.mkdir(parents=True,exist_ok=True)
        self.bindings={};self.n=0
    def request(self,command,payload=None,**extra):
        return {'api_version':'2','command':command,'payload':payload or {},**self.bindings,**extra}
    def record(self,request,result):
        self.n+=1
        stem=self.evidence/f'{self.n:03}-{request["command"]}'
        save(Path(str(stem)+'.request.json'),request)
        Path(str(stem)+'.stdout.json').write_text(result.stdout)
        Path(str(stem)+'.stderr.txt').write_text(result.stderr)
        save(Path(str(stem)+'.process.json'), {'exit_code': result.returncode, 'argv': result.args})
        return json.loads(result.stdout)
    def send(self,command,payload=None,**extra):
        request=self.request(command,payload,**extra)
        p=subprocess.run([str(PYTHON),'-B',str(CLI),'--root',str(self.root)],input=json.dumps(request),text=True,capture_output=True)
        r=self.record(request,p)
        expected=0 if r['ok'] else 2 if r['status'] in {'invalid_input','conflict'} else 3 if r['status'] in {'blocked','needs_input','needs_work','unknown'} else 4
        assert p.returncode==expected,(p.returncode,r)
        return r
    def ok(self,command,payload=None,**extra):
        r=self.send(command,payload,**extra)
        assert r['ok'],r
        return r['data']
    def initialize(self,name):
        inspected=self.send('workspace.inspect')
        assert inspected['errors'][0]['code']=='STORE_NOT_FOUND',inspected
        return self.ok('workspace.init',{'name':name})
    def seed_change(self,name):
        ctx=self.ok('context.commit',{'summary':name,'entries':[{'kind':'fact','name':'fixture-origin','content':name}]})
        r=self.send('change.create',{'context_id':ctx['context_id'],'slug':name,'title':name,'summary':'Isolated acceptance fixture',
            'goal':'Verify '+name,'in_scope':'Disposable local fixture only','out_of_scope':'Host settings and remotes','delivery_mode':'local',
            'delivery_target':'.sdlc/exports/'+name,'original_text':'Fixture identity '+name,
            'authorizations':[{'action':a,'target':'main' if a!='package_local' else '.sdlc/exports/'+name,'issued_by':'user','basis_text':'Explicit parent task authorization for disposable local acceptance fixtures'} for a in ['edit_local','run_check','package_local']]})
        assert r['ok'],r
        self.bindings={'change_id':r['data']['change_id'],'run_id':r['run_id']}
        return r['data']
    def submit(self,phase,operations):
        p=self.ok('phase.prepare',{'phase':phase})
        return self.ok('phase.submit',{'phase':phase,'revision_id':p['content']['revision']['revision_id'],'operations':operations},expected_generation=p['generation'])
    def complete(self,phase):
        p=self.ok('phase.prepare',{'phase':phase})
        return self.ok('phase.complete',{'phase':phase,'revision_id':p['content']['revision']['revision_id']},expected_generation=p['generation'])

def snapshot_package():
    manifest=json.loads((PACKAGE/'install-manifest.json').read_text())
    actual={p:hashlib.sha256((PACKAGE/p).read_bytes()).hexdigest() for p in manifest['files']}
    assert actual==manifest['files'],'Frozen package file mismatch'
    save(OUT/'package-baseline.json',{'manifest':manifest,'verified_files':len(actual),'python':str(PYTHON),'package':str(PACKAGE)})
    command([str(PYTHON),'-B',str(CLI),'--contract'],OUT,'public-contract',OUT)
    command([str(PYTHON),'-B',str(CLI),'--version'],OUT,'public-version',OUT)

if __name__=='__main__':snapshot_package()
