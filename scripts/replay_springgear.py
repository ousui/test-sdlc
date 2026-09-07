"""AI-authored SpringGear JDK21 requirement, replayed through public Skill CLIs."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from scenario_io import ScenarioIO
p=argparse.ArgumentParser()
for name in ('runtime','work','output','case-root'):p.add_argument('--'+name,required=True)
p.add_argument('--until',default='STATUS');a=p.parse_args()
WORK=Path(a.work).resolve();CASE=Path(a.case_root).resolve()
BOUNDARY='Isolated SpringGear four-module Maven reactor migration to JDK21; no disabled-module claim, upstream write or production deployment.'
EXECUTOR='web-realflow-springgear-executor'
if not WORK.exists():
    WORK.mkdir(parents=True);shutil.copytree(CASE/'baseline',WORK/'source')
    subprocess.run(['git','init','-q'],cwd=WORK,check=True)
    subprocess.run(['git','add','source'],cwd=WORK,check=True)
    subprocess.run(['git','-c','user.name=SDLC regression','-c','user.email=regression@example.invalid','commit','-qm','baseline: preserved SpringGear source'],cwd=WORK,check=True)
    d=WORK/'.sdlc/authority';d.mkdir(parents=True)
    (d/'work-authorization.md').write_text('User authorized this isolated JDK21 regression, generic fixes, real tests and local Sandbox release on 2026-09-07. Objective independent-process artifact review is delegated; production effects, risk acceptance, future PASS and upstream writes are not authorized. Minimal compatible design decisions are delegated to the model.\n')
io=ScenarioIO(a.runtime,WORK,a.output,EXECUTOR,BOUNDARY)
from packages.sdlc_runtime import parse_canonical_artifact,parse_markdown_tables
baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip()
F=lambda x:{'value':x,'basis':'observed','basis_references':['EVD-001']}
N={'none':{'basis':'confirmed','basis_references':['EVD-001']}}
prov=(WORK/'source/SOURCE.md').read_text()
ctx={'context':{'summary':'SpringGear existing four-module Java8-targeted reactor; controlled JDK21 compatibility migration.',
    'project_identity':{'project_name':F('SpringGear'),'purpose':F('Spring-based workflow framework'),
    'boundary':{**F(BOUNDARY),'basis':'confirmed'},'primary_resource_reference':F('RSC-001'),
    'authoritative_references':F('ousui/springgear@e855096ff19dcdb303dc4250ba19c30acd743ac7')},
    'resources':[{'id':'RSC-001','type':'library','name':'SpringGear reactor','role':'primary','locator':'source','baseline_reference':baseline,'basis':'observed','basis_references':['EVD-001']}],
    'technologies':[{'id':'TEC-001','category':'runtime','name':'Java / Maven / Spring / Lombok','version_or_constraint':'Baseline Java8 target and Spring5.3.22; approved migration target JDK21','purpose':'Compile and exercise existing workflow framework','basis':'referenced','basis_references':['EVD-001']}],
    'engineering_entries':[{'id':'ENG-001','purpose':'test','command_or_entry_point':'mvn -o test','working_scope':'source','preconditions':'Prepared JDK21 and external Maven cache; no dependency installation during Skill execution','basis':'confirmed','basis_references':['EVD-001']}],
    'components':[{'id':'CMP-001','name':'Workflow core','type':'library','resource_reference':'RSC-001','responsibility':'Workflow context, ordered handlers and Spring framework integration','entry_point':'springgear-core','depends_on':'None','authority_reference':'EVD-001','basis':'observed','basis_references':['EVD-001']}],
    'rules':N,'environments':[{'id':'ENV-001','environment':'test','purpose':'JDK21 isolated-copy testing and disposable local Sandbox target','accessibility':'available','data_and_network_boundary':'Public source only; no network or upstream writes in formal execution','basis':'confirmed','basis_references':['EVD-001']}], 'constraints':N,'exceptions':[]},
    'evidence':[{'id':'EVD-001','type':'source-inspection','supports_references':['RSC-001'],'source_or_producer':EXECUTOR,'reference':'SUP-001','integrity_or_digest':'sha256:'+hashlib.sha256(prov.encode()).hexdigest(),'produced_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'sensitivity_or_access':'Public open-source snapshot, no customer data'}],
    'supporting_members':[{'member_id':'SUP-001','canonical_name':'source-provenance.md','media_type':'text/markdown','purpose':'Exact source and user-selected JDK21 scope','content':prov}]}
ctxref=io.complete('000-ctx',ctx)
if a.until=='CTX':raise SystemExit(0)
requirements=[
 ('behavior','Compile the existing active four-module reactor on JDK21 and emit Java21 class files.'),
 ('behavior','Preserve existing workflow context, handler ordering, unsupported-handler behavior and exception conversion without changing public SpringGear source.'),
 ('constraint','Align the minimal compiler, processor, Spring and logging dependencies while retaining the Spring5 API generation; do not migrate to a new architecture.'),
 ('quality','Execute all declared regression tests with a real JUnit engine; zero failures, errors or skipped tests; a repeatable Maven verify succeeds.'),
 ('constraint','Document actual scope and local build commands; preserve upstream source/license and do not publish or modify upstream branches.')]
acs=[('JDK21 compiles the reactor','Runtime feature 21 and compiled class major 65 are asserted.'),
 ('Execute existing core behaviors','Context arguments, shared values, handler order/skip/failure and Spring configuration behavior pass.'),
 ('Compile Lombok-generated members and load Spring context','Constructors/accessors and Spring configuration enhancement work without add-opens or public-source rewriting.'),
 ('Execute the current test class on the current final result','Ten distinct tests execute, zero failures/errors/skips; Maven verify packages the active reactor.'),
 ('Inspect changed paths and migration instructions','Only POM compatibility, regression tests and migration instructions change; no deployment goals or upstream effects.')]
req={'context_reference':ctxref,'requirement':{'title':'SpringGear JDK21 compatibility migration','summary':'Upgrade the existing active reactor to JDK21 with preserved core behavior and executable regression evidence.',
 'sources':[{'type':'conversation','content':'User changed the SpringGear migration target to JDK21 and authorized bounded environment-compatible regression; do not pursue JDK26.','evidence_reference':ctxref+'/SUP-001'}],
 'goals':[{'problem':'The framework reactor still targets Java8 and uses older build/processor dependencies.','outcome':'Maintain and test the framework using JDK21 without redesigning its public API.','success_condition':'Current-result JDK21 compilation, bytecode and behavior tests pass, with exact source and complete SDLC evidence.'}],
 'in_scope':['Existing four-module Maven reactor','Compatible dependency/build alignment','Behavior tests, migration instructions and local Sandbox lifecycle'],
 'out_of_scope':['JDK26','Disabled historical modules','Production deployment or Maven Central release','Public API redesign','UI/UX review'],'affected_parties':[],
 'requirements':[{'type':t,'source_references':['SRC-001','GOAL-001'],'statement':s} for t,s in requirements],
 'acceptance_criteria':[{'requirement_references':[f'R-{n:03d}'],'condition':c,'expected_result':e} for n,(c,e) in enumerate(acs,1)],
 'dependencies':[],'profile':'full','lifecycle_applicability':[{'phase':x,'disposition':'required','host':'N/A','basis':'Compatibility design, ordered build/test implementation, current-result verification and local Sandbox delivery.'} for x in ('DSN','PLN','IMP','VFY','RLS')],
 'open_items':[],'evidence':[],'supporting_members':[],'exceptions':[]}}
reqref=io.complete('100-req',req)
if a.until=='REQ':raise SystemExit(0)
all_r=[f'{reqref}#R-{n:03d}' for n in range(1,6)];all_ac=[f'{reqref}#AC-{n:03d}' for n in range(1,6)]
def table(headers,rows):
    cell=lambda v:str(v).replace('\\','\\\\').replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']+['| '+' | '.join(cell(v) for v in row)+' |' for row in rows])
points={
 '210':('Retain reactor architecture','Keep build, parent, core and BOM relationships and the existing Spring5 generation. Upgrade only compatibility dependencies; disabled modules remain outside the claim.','Active modules compile together without a new service or public API redesign.',[1,3]),
 '220':('Build and processor compatibility','Use compiler release21, compiler plugin3.11.0, Lombok1.18.30, Spring5.3.39 and SLF4J2 log binding. Keep framework Java sources unchanged.','Generated accessors/constructors compile and Spring context enhancement works on21.',[1,2,3]),
 '340':('Source-only compatibility migration','POM edits have exact old-content preconditions. No production data/schema migration; preserve all public Java source and existing resources.','Diff touches only declared POMs, new tests and migration instructions.',[2,3,5]),
 '350':('Executable compatibility tests','Use JUnit5.7 API and engine with Surefire3.2.5. Add10 deterministic tests, including bytecode65; emit each actually executed method identity through JUnit AfterEach.','Ten tests execute without skip/failure, covering the stated runtime and behavior claims.',[1,2,3,4]),
 '410':('Local artifact and release boundary','Build offline from preinstalled JDK21 and a prepared Maven cache. Use verify for reactor packaging, then an independent current-result test in VFY. RLS only observes a disposable Sandbox version, never Maven deployment.','Maven verify builds the active reactor; test evidence and local target match the qualified current version.',[4,5])}
na={
 '110':'No new business workflow; existing library behavior is preserved and tested in DOM-220/350.',
 '120':'No interactive page or user journey in this library migration.', '130':'No UI components or display logic exist in the active migration scope.',
 '140':'No UI, language resources or accessibility changes in this library migration.',
 '230':'No interface/schema/HTTP contract change; public Java code is preserved, compatibility checked in DOM-220.',
 '240':'No persistent data model, collection or serialized schema is added.',
 '310':'No auth, trust or personal-data boundary change; dependencies are changed for compatibility, not claimed a security certification.',
 '320':'No throughput or capacity requirement; no performance guarantee is asserted.',
 '330':'No new distributed runtime, service availability or recovery topology; existing exception behavior is regression-tested.',
 '420':'No new telemetry or production operational workflow.'}
domains={}
for i in ('110','120','130','140','210','220','230','240','310','320','330','340','350','410','420'):
    if i in na:domains['DOM-'+i]={'disposition':'n/a','reason':na[i],'basis_references':[reqref]};continue
    title,design,expected,indices=points[i]
    domains['DOM-'+i]={'disposition':'required','completion':'complete','responsible_role':'Java maintainer','basis_references':[all_r[n-1] for n in indices],
        'design_result_markdown':'## 设计结果 Design Result\n\n### '+title+'\n\n'+design,
        'constraints_impacts':[{'type':'constraint','content':'Retain exact migration boundary, no public-source redesign or upstream publication.','affected_phase':'IMP, VFY, RLS','reference':reqref}],
        'vfy_points':[{'id':f'VFP-{i}-001','references':[all_ac[n-1] for n in indices],'verification_object':title,'observable_result':expected,'expected_evidence':'Current-source compiler/test output and immutable source/diff evidence.'}],
        'evidence_references':[{'reference':ctxref+'/SUP-001','supports':['CHG-001'],'purpose':'Upstream reactor baseline and scope'}]}
vfps=[f'VFP-{i}-001' for i in points]
objective='The active SpringGear reactor works on JDK21 with unchanged public Java source, Java21 bytecode and passing workflow compatibility tests.'
strategy='## 设计结果 Design Result\n\n### VFY 目标 VFY Objectives\n\n'+table(['ID','Kind','Requirement, AC, Goal or Intended-use References','Design or Decision References','Domain VFY Point References','可观察结果 Observable Result','风险或重要性 Risk or Importance','Method References','Pass Criteria References','Evidence Contract References'],[['VFO-001','both',', '.join([*all_ac,reqref+'#GOAL-001']),'CHG-001, CHG-002, DEC-001',', '.join(vfps),objective,'Prevent build success with missing tests or broken framework behavior.','VFM-001','VPC-001','VEC-001']])
strategy+='\n\n### 方法选择 VFY Methods\n\n'+table(['ID','类型 Type','Disposition','方法明细 Method Detail','适用范围 Scope','方法 Method','选择依据 Selection Basis','承载位置 Host','Exception Reference'],[['VFM-001','test','required','level=integration, mode=automated','VFO-001','Offline Maven test of the current terminal result.','Real Java runtime, bytecode and workflow assertions verify intended library use.','VFY','N/A']])
strategy+='\n\n### 可验证性设计 Verifiability Design\n\nUse existing public context/executor types and a real Spring application context. JUnit tests assert Java feature21 and actual class major65, not just configuration strings.\n\n### 环境与数据 Environment and Data\n\nJDK21 and external Maven dependency cache are prepared before runtime. Formal execution is an OS-isolated copy without network. Tests use no external database or server.\n\n### 覆盖策略 Coverage Strategy\n\nTen unique JUnit tests cover runtime21, bytecode65, Lombok construction, argument/value transport, invalid indices, empty/order/skip/failure pipeline behavior and Spring enhancement. All existing public sources and disabled-module exclusion are retained.\n\n### 通过条件 Pass Criteria\n\n'+table(['ID','VFY Objective','输入或条件 Input or Condition','预期结果 Expected Result','容差 Tolerance','失败条件 Failure Condition'],[['VPC-001','VFO-001','Current terminal source and JDK21 toolchain','Ten executed tests; zero failure, error or skip; existing behavior and Java21 class assertion pass.','None','Missing test identity, wrong runtime or bytecode, test failure, source drift or unsupported environment.']])
strategy+='\n\n### Evidence Contract\n\n'+table(['ID','VFY Objective','Evidence Type','生成方或来源 Producer or Source','必要内容 Required Content','敏感性与处理 Sensitivity and Handling','保留要求 Retention Requirement','保存或引用位置 Storage or Reference'],[['VEC-001','VFO-001','Execution log and immutable result','Actual Maven/JUnit process','Current result hashes, Java version assertions, executed method identities, Maven summary and exit code','Public source and synthetic test values only','Retain original evidence with delivery','VFY supporting evidence and readable case archive']])
domains['DOM-510']={'disposition':'required','completion':'complete','responsible_role':'Verification designer','basis_references':[reqref],'design_result_markdown':strategy,'constraints_impacts':[],'vfy_points':[],'evidence_references':[]}
composite=[{'domain_code':code,'subdomain':name,'disposition':'n/a','basis_references':[reqref],'reason':reason,'exception_references':[]} for code,name,reason in [('DOM-140','可访问性 Accessibility',na['140']),('DOM-140','国际化 Internationalization',na['140']),('DOM-310','安全 Security',na['310']),('DOM-310','隐私 Privacy','No personal data is processed.'),('DOM-310','合规 Compliance','No new regulated processing; preserve existing open-source licensing.')]]
design={'title':'SpringGear JDK21 compatibility design','summary':'Retain reactor/public APIs; align build dependencies and prove behavior with current-result tests.',
 'boundary':BOUNDARY,'change_type':'incremental','baseline_references':[ctxref],'target_state_summary':objective,'impact_summary':'POM compatibility and new regression/usage documentation only.',
 'changes':[{'id':'CHG-001','object_or_boundary':'resource:RSC-001','change':'modify','baseline_references':[ctxref],'baseline_state':'Java8 target and older processor/build versions.','target_state':'JDK21 build-compatible POMs without public Java source change.','affected_domains':['DOM-210','DOM-220','DOM-340','DOM-410']},{'id':'CHG-002','object_or_boundary':'resource:RSC-001','change':'add','baseline_references':[ctxref],'baseline_state':'No JDK21 migration assertions.','target_state':'Ten actual compatibility tests and precise migration notes.','affected_domains':['DOM-350','DOM-510']}],
 'decisions':[{'id':'DEC-001','requirement_references':[all_r[2]],'question':'Which compatibility path minimizes unrelated API migration?','options':['Move to a new Spring major','Retain Spring5 API generation and align JDK21-compatible build/processor versions'],'decision':'Retain Spring5.3.39, use Lombok1.18.30, compiler3.11.0 and Surefire3.2.5.','rationale':'Meets JDK21 while preserving existing framework code and avoiding unrelated service/web changes.','affected_domains':['DOM-210','DOM-220','DOM-340']}],
 'traceability':[{'source_references':[r,ac],'design_references':['CHG-001','CHG-002','DOM-510'],'decision_references':['DEC-001'],'vfy_references':['VFO-001']} for r,ac in zip(all_r,all_ac)],
 'domains':domains,'composite_subdomains':composite,'cross_domain_conflicts':[],'scope_expansion':False,'simplicity_rationale':'Existing Maven reactor and public code retained; no new shared abstraction, server, UI or provider.',
 'lifecycle_applicability':[{'phase':ph,'disposition':'required','host':'N/A','basis':'Ordered migration and test work, current-result verification and local Sandbox qualification.'} for ph in ('PLN','IMP','VFY','RLS')], 'evidence':[],'supporting_members':[],'open_items':[],'exceptions':[]}
dsref=io.complete('200-dsn',{'design':design},[reqref])
if a.until=='DSN':raise SystemExit(0)
s=io.read(dsref);tables=list(parse_canonical_artifact(s.payload.primary_blob).tables)
for m in s.payload.members:
    if m.media_type=='text/markdown':tables.extend(parse_markdown_tables(m.raw_bytes.decode()))
obligations=[]
for t in tables:
    for row in t.rows:
        item=row.get('ID') or row.get('Change ID')
        if isinstance(item,str) and re.fullmatch(r'(?:CHG|VFP|OBJ|OBL|EX|R|AC)-[A-Za-z0-9._-]+',item):
            reference=f'{dsref}#{item}'
            if reference not in obligations:obligations.append(reference)
change1=dsref+'#CHG-001';change2=dsref+'#CHG-002'
work=[]
for n,phase,outcome,sources,depends,completion,evidence in [
 (1,'IMP','Align the reactor build and processor dependencies for JDK21.',[change1],[],'POMs explicitly target JDK21 and retain public Java source.','Exact preconditioned POM changes and content checks.'),
 (2,'IMP','Add and execute JDK21 behavior regression and migration instructions.',[change2],['WI-001'],'Ten real compatibility tests and migration notes exist and Maven verify succeeds.','Current immutable result, actual Maven test output and packaging log.'),
 (3,'VFY','Verify the full current migration requirement and design.',[x for x in obligations if '#VFP-' in x],['WI-002'],'All current objectives have real passing JDK21 behavior evidence.','Actual current-subject Maven/JUnit output and source hashes.'),
 (4,'RLS','Qualify the approved version in a disposable local Sandbox.',[change1],['WI-003'],'The exact qualified version is applied and observed on the local target.','Bound release effect and target version readback.')]:
    work.append({'id':f'WI-{n:03d}','target_phase':phase,'outcome':outcome,'execution_scope':['resource:RSC-001']+(['environment:ENV-001'] if phase=='RLS' else []),'source_references':sources,'constraint_references':[],'depends_on':depends,'completion_criteria':completion,'expected_evidence':evidence,'responsible_role':'Java maintainer' if phase=='IMP' else 'Verification or local release executor'})
plan={'title':'SpringGear ordered JDK21 migration','summary':'Build alignment, executable behavior tests, full verification and local Sandbox release.',
 'profile':'full','pln_disposition':'required','delivery_scope':[{'source_artifact_reference':dsref,'inclusion_basis':'Complete selected JDK21 design; no partial obligation selection.'}],
 'obligations':obligations,'work_items':work,'aggregated_applicability':[],
 'lifecycle_applicability':[{'phase':ph,'disposition':'required','host':'N/A','basis':'Consume the complete design with a sequential current-result chain.'} for ph in ('IMP','VFY','RLS')],
 'open_items':[],'exceptions':[],'evidence':[],'supporting_members':[]}
plnref=io.complete('300-pln',{'plan':plan},[dsref])
if a.until=='PLN':raise SystemExit(0)
CONSIDERATIONS=('Calculation Rules','Decision Rules','State Transitions','Algorithm & Invariants','Data Contract & Transformation','Boundary & Failure Handling','Effects & Consistency')
for n in (1,2):
    label=f'IMP-{n}'
    if label in io.state['stages']:continue
    methodpath=io.out/f'implementation-{n}.json'
    if methodpath.exists():method=json.loads(methodpath.read_text())
    else:
        files=['pom.xml','springgear-parent/pom.xml'] if n==1 else ['springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java','JDK21-MIGRATION.md']
        ops=[]
        for name in files:
            old=WORK/'source'/name
            ops.append({'resource':'RSC-001','path':name,'step':'STEP-001','op':'write_text','expected_sha256':'sha256:'+hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else 'absent','content':(CASE/'candidate'/name).read_text()})
        blocks=[{'consideration':'Boundary & Failure Handling','id':'ERR-001','trigger':'Source precondition, compilation, test discovery or compatibility assertion fails.','classification':'Incomplete migration rather than successful delivery.','handling':'Retain exact failure and source result; correct the bounded migration or environment and retry.','observable_result':'No false VFY-ready state or hidden failed tests.','recovery':'Resume the same valid attempt or use the formal rework path without deleting evidence.'},
        {'consideration':'Effects & Consistency','id':'EFF-001','resource_or_effect':'Declared Maven reactor files and isolated test/build outputs','order_and_condition':'Align POMs before adding tests; all writes bind current expected content.','consistency_or_atomicity':'Each source effect has a persistent checkpoint and immutable resource result.','idempotency':'Completed writes are not replayed on confirmation or retry.','failure_handling':'Leave failed checks visible; no Maven deployment, Git update or external system mutation.'}]
        names=[b['consideration'] for b in blocks]
        method={'considerations':[{'name':c,'disposition':'required' if c in names else 'n/a','basis':'Preserve bounded source and build effects with visible failures.' if c in names else 'No new product calculation, decision, state, algorithm or data schema; existing Java behavior remains unchanged.','steps':['STEP-001'] if c in names else [],'exception':'N/A'} for c in CONSIDERATIONS],
        'steps':[{'id':'STEP-001','order':1,'purpose':work[n-1]['outcome'],'target':['resource:RSC-001'],'basis_references':[f'{plnref}#WI-{n:03d}',change1 if n==1 else change2],'considerations':names,'logic':['Read exact selected design and current resource baseline.','Apply only declared compatibility or regression files with content preconditions.','Execute bounded checks and retain the complete current immutable source result.'],'expected_result':work[n-1]['completion_criteria'],'transaction_boundary':'One dependency-ordered source migration increment; isolated local build outputs only.','failure_boundary':'Any incompatible source, toolchain or test result prevents completion.','blocks':blocks}],
        'resources':[{'id':'RSC-001','root':'source'}],'operations':ops,
        'checks':[{'id':'CHK-001','name':'Declared Java21 compiler release','resource':'RSC-001','kind':'contains','path':'pom.xml','expected':'<maven.compiler.release>21</maven.compiler.release>'}],
        'design_decision_references':[dsref+'#DEC-001'],'exceptions':[],'open_items':[]}
        if n==2:method['checks'].append({'id':'CHK-002','name':'Offline JDK21 reactor verify with actual regression','resource':'RSC-001','kind':'project_command','cwd':'.','command':['mvn','verify'],'timeout_seconds':180})
        methodpath.write_text(json.dumps(method,ensure_ascii=False,indent=2)+'\n')
    io.complete('400-imp',{'inputs':{'implementation':method}},[plnref]+([io.state['stages']['IMP-1']] if n==2 else []),label=label,binding=f'{plnref}#WI-{n:03d}')
if a.until=='IMP':raise SystemExit(0)
terminal=io.state['stages']['IMP-2']+'/RESULT-RES-001'
vfo=next(row for m in io.read(dsref).payload.members if m.member_id=='DOM-510' for t in parse_markdown_tables(m.raw_bytes.decode()) for row in t.rows if row.get('ID')=='VFO-001')
vfy={'targets':[{'reference':dsref+'#VFO-001','purpose':vfo['Kind'],'summary':vfo['可观察结果 Observable Result'],'source_kind':'vfo','obligation_references':[dsref+'#'+x.strip() for x in vfo['Domain VFY Point References'].split(',')]}],
 'methods':[{'id':'VFM-001','title':'Current-result JDK21 reactor tests','purpose':'both','target_references':[dsref+'#VFO-001'],'subject_references':[terminal],
 'obligation_references':sorted([dsref+'#'+x for x in [*vfps,'VFM-001','VPC-001','VEC-001']]+[plnref+f'#WI-{n:03d}' for n in (1,2,3)]),
 'method_type':'test','disposition':'required','execution_mode':'automated','executor_identity':EXECUTOR,
 'environment':{'project_root':'.','data_contract':'Public exact current source; JDK21 and prepared offline Maven cache; no external services.'},
 'procedure':{'kind':'command','argv':['mvn','-o','-B','-ntp','test'],'policy':'deterministic-test-v1','workspace':'isolated-copy','network':'disabled','cwd':'source','timeout_seconds':180,'max_output_bytes':1048576},
 'pass_criteria':'Ten actually executed JUnit methods, zero failures/errors/skips, runtime21 and bytecode65 assertions, preserved context and pipeline behavior.',
 'evidence_requirement':'Actual Maven output, JUnit execution identities, exit code, OS containment and unchanged source hashes; no reuse of preparation output.'}]}
io.verify_and_close(plnref,terminal,vfy,reqref)
