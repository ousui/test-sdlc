---
contract: sdlc-ai-spec/artifact/v1
phase: REQ
id: REQ-20260907134708-01
revision: 1
status: ready
context: CTX-20260907134707-01@1
profile: full
inputs:
---

# 从零构建杨千嬅主题非官方粉丝网站

## 摘要 Summary

Go/HTML/native JavaScript site: fans, music previews, albums and minimal administrator management, with real local functional tests.

## 原始输入 Source Input

| ID | Type | Content or Immutable Reference | Evidence Reference |
|---|---|---|---|
| SRC-001 | conversation | 用户原需求：做一个杨千嬅主题个人粉丝网站，Go+jQuery+HTML，基本展示、用户（粉丝）体系、音乐试听、相册、简单后台。后续明确批准既有Go版本，必要时原生JavaScript代替jQuery，合理精简环境；目标是通用SDLC验证，不是生产上线。本次保留全部模块，限定WAV试听与PNG/JPEG相片、单进程本地JSON，三工作项衔接验证。 | CTX-20260907134707-01@1/SUP-001 |

## 目标与成功条件 Goal and Success

| ID | 当前问题 Current Problem | 目标结果与预期用途 Goal, Intended Outcome and Use | 成功条件 Success Condition |
|---|---|---|---|
| GOAL-001 | No usable application exists in the new versioned scaffold. | A complete local fan site with connected public/account/media/admin functions and traceable lifecycle. | All stated acceptance conditions pass on the current final implementation; formal VFY, local Sandbox RLS and Status agree. |

## 范围 Scope

### 包含 In Scope

- Public site and native frontend assets
- Fans and protected administrator accounts
- Bounded WAV previews and image albums
- Local transactional persistence, offline tests and Sandbox lifecycle

### 不包含 Out of Scope

- Production hosting or payment
- Artist recordings or photos
- Subjective UI/UX approval
- Distributed persistence, translation, SEO or feature expansion

## 影响对象 Affected Parties

| ID | 对象 Affected Party | Stakeholder Need or Impact |
|---|---|---|
| None | No distinct affected parties | N/A |

## 需求项 Requirements

| ID | 类型 Type | 来源或父项引用 Source or Parent References | 需求描述 Requirement Statement |
|---|---|---|---|
| R-001 | behavior | SRC-001, GOAL-001 | Display an unofficial Miriam Yeung themed home, music, album and account pages using Go, HTML and native JavaScript without remote page dependencies. |
| R-002 | behavior | SRC-001, GOAL-001 | Fans can register, log in, view/edit only their own profile and log out; email is normalized and unique, input limits apply. |
| R-003 | rule | SRC-001, GOAL-001 | Use explicit one-time administrator initialization; ordinary registration cannot grant roles. Only enabled admins manage users, homepage, tracks, albums and photos. |
| R-004 | rule | SRC-001, GOAL-001 | Use salted slow password derivation, random expiring opaque sessions, protected cookies, CSRF and same-origin checks. Disable revokes current and stale-generation sessions; re-enable needs a new login. |
| R-005 | behavior | SRC-001, GOAL-001 | Published WAV previews support real GET/HEAD/Range; drafts, removed and unpublished media remain inaccessible by direct URL. |
| R-006 | behavior | SRC-001, GOAL-001 | Administrators create/edit/publish/unpublish/delete albums, upload bounded PNG/JPEG photos and delete photos. Associations persist and removed albums expose no orphan images. |
| R-007 | behavior | SRC-001, GOAL-001 | Administrators can edit public site text and create/edit/publish/unpublish/delete music, and list/enable/disable fans without disabling the last management account. |
| R-008 | quality | SRC-001, GOAL-001 | Persist users, site, albums and music in a single-process local JSON store across restart. Concurrent updates preserve uniqueness and no lost writes; persistence failure does not publish partial in-memory state. |
| R-009 | quality | SRC-001, GOAL-001 | Reject unauthorized, unknown-field, oversized or malformed writes. Escape user content, bound media types and sizes, and do not expose credential material. |
| R-010 | constraint | SRC-001, GOAL-001 | Use no artist recordings/photos or real customer data; provide generated test-media tooling, complete source/license and run instructions. RLS is local Sandbox only, not application deployment. |

## 验收条件 Acceptance Criteria

| ID | 关联需求 Requirement References | 条件 Condition | 预期结果 Expected Result |
|---|---|---|---|
| AC-001 | R-001 | Read all public pages and native assets | Pages/assets load, unofficial notice present; unauthenticated profile/admin denied. |
| AC-002 | R-002 | Register, edit profile, logout, replay cookie and login again | Own profile persists; old cookie rejected; duplicate normalized email, invalid email/password and oversized fields rejected. |
| AC-003 | R-003 | Bootstrap, normal register and try administrative routes/role injection | Only the explicitly bootstrapped administrator manages content/users; fan or forged role input does not escalate. |
| AC-004 | R-004 | Disable/re-enable, expire/replay sessions, tamper CSRF and Origin | Current and stale login generations remain revoked, invalid writes denied, required cookie flags set and no plaintext stored. |
| AC-005 | R-005 | Create a draft track, publish and retrieve full/ranged audio, then unpublish/delete | Actual bytes match; HEAD empty, valid Range206/invalid Range416; unpublished/deleted URLs404. |
| AC-006 | R-006 | Create/edit album, upload valid/invalid photo, publish/unpublish and delete | Valid photo round-trips; bad type/size/missing association rejected; no direct draft or orphan media access. |
| AC-007 | R-007 | Admin edits homepage and manages listings and fan state | Current public text reflects edits, lists show actual records, administrator disable rejected and fan disable enforced. |
| AC-008 | R-008 | Restart, race duplicate registration and content writes, inject storage failure | Entities and references survive; sessions restart invalid; exactly one duplicate account, no lost updates, rejected write preserves memory/disk. |
| AC-009 | R-009 | Send bad content types/unknown JSON fields/oversized bodies and display markup text | Requests rejected without unauthorized state changes; template and JS text nodes escape untrusted content. |
| AC-010 | R-010 | Inspect run instructions, licensing, sample generator and full combined user journey | No unlicensed media or actual secrets; source builds offline, generated media plays, whole fan/admin journey succeeds. |

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
| DSN | required | N/A | Multi-module design, dependency-ordered implementation, current-result verification and local Sandbox delivery. |
| PLN | required | N/A | Multi-module design, dependency-ordered implementation, current-result verification and local Sandbox delivery. |
| IMP | required | N/A | Multi-module design, dependency-ordered implementation, current-result verification and local Sandbox delivery. |
| VFY | required | N/A | Multi-module design, dependency-ordered implementation, current-result verification and local Sandbox delivery. |
| RLS | required | N/A | Multi-module design, dependency-ordered implementation, current-result verification and local Sandbox delivery. |

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
| 1 | sha256:2e379bd11acfe245b5dc33c7afdf77d13cb948d6a96bd517c34e9f9559bea8f0 | docs/v1.1/100-req-spec.md@sha256:13907cab3f1a9a5575d0d292901dc532f2a1c15f5b345f4fa8b7e20b137ed3f0, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:be72a77a11285fc409116f296aea8d370e5308077b425050127e9dc87bee4b7c | approved | delegated | deterministic-review-process:2398 | Delegated Independent Reviewer | .sdlc/authority/REQ-20260907134708-01-r1-2398.md@sha256:1e9c3c4b393b172ebe73b565d74d701ce9b1bf079bc45c61d443a2b1dcf4e693 | None | 2026-09-07T13:47:08+00:00 |

### Artifact Gate Summary

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 | sha256:2e379bd11acfe245b5dc33c7afdf77d13cb948d6a96bd517c34e9f9559bea8f0 | docs/v1.1/100-req-spec.md@sha256:13907cab3f1a9a5575d0d292901dc532f2a1c15f5b345f4fa8b7e20b137ed3f0, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:be72a77a11285fc409116f296aea8d370e5308077b425050127e9dc87bee4b7c | pass | None | sdlc-100-req-runtime | 2026-09-07T13:47:08Z |
