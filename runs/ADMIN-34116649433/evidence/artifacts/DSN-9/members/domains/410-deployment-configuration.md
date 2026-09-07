# 部署与配置 Deployment and Configuration

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907112710-01 |
| Parent Revision | 2 |
| Requirement References | REQ-20260907112710-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### Local runtime and sandbox delivery

Keep the example local-only with explicit instance configuration and SQLite location. The SDLC RLS target is a disposable local sandbox, not publishing a service or production credentials.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-410-001 | constraint | Preserve the existing teaching-project boundary and satisfy the requirement without production effects. | IMP, VFY, RLS | REQ-20260907112710-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-410-001 | REQ-20260907112710-01@1 | Local runtime and sandbox delivery | The application configuration and start command are local-only, use isolated SQLite and require externally supplied instance configuration; delivery version observation occurs later in RLS. | Actual request assertions, database readback and execution output bound to the tested result. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907112709-01@1/SUP-001 | CHG-001 | Existing project provenance and isolated preparation |
