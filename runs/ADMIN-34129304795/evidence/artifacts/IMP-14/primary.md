---
contract: sdlc-ai-spec/artifact/v1
phase: IMP
id: IMP-20260907134735-01
revision: 1
status: waiting_input
context: CTX-20260907134729-01@1
profile: full
inputs:
  - PLN-20260907134731-01@1
  - IMP-20260907134732-01@1
---
# Implementation

## 摘要 Summary

Add reproducible account lifecycle tests and local usage documentation.

## 范围 Scope

- 结果 Outcome: Add reproducible account lifecycle tests and local usage documentation.
- 执行范围 Execution Scope: resource:RSC-001
- 排除项 Exclusions: Claim Scope 外资源、上游决策、完整 VFY 与发布

## 实施控制 Implementation Control

| Relationship | Reference |
|---|---|
| PLN Reference | PLN-20260907134731-01@1 |
| WI Binding | PLN-20260907134731-01@1#WI-002 |
| Context Reference | CTX-20260907134729-01@1 |
| Lineage | PLN-20260907134731-01@1, DSN-20260907134730-01@2, REQ-20260907134730-01@1, CTX-20260907134729-01@1 |

### 实施绑定 Implementation Binding

| IMP Binding Reference | Binding Lineage Key | Attempt | Owner | Rework References |
|---|---|---|---|---|
| PLN-20260907134731-01@1#WI-002 | PLN-20260907134731-01#WI-002 | 1 | web-realflow-admin-executor | None |

### 输入就绪检查 Input Readiness Check Set

| Check ID | 检查项 Check | Result | Evidence or Notes |
|---|---|---|---|
| IMP-RDY-001 | Binding uniquely resolves to the declared upstream disposition | pass | PLN-20260907134731-01@1#WI-002 |
| IMP-RDY-002 | One atomic Outcome is preserved | pass | PLN-20260907134731-01@1#WI-002 |
| IMP-RDY-003 | Completion Criteria and Expected Evidence are authoritative | pass | PLN-20260907134731-01@1#WI-002 |
| IMP-RDY-004 | Every Claim Resource has an exact Scope and Baseline source | pass | PLN-20260907134731-01@1#WI-002 |
| IMP-RDY-005 | All seven Implementation Considerations have a complete disposition | pass | PLN-20260907134731-01@1#WI-002 |
| IMP-RDY-006 | Context, Decisions, Dependencies and Exceptions remain traceable | pass | PLN-20260907134731-01@1#WI-002 |

## 实施方法合约 Implementation Method Contract

仅落实准确上游决定；公共抽象、依赖和跨模块接口必须有 DSN Decision。

### 实施考量矩阵 Implementation Consideration Matrix

| 实施考量项 Implementation Consideration | Disposition | 触发依据或 N/A 原因 | Approach Step 引用 | Exception 引用 |
|---|---|---|---|---|
| Calculation Rules | n/a | This work item adds regression and usage instructions, not new product calculation/decision/data/state rules. | None | N/A |
| Decision Rules | n/a | This work item adds regression and usage instructions, not new product calculation/decision/data/state rules. | None | N/A |
| State Transitions | n/a | This work item adds regression and usage instructions, not new product calculation/decision/data/state rules. | None | N/A |
| Algorithm & Invariants | n/a | This work item adds regression and usage instructions, not new product calculation/decision/data/state rules. | None | N/A |
| Data Contract & Transformation | n/a | This work item adds regression and usage instructions, not new product calculation/decision/data/state rules. | None | N/A |
| Boundary & Failure Handling | required | Required by account state, revocation and test consistency. | STEP-001 | N/A |
| Effects & Consistency | required | Required by account state, revocation and test consistency. | STEP-001 | N/A |

### 实施步骤 Implementation Approach

#### STEP-001 Add reproducible account lifecycle tests and local usage documentation.

- 顺序 Order: 1
- 目标位置 Target: resource:RSC-001
- 依据引用 Basis References: PLN-20260907134731-01@1#WI-002, DSN-20260907134730-01@2#CHG-002
- 适用考量项 Considerations: Boundary & Failure Handling, Effects & Consistency
- 预期结果 Expected Result: Executable tests and documentation exist on top of the exact first implementation result.
- Transaction Boundary: One bounded source implementation work item; request-time data transactions follow the approved design.
- Failure Boundary: Any failed precondition, source check or test leaves a visible incomplete work item.

实施逻辑：

1. Read the exact current baseline and declared design.
2. Add isolated current-source tests and reproducible account-state instructions.
3. Execute the declared local checks, retaining actual output and immutable final source.

##### ERR-001 Boundary & Failure Handling

- trigger: An invalid login, forged/disabled session, missing CSRF or schema initialization error.
- classification: Reject invalid/unauthorized requests; treat migration errors as failures rather than default success.
- handling: Validate before mutation, retain existing account data and report actionable errors without sensitive values.
- observable_result: Rejected request does not change stored state; failed initialization does not drop rows.
- recovery: Correct the input or isolated configuration, rerun the exact failed request and regression.

##### EFF-001 Effects & Consistency

- resource_or_effect: Declared application resource and its isolated test database
- order_and_condition: Read the exact predecessor result and precondition every source write; tests use fresh database state.
- consistency_or_atomicity: Account availability and session identifier rotate within one transaction; source effects remain recorded by IMP.
- idempotency: Same completed operation is not repeated; migration and repeated disable do not re-seed or resurrect data.
- failure_handling: Keep failed evidence and source state; never claim VFY success from an IMP syntax check.

## 实施结果 Implementation Result

| ID | Resource | Baseline Reference | Change Reference | Result Reference | Changed Scope | Approach Step References |
|---|---|---|---|---|---|---|
| RES-001 | RSC-001 | IMP-20260907134732-01@1/RESULT-RES-001 | IMP-20260907134735-01@1/CHANGE-RES-001 | IMP-20260907134735-01@1/RESULT-RES-001 | resource:RSC-001 | STEP-001 |

## 实施检查 Implementation Checks

| ID | 检查或方法 Check or Method | 范围 Scope | 结果 Result | 依据 Basis |
|---|---|---|---|---|
| CHK-001 | Parse application Python source | resource:RSC-001 | pass | IMP-20260907134735-01@1/EVD-CHK-001 |
| CHK-002 | Parse account lifecycle regression | resource:RSC-001 | pass | IMP-20260907134735-01@1/EVD-CHK-002 |
| CHK-003 | Actual isolated account lifecycle tests | resource:RSC-001 | pass | IMP-20260907134735-01@1/EVD-CHK-003 |

## 待确认项 Open Items

| ID | 所需输入或待确认决策 Needed Input or Decision | 预期来源 Expected Source | 被阻塞项 Blocked References | 状态 State | 解决结果或证据 Resolution or Evidence |
|---|---|---|---|---|---|
| None | No open items | N/A | N/A | closed | N/A |

## 证据 Evidence

| ID | Type | Supports References | Source or Producer | Reference | Integrity or Digest | Produced At | Sensitivity or Access | Empty Reason |
|---|---|---|---|---|---|---|---|---|
| BASE-RES-001 | snapshot | PLN-20260907134731-01@1#WI-002 | IMP Runtime | IMP-20260907134735-01@1/BASE-RES-001 | sha256:aea81c6e414c8f274dabbe14fa8789300a466c52f5eb2d5f0387edecf2e540d8 | N/A | project-local | N/A |
| CHANGE-RES-001 | execution | PLN-20260907134731-01@1#WI-002 | IMP Runtime | IMP-20260907134735-01@1/CHANGE-RES-001 | sha256:8ecc35f1ee36a7dbf0cc9c46a860780390d9845d941416846004530cfc9f6980 | N/A | project-local | N/A |
| EVD-CHK-001 | execution | PLN-20260907134731-01@1#WI-002 | IMP Runtime | IMP-20260907134735-01@1/EVD-CHK-001 | sha256:d9d981dae5b69862e3c7120ed971a578a807d12fd097920a5dad9db34f0253bf | N/A | project-local | N/A |
| EVD-CHK-002 | execution | PLN-20260907134731-01@1#WI-002 | IMP Runtime | IMP-20260907134735-01@1/EVD-CHK-002 | sha256:6919fb0399e20fc5374bd12fcaed67fc867544363bd6b1f17b794b77ac15e6d4 | N/A | project-local | N/A |
| EVD-CHK-003 | execution | PLN-20260907134731-01@1#WI-002 | IMP Runtime | IMP-20260907134735-01@1/EVD-CHK-003 | sha256:e28042ba75926b1ce2cbfe1569a5f8a3cb2129de487ada4b79e9eedece2052c1 | N/A | project-local | N/A |
| EVD-PRE | execution | PLN-20260907134731-01@1#WI-002 | IMP Runtime | IMP-20260907134735-01@1/EVD-PRE | sha256:e006d3bca979a54c2f6094ee5e229c5bc9df24efa6bafee8be542d5228da184d | N/A | project-local | N/A |
| RESULT-RES-001 | snapshot | PLN-20260907134731-01@1#WI-002 | IMP Runtime | IMP-20260907134735-01@1/RESULT-RES-001 | sha256:ded966a603f558d1e9b85c90274e705eed4c54c18daa9f56b867e5ce8d18a314 | N/A | project-local | N/A |

## Supporting Artifact Manifest

| Member ID | Type | Path or Reference | Media Type | Purpose | SHA-256 Digest | Empty Reason |
|---|---|---|---|---|---|---|
| BASE-RES-001 | supporting | snapshots/base-res-001.json | application/json | Supporting phase evidence | sha256:aea81c6e414c8f274dabbe14fa8789300a466c52f5eb2d5f0387edecf2e540d8 | N/A |
| CHANGE-RES-001 | supporting | evidence/change-res-001.json | application/json | Supporting phase evidence | sha256:8ecc35f1ee36a7dbf0cc9c46a860780390d9845d941416846004530cfc9f6980 | N/A |
| EVD-CHK-001 | supporting | evidence/evd-chk-001.json | application/json | Supporting phase evidence | sha256:d9d981dae5b69862e3c7120ed971a578a807d12fd097920a5dad9db34f0253bf | N/A |
| EVD-CHK-002 | supporting | evidence/evd-chk-002.json | application/json | Supporting phase evidence | sha256:6919fb0399e20fc5374bd12fcaed67fc867544363bd6b1f17b794b77ac15e6d4 | N/A |
| EVD-CHK-003 | supporting | evidence/evd-chk-003.json | application/json | Supporting phase evidence | sha256:e28042ba75926b1ce2cbfe1569a5f8a3cb2129de487ada4b79e9eedece2052c1 | N/A |
| EVD-PRE | supporting | evidence/evd-pre.json | application/json | Supporting phase evidence | sha256:e006d3bca979a54c2f6094ee5e229c5bc9df24efa6bafee8be542d5228da184d | N/A |
| IMP-STATE | supporting | evidence/imp-state.json | application/json | Supporting phase evidence | sha256:91e53e33e00424909c113013a6bb7daf02f0985e617da7531b03c8b5eb733ae4 | N/A |
| RESULT-RES-001 | supporting | snapshots/result-res-001.json | application/json | Supporting phase evidence | sha256:ded966a603f558d1e9b85c90274e705eed4c54c18daa9f56b867e5ce8d18a314 | N/A |

## 豁免 Exceptions

| ID | State | Origin Exception Reference | 作用域或被跳过义务 Scope or Skipped Obligation | 原因 Reason | 已知风险 Known Risk | 补偿措施 Compensating Control | 批准记录 Approver, Role and Time | 复查条件 Revisit Condition | 下游限制 Downstream Obligation | 解决或替代引用 Resolution or Superseding References |
|---|---|---|---|---|---|---|---|---|---|---|
| None | none | N/A | N/A | No Exceptions | N/A | N/A | N/A | N/A | N/A | N/A |

## 生命周期适用性 Lifecycle Applicability

| Phase | Disposition | Host | 判断依据 Basis |
|---|---|---|---|
| VFY | required | N/A | Consume complete design scope and preserve the ordered resource result chain. |
| RLS | required | N/A | Consume complete design scope and preserve the ordered resource result chain. |

## 门禁 Gate

| Check ID | 检查项 Check | 结果 Result | 证据或说明 Evidence or Notes |
|---|---|---|---|
| CORE-G-001 | CORE-G-001 | pass | Canonical records and immutable closure are checked |
| CORE-G-002 | CORE-G-002 | pass | Canonical records and immutable closure are checked |
| CORE-G-003 | CORE-G-003 | pass | Canonical records and immutable closure are checked |
| CORE-G-004 | CORE-G-004 | pass | Canonical records and immutable closure are checked |
| CORE-G-005 | CORE-G-005 | pass | Canonical records and immutable closure are checked |
| CORE-G-006 | CORE-G-006 | pass | Canonical records and immutable closure are checked |
| CORE-G-007 | CORE-G-007 | pass | Canonical records and immutable closure are checked |
| CORE-G-008 | CORE-G-008 | pass | Canonical records and immutable closure are checked |
| CORE-G-009 | CORE-G-009 | pending | Final Confirmation is required |
| IMP-G-001 | IMP-G-001 | pass | Exact Context, Binding, Claim and current Dependency chain |
| IMP-G-002 | IMP-G-002 | pass | One atomic Outcome and unchanged Claim Scope |
| IMP-G-003 | IMP-G-003 | pass | Method and persisted pre-execution readback |
| IMP-G-004 | IMP-G-004 | pass | Immutable Result readback and exact Changed Scope |
| IMP-G-005 | IMP-G-005 | pass | Applicable local Checks only; VFY readiness |
| IMP-G-006 | IMP-G-006 | pass | Result, Evidence and open obligations |
### Final Confirmation

| Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Result | Mode | Confirmer | Role | Authority Reference | Accepted Exception References | Confirmed At |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sha256:0ee2455615ce0aefc229930d5608d5bbbcd4583adf7302ffa4e6cbf354f72199 | docs/v1.1/400-imp-spec.md@sha256:1942f7eb0aaa641c04ddd29581d672fcbbd954d539f752a8ad4f606812f0d84c, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:d632081a57e8e6e884d0a1250c5bcb3bbba6645fdebd0dbd8ed96d22a5a462e8 | pending | N/A | N/A | N/A | N/A | None | N/A |

### Artifact Gate Summary

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 | sha256:0ee2455615ce0aefc229930d5608d5bbbcd4583adf7302ffa4e6cbf354f72199 | docs/v1.1/400-imp-spec.md@sha256:1942f7eb0aaa641c04ddd29581d672fcbbd954d539f752a8ad4f606812f0d84c, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:d632081a57e8e6e884d0a1250c5bcb3bbba6645fdebd0dbd8ed96d22a5a462e8 | pending | None | sdlc-400-imp | N/A |
