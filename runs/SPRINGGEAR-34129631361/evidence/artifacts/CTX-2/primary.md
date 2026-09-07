---
contract: sdlc-ai-spec/project-context/v1
id: CTX-20260907135104-01
revision: 1
status: draft
---

# SpringGear Project Context

## 摘要 Summary

SpringGear existing four-module Java8-targeted reactor; controlled JDK21 compatibility migration.

## 项目标识 Project Identity

| Field | Value | Basis | Basis References |
|---|---|---|---|
| Project Name | SpringGear | observed | EVD-001 |
| Purpose | Spring-based workflow framework | observed | EVD-001 |
| Boundary | Isolated SpringGear four-module Maven reactor migration to JDK21; no disabled-module claim, upstream write or production deployment. | confirmed | EVD-001 |
| Primary Resource Reference | RSC-001 | observed | EVD-001 |
| Authoritative References | ousui/springgear@e855096ff19dcdb303dc4250ba19c30acd743ac7 | observed | EVD-001 |

## 资源登记 Resource Registry

| ID | Type | Name | Role | Locator | Baseline Reference | Basis | Basis References |
|---|---|---|---|---|---|---|---|
| RSC-001 | library | SpringGear reactor | primary | source | 20afb1cfbdaf2f64e4353e41298e1dde78d3e52d | observed | EVD-001 |

## 技术与工程基线 Technical and Engineering Baseline

### 技术基线 Technology Baseline

| ID | Category | Name | Version or Constraint | Purpose | Basis | Basis References |
|---|---|---|---|---|---|---|
| TEC-001 | runtime | Java / Maven / Spring / Lombok | Baseline Java8 target and Spring5.3.22; approved migration target JDK21 | Compile and exercise existing workflow framework | referenced | EVD-001 |

### 工程入口 Engineering Entry Points

| ID | Purpose | Command or Entry Point | Working Scope | Preconditions | Basis | Basis References |
|---|---|---|---|---|---|---|
| ENG-001 | test | mvn -o test | source | Prepared JDK21 and external Maven cache; no dependency installation during Skill execution | confirmed | EVD-001 |

## 项目结构 Project Topology

| ID | Name | Type | Resource Reference | Responsibility | Entry Point | Depends On | Authority Reference | Basis | Basis References |
|---|---|---|---|---|---|---|---|---|---|
| CMP-001 | Workflow core | library | RSC-001 | Workflow context, ordered handlers and Spring framework integration | springgear-core | None | EVD-001 | observed | EVD-001 |

## 项目规则 Project Rules

| ID | Category | Rule Summary | Scope | Authority Reference | Basis | Basis References |
|---|---|---|---|---|---|---|
| None | N/A | N/A | N/A | N/A | confirmed | EVD-001 |

## 环境与约束 Environment and Constraints

### 环境 Environment

| ID | Environment | Purpose | Accessibility | Data and Network Boundary | Basis | Basis References |
|---|---|---|---|---|---|---|
| ENV-001 | test | JDK21 isolated-copy testing and disposable local Sandbox target | available | Public source only; no network or upstream writes in formal execution | confirmed | EVD-001 |

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
| EVD-001 | source-inspection | RSC-001 | web-realflow-springgear-executor | SUP-001 | sha256:a1cff60852b1f3e288fffb5ab9357b00784cd1507028ed2b48709a63821ed540 | 2026-09-07T13:51:04+00:00 | Public open-source snapshot, no customer data | N/A |

## 刷新摘要 Refresh Summary

| Base Revision | Observed At | Observation Baseline | Refresh Reason | Effective Change References | Evidence References |
|---|---|---|---|---|---|
| None | 2026-09-07T13:51:04+00:00 | 20afb1cfbdaf2f64e4353e41298e1dde78d3e52d | Confirm complete observed project context | None | EVD-001 |

## 支撑产物清单 Supporting Artifact Manifest

| Member ID | Type | Path or Reference | Media Type | Purpose | SHA-256 Digest | Empty Reason |
|---|---|---|---|---|---|---|
| SUP-001 | supporting | source-provenance.md | text/markdown | Exact source and user-selected JDK21 scope | sha256:a1cff60852b1f3e288fffb5ab9357b00784cd1507028ed2b48709a63821ed540 | N/A |

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
| 1 |  | docs/v1.1/000-ctx-spec.md@sha256:1d98e7cce686664cbf9897cbac852c425644ba3ea81a0d9c1db5e27b0e530470, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b |  | pending | None | sdlc-000-ctx-runtime | 2026-09-07T13:51:05+00:00 |
