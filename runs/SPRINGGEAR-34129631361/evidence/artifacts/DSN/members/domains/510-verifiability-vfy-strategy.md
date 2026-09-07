# 可验证性与 VFY 策略 Verifiability and VFY Strategy

| 关联项 Relation | 值 Value |
|---|---|
| 父 DSN ID Parent DSN ID | DSN-20260907135106-01 |
| Parent Revision | 1 |
| Requirement References | REQ-20260907135105-01@1 |
| Decision References | DEC-001 |

## 设计结果 Design Result

### VFY 目标 VFY Objectives

| ID | Kind | Requirement, AC, Goal or Intended-use References | Design or Decision References | Domain VFY Point References | 可观察结果 Observable Result | 风险或重要性 Risk or Importance | Method References | Pass Criteria References | Evidence Contract References |
|---|---|---|---|---|---|---|---|---|---|
| VFO-001 | both | REQ-20260907135105-01@1#AC-001, REQ-20260907135105-01@1#AC-002, REQ-20260907135105-01@1#AC-003, REQ-20260907135105-01@1#AC-004, REQ-20260907135105-01@1#AC-005, REQ-20260907135105-01@1#GOAL-001 | CHG-001, CHG-002, DEC-001 | VFP-210-001, VFP-220-001, VFP-340-001, VFP-350-001, VFP-410-001 | The active SpringGear reactor works on JDK21 with unchanged public Java source, Java21 bytecode and passing workflow compatibility tests. | Prevent build success with missing tests or broken framework behavior. | VFM-001 | VPC-001 | VEC-001 |

### 方法选择 VFY Methods

| ID | 类型 Type | Disposition | 方法明细 Method Detail | 适用范围 Scope | 方法 Method | 选择依据 Selection Basis | 承载位置 Host | Exception Reference |
|---|---|---|---|---|---|---|---|---|
| VFM-001 | test | required | level=integration, mode=automated | VFO-001 | Offline Maven test of the current terminal result. | Real Java runtime, bytecode and workflow assertions verify intended library use. | VFY | N/A |

### 可验证性设计 Verifiability Design

Use existing public context/executor types and a real Spring application context. JUnit tests assert Java feature21 and actual class major65, not just configuration strings.

### 环境与数据 Environment and Data

JDK21 and external Maven dependency cache are prepared before runtime. Formal execution is an OS-isolated copy without network. Tests use no external database or server.

### 覆盖策略 Coverage Strategy

Ten unique JUnit tests cover runtime21, bytecode65, Lombok construction, argument/value transport, invalid indices, empty/order/skip/failure pipeline behavior and Spring enhancement. All existing public sources and disabled-module exclusion are retained.

### 通过条件 Pass Criteria

| ID | VFY Objective | 输入或条件 Input or Condition | 预期结果 Expected Result | 容差 Tolerance | 失败条件 Failure Condition |
|---|---|---|---|---|---|
| VPC-001 | VFO-001 | Current terminal source and JDK21 toolchain | Ten executed tests; zero failure, error or skip; existing behavior and Java21 class assertion pass. | None | Missing test identity, wrong runtime or bytecode, test failure, source drift or unsupported environment. |

### Evidence Contract

| ID | VFY Objective | Evidence Type | 生成方或来源 Producer or Source | 必要内容 Required Content | 敏感性与处理 Sensitivity and Handling | 保留要求 Retention Requirement | 保存或引用位置 Storage or Reference |
|---|---|---|---|---|---|---|---|
| VEC-001 | VFO-001 | Execution log and immutable result | Actual Maven/JUnit process | Current result hashes, Java version assertions, executed method identities, Maven summary and exit code | Public source and synthetic test values only | Retain original evidence with delivery | VFY supporting evidence and readable case archive |

## 约束与影响 Constraints and Impact

None — no additional constraint or impact.

## 证据引用 Evidence References

| Evidence or Member Reference | Supports Item References | Purpose |
|---|---|---|
| None | N/A | No domain-specific Evidence references |
