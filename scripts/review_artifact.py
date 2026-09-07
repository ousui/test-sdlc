"""Separate deterministic readback reviewer; not an AI or human review.

Reads current bytes through public ArtifactStore and recomputes bindings.
Never creates or modifies the Artifact or its product.
"""
import argparse, hashlib, json, os, re, sys
from pathlib import Path
from datetime import datetime, timezone
p=argparse.ArgumentParser()
for name in ('runtime','project','reference','executor','out'):p.add_argument('--'+name,required=True)
a=p.parse_args();root=Path(a.project).resolve();sys.path.insert(0,str(Path(a.runtime).resolve()))
from packages.sdlc_artifact_store import ArtifactStore
from packages.sdlc_runtime import parse_canonical_artifact, compute_control_input_digest, compute_check_set_result_digest
from packages.sdlc_runtime.canonical import CHECK_HEADERS, find_tables
identity,rev=a.reference.split('@');stored=ArtifactStore.open_read_only(root).read_revision(identity,int(rev))
assert stored.control.state=='open','Only a materialized open candidate may receive new approval'
raw=stored.payload.primary_blob;parsed=parse_canonical_artifact(raw)
assert stored.payload.primary_sha256=='sha256:'+hashlib.sha256(raw).hexdigest()
for member in stored.payload.members:assert member.sha256=='sha256:'+hashlib.sha256(member.raw_bytes).hexdigest()
rows=[row for table in find_tables(parsed,CHECK_HEADERS) for row in table.rows]
assert rows and len({r['Check ID'] for r in rows})==len(rows)
assert all(r['结果 Result']=='pass' for r in rows if r['Check ID']!='CORE-G-009')
sets={r['Evaluation Contract Set'] for t in parsed.tables for r in t.rows if r.get('Evaluation Contract Set') not in (None,'','N/A')}
assert len(sets)==1
evaluation=sets.pop();refs=evaluation.split(', ')
assert refs==sorted(set(refs)) and all(re.fullmatch(r'docs/v1\.1/[a-zA-Z0-9_./-]+\.md@sha256:[0-9a-f]{64}',x) for x in refs)
if stored.payload.artifact_type=='CTX':
 from packages.sdlc_runtime.authority_compat import compute_ctx_control_input_digest, CTX_CHECK_HEADERS
 ctx_tables=find_tables(parsed,CTX_CHECK_HEADERS)
 assert len(ctx_tables)==1 and all(row['Result']=='pass' for row in ctx_tables[0].rows)
 control=compute_ctx_control_input_digest(raw);digest_rows=[]
 for table in (*find_tables(parsed,CHECK_HEADERS),*ctx_tables):
  digest_rows.extend(line for row,line in zip(table.rows,table.raw_rows) if row['Check ID']!='CORE-G-009')
 check='sha256:'+hashlib.sha256(('\n'.join(digest_rows)+'\n').encode()).hexdigest()
else:
 control=compute_control_input_digest(raw);check=compute_check_set_result_digest(parsed)
basis=root/'.sdlc/authority/work-authorization.md';assert basis.is_file()
basis_ref=str(basis.relative_to(root))+'@sha256:'+hashlib.sha256(basis.read_bytes()).hexdigest()
reviewer='deterministic-review-process:'+str(os.getpid());assert reviewer!=a.executor
now=datetime.now(timezone.utc).isoformat(timespec='seconds')
excluded='business_or_design_choice, exception_or_risk_acceptance, external_action_or_side_effect, external_permission_or_authorization, subjective_or_human_experience_judgment'
text=f'''---
contract: sdlc-ai-spec/final-confirmation-authority/v1
artifact: {a.reference}
decision: approved
decided_at: {now}
---

| Delegation Basis | Reviewer Identity | Reviewer Role | Reviewed Executor Identity | Independence | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Excluded Authority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {basis_ref} | {reviewer} | Delegated Independent Reviewer | {a.executor} | fresh_read, recomputed, separate_execution_identity | {control} | {evaluation} | {check} | {excluded} |
'''
f=root/f'.sdlc/authority/{identity}-r{rev}-{os.getpid()}.md';f.write_text(text.rstrip()+'\n')
result={'type':'final_confirmation','result':'approved','mode':'delegated','confirmer':reviewer,'role':'Delegated Independent Reviewer','reviewed_executor':a.executor,'authority_reference':str(f.relative_to(root))+'@sha256:'+hashlib.sha256(f.read_bytes()).hexdigest(),'accepted_exception_references':[],'confirmed_at':now,'control_input_digest':control,'evaluation_contract_set':evaluation,'check_set_result_digest':check}
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
