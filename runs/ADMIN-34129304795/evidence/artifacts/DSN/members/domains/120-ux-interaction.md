# 用户体验与交互 UX and Interaction

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907134730-01 |
| Parent Revision | 2 |
| Requirement References | REQ-20260907134730-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### Manager editing and sign-in interactions

Reuse Flask-Admin account list/edit/filter and the default form error interaction. Keep logout as an explicit POST form with CSRF. Authentication failures remain on the sign-in page without revealing credentials.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-120-001 | constraint | Preserve the existing teaching-project boundary and satisfy the requirement without production effects. | IMP, VFY, RLS | REQ-20260907134730-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-120-001 | REQ-20260907134730-01@1 | Manager editing and sign-in interactions | A manager can edit status, filter results, and receive non-success responses for invalid input without a hidden mutation. | Actual request assertions, database readback and execution output bound to the tested result. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907134729-01@1/SUP-001 | CHG-001 | Existing project provenance and isolated preparation |
