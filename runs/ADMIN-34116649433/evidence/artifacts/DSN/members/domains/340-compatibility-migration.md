# 兼容与迁移 Compatibility and Migration

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907112710-01 |
| Parent Revision | 2 |
| Requirement References | REQ-20260907112710-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### Existing SQLite account migration

Inspect existing user columns before adding enabled with DEFAULT 1. Preserve id, username and other account data. Repeating migration is a no-op. Never drop or re-seed the legacy table.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-340-001 | constraint | Preserve the existing teaching-project boundary and satisfy the requirement without production effects. | IMP, VFY, RLS | REQ-20260907112710-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-340-001 | REQ-20260907112710-01@1 | Existing SQLite account migration | Two migration runs retain the original row identity and data; migrated accounts have an explicit enabled state. | Actual request assertions, database readback and execution output bound to the tested result. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907112709-01@1/SUP-001 | CHG-001 | Existing project provenance and isolated preparation |
