# 安全、隐私与合规 Security, Privacy and Compliance

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907134709-01 |
| Parent Revision | 1 |
| Requirement References | REQ-20260907134708-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### Account security and data minimization

Session cookies are HttpOnly/SameSiteStrict with Secure when TLS configured; raw tokens are not persisted. Server-issued independent CSRF values and Origin checks protect writes; session version increments on disable, so stale in-flight authentication cannot restore revoked sessions. Private credentials never appear in response projections. Test identities/media are synthetic.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-310-001 | constraint | Retain all requested modules, bounded local scope and the selected trust/consistency rules. | IMP, VFY, RLS | REQ-20260907134708-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-310-001 | REQ-20260907134708-01@1#AC-002, REQ-20260907134708-01@1#AC-003, REQ-20260907134708-01@1#AC-004, REQ-20260907134708-01@1#AC-009, REQ-20260907134708-01@1#AC-010 | Account security and data minimization | Security/privacy negative tests reject role injection, CSRF, forged/expired/revoked sessions and unauthorized edits. | Named current-source tests, actual logs, immutable result and matching source/permission boundaries. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907134707-01@1/SUP-001 | CHG-001, CHG-002, CHG-003 | Authorized new-project scope and dependency provenance |
