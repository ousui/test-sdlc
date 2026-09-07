---
contract: sdlc-ai-spec/artifact/v1
phase: REQ
id: REQ-20260907102036-01
revision: 1
status: ready
context: CTX-20260907102036-01@1
profile: full
inputs:
---

# Enable and disable managed accounts

## 摘要 Summary

Add a persisted account availability state with immediate old-session revocation and a working admin filter/edit flow.

## 原始输入 Source Input

| ID | Type | Content or Immutable Reference | Evidence Reference |
|---|---|---|---|
| SRC-001 | conversation | Add enabled/disabled account state with filtering, editing and disabled-user access revocation; use a small existing web admin project for SDLC validation. | CTX-20260907102036-01@1/SUP-001 |

## 目标与成功条件 Goal and Success

| ID | 当前问题 Current Problem | 目标结果与预期用途 Goal, Intended Outcome and Use | 成功条件 Success Condition |
|---|---|---|---|
| GOAL-001 | An account cannot currently be administratively disabled without deletion. | An enabled manager can suspend and restore access without deleting accounts. | Real application requests demonstrate filtering, edits, revocation and persistence with no unauthorized mutation. |

## 范围 Scope

### 包含 In Scope

- Existing Flask-Admin authentication example
- Enabled flag, filter/edit, session revocation and additive SQLite migration
- Functional automated tests and local sandbox release

### 不包含 Out of Scope

- Production deployment
- New role hierarchy or full RBAC
- Subjective visual/UX acceptance
- Upstream changes or user data

## 影响对象 Affected Parties

| ID | 对象 Affected Party | Stakeholder Need or Impact |
|---|---|---|
| None | No distinct affected parties | N/A |

## 需求项 Requirements

| ID | 类型 Type | 来源或父项引用 Source or Parent References | 需求描述 Requirement Statement |
|---|---|---|---|
| R-001 | behavior | SRC-001, GOAL-001 | An enabled account can authenticate and use the account administration view; a disabled account cannot authenticate. |
| R-002 | behavior | SRC-001, GOAL-001 | The account view shows and filters enabled status and permits an authenticated enabled manager to change it. |
| R-003 | rule | SRC-001, GOAL-001 | Disabling an account revokes previously issued login sessions on the next protected request; re-enabling it does not resurrect revoked sessions. |
| R-004 | quality | SRC-001, GOAL-001 | The enabled state survives restart; additive migration preserves existing account rows and is idempotent. |
| R-005 | constraint | SRC-001, GOAL-001 | Protect authentication and writes with CSRF, reject anonymous and forged sessions and off-site next redirects; retain the teaching example authorization model without a new RBAC system. |

## 验收条件 Acceptance Criteria

| ID | 关联需求 Requirement References | 条件 Condition | 预期结果 Expected Result |
|---|---|---|---|
| AC-001 | R-001 | Login with enabled versus disabled account credentials | Enabled account reaches protected list; disabled login is rejected. |
| AC-002 | R-002 | An enabled manager edits another account and filters the list by status | Stored status changes and filtered results match database state. |
| AC-003 | R-003 | Retain a cookie, disable and re-enable its account | Old cookie is rejected both times; fresh login after enable succeeds; unaffected manager retains access. |
| AC-004 | R-004 | Restart after a state change and migrate a legacy SQLite table twice | State and original rows/IDs remain; migration is idempotent. |
| AC-005 | R-005 | Try missing/invalid CSRF, forged/anonymous sessions, off-site next and malformed registration | Unauthorized mutation/login fails; logout is POST-only; redirect stays local; no silent account creation. |

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
| DSN | required | N/A | Bounded real feature needs design, ordered implementation, actual tests and local sandbox delivery. |
| PLN | required | N/A | Bounded real feature needs design, ordered implementation, actual tests and local sandbox delivery. |
| IMP | required | N/A | Bounded real feature needs design, ordered implementation, actual tests and local sandbox delivery. |
| VFY | required | N/A | Bounded real feature needs design, ordered implementation, actual tests and local sandbox delivery. |
| RLS | required | N/A | Bounded real feature needs design, ordered implementation, actual tests and local sandbox delivery. |

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
| 1 | sha256:6d7db1ff48f9acdcfe067a06440ac07582f1bcc22962b80a472f02e736836abb | docs/v1.1/100-req-spec.md@sha256:13907cab3f1a9a5575d0d292901dc532f2a1c15f5b345f4fa8b7e20b137ed3f0, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:be72a77a11285fc409116f296aea8d370e5308077b425050127e9dc87bee4b7c | approved | delegated | deterministic-review-process:2335 | Delegated Independent Reviewer | .sdlc/authority/REQ-20260907102036-01-r1-2335.md@sha256:e17f66399105ab49a278cfcf755307b11ab15730fab53066633ebdd6537c6073 | None | 2026-09-07T10:20:37+00:00 |

### Artifact Gate Summary

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 | sha256:6d7db1ff48f9acdcfe067a06440ac07582f1bcc22962b80a472f02e736836abb | docs/v1.1/100-req-spec.md@sha256:13907cab3f1a9a5575d0d292901dc532f2a1c15f5b345f4fa8b7e20b137ed3f0, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:be72a77a11285fc409116f296aea8d370e5308077b425050127e9dc87bee4b7c | pass | None | sdlc-100-req-runtime | 2026-09-07T10:20:37Z |
