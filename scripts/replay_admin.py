"""Real Admin scenario driver. Executes bundled phase CLIs; no eval Fixtures.

The AI-authored scenario data is kept outside the installed runtime. Each public
phase entry runs alone, and a separate process performs bounded readback review.
All requests, responses, raw artifacts, members and authority are exported.
"""
from pathlib import Path
import argparse, copy, hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone

p=argparse.ArgumentParser();p.add_argument('--runtime',required=True);p.add_argument('--work',required=True);p.add_argument('--output',required=True);p.add_argument('--until',default='PLN');p.add_argument('--dependencies');p.add_argument('--revise-stage');p.add_argument('--exercise-design-revision',action='store_true');a=p.parse_args()
RUNTIME=Path(a.runtime).resolve();WORK=Path(a.work).resolve();OUT=Path(a.output).resolve();HERE=Path(__file__).resolve().parent;CASE=HERE.parent/'cases/admin';EXECUTOR='web-realflow-admin-executor'
OUT.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(RUNTIME))
from packages.sdlc_artifact_store import ArtifactStore
from packages.sdlc_runtime import parse_canonical_artifact
statefile=OUT/'checkpoint.json';state=json.loads(statefile.read_text()) if statefile.exists() else {'stages':{},'sequence':0,'source_sha':os.environ.get('SDLC_SOURCE_SHA','development-replay-uncommitted')}

def save():statefile.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
def ref(result):
 art=result.get('artifact');assert art,result
 return art.get('reference') or f"{art['id']}@{art['revision']}"
def stored(reference):
 identity,rev=reference.split('@');return ArtifactStore.open_read_only(WORK).read_revision(identity,int(rev))
def export(reference,label):
 s=stored(reference);d=OUT/'artifacts'/label;d.mkdir(parents=True,exist_ok=True)
 (d/'primary.md').write_bytes(s.payload.primary_blob);(d/'manifest.json').write_bytes(s.payload.manifest.raw_bytes)
 for member in s.payload.members:
  q=d/'members'/member.canonical_name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(member.raw_bytes)
 (d/'identity.json').write_text(json.dumps({'reference':reference,'revision_state':s.control.state,'status':s.payload.artifact_status,'primary_sha256':s.payload.primary_sha256},indent=2)+'\n')
 shutil.copytree(WORK/'.sdlc/authority',OUT/'authority',dirs_exist_ok=True)
 return s

def invoke(phase,operation,body,reference=None,inputs=(),binding=None):
 state['sequence']+=1;save();tag=f"{state['sequence']:03d}-{phase}-{operation}";base=RUNTIME/f'skills/sdlc-{phase}/scripts'
 env=os.environ.copy();env['SDLC_EXECUTOR_TOKEN']=EXECUTOR
 if a.dependencies:env['PYTHONPATH']=str(Path(a.dependencies).resolve())
 if phase in ('000-ctx','100-req'):
  request={'contract':'sdlc-ai-spec/runtime-invocation/v1','operation':operation,'project_root':str(WORK),'artifact_reference':reference,'inputs':body,'confirmations':[{'type':'write' if phase=='000-ctx' else 'artifact_store_write','approved':True}],'options':{'dry_run':False}}
  if phase=='000-ctx':
   request['confirmations'].append({'type':'project_boundary','value':BOUNDARY,'authority_reference':'EVD-001'})
   request['options']['prepare_confirmation']=True
   if body.get('final_confirmation'):request['confirmations'].append(body['final_confirmation']);request['inputs']={k:v for k,v in body.items() if k!='final_confirmation'}
  command=[sys.executable,'-B',str(base/('runtime_final.py' if phase=='100-req' else 'runtime.py'))]
 else:
  request={'inputs':body,'confirmations':[{'type':'artifact_store_write','approved':True}]} if phase in ('200-dsn','300-pln') else body;command=[sys.executable,'-B',str(base/'runtime.py'),operation,'-p',str(WORK),'-f','json','-d','model','-w','auto']
  if reference:command+=['-r',reference]
  for item in inputs:command+=['-i',item]
  if binding:command+=['--binding',binding,'--owner',EXECUTOR]
 (OUT/'calls').mkdir(exist_ok=True);(OUT/'calls'/f'{tag}.request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
 run=subprocess.run(command,input=json.dumps(request,ensure_ascii=False),text=True,capture_output=True,cwd=WORK,env=env,timeout=180)
 (OUT/'calls'/f'{tag}.stdout').write_text(run.stdout);(OUT/'calls'/f'{tag}.stderr').write_text(run.stderr)
 result=json.loads(run.stdout);(OUT/'calls'/f'{tag}.result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(tag,json.dumps(result,ensure_ascii=False)[:1500],flush=True)
 if result.get('artifact'):export(ref(result),phase.split('-')[1].upper()+'-'+str(state['sequence']))
 return result

def review(reference,result):
 dest=OUT/'review.json'
 r=subprocess.run([sys.executable,'-B',str(HERE/'review_artifact.py'),'--runtime',str(RUNTIME),'--project',str(WORK),'--reference',reference,'--executor',EXECUTOR,'--out',str(dest)],text=True,capture_output=True,timeout=60)
 if r.returncode:raise RuntimeError(r.stderr)
 conf=json.loads(dest.read_text())
 # Subject is the exact normalized candidate binding published by the phase.
 def find(v):
  if isinstance(v,dict):
   if isinstance(v.get('subject_digest'),str):return v['subject_digest']
   for x in v.values():
    hit=find(x)
    if hit:return hit
  if isinstance(v,list):
   for x in v:
    hit=find(x)
    if hit:return hit
 subject=find(result)
 if subject:conf['subject_digest']=subject
 return conf

def finish(phase,body,inputs=()):
 label=phase.split('-')[1].upper()
 if label in state['stages'] and a.revise_stage!=label:return state['stages'][label]
 if label in state['stages'] and a.revise_stage==label:
  state.setdefault('history',{}).setdefault(label,[]).append(state['stages'][label])
  state.setdefault('pending',{})[label]=state['stages'].pop(label);save()
 pending=state.get('pending',{}).get(label)
 if pending:
  if phase=='000-ctx':
   body['refresh']={'base_revision':stored(pending).control.base_revision,'observed_at':state['ctx_observed_at'],'observation_baseline':baseline,'refresh_reason':'Confirm complete observed context','effective_change_references':'None','evidence_references':'EVD-001'}
  r=invoke(phase,'revise',body,reference=pending,inputs=inputs)
 else:r=invoke(phase,'create',body,inputs=inputs)
 reference=ref(r);state.setdefault('pending',{})[label]=reference;save()
 assert not r.get('errors') and r['gate']['result']!='fail',r
 if phase=='000-ctx':
  current=stored(reference)
  body['refresh']={'base_revision':current.control.base_revision,'observed_at':state.setdefault('ctx_observed_at',datetime.now(timezone.utc).isoformat(timespec='seconds')),'observation_baseline':baseline,'refresh_reason':'Confirm complete observed context','effective_change_references':'None','evidence_references':'EVD-001'}
  save();r=invoke(phase,'revise',body,reference=reference)
  assert not r.get('errors') and r['gate']['result']!='fail',r
 conf=review(reference,r);approved=copy.deepcopy(body);approved['final_confirmation']=conf
 final=invoke(phase,'revise',approved,reference=reference,inputs=inputs)
 assert final['ok'] and final['artifact']['revision_state']=='frozen',final
 state['stages'][label]=reference;state['pending'].pop(label,None);save();export(reference,label)
 return reference

BOUNDARY='Isolated Flask-Admin teaching application source and ephemeral local SQLite only; no upstream or production writes.'
if not WORK.exists():
 WORK.mkdir(parents=True);shutil.copytree(CASE/'baseline',WORK/'source')
 subprocess.run(['git','init','-q'],cwd=WORK,check=True)
 subprocess.run(['git','add','source'],cwd=WORK,check=True)
 subprocess.run(['git','-c','user.name=SDLC regression','-c','user.email=regression@example.invalid','commit','-qm','baseline: exact prepared upstream teaching example'],cwd=WORK,check=True)
 (WORK/'.sdlc/authority').mkdir(parents=True)
 (WORK/'.sdlc/authority/work-authorization.md').write_text('''# Work and review authorization\n\nUser explicitly authorized isolated Admin feature development, automatic bounded repair,\nreal tests, local Sandbox release, and independent deterministic objective artifact\nreview in this conversation on 2026-09-07. No exception, production deployment,\nexternal upstream write, human UI review, or future unobserved PASS is authorized.\nModel may choose the smallest compatible implementation and use existing environment.\nReview confirms only current exact persisted contract checks, not business/effect authority.\n''')

# AI-authored observed/confirmed context from actual pinned source, not a fixture.
baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip()
F=lambda x:{'value':x,'basis':'observed','basis_references':['EVD-001']}
N={'none':{'basis':'confirmed','basis_references':['EVD-001']}}
evd={'id':'EVD-001','type':'source-inspection','supports_references':['RSC-001'],'source_or_producer':EXECUTOR,'reference':'SUP-001','integrity_or_digest':'sha256:'+hashlib.sha256((WORK/'source/SOURCE.md').read_bytes()).hexdigest(),'produced_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'sensitivity_or_access':'Public example and synthetic test data only'}
ctx={'context':{'summary':'Pinned Flask-Admin login example; SQLite; enabled-account lifecycle increment in an isolated clone.','project_identity':{'project_name':F('Minimal Admin regression'),'purpose':F('Manage example accounts and validate a real bounded account lifecycle change'),'boundary':{**F(BOUNDARY),'basis':'confirmed'},'primary_resource_reference':F('RSC-001'),'authoritative_references':F('pallets-eco/flask-admin@7fee0246b05476fb6bc38e44bcfb7cc87b978853')},'resources':[{'id':'RSC-001','type':'application','name':'Admin application','role':'primary','locator':'source','baseline_reference':baseline,'basis':'observed','basis_references':['EVD-001']}],'technologies':[{'id':'TEC-001','category':'runtime','name':'Python / Flask-Admin / SQLite','version_or_constraint':'Python 3.12 CI; Flask 3.1.2; Flask-Admin 2.0.2; local compatibility diagnostics 3.13','purpose':'Small authenticated SQLAlchemy administration application','basis':'observed','basis_references':['EVD-001']}],'engineering_entries':[{'id':'ENG-001','purpose':'run','command_or_entry_point':'python3 main.py','working_scope':'source','preconditions':'Dependencies prepared outside runtime; isolated temporary SQLite and instance secret supplied by environment','basis':'confirmed','basis_references':['EVD-001']}],'components':[{'id':'CMP-001','name':'Account admin','type':'web-app','resource_reference':'RSC-001','responsibility':'Authentication, account list and editable status','entry_point':'main.py','depends_on':'None','authority_reference':'EVD-001','basis':'observed','basis_references':['EVD-001']}],'rules':N,'environments':[{'id':'ENV-001','environment':'test','purpose':'Synthetic development verification and local release target','accessibility':'available','data_and_network_boundary':'No production data; isolated-copy verification; no network during runtime','basis':'confirmed','basis_references':['EVD-001']}],'constraints':N,'exceptions':[]},'evidence':[evd],'supporting_members':[{'member_id':'SUP-001','canonical_name':'source-provenance.md','media_type':'text/markdown','purpose':'Pinned source and safety-preparation provenance','content':(WORK/'source/SOURCE.md').read_text()}]}
ctxref=finish('000-ctx',ctx)
if a.until=='CTX':raise SystemExit(0)

requirements=[
 ('behavior','An enabled account can authenticate and use the account administration view; a disabled account cannot authenticate.'),
 ('behavior','The account view shows and filters enabled status and permits an authenticated enabled manager to change it.'),
 ('rule','Disabling an account revokes previously issued login sessions on the next protected request; re-enabling it does not resurrect revoked sessions.'),
 ('quality','The enabled state survives restart; additive migration preserves existing account rows and is idempotent.'),
 ('constraint','Protect authentication and writes with CSRF, reject anonymous and forged sessions and off-site next redirects; retain the teaching example authorization model without a new RBAC system.')]
ac=[
 ('R-001','Login with enabled versus disabled account credentials','Enabled account reaches protected list; disabled login is rejected.'),
 ('R-002','An enabled manager edits another account and filters the list by status','Stored status changes and filtered results match database state.'),
 ('R-003','Retain a cookie, disable and re-enable its account','Old cookie is rejected both times; fresh login after enable succeeds; unaffected manager retains access.'),
 ('R-004','Restart after a state change and migrate a legacy SQLite table twice','State and original rows/IDs remain; migration is idempotent.'),
 ('R-005','Try missing/invalid CSRF, forged/anonymous sessions, off-site next and malformed registration','Unauthorized mutation/login fails; logout is POST-only; redirect stays local; no silent account creation.')]
req={'context_reference':ctxref,'requirement':{'title':'Enable and disable managed accounts','summary':'Add a persisted account availability state with immediate old-session revocation and a working admin filter/edit flow.','sources':[{'type':'conversation','content':'Add enabled/disabled account state with filtering, editing and disabled-user access revocation; use a small existing web admin project for SDLC validation.','evidence_reference':ctxref+'/SUP-001'}],'goals':[{'problem':'An account cannot currently be administratively disabled without deletion.','outcome':'An enabled manager can suspend and restore access without deleting accounts.','success_condition':'Real application requests demonstrate filtering, edits, revocation and persistence with no unauthorized mutation.'}],'in_scope':['Existing Flask-Admin authentication example','Enabled flag, filter/edit, session revocation and additive SQLite migration','Functional automated tests and local sandbox release'],'out_of_scope':['Production deployment','New role hierarchy or full RBAC','Subjective visual/UX acceptance','Upstream changes or user data'],'affected_parties':[],'requirements':[{'type':t,'source_references':['SRC-001','GOAL-001'],'statement':s} for t,s in requirements],'acceptance_criteria':[{'requirement_references':[r],'condition':c,'expected_result':e} for r,c,e in ac],'dependencies':[],'profile':'full','lifecycle_applicability':[{'phase':x,'disposition':'required','host':'N/A','basis':'Bounded real feature needs design, ordered implementation, actual tests and local sandbox delivery.'} for x in ('DSN','PLN','IMP','VFY','RLS')],'open_items':[],'evidence':[],'supporting_members':[],'exceptions':[]}}
reqref=finish('100-req',req)
if a.until=='REQ':raise SystemExit(0)

def table(headers,rows):
 cell=lambda v:str(v).replace('|','\\|').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']+['| '+' | '.join(cell(v) for v in row)+' |' for row in rows])
all_ac=[f'{reqref}#AC-{n:03d}' for n in range(1,6)]; all_r=[f'{reqref}#R-{n:03d}' for n in range(1,6)]
points={
 '110':('Account state and current session transitions','Enabled is the default. Disabling rotates the alternative login identifier in the same update transaction. Re-enable does not revert that identifier. Logout removes the current session.','Active login succeeds, disabled login is rejected and a retained old cookie stays rejected after re-enable.'),
 '120':('Manager editing and sign-in interactions','Reuse Flask-Admin account list/edit/filter and the default form error interaction. Keep logout as an explicit POST form with CSRF. Authentication failures remain on the sign-in page without revealing credentials.','A manager can edit status, filter results, and receive non-success responses for invalid input without a hidden mutation.'),
 '130':('Status field and auth forms','Expose enabled as a named Boolean column and Boolean edit control. Keep existing page template inheritance, labels and validation errors. No unrelated theme or aesthetic changes.','The enabled column/filter and auth/logout forms exist and submit the documented fields.'),
 '220':('User model, login loader and model administration','Keep an app factory with SQLAlchemy and Flask-Login extension initialization. User.get_id returns the alternative identifier; the loader returns only enabled rows. Model-view access follows the existing enabled-authenticated-manager teaching boundary.','Model updates, login loading, and protected views agree on account availability.'),
 '230':('Authentication and mutation endpoints','Reuse /admin/login/, /admin/register/, /admin/logout/ and account CRUD routes. Mutations are POST and CSRF protected; next accepts only local URLs. Read access alone never changes account state.','Anonymous/forged requests are denied, missing CSRF cannot mutate, and external next never navigates off-site.'),
 '240':('Persisted enabled status and alternative identifier','Add Boolean enabled with non-null true default and rotate alternative_id only on a true-to-false transition. New credentials use salted password hashing. The per-app instance secret is supplied externally, never committed.','Database flags match forms; password storage is not plaintext; disable transitions rotate identifiers once.'),
 '310':('Authentication, session revocation and CSRF','Reject disabled accounts both during login validation and subsequent user loading. Protect auth and edit forms with Flask-WTF CSRF. Reject forged sessions and unsafe redirects. This synthetic-data example keeps its prior simple manager model; it is not a new production RBAC implementation.','Disabled and forged sessions fail, CSRF-invalid state changes fail, while legitimate manager workflows remain available.'),
 '330':('Restart and failed-request consistency','Commit account updates transactionally; failed validation/CSRF must leave state unchanged. Dispose test connections; initialize per-app extensions, not persistent module-global state.','Restart preserves state; rejected requests do not alter accounts; two clients cannot revive a revoked old cookie.'),
 '340':('Existing SQLite account migration','Inspect existing user columns before adding enabled with DEFAULT 1. Preserve id, username and other account data. Repeating migration is a no-op. Never drop or re-seed the legacy table.','Two migration runs retain the original row identity and data; migrated accounts have an explicit enabled state.'),
 '350':('Maintainable reproducible regression','Place feature regression in a test module with isolated temporary databases and explicit client sessions. Preserve the upstream BSD license and source provenance. Keep dependencies fixed and application configuration injectable.','The same test command exercises positive, rejection, restart and migration cases with isolated cleanup.'),
 '410':('Local runtime and sandbox delivery','Keep the example local-only with explicit instance configuration and SQLite location. The SDLC RLS target is a disposable local sandbox, not publishing a service or production credentials.','The application configuration and start command are local-only, use isolated SQLite and require externally supplied instance configuration; delivery version observation occurs later in RLS.'),
}
na={'140':'No new accessibility or locale mechanism; reuse existing labeled form widgets. No claim of subjective usability, translation or accessibility certification.', '210':'Existing single-process Flask application and dependency architecture retained; no service boundaries or new shared abstraction.', '320':'No throughput/latency requirement or new workload; one indexed account load per protected request, no capacity certification.', '420':'No new operational telemetry or production incident workflow; retain existing server diagnostics without logging credentials.'}
domains={}
for i in ('110','120','130','140','210','220','230','240','310','320','330','340','350','410','420','510'):
 code='DOM-'+i
 if i in na:domains[code]={'disposition':'n/a','reason':na[i],'basis_references':[reqref]};continue
 if i=='510':continue
 title,design_text,expected=points[i]
 domains[code]={'disposition':'required','completion':'complete','responsible_role':'Application developer','basis_references':all_r,'design_result_markdown':'## 设计结果 Design Result\n\n### '+title+'\n\n'+design_text,'constraints_impacts':[{'type':'constraint','content':'Preserve the existing teaching-project boundary and satisfy the requirement without production effects.','affected_phase':'IMP, VFY, RLS','reference':reqref}], 'vfy_points':[{'id':f'VFP-{i}-001','references':all_ac if i=='350' else [reqref],'verification_object':title,'observable_result':expected,'expected_evidence':'Actual request assertions, database readback and execution output bound to the tested result.'}],'evidence_references':[{'reference':ctxref+'/SUP-001','supports':['CHG-001'],'purpose':'Existing project provenance and isolated preparation'}]}
vfps=[f'VFP-{i}-001' for i in points]
strategy='## 设计结果 Design Result\n\n### VFY 目标 VFY Objectives\n\n'+table(['ID','Kind','Requirement, AC, Goal or Intended-use References','Design or Decision References','Domain VFY Point References','可观察结果 Observable Result','风险或重要性 Risk or Importance','Method References','Pass Criteria References','Evidence Contract References'],[['VFO-001','both',', '.join([*all_ac,f'{reqref}#GOAL-001']),'CHG-001, CHG-002, DEC-001',', '.join(vfps),'An enabled manager suspends and restores another account without data loss or revival of revoked sessions; actual request and persistence tests pass.','Access revocation and preserved legacy data are essential to intended use.','VFM-001','VPC-001','VEC-001']])
strategy+='\n\n### 方法选择 VFY Methods\n\n'+table(['ID','类型 Type','Disposition','方法明细 Method Detail','适用范围 Scope','方法 Method','选择依据 Selection Basis','承载位置 Host','Exception Reference'],[['VFM-001','test','required','level=integration, mode=automated','VFO-001','Execute application requests with isolated SQLite state and compare responses and stored data.','Observable state transitions and rejected writes can be asserted without subjective UI judgments.','VFY','N/A']])
strategy+='\n\n### 可验证性设计 Verifiability Design\n\nInject app configuration and isolated SQLite; retain alternative identifier and load enabled accounts on every protected request. Host domains DOM-220, DOM-240 and DOM-350. No test-only success hook.\n\n### 环境与数据 Environment and Data\n\nUse prepared fixed Python dependencies, actual Flask WSGI request handling, temporary SQLite and synthetic credentials. Reset each test, close connections, disable network during formal methods. No external accounts or production data.\n\n### 覆盖策略 Coverage Strategy\n\nCover normal login, disable/re-enable and another active manager; invalid credentials, CSRF and forged cookies; duplicate/blank registration; restart and repeated legacy migration. Exclude production performance and subjective aesthetics, which are not acceptance objectives.\n\n### 通过条件 Pass Criteria\n\n'+table(['ID','VFY Objective','输入或条件 Input or Condition','预期结果 Expected Result','容差 Tolerance','失败条件 Failure Condition'],[['VPC-001','VFO-001','Current terminal implementation result plus synthetic request/state scenarios','All selected assertions run and pass; zero skips/errors; unauthorized writes leave stored state unchanged.','None','Any assertion failure, missing scenario, skipped test, evidence mismatch or incorrect tested source.']])
strategy+='\n\n### Evidence Contract\n\n'+table(['ID','VFY Objective','Evidence Type','生成方或来源 Producer or Source','必要内容 Required Content','敏感性与处理 Sensitivity and Handling','保留要求 Retention Requirement','保存或引用位置 Storage or Reference'],[['VEC-001','VFO-001','Execution log and immutable source evidence','Actual automated test process','Exact source/result digests, method/environment, executed test identities, exit code, stdout/stderr and current outcomes','Synthetic data only; exclude live credentials and session values','Retain with this regression delivery','Formal VFY supporting members and readable case evidence']])
domains['DOM-510']={'disposition':'required','completion':'complete','responsible_role':'Verification designer','basis_references':[reqref],'design_result_markdown':strategy,'constraints_impacts':[],'vfy_points':[],'evidence_references':[]}
composite=[{'domain_code':code,'subdomain':name,'disposition':disp,'basis_references':[reqref],'reason':reason,'exception_references':[]} for code,name,disp,reason in [('DOM-140','可访问性 Accessibility','n/a',na['140']),('DOM-140','国际化 Internationalization','n/a',na['140']),('DOM-310','安全 Security','required','N/A'),('DOM-310','隐私 Privacy','n/a','Only synthetic test accounts; no new personal-data collection or privacy workflow.'),('DOM-310','合规 Compliance','n/a','No new regulated processing or jurisdictional change; preserve source license.')]]
design={'title':'Account availability and revocation design','summary':'Extend the existing app/model/admin forms; use transactional session-identifier rotation and additive SQLite migration.','boundary':BOUNDARY,'change_type':'incremental','baseline_references':[ctxref],'target_state_summary':'Enabled state is visible/editable, revoked sessions stay revoked, and persisted accounts survive restart/migration.','impact_summary':'App/model/forms and isolated tests only; existing teaching authorization model retained.','changes':[{'id':'CHG-001','object_or_boundary':'resource:RSC-001','change':'modify','baseline_references':[ctxref],'baseline_state':'No persisted availability switch or suspended-account access guard.','target_state':'Working status edit/filter, immediate session revocation and additive migration.','affected_domains':['DOM-'+i for i in points if i!='350']},{'id':'CHG-002','object_or_boundary':'resource:RSC-001','change':'add','baseline_references':[ctxref],'baseline_state':'No regression for account suspension.','target_state':'Deterministic tests and minimal local delivery documentation.','affected_domains':['DOM-350','DOM-510']}],'decisions':[{'id':'DEC-001','requirement_references':all_r,'question':'How should disabling invalidate outstanding sessions without deleting accounts?','options':['Reject only fresh login','Rotate alternative login identity and reject disabled loads'],'decision':'Rotate identity on disable and reject disabled accounts on every protected load.','rationale':'Meets immediate revocation and prevents old-session resurrection while retaining existing accounts.','affected_domains':['DOM-110','DOM-220','DOM-240','DOM-310']}],'traceability':[{'source_references':[rr,ar],'design_references':['CHG-001','CHG-002','DOM-510'],'decision_references':['DEC-001'],'vfy_references':['VFO-001']} for rr,ar in zip(all_r,all_ac)],'domains':domains,'composite_subdomains':composite,'cross_domain_conflicts':[],'scope_expansion':False,'simplicity_rationale':'Reuse the existing monolith, SQLAlchemy, Flask-Login and standard admin widgets; no extra service/provider or production release.','lifecycle_applicability':[{'phase':ph,'disposition':'required','host':'N/A','basis':'Ordered implementation, whole-scope verification and authorized local sandbox delivery.'} for ph in ('PLN','IMP','VFY','RLS')],'evidence':[],'supporting_members':[],'open_items':[],'exceptions':[]}
dsref=finish('200-dsn',{'design':design},[reqref])
if a.exercise_design_revision and not state.get('design_revision_exercised'):
 design['summary'] += ' Clarification: target-side version observation belongs to RLS; VFY tests the current application and its local configuration.'
 previous=a.revise_stage;a.revise_stage='DSN';dsref=finish('200-dsn',{'design':design},[reqref]);a.revise_stage=previous
 state['design_revision_exercised']=True;save()
if a.until=='DSN':raise SystemExit(0)

# Planner consumes the complete exact DSN, retaining the actual declared identities.
from packages.sdlc_runtime.canonical import parse_markdown_tables
import re
s=stored(dsref);tables=list(parse_canonical_artifact(s.payload.primary_blob).tables)
for m in s.payload.members:
 if m.media_type=='text/markdown':tables.extend(parse_markdown_tables(m.raw_bytes.decode()))
obligations=[]
for t in tables:
 for row in t.rows:
  item=row.get('ID') or row.get('Change ID')
  if isinstance(item,str) and re.fullmatch(r'(?:CHG|VFP|OBJ|OBL|EX|R|AC)-[A-Za-z0-9._-]+',item):
   rr=f'{dsref}#{item}'
   if rr not in obligations:obligations.append(rr)
change1=f'{dsref}#CHG-001';change2=f'{dsref}#CHG-002';pointrefs=[x for x in obligations if '#VFP-' in x]
work=[]
for number,phase,outcome,sources,depends,completion,evidence,role in [
 (1,'IMP','Implement account availability, protected admin editing, revocation and additive SQLite migration.',[change1],[], 'Current application code handles enabled status, session revocation and legacy data without broadening access.','Immutable source snapshot and syntax/current-content checks.','Application developer'),
 (2,'IMP','Add reproducible account lifecycle tests and local usage documentation.',[change2],['WI-001'],'Executable tests and documentation exist on top of the exact first implementation result.','Immutable test source, syntax checks and actual functional test output.','Application test developer'),
 (3,'VFY','Verify and validate the complete current requirement and design scope.',pointrefs,['WI-002'],'All required objectives have current real method evidence with passing verification and validation.','Actual current-subject method logs, assertion identities and VFY conclusions.','Verification executor'),
 (4,'RLS','Deliver the verified result to a disposable local sandbox and confirm its exact version.',[change1],['WI-003'],'The current VFY-approved candidate is applied to the authorized local target and its version matches.','Release effect observation, target version readback and terminal lifecycle status.','Local release executor')]:
 work.append({'id':f'WI-{number:03d}','target_phase':phase,'outcome':outcome,'execution_scope':['resource:RSC-001']+(['environment:ENV-001'] if phase=='RLS' else []),'source_references':sources,'constraint_references':[],'depends_on':depends,'completion_criteria':completion,'expected_evidence':evidence,'responsible_role':role})
plan={'title':'Ordered account lifecycle delivery','summary':'Two sequential same-resource implementation work items followed by complete-scope verification and local sandbox delivery.','profile':'full','pln_disposition':'required','delivery_scope':[{'source_artifact_reference':dsref,'inclusion_basis':'Entire confirmed account-availability design; no selected-item truncation.'}],'obligations':obligations,'work_items':work,'aggregated_applicability':[],'lifecycle_applicability':[{'phase':ph,'disposition':'required','host':'N/A','basis':'Consume complete design scope and preserve the ordered resource result chain.'} for ph in ('IMP','VFY','RLS')],'open_items':[],'exceptions':[],'evidence':[],'supporting_members':[]}
plnref=finish('300-pln',{'plan':plan},[dsref])
if a.until=='PLN':raise SystemExit(0)

# Each implementation is a real formal Claim; no source mutation by this driver.
# Candidate files are outside the working product and become declared preconditioned operations.
CONSIDERATIONS=('Calculation Rules','Decision Rules','State Transitions','Algorithm & Invariants','Data Contract & Transformation','Boundary & Failure Handling','Effects & Consistency')
def implementation(number):
 files=['main.py','templates/auth.html','templates/my_master.html'] if number==1 else ['test_enabled.py','ACCOUNT-STATUS.md']
 if number==2 and not (CASE/'candidate/ACCOUNT-STATUS.md').exists():
  (CASE/'candidate/ACCOUNT-STATUS.md').write_text('''# Account availability\n\nStart locally with an externally supplied ADMIN_DEMO_SECRET and SQLite configuration.\nAll enabled authenticated users retain the upstream teaching example manager privilege;\nthis is not a production RBAC system. Edit and filter Enabled in the user model view.\nDisabling rotates the login identity; re-enabling never revives an old cookie.\nSQLite migration is additive and idempotent, never drops or re-seeds existing rows.\nRun `python3 -m unittest test_enabled -v` using the prepared dependency lock.\nThirteen tests cover real requests, CSRF, old cookies, restart and legacy migration.\nNo deployment, external accounts, or production credentials are required.\n''')
 ops=[]
 for name in files:
  current=WORK/'source'/name
  # On a resumed invocation preserve the original exact operation prefix.
  ops.append({'resource':'RSC-001','path':name,'step':'STEP-001','op':'write_text','expected_sha256':'sha256:'+hashlib.sha256(current.read_bytes()).hexdigest() if current.exists() else 'absent','content':(CASE/'candidate'/name).read_text()})
 blocks=[
 {'consideration':'Boundary & Failure Handling','id':'ERR-001','trigger':'An invalid login, forged/disabled session, missing CSRF or schema initialization error.','classification':'Reject invalid/unauthorized requests; treat migration errors as failures rather than default success.','handling':'Validate before mutation, retain existing account data and report actionable errors without sensitive values.','observable_result':'Rejected request does not change stored state; failed initialization does not drop rows.','recovery':'Correct the input or isolated configuration, rerun the exact failed request and regression.'},
 {'consideration':'Effects & Consistency','id':'EFF-001','resource_or_effect':'Declared application resource and its isolated test database','order_and_condition':'Read the exact predecessor result and precondition every source write; tests use fresh database state.','consistency_or_atomicity':'Account availability and session identifier rotate within one transaction; source effects remain recorded by IMP.','idempotency':'Same completed operation is not repeated; migration and repeated disable do not re-seed or resurrect data.','failure_handling':'Keep failed evidence and source state; never claim VFY success from an IMP syntax check.'}]
 if number==1:
  blocks=[
   {'consideration':'Decision Rules','id':'DEC-001','rules':[{'id':'DR-001','priority':'1','conditions':'account missing or disabled, invalid form, or CSRF rejected','outcome':'Reject authentication or mutation without changes'},{'id':'DR-002','priority':'2','conditions':'DEFAULT','outcome':'Allow existing authenticated-manager workflow after validation'}]},
   {'consideration':'State Transitions','id':'STA-001','transitions':[{'id':'TR-001','current':'enabled','event':'manager disables','next':'disabled','effect':'Persist flag and new alternative login identity in one transaction','illegal_handling':'Reject unauthorized/invalid request'},{'id':'TR-002','current':'disabled','event':'manager enables','next':'enabled','effect':'Retain rotated identity; require fresh login','illegal_handling':'Old cookie remains invalid'}]},
   {'consideration':'Algorithm & Invariants','id':'ALG-001','inputs':'Validated account and form fields; current stored enabled flag and alternative identity.','outputs':'Updated availability or authenticated enabled account, never credential bytes in responses.','invariants':'A disabled account cannot authenticate; re-enable cannot restore an old login identifier; existing database row IDs are preserved.','scale_or_limits':'One account lookup per protected request; bounded teaching application with no new capacity guarantee.','pseudocode':'Validate request; load account; reject disabled or invalid; on true-to-false rotate identity; commit flag plus identity; reload state on later requests.'},
   {'consideration':'Data Contract & Transformation','id':'MAP-001','mappings':[{'source':'Existing user row without enabled column','target':'User row with enabled flag','transformation':'Add column with true default without drop/reseed','validation':'Inspect table columns and preserve row identity','null_or_default':'Existing rows become enabled; new rows default true'},{'source':'Availability form update','target':'enabled and alternative_id','transformation':'On disable rotate login identity once','validation':'CSRF and authenticated enabled-manager checks precede mutation','null_or_default':'Missing or invalid fields are rejected'}]},*blocks]
 names=[n for n in CONSIDERATIONS if any(b['consideration']==n for b in blocks)]
 method={'considerations':[{'name':n,'disposition':'required' if n in names else 'n/a','basis':('Required by account state, revocation and test consistency.' if n in names else ('Use existing password-hashing library, no new calculation rule.' if number==1 else 'This work item adds regression and usage instructions, not new product calculation/decision/data/state rules.')),'steps':['STEP-001'] if n in names else [],'exception':'N/A'} for n in CONSIDERATIONS], 'steps':[{'id':'STEP-001','order':1,'purpose':work[number-1]['outcome'],'target':['resource:RSC-001'],'basis_references':[f'{plnref}#WI-{number:03d}',change1 if number==1 else change2],'considerations':names,'logic':['Read the exact current baseline and declared design.','Apply only the preconditioned implementation files.' if number==1 else 'Add isolated current-source tests and reproducible account-state instructions.','Execute the declared local checks, retaining actual output and immutable final source.'],'expected_result':work[number-1]['completion_criteria'],'transaction_boundary':'One bounded source implementation work item; request-time data transactions follow the approved design.','failure_boundary':'Any failed precondition, source check or test leaves a visible incomplete work item.','blocks':blocks}], 'resources':[{'id':'RSC-001','root':'source'}],'operations':ops,'checks':[{'id':'CHK-001','name':'Parse application Python source','resource':'RSC-001','kind':'python_syntax','path':'main.py'}], 'design_decision_references':[dsref+'#DEC-001'],'exceptions':[],'open_items':[]}
 if number==2:
  method['checks'] += [{'id':'CHK-002','name':'Parse account lifecycle regression','resource':'RSC-001','kind':'python_syntax','path':'test_enabled.py'},{'id':'CHK-003','name':'Actual isolated account lifecycle tests','resource':'RSC-001','kind':'project_command','cwd':'.','command':['python','-m','unittest','test_enabled','-v'],'timeout_seconds':120}]
 return method

for number in (1,2):
 label=f'IMP-{number}'
 if label in state['stages']:continue
 method_path=OUT/f'implementation-{number}.json'
 if method_path.exists():method=json.loads(method_path.read_text())
 else:method=implementation(number);method_path.write_text(json.dumps(method,ensure_ascii=False,indent=2)+'\n')
 body={'inputs':{'implementation':method}}
 upstream=[plnref]+([state['stages']['IMP-1']] if number==2 else [])
 pending=state.get('pending',{}).get(label)
 r=invoke('400-imp','revise' if pending else 'create',body,reference=pending,inputs=upstream,binding=f'{plnref}#WI-{number:03d}')
 reference=ref(r);state.setdefault('pending',{})[label]=reference;save()
 assert not r.get('errors') and r['gate']['result']!='fail',r
 conf=review(reference,r);body['inputs']['final_confirmation']=conf
 r=invoke('400-imp','revise',body,reference=reference,inputs=upstream,binding=f'{plnref}#WI-{number:03d}')
 assert r['ok'] and r['artifact']['revision_state']=='frozen',r
 assert next(w for w in r['warnings'] if w['code']=='IMP_EXECUTION_STATE')['claim_state']=='completed',r
 state['stages'][label]=reference;state['pending'].pop(label,None);save();export(reference,label)
if a.until=='IMP':raise SystemExit(0)

# VFY consumes the entire Plan and only the current terminal implementation result.
terminal=state['stages']['IMP-2']+'/RESULT-RES-001'
vfy_obligations=sorted([f'{dsref}#{x}' for x in vfps]+[f'{dsref}#{x}' for x in ('VFM-001','VPC-001','VEC-001')]+[f'{plnref}#WI-{i:03d}' for i in (1,2,3)])
from packages.sdlc_runtime import parse_markdown_tables
vfo_rows=[row for member in stored(dsref).payload.members if member.member_id=='DOM-510'
          for t in parse_markdown_tables(member.raw_bytes.decode()) for row in t.rows if row.get('ID')=='VFO-001']
assert len(vfo_rows)==1
vfo=vfo_rows[0]
vfy_candidate={'targets':[{'reference':dsref+'#VFO-001','purpose':vfo['Kind'],
 'summary':vfo['可观察结果 Observable Result'],'source_kind':'vfo',
 'obligation_references':[dsref+'#'+x.strip() for x in vfo['Domain VFY Point References'].split(',')]}], 'methods':[{
 'id':'VFM-001','title':'Current-subject account lifecycle integration','purpose':'both',
 'target_references':[dsref+'#VFO-001'],'subject_references':[terminal],
 'obligation_references':vfy_obligations,'method_type':'test','disposition':'required',
 'execution_mode':'automated','executor_identity':EXECUTOR,
 'environment':{'project_root':'.','data_contract':'Ephemeral synthetic SQLite; exact current terminal source; existing prepared interpreter dependencies'},
 'procedure':{'kind':'command','argv':['python','-m','unittest','test_enabled','-v'],
   'policy':'deterministic-test-v1','workspace':'isolated-copy','network':'disabled','cwd':'source','timeout_seconds':120,'max_output_bytes':262144},
 'pass_criteria':'All thirteen current-source integration tests execute with zero failure, error or skip; enabled-account, session revocation, CSRF, restart and legacy migration assertions hold.',
 'evidence_requirement':'Actual stdout/stderr and exit code, test identities, OS containment and source snapshot digests; not earlier standalone test results.'}]}
if 'VFY' not in state['stages']:
 pending=state.get('pending',{}).get('VFY')
 if not pending:
  result=invoke('500-vfy','create',{'persist':True,'run_automated':False,'candidate':vfy_candidate},inputs=[plnref,terminal])
  assert result.get('ok'),result
  pending=ref(result);state.setdefault('pending',{})['VFY']=pending;save()
 if a.until=='VFY-CONTRACT':raise SystemExit(0)
 result=invoke('500-vfy','run',{'persist':True,'allow_commands':True,'finalize':False},reference=pending)
 assert result.get('ok') and result['product_result']=='pass',result
 # Public deterministic helpers recompute phase-specific bindings from the
 # actual readback state. The independent reviewer checks canonical bytes itself.
 sys.path.insert(0,str(RUNTIME/'skills/sdlc-500-vfy/scripts'))
 from vfy_handler import VfyHandler
 from vfy_builder import confirmation_subject_digest
 actual=VfyHandler(WORK).check(reference=pending)['state']
 expected=VfyHandler(WORK).confirmation_requirements(actual)
 conf=review(pending,result);conf['subject_digest']=confirmation_subject_digest(actual)
 assert all(conf[k]==v for k,v in expected.items()),(conf,expected)
 result=invoke('500-vfy','run',{'persist':True,'allow_commands':True,'finalize':True,'confirmation':conf},reference=pending)
 assert result.get('ok') and result['artifact']['revision_state']=='frozen' and result['product_result']=='pass' and result['rls_ready'],result
 state['stages']['VFY']=pending;state['pending'].pop('VFY',None);save();export(pending,'VFY')
if a.until=='VFY':raise SystemExit(0)

# RLS does not deploy a real site. Its authorized effect is the existing local
# sandbox target's version transition, tied to the exact VFY/IMP source set.
# The host adapter is a separate subprocess; it cannot sign artifact review.
rlsargs=[sys.executable,'-B',str(HERE/'close_release.py'),'--runtime',str(RUNTIME),'--work',str(WORK),
         '--output',str(OUT),'--vfy',state['stages']['VFY'],'--executor',EXECUTOR]
result=subprocess.run(rlsargs,text=True,capture_output=True,timeout=180)
(OUT/'rls-adapter.stdout').write_text(result.stdout);(OUT/'rls-adapter.stderr').write_text(result.stderr)
assert result.returncode==0,result.stderr
rlsresult=json.loads((OUT/'rls-closed.json').read_text());state['stages']['RLS']=rlsresult['reference'];save();export(rlsresult['reference'],'RLS')
statusrun=subprocess.run([sys.executable,'-B',str(RUNTIME/'skills/sdlc-status/scripts/runtime.py'),'inspect','-p',str(WORK),'-r',reqref,'-f','json'],text=True,capture_output=True,timeout=60)
(OUT/'status.json').write_text(statusrun.stdout);(OUT/'status.stderr').write_text(statusrun.stderr)
assert statusrun.returncode==0,statusrun.stderr
print('STATUS',statusrun.stdout,flush=True)
