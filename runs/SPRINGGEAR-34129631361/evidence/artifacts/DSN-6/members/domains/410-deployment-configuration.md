# 部署与配置 Deployment and Configuration

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907135106-01 |
| Parent Revision | 1 |
| Requirement References | REQ-20260907135105-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### Local artifact and release boundary

Build offline from preinstalled JDK21 and a prepared Maven cache. Use verify for reactor packaging, then an independent current-result test in VFY. RLS only observes a disposable Sandbox version, never Maven deployment.

## 约束与影响 Constraints and Impact

| ID | 类型 Type | 内容 Content | 影响的下游 Phase Affected Downstream Phase | Reference |
|---|---|---|---|---|
| CIM-410-001 | constraint | Retain exact migration boundary, no public-source redesign or upstream publication. | IMP, VFY, RLS | REQ-20260907135105-01@1 |

## VFY 要点 VFY Points

| ID | Requirement, AC or Design References | 验证对象 Verification Object | 可观察结果 Observable Result | 预期 Evidence Expected Evidence |
|---|---|---|---|---|
| VFP-410-001 | REQ-20260907135105-01@1#AC-004, REQ-20260907135105-01@1#AC-005 | Local artifact and release boundary | Maven verify builds the active reactor; test evidence and local target match the qualified current version. | Current-source compiler/test output and immutable source/diff evidence. |

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| CTX-20260907135104-01@1/SUP-001 | CHG-001 | Upstream reactor baseline and scope |
