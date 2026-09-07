# 接口与集成 Interfaces and Integration

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907134730-01 |
| Parent Revision | 1 |
| Requirement References | REQ-20260907134730-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### Authentication and mutation endpoints

Reuse /admin/login/, /admin/register/, /admin/logout/ and account CRUD routes. Mutations are POST and CSRF protected; next accepts only local URLs. Read access alone never changes account state.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-230-001 | constraint | Preserve the existing teaching-project boundary and satisfy the requirement without production effects. | IMP, VFY, RLS | REQ-20260907134730-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-230-001 | REQ-20260907134730-01@1 | Authentication and mutation endpoints | Anonymous/forged requests are denied, missing CSRF cannot mutate, and external next never navigates off-site. | Actual request assertions, database readback and execution output bound to the tested result. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907134729-01@1/SUP-001 | CHG-001 | Existing project provenance and isolated preparation |
