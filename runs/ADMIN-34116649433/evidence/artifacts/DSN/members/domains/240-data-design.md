# 数据设计 Data Design

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907112710-01 |
| Parent Revision | 2 |
| Requirement References | REQ-20260907112710-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### Persisted enabled status and alternative identifier

Add Boolean enabled with non-null true default and rotate alternative_id only on a true-to-false transition. New credentials use salted password hashing. The per-app instance secret is supplied externally, never committed.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-240-001 | constraint | Preserve the existing teaching-project boundary and satisfy the requirement without production effects. | IMP, VFY, RLS | REQ-20260907112710-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-240-001 | REQ-20260907112710-01@1 | Persisted enabled status and alternative identifier | Database flags match forms; password storage is not plaintext; disable transitions rotate identifiers once. | Actual request assertions, database readback and execution output bound to the tested result. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907112709-01@1/SUP-001 | CHG-001 | Existing project provenance and isolated preparation |
