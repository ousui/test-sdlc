# 接口与集成 Interfaces and Integration

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907134709-01 |
| Parent Revision | 1 |
| Requirement References | REQ-20260907134708-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### HTTP and media contracts

Public GET endpoints expose only projections without hashes/media bytes except dedicated media routes. Writes are POST application/json with exact field sets, 2MiB body cap and CSRF. Audio URLs support GET/HEAD/Range; photo URLs recheck published parent.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-230-001 | constraint | Retain all requested modules, bounded local scope and the selected trust/consistency rules. | IMP, VFY, RLS | REQ-20260907134708-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-230-001 | REQ-20260907134708-01@1#AC-004, REQ-20260907134708-01@1#AC-005, REQ-20260907134708-01@1#AC-006, REQ-20260907134708-01@1#AC-009 | HTTP and media contracts | Statuses, projection fields, protected writes and stream bytes match API contracts. | Named current-source tests, actual logs, immutable result and matching source/permission boundaries. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907134707-01@1/SUP-001 | CHG-001, CHG-002, CHG-003 | Authorized new-project scope and dependency provenance |
