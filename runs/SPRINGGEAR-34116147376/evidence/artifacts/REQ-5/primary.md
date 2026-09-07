---
contract: sdlc-ai-spec/artifact/v1
phase: REQ
id: REQ-20260907112126-01
revision: 1
status: ready
context: CTX-20260907112125-01@1
profile: full
inputs:
---

# SpringGear JDK21 compatibility migration

## 摘要 Summary

Upgrade the existing active reactor to JDK21 with preserved core behavior and executable regression evidence.

## 原始输入 Source Input

| ID | Type | Content or Immutable Reference | Evidence Reference |
|---|---|---|---|
| SRC-001 | conversation | User changed the SpringGear migration target to JDK21 and authorized bounded environment-compatible regression; do not pursue JDK26. | CTX-20260907112125-01@1/SUP-001 |

## 目标与成功条件 Goal and Success

| ID | 当前问题 Current Problem | 目标结果与预期用途 Goal, Intended Outcome and Use | 成功条件 Success Condition |
|---|---|---|---|
| GOAL-001 | The framework reactor still targets Java8 and uses older build/processor dependencies. | Maintain and test the framework using JDK21 without redesigning its public API. | Current-result JDK21 compilation, bytecode and behavior tests pass, with exact source and complete SDLC evidence. |

## 范围 Scope

### 包含 In Scope

- Existing four-module Maven reactor
- Compatible dependency/build alignment
- Behavior tests, migration instructions and local Sandbox lifecycle

### 不包含 Out of Scope

- JDK26
- Disabled historical modules
- Production deployment or Maven Central release
- Public API redesign
- UI/UX review

## 影响对象 Affected Parties

| ID | 对象 Affected Party | Stakeholder Need or Impact |
|---|---|---|
| None | No distinct affected parties | N/A |

## 需求项 Requirements

| ID | 类型 Type | 来源或父项引用 Source or Parent References | 需求描述 Requirement Statement |
|---|---|---|---|
| R-001 | behavior | SRC-001, GOAL-001 | Compile the existing active four-module reactor on JDK21 and emit Java21 class files. |
| R-002 | behavior | SRC-001, GOAL-001 | Preserve existing workflow context, handler ordering, unsupported-handler behavior and exception conversion without changing public SpringGear source. |
| R-003 | constraint | SRC-001, GOAL-001 | Align the minimal compiler, processor, Spring and logging dependencies while retaining the Spring5 API generation; do not migrate to a new architecture. |
| R-004 | quality | SRC-001, GOAL-001 | Execute all declared regression tests with a real JUnit engine; zero failures, errors or skipped tests; a repeatable Maven verify succeeds. |
| R-005 | constraint | SRC-001, GOAL-001 | Document actual scope and local build commands; preserve upstream source/license and do not publish or modify upstream branches. |

## 验收条件 Acceptance Criteria

| ID | 关联需求 Requirement References | 条件 Condition | 预期结果 Expected Result |
|---|---|---|---|
| AC-001 | R-001 | JDK21 compiles the reactor | Runtime feature 21 and compiled class major 65 are asserted. |
| AC-002 | R-002 | Execute existing core behaviors | Context arguments, shared values, handler order/skip/failure and Spring configuration behavior pass. |
| AC-003 | R-003 | Compile Lombok-generated members and load Spring context | Constructors/accessors and Spring configuration enhancement work without add-opens or public-source rewriting. |
| AC-004 | R-004 | Execute the current test class on the current final result | Ten distinct tests execute, zero failures/errors/skips; Maven verify packages the active reactor. |
| AC-005 | R-005 | Inspect changed paths and migration instructions | Only POM compatibility, regression tests and migration instructions change; no deployment goals or upstream effects. |

## 依赖 Dependencies

| ID | 依赖项 Dependency | 要求状态 Required State | 当前状态 Current State | 状态检查引用 State Check Reference |
|---|---|---|---|---|
| None | No dependencies | N/A | N/A | N/A |

## 生命周期配置 Lifecycle Profile

| Selected Profile | Basis |
|---|---|
| full | Confirmed selection |

## 待确认项 Open Items

| ID | 所需输入或待确认决策 Needed Input or Decision | 预期来源 Expected Source | 被阻塞项 Blocked References | 状态 State | 解决结果或证据 Resolution or Evidence |
|---|---|---|---|---|---|
| None | No open items | N/A | N/A | none | N/A |

## 证据 Evidence

| ID | Type | Supports References | Source or Producer | Reference | Integrity or Digest | Produced At | Sensitivity or Access | Empty Reason |
|---|---|---|---|---|---|---|---|---|
| None | none | N/A | N/A | N/A | N/A | N/A | N/A | No independent Evidence |

## 支撑产物清单 Supporting Artifact Manifest

| Member ID | Type | Path or Reference | Media Type | Purpose | SHA-256 Digest | Empty Reason |
|---|---|---|---|---|---|---|
| None | none | N/A | N/A | N/A | N/A | No supporting artifacts |

## 豁免 Exceptions

| ID | State | Origin Exception Reference | 作用域或被跳过义务 Scope or Skipped Obligation | 原因 Reason | 已知风险 Known Risk | 补偿措施 Compensating Control | 批准记录 Approver, Role and Time | 复查条件 Revisit Condition | 下游限制 Downstream Obligation | 解决或替代引用 Resolution or Superseding References |
|---|---|---|---|---|---|---|---|---|---|---|
| None | none | N/A | N/A | No Exceptions | N/A | N/A | N/A | N/A | N/A | N/A |

## 生命周期适用性 Lifecycle Applicability

| Phase | Disposition | Host | 判断依据 Basis |
|---|---|---|---|
| DSN | required | N/A | Compatibility design, ordered build/test implementation, current-result verification and local Sandbox delivery. |
| PLN | required | N/A | Compatibility design, ordered build/test implementation, current-result verification and local Sandbox delivery. |
| IMP | required | N/A | Compatibility design, ordered build/test implementation, current-result verification and local Sandbox delivery. |
| VFY | required | N/A | Compatibility design, ordered build/test implementation, current-result verification and local Sandbox delivery. |
| RLS | required | N/A | Compatibility design, ordered build/test implementation, current-result verification and local Sandbox delivery. |

## 门禁 Gate

### Core Checks

| Check ID | 检查项 Check | 结果 Result | 证据或说明 Evidence or Notes |
|---|---|---|---|
| CORE-G-001 | Core Contract Integrity | pass | Artifact ID、Revision 与 Lineage 一致 |
| CORE-G-002 | Core Contract Integrity | pass | CTX 与直接 Input 已按准确 frozen Reference 解析 |
| CORE-G-003 | Core Contract Integrity | pass | 固定模板与 Canonical Payload 可构造 |
| CORE-G-004 | Core Contract Integrity | pass | Disposition 与 Lifecycle Applicability 一致 |
| CORE-G-005 | Core Contract Integrity | pass | Evidence 与 Supporting Member 使用固定索引 |
| CORE-G-006 | Core Contract Integrity | pass | 无未解决阻塞项 |
| CORE-G-007 | Core Contract Integrity | pass | Exception 记录结构有效 |
| CORE-G-008 | Core Contract Integrity | pass | Core 与 REQ Check Set 已完整登记 |
| CORE-G-009 | Core Contract Integrity | pass | Final Confirmation 绑定当前 Revision 与摘要 |

### REQ Checks

| Check ID | 检查项 Check | 结果 Result | 证据或说明 Evidence or Notes |
|---|---|---|---|
| REQ-G-001 | REQ Contract Integrity | pass | 原始输入已保留 |
| REQ-G-002 | REQ Contract Integrity | pass | 问题、目标与成功条件可判定 |
| REQ-G-003 | REQ Contract Integrity | pass | Scope 与可选对象/依赖使用合法结构 |
| REQ-G-004 | REQ Contract Integrity | pass | Requirement 原子且使用合法类型 |
| REQ-G-005 | REQ Contract Integrity | pass | Requirement 来源图有根、无环且引用可解析 |
| REQ-G-006 | REQ Contract Integrity | pass | Acceptance Criteria 覆盖全部 Requirement |
| REQ-G-007 | REQ Contract Integrity | pass | Profile 与 Basis 可保存 |
| REQ-G-008 | REQ Contract Integrity | pass | Lifecycle Applicability 完整 |

### Final Confirmation

| Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Result | Mode | Confirmer | Role | Authority Reference | Accepted Exception References | Confirmed At |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sha256:8c54cf390c5fe916a35746617892dc04ea2e941af331afb2c8ca0042cea2accb | docs/v1.1/100-req-spec.md@sha256:13907cab3f1a9a5575d0d292901dc532f2a1c15f5b345f4fa8b7e20b137ed3f0, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:be72a77a11285fc409116f296aea8d370e5308077b425050127e9dc87bee4b7c | approved | delegated | deterministic-review-process:2924 | Delegated Independent Reviewer | .sdlc/authority/REQ-20260907112126-01-r1-2924.md@sha256:b8222ed66c7ac278fd69edf22e4a6ffc14338fe5415226493379ad2175966a76 | None | 2026-09-07T11:21:26+00:00 |

### Artifact Gate Summary

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 | sha256:8c54cf390c5fe916a35746617892dc04ea2e941af331afb2c8ca0042cea2accb | docs/v1.1/100-req-spec.md@sha256:13907cab3f1a9a5575d0d292901dc532f2a1c15f5b345f4fa8b7e20b137ed3f0, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:be72a77a11285fc409116f296aea8d370e5308077b425050127e9dc87bee4b7c | pass | None | sdlc-100-req-runtime | 2026-09-07T11:21:26Z |
