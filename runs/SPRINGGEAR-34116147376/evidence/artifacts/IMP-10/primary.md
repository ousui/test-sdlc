---
contract: sdlc-ai-spec/artifact/v1
phase: IMP
id: IMP-20260907112128-01
revision: 1
status: waiting_input
context: CTX-20260907112125-01@1
profile: full
inputs:
  - PLN-20260907112127-01@1
---
# Implementation

## 摘要 Summary

Align the reactor build and processor dependencies for JDK21.

## 范围 Scope

- 结果 Outcome: Align the reactor build and processor dependencies for JDK21.
- 执行范围 Execution Scope: resource:RSC-001
- 排除项 Exclusions: Claim Scope 外资源、上游决策、完整 VFY 与发布

## 实施控制 Implementation Control

| Relationship | Reference |
|---|---|
| PLN Reference | PLN-20260907112127-01@1 |
| WI Binding | PLN-20260907112127-01@1#WI-001 |
| Context Reference | CTX-20260907112125-01@1 |
| Lineage | PLN-20260907112127-01@1, DSN-20260907112126-01@1, REQ-20260907112126-01@1, CTX-20260907112125-01@1 |

### 实施绑定 Implementation Binding

| IMP Binding Reference | Binding Lineage Key | Attempt | Owner | Rework References |
|---|---|---|---|---|
| PLN-20260907112127-01@1#WI-001 | PLN-20260907112127-01#WI-001 | 1 | web-realflow-springgear-executor | None |

### 输入就绪检查 Input Readiness Check Set

| Check ID | 检查项 Check | Result | Evidence or Notes |
|---|---|---|---|
| IMP-RDY-001 | Binding uniquely resolves to the declared upstream disposition | pass | PLN-20260907112127-01@1#WI-001 |
| IMP-RDY-002 | One atomic Outcome is preserved | pass | PLN-20260907112127-01@1#WI-001 |
| IMP-RDY-003 | Completion Criteria and Expected Evidence are authoritative | pass | PLN-20260907112127-01@1#WI-001 |
| IMP-RDY-004 | Every Claim Resource has an exact Scope and Baseline source | pass | PLN-20260907112127-01@1#WI-001 |
| IMP-RDY-005 | All seven Implementation Considerations have a complete disposition | pass | PLN-20260907112127-01@1#WI-001 |
| IMP-RDY-006 | Context, Decisions, Dependencies and Exceptions remain traceable | pass | PLN-20260907112127-01@1#WI-001 |

## 实施方法合约 Implementation Method Contract

仅落实准确上游决定；公共抽象、依赖和跨模块接口必须有 DSN Decision。

### 实施考量矩阵 Implementation Consideration Matrix

| 实施考量项 Implementation Consideration | Disposition | 触发依据或 N/A 原因 | Approach Step 引用 | Exception 引用 |
|---|---|---|---|---|
| Calculation Rules | n/a | No new product calculation, decision, state, algorithm or data schema; existing Java behavior remains unchanged. | None | N/A |
| Decision Rules | n/a | No new product calculation, decision, state, algorithm or data schema; existing Java behavior remains unchanged. | None | N/A |
| State Transitions | n/a | No new product calculation, decision, state, algorithm or data schema; existing Java behavior remains unchanged. | None | N/A |
| Algorithm & Invariants | n/a | No new product calculation, decision, state, algorithm or data schema; existing Java behavior remains unchanged. | None | N/A |
| Data Contract & Transformation | n/a | No new product calculation, decision, state, algorithm or data schema; existing Java behavior remains unchanged. | None | N/A |
| Boundary & Failure Handling | required | Preserve bounded source and build effects with visible failures. | STEP-001 | N/A |
| Effects & Consistency | required | Preserve bounded source and build effects with visible failures. | STEP-001 | N/A |

### 实施步骤 Implementation Approach

#### STEP-001 Align the reactor build and processor dependencies for JDK21.

- 顺序 Order: 1
- 目标位置 Target: resource:RSC-001
- 依据引用 Basis References: PLN-20260907112127-01@1#WI-001, DSN-20260907112126-01@1#CHG-001
- 适用考量项 Considerations: Boundary & Failure Handling, Effects & Consistency
- 预期结果 Expected Result: POMs explicitly target JDK21 and retain public Java source.
- Transaction Boundary: One dependency-ordered source migration increment; isolated local build outputs only.
- Failure Boundary: Any incompatible source, toolchain or test result prevents completion.

实施逻辑：

1. Read exact selected design and current resource baseline.
2. Apply only declared compatibility or regression files with content preconditions.
3. Execute bounded checks and retain the complete current immutable source result.

##### ERR-001 Boundary & Failure Handling

- trigger: Source precondition, compilation, test discovery or compatibility assertion fails.
- classification: Incomplete migration rather than successful delivery.
- handling: Retain exact failure and source result; correct the bounded migration or environment and retry.
- observable_result: No false VFY-ready state or hidden failed tests.
- recovery: Resume the same valid attempt or use the formal rework path without deleting evidence.

##### EFF-001 Effects & Consistency

- resource_or_effect: Declared Maven reactor files and isolated test/build outputs
- order_and_condition: Align POMs before adding tests; all writes bind current expected content.
- consistency_or_atomicity: Each source effect has a persistent checkpoint and immutable resource result.
- idempotency: Completed writes are not replayed on confirmation or retry.
- failure_handling: Leave failed checks visible; no Maven deployment, Git update or external system mutation.

## 实施结果 Implementation Result

| ID | Resource | Baseline Reference | Change Reference | Result Reference | Changed Scope | Approach Step References |
|---|---|---|---|---|---|---|
| RES-001 | RSC-001 | IMP-20260907112128-01@1/BASE-RES-001 | IMP-20260907112128-01@1/CHANGE-RES-001 | IMP-20260907112128-01@1/RESULT-RES-001 | resource:RSC-001 | STEP-001 |

## 实施检查 Implementation Checks

| ID | 检查或方法 Check or Method | 范围 Scope | 结果 Result | 依据 Basis |
|---|---|---|---|---|
| CHK-001 | Declared Java21 compiler release | resource:RSC-001 | pass | IMP-20260907112128-01@1/EVD-CHK-001 |

## 待确认项 Open Items

| ID | 所需输入或待确认决策 Needed Input or Decision | 预期来源 Expected Source | 被阻塞项 Blocked References | 状态 State | 解决结果或证据 Resolution or Evidence |
|---|---|---|---|---|---|
| None | No open items | N/A | N/A | closed | N/A |

## 证据 Evidence

| ID | Type | Supports References | Source or Producer | Reference | Integrity or Digest | Produced At | Sensitivity or Access | Empty Reason |
|---|---|---|---|---|---|---|---|---|
| BASE-RES-001 | snapshot | PLN-20260907112127-01@1#WI-001 | IMP Runtime | IMP-20260907112128-01@1/BASE-RES-001 | sha256:baa95d55a98281c983ea9975d14c1b22c9f2364ba5c30c01e6898be2d04103aa | N/A | project-local | N/A |
| CHANGE-RES-001 | execution | PLN-20260907112127-01@1#WI-001 | IMP Runtime | IMP-20260907112128-01@1/CHANGE-RES-001 | sha256:4157519954795722b28405c80a8ae05c8d3e8f87633f88f522e5bdbc84278702 | N/A | project-local | N/A |
| EVD-CHK-001 | execution | PLN-20260907112127-01@1#WI-001 | IMP Runtime | IMP-20260907112128-01@1/EVD-CHK-001 | sha256:4a3a16e94b12ae3c8b14f0b260fa31a5af0950992fdb87bb4b348afc99dca2d2 | N/A | project-local | N/A |
| EVD-PRE | execution | PLN-20260907112127-01@1#WI-001 | IMP Runtime | IMP-20260907112128-01@1/EVD-PRE | sha256:d91c262049b95f2923cef6412b5cda336b32f8f42deb1b63e692a6ec9682926f | N/A | project-local | N/A |
| RESULT-RES-001 | snapshot | PLN-20260907112127-01@1#WI-001 | IMP Runtime | IMP-20260907112128-01@1/RESULT-RES-001 | sha256:ce40b25b1c3a4bdf67a7af0253320515a86c2ad89b2ecba2ddc1593e5c18f2c5 | N/A | project-local | N/A |

## Supporting Artifact Manifest

| Member ID | Type | Path or Reference | Media Type | Purpose | SHA-256 Digest | Empty Reason |
|---|---|---|---|---|---|---|
| BASE-RES-001 | supporting | snapshots/base-res-001.json | application/json | Supporting phase evidence | sha256:baa95d55a98281c983ea9975d14c1b22c9f2364ba5c30c01e6898be2d04103aa | N/A |
| CHANGE-RES-001 | supporting | evidence/change-res-001.json | application/json | Supporting phase evidence | sha256:4157519954795722b28405c80a8ae05c8d3e8f87633f88f522e5bdbc84278702 | N/A |
| EVD-CHK-001 | supporting | evidence/evd-chk-001.json | application/json | Supporting phase evidence | sha256:4a3a16e94b12ae3c8b14f0b260fa31a5af0950992fdb87bb4b348afc99dca2d2 | N/A |
| EVD-PRE | supporting | evidence/evd-pre.json | application/json | Supporting phase evidence | sha256:d91c262049b95f2923cef6412b5cda336b32f8f42deb1b63e692a6ec9682926f | N/A |
| IMP-STATE | supporting | evidence/imp-state.json | application/json | Supporting phase evidence | sha256:f3325a702560a2b9876a930456ac046541452d5070802f2dc535abc297410caa | N/A |
| RESULT-RES-001 | supporting | snapshots/result-res-001.json | application/json | Supporting phase evidence | sha256:ce40b25b1c3a4bdf67a7af0253320515a86c2ad89b2ecba2ddc1593e5c18f2c5 | N/A |

## 豁免 Exceptions

| ID | State | Origin Exception Reference | 作用域或被跳过义务 Scope or Skipped Obligation | 原因 Reason | 已知风险 Known Risk | 补偿措施 Compensating Control | 批准记录 Approver, Role and Time | 复查条件 Revisit Condition | 下游限制 Downstream Obligation | 解决或替代引用 Resolution or Superseding References |
|---|---|---|---|---|---|---|---|---|---|---|
| None | none | N/A | N/A | No Exceptions | N/A | N/A | N/A | N/A | N/A | N/A |

## 生命周期适用性 Lifecycle Applicability

| Phase | Disposition | Host | 判断依据 Basis |
|---|---|---|---|
| VFY | required | N/A | Consume the complete design with a sequential current-result chain. |
| RLS | required | N/A | Consume the complete design with a sequential current-result chain. |

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
| 1 | sha256:3167b318fd2198277477dc4b947c536376190a3c0b79ceba3681e590a85c7df1 | docs/v1.1/400-imp-spec.md@sha256:1942f7eb0aaa641c04ddd29581d672fcbbd954d539f752a8ad4f606812f0d84c, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:d632081a57e8e6e884d0a1250c5bcb3bbba6645fdebd0dbd8ed96d22a5a462e8 | pending | N/A | N/A | N/A | N/A | None | N/A |

### Artifact Gate Summary

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 | sha256:3167b318fd2198277477dc4b947c536376190a3c0b79ceba3681e590a85c7df1 | docs/v1.1/400-imp-spec.md@sha256:1942f7eb0aaa641c04ddd29581d672fcbbd954d539f752a8ad4f606812f0d84c, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:d632081a57e8e6e884d0a1250c5bcb3bbba6645fdebd0dbd8ed96d22a5a462e8 | pending | None | sdlc-400-imp | N/A |
