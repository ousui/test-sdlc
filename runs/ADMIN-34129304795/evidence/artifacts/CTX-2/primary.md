---
contract: sdlc-ai-spec/project-context/v1
id: CTX-20260907134729-01
revision: 1
status: draft
---

# Minimal Admin regression Project Context

## 摘要 Summary

Pinned Flask-Admin login example; SQLite; enabled-account lifecycle increment in an isolated clone.

## 项目标识 Project Identity

| Field | Value | Basis | Basis References |
|---|---|---|---|
| Project Name | Minimal Admin regression | observed | EVD-001 |
| Purpose | Manage example accounts and validate a real bounded account lifecycle change | observed | EVD-001 |
| Boundary | Isolated Flask-Admin teaching application source and ephemeral local SQLite only; no upstream or production writes. | confirmed | EVD-001 |
| Primary Resource Reference | RSC-001 | observed | EVD-001 |
| Authoritative References | pallets-eco/flask-admin@7fee0246b05476fb6bc38e44bcfb7cc87b978853 | observed | EVD-001 |

## 资源登记 Resource Registry

| ID | Type | Name | Role | Locator | Baseline Reference | Basis | Basis References |
|---|---|---|---|---|---|---|---|
| RSC-001 | application | Admin application | primary | source | d9924c2ddf36b9f28d717694018d53b4ce8f5e5b | observed | EVD-001 |

## 技术与工程基线 Technical and Engineering Baseline

### 技术基线 Technology Baseline

| ID | Category | Name | Version or Constraint | Purpose | Basis | Basis References |
|---|---|---|---|---|---|---|
| TEC-001 | runtime | Python / Flask-Admin / SQLite | Python 3.12 CI; Flask 3.1.2; Flask-Admin 2.0.2; local compatibility diagnostics 3.13 | Small authenticated SQLAlchemy administration application | observed | EVD-001 |

### 工程入口 Engineering Entry Points

| ID | Purpose | Command or Entry Point | Working Scope | Preconditions | Basis | Basis References |
|---|---|---|---|---|---|---|
| ENG-001 | run | python3 main.py | source | Dependencies prepared outside runtime; isolated temporary SQLite and instance secret supplied by environment | confirmed | EVD-001 |

## 项目结构 Project Topology

| ID | Name | Type | Resource Reference | Responsibility | Entry Point | Depends On | Authority Reference | Basis | Basis References |
|---|---|---|---|---|---|---|---|---|---|
| CMP-001 | Account admin | web-app | RSC-001 | Authentication, account list and editable status | main.py | None | EVD-001 | observed | EVD-001 |

## 项目规则 Project Rules

| ID | Category | Rule Summary | Scope | Authority Reference | Basis | Basis References |
|---|---|---|---|---|---|---|
| None | N/A | N/A | N/A | N/A | confirmed | EVD-001 |

## 环境与约束 Environment and Constraints

### 环境 Environment

| ID | Environment | Purpose | Accessibility | Data and Network Boundary | Basis | Basis References |
|---|---|---|---|---|---|---|
| ENV-001 | test | Synthetic development verification and local release target | available | No production data; isolated-copy verification; no network during runtime | confirmed | EVD-001 |

### 约束 Constraints

| ID | Constraint | Scope | Impact | Required Handling | Authority Reference | Basis | Basis References |
|---|---|---|---|---|---|---|---|
| None | N/A | N/A | N/A | N/A | N/A | confirmed | EVD-001 |

## 待确认项 Open Items

| ID | 所需输入或待确认决策 Needed Input or Decision | 预期来源 Expected Source | 被阻塞项 Blocked References | 状态 State | 解决结果或证据 Resolution or Evidence |
|---|---|---|---|---|---|
| None | No open items | N/A | N/A | none | N/A |

## 证据 Evidence

| ID | Type | Supports References | Source or Producer | Reference | Integrity or Digest | Produced At | Sensitivity or Access | Empty Reason |
|---|---|---|---|---|---|---|---|---|
| EVD-001 | source-inspection | RSC-001 | web-realflow-admin-executor | SUP-001 | sha256:586b189ceac7bf1ad8312f7c576880a5d40a5009ce6971c27753aa747549da46 | 2026-09-07T13:47:29+00:00 | Public example and synthetic test data only | N/A |

## 刷新摘要 Refresh Summary

| Base Revision | Observed At | Observation Baseline | Refresh Reason | Effective Change References | Evidence References |
|---|---|---|---|---|---|
| None | 2026-09-07T13:47:29+00:00 | d9924c2ddf36b9f28d717694018d53b4ce8f5e5b | Confirm complete observed context | None | EVD-001 |

## 支撑产物清单 Supporting Artifact Manifest

| Member ID | Type | Path or Reference | Media Type | Purpose | SHA-256 Digest | Empty Reason |
|---|---|---|---|---|---|---|
| SUP-001 | supporting | source-provenance.md | text/markdown | Pinned source and safety-preparation provenance | sha256:586b189ceac7bf1ad8312f7c576880a5d40a5009ce6971c27753aa747549da46 | N/A |

## 豁免 Exceptions

| ID | State | Origin Exception Reference | 作用域或被跳过义务 Scope or Skipped Obligation | 原因 Reason | 已知风险 Known Risk | 补偿措施 Compensating Control | 批准记录 Approver, Role and Time | 复查条件 Revisit Condition | 下游限制 Downstream Obligation | 解决或替代引用 Resolution or Superseding References |
|---|---|---|---|---|---|---|---|---|---|---|
| None | none | N/A | N/A | No Exceptions | N/A | N/A | N/A | N/A | N/A | N/A |

## 门禁 Gate

### Core Checks

| Check ID | 检查项 Check | 结果 Result | 证据或说明 Evidence or Notes |
|---|---|---|---|
| CORE-G-001 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-002 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-003 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-004 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-005 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-006 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-007 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-008 | Core Contract Integrity | pass | Deterministic runtime validation |
| CORE-G-009 | Core Contract Integrity | pending | Final Confirmation is not bound |

### CTX Checks

| Check ID | Check | Result | Basis References |
|---|---|---|---|
| CTX-G-001 | Project Context Contract | pass | Deterministic runtime validation |
| CTX-G-002 | Project Context Contract | pass | Deterministic runtime validation |
| CTX-G-003 | Project Context Contract | pass | Deterministic runtime validation |
| CTX-G-004 | Project Context Contract | pass | Deterministic runtime validation |
| CTX-G-005 | Project Context Contract | pass | Deterministic runtime validation |
| CTX-G-006 | Project Context Contract | pass | Deterministic runtime validation |

### Final Confirmation

| Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Result | Mode | Confirmer | Role | Authority Reference | Accepted Exception References | Confirmed At |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 |  | docs/v1.1/000-ctx-spec.md@sha256:1d98e7cce686664cbf9897cbac852c425644ba3ea81a0d9c1db5e27b0e530470, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b |  | pending |  |  |  | None | None |  |

### Artifact Gate Summary

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 |  | docs/v1.1/000-ctx-spec.md@sha256:1d98e7cce686664cbf9897cbac852c425644ba3ea81a0d9c1db5e27b0e530470, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b |  | pending | None | sdlc-000-ctx-runtime | 2026-09-07T13:47:29+00:00 |
