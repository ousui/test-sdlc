---
contract: sdlc-ai-spec/artifact/v1
phase: DSN
id: DSN-20260907112126-01
revision: 1
status: waiting_input
context: CTX-20260907112125-01@1
profile: full
inputs:
  - REQ-20260907112126-01@1
---
# SpringGear JDK21 compatibility design

## 摘要 Summary

Retain reactor/public APIs; align build dependencies and prove behavior with current-result tests.

## 范围 Scope

| Scope Item | Value |
|---|---|
| Design Boundary | Isolated SpringGear four-module Maven reactor migration to JDK21; no disabled-module claim, upstream write or production deployment. |
| Requirement Scope Inputs | REQ-20260907112126-01@1 |
| Control Inputs | None |

## 设计基线与变更 Design Baseline and Change

| Change Type | Current Baseline References | Target State Summary | Impact Summary |
|---|---|---|---|
| incremental | CTX-20260907112125-01@1 | The active SpringGear reactor works on JDK21 with unchanged public Java source, Java21 bytecode and passing workflow compatibility tests. | POM compatibility and new regression/usage documentation only. |

| Change ID | Object or Boundary | Change | Baseline References | Baseline State | Target State | Affected Domains |
|---|---|---|---|---|---|---|
| CHG-001 | resource:RSC-001 | modify | CTX-20260907112125-01@1 | Java8 target and older processor/build versions. | JDK21 build-compatible POMs without public Java source change. | DOM-210, DOM-220, DOM-340, DOM-410 |
| CHG-002 | resource:RSC-001 | add | CTX-20260907112125-01@1 | No JDK21 migration assertions. | Ten actual compatibility tests and precise migration notes. | DOM-350, DOM-510 |

## 需求追踪 Requirement Traceability

| Source References | Design Item or Member References | Decision References | VFY Point or Objective References | N/A Reason |
|---|---|---|---|---|
| REQ-20260907112126-01@1#R-001, REQ-20260907112126-01@1#AC-001 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112126-01@1#R-002, REQ-20260907112126-01@1#AC-002 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112126-01@1#R-003, REQ-20260907112126-01@1#AC-003 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112126-01@1#R-004, REQ-20260907112126-01@1#AC-004 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112126-01@1#R-005, REQ-20260907112126-01@1#AC-005 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |

## 设计决策 Design Decisions

| ID | Requirement or Constraint References | 决策问题 Decision Question | 候选方案 Options | 选择结果 Decision | 选择依据 Rationale | 影响 Domain Affected Domains |
|---|---|---|---|---|---|---|
| DEC-001 | REQ-20260907112126-01@1#R-003 | Which compatibility path minimizes unrelated API migration? | Move to a new Spring major, Retain Spring5 API generation and align JDK21-compatible build/processor versions | Retain Spring5.3.39, use Lombok1.18.30, compiler3.11.0 and Surefire3.2.5. | Meets JDK21 while preserving existing framework code and avoiding unrelated service/web changes. | DOM-210, DOM-220, DOM-340 |

## 设计总纲 Design Index

| 分组 Group | 设计领域 Design Domain | 处置 Disposition | 完成状态 Completion | 责任角色 Responsible Role | 内容引用 Content Reference | 适用性依据引用 Applicability Basis References | 不适用或豁免说明 N/A or Waiver Reason |
|---|---|---|---|---|---|---|---|
| 行为设计 Behavior | 流程与状态 Workflow and State | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No new business workflow; existing library behavior is preserved and tested in DOM-220/350. |
| 行为设计 Behavior | 用户体验与交互 UX and Interaction | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No interactive page or user journey in this library migration. |
| 行为设计 Behavior | 界面与内容 UI and Content | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No UI components or display logic exist in the active migration scope. |
| 行为设计 Behavior | 可访问性与国际化 Accessibility and Internationalization | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No UI, language resources or accessibility changes in this library migration. |
| 技术设计 Technical | 系统与架构 System and Architecture | required | complete | Java maintainer | DSN-20260907112126-01@1/DOM-210 | REQ-20260907112126-01@1#R-001, REQ-20260907112126-01@1#R-003 | N/A |
| 技术设计 Technical | 组件与模块 Components and Modules | required | complete | Java maintainer | DSN-20260907112126-01@1/DOM-220 | REQ-20260907112126-01@1#R-001, REQ-20260907112126-01@1#R-002, REQ-20260907112126-01@1#R-003 | N/A |
| 技术设计 Technical | 接口与集成 Interfaces and Integration | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No interface/schema/HTTP contract change; public Java code is preserved, compatibility checked in DOM-220. |
| 技术设计 Technical | 数据设计 Data Design | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No persistent data model, collection or serialized schema is added. |
| 质量属性 Quality | 安全、隐私与合规 Security, Privacy and Compliance | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No auth, trust or personal-data boundary change; dependencies are changed for compatibility, not claimed a security certification. |
| 质量属性 Quality | 性能与容量 Performance and Capacity | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No throughput or capacity requirement; no performance guarantee is asserted. |
| 质量属性 Quality | 可靠性与恢复 Reliability and Recovery | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No new distributed runtime, service availability or recovery topology; existing exception behavior is regression-tested. |
| 质量属性 Quality | 兼容与迁移 Compatibility and Migration | required | complete | Java maintainer | DSN-20260907112126-01@1/DOM-340 | REQ-20260907112126-01@1#R-002, REQ-20260907112126-01@1#R-003, REQ-20260907112126-01@1#R-005 | N/A |
| 质量属性 Quality | 可维护性与扩展性 Maintainability and Extensibility | required | complete | Java maintainer | DSN-20260907112126-01@1/DOM-350 | REQ-20260907112126-01@1#R-001, REQ-20260907112126-01@1#R-002, REQ-20260907112126-01@1#R-003, REQ-20260907112126-01@1#R-004 | N/A |
| 运行设计 Operations | 部署与配置 Deployment and Configuration | required | complete | Java maintainer | DSN-20260907112126-01@1/DOM-410 | REQ-20260907112126-01@1#R-004, REQ-20260907112126-01@1#R-005 | N/A |
| 运行设计 Operations | 可观测性与可运维性 Observability and Operability | n/a | not_applicable | N/A | N/A | REQ-20260907112126-01@1 | No new telemetry or production operational workflow. |
| 验证设计 Verification | 可验证性与 VFY 策略 Verifiability and VFY Strategy | required | complete | Verification designer | DSN-20260907112126-01@1/DOM-510 | REQ-20260907112126-01@1 | N/A |

### 复合 Domain 子领域适用性 Composite Domain Subdomain Applicability

| 复合 Domain 分类码 Composite Domain Catalog Code | 子领域 Subdomain | Disposition | Applicability Basis References | 不适用、豁免或待确认说明 N/A, Waiver or Pending Reason | Exception References |
|---|---|---|---|---|---|
| DOM-140 | 可访问性 Accessibility | n/a | REQ-20260907112126-01@1 | No UI, language resources or accessibility changes in this library migration. | N/A |
| DOM-140 | 国际化 Internationalization | n/a | REQ-20260907112126-01@1 | No UI, language resources or accessibility changes in this library migration. | N/A |
| DOM-310 | 安全 Security | n/a | REQ-20260907112126-01@1 | No auth, trust or personal-data boundary change; dependencies are changed for compatibility, not claimed a security certification. | N/A |
| DOM-310 | 隐私 Privacy | n/a | REQ-20260907112126-01@1 | No personal data is processed. | N/A |
| DOM-310 | 合规 Compliance | n/a | REQ-20260907112126-01@1 | No new regulated processing; preserve existing open-source licensing. | N/A |

## 产物集清单 Artifact Set Manifest

| Member ID | Type | Domain | Domain Spec Reference or Digest | Path or Reference | Media Type | Purpose | SHA-256 Digest | Empty Reason |
|---|---|---|---|---|---|---|---|---|
| DOM-210 | domain | 系统与架构 System and Architecture | docs/v1.1/200-dsn-domains/210-system-architecture.md@sha256:84a62b6f15542663e7ecf93cd6e12d96b1453e9a52a64cdd1f510a9076400eef | domains/210-system-architecture.md | text/markdown | Domain Design | sha256:69fe74280194887df39b75b947a315efdd571468a66ccf125424f9a8c1e4fbc5 | N/A |
| DOM-220 | domain | 组件与模块 Components and Modules | docs/v1.1/200-dsn-domains/220-components-modules.md@sha256:67d238cd54eccd896ad99111db2692676a5f504fd3c0114c1b296be4fa9dcd6c | domains/220-components-modules.md | text/markdown | Domain Design | sha256:a20b6eea5c5e7f0fe3fe453bc37ce8cc4a7d810b17b5e456267a673ea72da116 | N/A |
| DOM-340 | domain | 兼容与迁移 Compatibility and Migration | docs/v1.1/200-dsn-domains/340-compatibility-migration.md@sha256:46ae3ddea5bd98930a065431e201e67bb81f404f42867a015bf0db8738430cb1 | domains/340-compatibility-migration.md | text/markdown | Domain Design | sha256:af9b404a333f32786f63ebfd4976eac64d26b73a856edbb959c1cfd2eb4f855b | N/A |
| DOM-350 | domain | 可维护性与扩展性 Maintainability and Extensibility | docs/v1.1/200-dsn-domains/350-maintainability-extensibility.md@sha256:c419d0da292d36dbd1531d3305f753bfe2e67cc9750bcbe5db403d66d1555619 | domains/350-maintainability-extensibility.md | text/markdown | Domain Design | sha256:55195a44887ba3a72d19997df46104780d521fdae4ddd166af571b9f7f73d5b0 | N/A |
| DOM-410 | domain | 部署与配置 Deployment and Configuration | docs/v1.1/200-dsn-domains/410-deployment-configuration.md@sha256:8d5968912851696706c894c93c4319e122a0f527aa5035439ce33ac01d5b0291 | domains/410-deployment-configuration.md | text/markdown | Domain Design | sha256:12099be9298a450c255348ece72878058161ca98ac2c8cdc7dd2b9cc7b697d9c | N/A |
| DOM-510 | domain | 可验证性与 VFY 策略 Verifiability and VFY Strategy | docs/v1.1/200-dsn-domains/510-verifiability-vfy-strategy.md@sha256:30cea8dec4a69793a5bcc10ae9a6d4fa420fbff1b81e85bc4fe3f6450ba640f6 | domains/510-verifiability-vfy-strategy.md | text/markdown | Domain Design | sha256:ce2068b8517b71286f3e417029da7c2e82a283a0d8cca06c6873e70f5d4c8043 | N/A |

## 待确认项 Open Items

| ID | 所需输入或待确认决策 Needed Input or Decision | 预期来源 Expected Source | 被阻塞项 Blocked References | 状态 State | 解决结果或证据 Resolution or Evidence |
|---|---|---|---|---|---|
| None | No open items | N/A | N/A | none | N/A |

## 证据 Evidence

| ID | Type | Supports References | Source or Producer | Reference | Integrity or Digest | Produced At | Sensitivity or Access | Empty Reason |
|---|---|---|---|---|---|---|---|---|
| None | none | N/A | N/A | N/A | N/A | N/A | N/A | No independent Evidence |

## 豁免 Exceptions

| ID | State | Origin Exception Reference | 作用域或被跳过义务 Scope or Skipped Obligation | 原因 Reason | 已知风险 Known Risk | 补偿措施 Compensating Control | 批准记录 Approver, Role and Time | 复查条件 Revisit Condition | 下游限制 Downstream Obligation | 解决或替代引用 Resolution or Superseding References |
|---|---|---|---|---|---|---|---|---|---|---|
| None | none | N/A | N/A | No Exceptions | N/A | N/A | N/A | N/A | N/A | N/A |

## 生命周期适用性 Lifecycle Applicability

| Phase | Disposition | Host | 判断依据 Basis |
|---|---|---|---|
| PLN | required | N/A | Ordered migration and test work, current-result verification and local Sandbox qualification. |
| IMP | required | N/A | Ordered migration and test work, current-result verification and local Sandbox qualification. |
| VFY | required | N/A | Ordered migration and test work, current-result verification and local Sandbox qualification. |
| RLS | required | N/A | Ordered migration and test work, current-result verification and local Sandbox qualification. |

## 门禁 Gate

| Check ID | 检查项 Check | 结果 Result | 证据或说明 Evidence or Notes |
|---|---|---|---|
| CORE-G-001 | CORE-G-001 | pass | Artifact ID、Revision 与 Lineage 一致 |
| CORE-G-002 | CORE-G-002 | pass | CTX、Scope Input 与 Control Input 使用准确 Reference |
| CORE-G-003 | CORE-G-003 | pass | primary Blob 使用固定 DSN 结构 |
| CORE-G-004 | CORE-G-004 | pass | Member 与 Manifest 由同一 Builder 生成 |
| CORE-G-005 | CORE-G-005 | pass | REQ、AC、Design 与 VFY 双向追踪完整 |
| CORE-G-006 | CORE-G-006 | pass | Evidence 可追踪 |
| CORE-G-007 | CORE-G-007 | pass | Exception 记录有效 |
| CORE-G-008 | CORE-G-008 | pass | Status、Gate 与 Open Item 由确定性聚合派生 |
| CORE-G-009 | CORE-G-009 | pending | 需要 Final Confirmation |
| DSN-DG-210-001 | DSN-DG-210-001 | pass | 系统与架构 System and Architecture 固定 Contract 已满足 |
| DSN-DG-210-002 | DSN-DG-210-002 | pass | 系统与架构 System and Architecture 固定 Contract 已满足 |
| DSN-DG-210-003 | DSN-DG-210-003 | pass | 系统与架构 System and Architecture 固定 Contract 已满足 |
| DSN-DG-220-001 | DSN-DG-220-001 | pass | 组件与模块 Components and Modules 固定 Contract 已满足 |
| DSN-DG-220-002 | DSN-DG-220-002 | pass | 组件与模块 Components and Modules 固定 Contract 已满足 |
| DSN-DG-220-003 | DSN-DG-220-003 | pass | 组件与模块 Components and Modules 固定 Contract 已满足 |
| DSN-DG-340-001 | DSN-DG-340-001 | pass | 兼容与迁移 Compatibility and Migration 固定 Contract 已满足 |
| DSN-DG-340-002 | DSN-DG-340-002 | pass | 兼容与迁移 Compatibility and Migration 固定 Contract 已满足 |
| DSN-DG-340-003 | DSN-DG-340-003 | pass | 兼容与迁移 Compatibility and Migration 固定 Contract 已满足 |
| DSN-DG-350-001 | DSN-DG-350-001 | pass | 可维护性与扩展性 Maintainability and Extensibility 固定 Contract 已满足 |
| DSN-DG-350-002 | DSN-DG-350-002 | pass | 可维护性与扩展性 Maintainability and Extensibility 固定 Contract 已满足 |
| DSN-DG-350-003 | DSN-DG-350-003 | pass | 可维护性与扩展性 Maintainability and Extensibility 固定 Contract 已满足 |
| DSN-DG-410-001 | DSN-DG-410-001 | pass | 部署与配置 Deployment and Configuration 固定 Contract 已满足 |
| DSN-DG-410-002 | DSN-DG-410-002 | pass | 部署与配置 Deployment and Configuration 固定 Contract 已满足 |
| DSN-DG-410-003 | DSN-DG-410-003 | pass | 部署与配置 Deployment and Configuration 固定 Contract 已满足 |
| DSN-DG-510-001 | DSN-DG-510-001 | pass | 可验证性与 VFY 策略 Verifiability and VFY Strategy 固定 Contract 已满足 |
| DSN-DG-510-002 | DSN-DG-510-002 | pass | 可验证性与 VFY 策略 Verifiability and VFY Strategy 固定 Contract 已满足 |
| DSN-DG-510-003 | DSN-DG-510-003 | pass | 可验证性与 VFY 策略 Verifiability and VFY Strategy 固定 Contract 已满足 |
| DSN-DG-510-004 | DSN-DG-510-004 | pass | 可验证性与 VFY 策略 Verifiability and VFY Strategy 固定 Contract 已满足 |
| DSN-DG-510-005 | DSN-DG-510-005 | pass | 可验证性与 VFY 策略 Verifiability and VFY Strategy 固定 Contract 已满足 |
| DSN-G-001 | DSN-G-001 | pass | 至少一个准确 frozen REQ 与适用 Control Input 已解析 |
| DSN-G-002 | DSN-G-002 | pass | Scope、Baseline、Change 与 Target State 完整 |
| DSN-G-003 | DSN-G-003 | pass | REQ、AC、Design 与 VFY 双向追踪完整 |
| DSN-G-004 | DSN-G-004 | pass | Summary、Decision 与 Design Index 可保持单一权威 |
| DSN-G-005 | DSN-G-005 | pass | 16 个 Domain 均已完成适用性判断 |
| DSN-G-006 | DSN-G-006 | pass | required Domain Member 与 Manifest 可完整构造 |
| DSN-G-007 | DSN-G-007 | pass | Composite Domain 与父 Matrix 一致 |
| DSN-G-008 | DSN-G-008 | pass | 不存在未解决的跨 Domain 冲突 |
| DSN-G-009 | DSN-G-009 | pass | 设计保持最小充分且复杂度有依据 |
| DSN-G-010 | DSN-G-010 | pass | Lifecycle Applicability 完整 |

| Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Result | Mode | Confirmer | Role | Authority Reference | Accepted Exception References | Confirmed At |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sha256:388bed6d78bfd07e72f52ad5f344d9cd36a625c40c0deef571095957bda4842f | docs/v1.1/200-dsn-domains/110-workflow-state.md@sha256:816a9c5144fa2980e5d9675c6b74bed74a7bb07c9cacab655a9ce57c64790f0c, docs/v1.1/200-dsn-domains/120-ux-interaction.md@sha256:dd46d3f9ab07702e65b776ef1e1a2036e8bf1413f36487334f85b7b525b21ca6, docs/v1.1/200-dsn-domains/130-ui-content.md@sha256:97c0733673fc7141dd704b6e254929ec08d2ba96d8e6818b69782e7160991386, docs/v1.1/200-dsn-domains/140-accessibility-i18n.md@sha256:60a881cd1c69fbda8a02befb641f4dd8ab510c6147e02e892c3f9ba530319e01, docs/v1.1/200-dsn-domains/210-system-architecture.md@sha256:84a62b6f15542663e7ecf93cd6e12d96b1453e9a52a64cdd1f510a9076400eef, docs/v1.1/200-dsn-domains/220-components-modules.md@sha256:67d238cd54eccd896ad99111db2692676a5f504fd3c0114c1b296be4fa9dcd6c, docs/v1.1/200-dsn-domains/230-interfaces-integration.md@sha256:db196e684b4d86ff6d1343633a368c34059b285524703dacebf47c23738af842, docs/v1.1/200-dsn-domains/240-data-design.md@sha256:0d6383f895b1a43349c38a9fd22e5704451c451e66c3b4063938c098c22f4fef, docs/v1.1/200-dsn-domains/310-security-privacy-compliance.md@sha256:9b9c2764f57d96e0861ed7a5c841f622bc19f6ac1125ac538a6337978696d105, docs/v1.1/200-dsn-domains/320-performance-capacity.md@sha256:28928cb2d6dd99ccb98cb68e85a7c990e55c6590e5e6fa04207d8fa8df6bebc6, docs/v1.1/200-dsn-domains/330-reliability-recovery.md@sha256:7d3196dad795838f906f351aa462b06637f0c377cf5dd70c866a278b91db8a10, docs/v1.1/200-dsn-domains/340-compatibility-migration.md@sha256:46ae3ddea5bd98930a065431e201e67bb81f404f42867a015bf0db8738430cb1, docs/v1.1/200-dsn-domains/350-maintainability-extensibility.md@sha256:c419d0da292d36dbd1531d3305f753bfe2e67cc9750bcbe5db403d66d1555619, docs/v1.1/200-dsn-domains/410-deployment-configuration.md@sha256:8d5968912851696706c894c93c4319e122a0f527aa5035439ce33ac01d5b0291, docs/v1.1/200-dsn-domains/420-observability-operability.md@sha256:92b19fd4a50fe1e887f64a69d13c9713fdf64198e2bd9c6ef2f9da9456579c34, docs/v1.1/200-dsn-domains/510-verifiability-vfy-strategy.md@sha256:30cea8dec4a69793a5bcc10ae9a6d4fa420fbff1b81e85bc4fe3f6450ba640f6, docs/v1.1/200-dsn-spec.md@sha256:998b76ebf72714706bca045d22f2b5b09ac655404f324cb904edcc241bc4f0ee, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:4ffe2b11c7ab7d90efc6e0d8a153e75960541b03d57396d39ab19719c3abb05c | pending | N/A | N/A | N/A | N/A | None | N/A |

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 | sha256:388bed6d78bfd07e72f52ad5f344d9cd36a625c40c0deef571095957bda4842f | docs/v1.1/200-dsn-domains/110-workflow-state.md@sha256:816a9c5144fa2980e5d9675c6b74bed74a7bb07c9cacab655a9ce57c64790f0c, docs/v1.1/200-dsn-domains/120-ux-interaction.md@sha256:dd46d3f9ab07702e65b776ef1e1a2036e8bf1413f36487334f85b7b525b21ca6, docs/v1.1/200-dsn-domains/130-ui-content.md@sha256:97c0733673fc7141dd704b6e254929ec08d2ba96d8e6818b69782e7160991386, docs/v1.1/200-dsn-domains/140-accessibility-i18n.md@sha256:60a881cd1c69fbda8a02befb641f4dd8ab510c6147e02e892c3f9ba530319e01, docs/v1.1/200-dsn-domains/210-system-architecture.md@sha256:84a62b6f15542663e7ecf93cd6e12d96b1453e9a52a64cdd1f510a9076400eef, docs/v1.1/200-dsn-domains/220-components-modules.md@sha256:67d238cd54eccd896ad99111db2692676a5f504fd3c0114c1b296be4fa9dcd6c, docs/v1.1/200-dsn-domains/230-interfaces-integration.md@sha256:db196e684b4d86ff6d1343633a368c34059b285524703dacebf47c23738af842, docs/v1.1/200-dsn-domains/240-data-design.md@sha256:0d6383f895b1a43349c38a9fd22e5704451c451e66c3b4063938c098c22f4fef, docs/v1.1/200-dsn-domains/310-security-privacy-compliance.md@sha256:9b9c2764f57d96e0861ed7a5c841f622bc19f6ac1125ac538a6337978696d105, docs/v1.1/200-dsn-domains/320-performance-capacity.md@sha256:28928cb2d6dd99ccb98cb68e85a7c990e55c6590e5e6fa04207d8fa8df6bebc6, docs/v1.1/200-dsn-domains/330-reliability-recovery.md@sha256:7d3196dad795838f906f351aa462b06637f0c377cf5dd70c866a278b91db8a10, docs/v1.1/200-dsn-domains/340-compatibility-migration.md@sha256:46ae3ddea5bd98930a065431e201e67bb81f404f42867a015bf0db8738430cb1, docs/v1.1/200-dsn-domains/350-maintainability-extensibility.md@sha256:c419d0da292d36dbd1531d3305f753bfe2e67cc9750bcbe5db403d66d1555619, docs/v1.1/200-dsn-domains/410-deployment-configuration.md@sha256:8d5968912851696706c894c93c4319e122a0f527aa5035439ce33ac01d5b0291, docs/v1.1/200-dsn-domains/420-observability-operability.md@sha256:92b19fd4a50fe1e887f64a69d13c9713fdf64198e2bd9c6ef2f9da9456579c34, docs/v1.1/200-dsn-domains/510-verifiability-vfy-strategy.md@sha256:30cea8dec4a69793a5bcc10ae9a6d4fa420fbff1b81e85bc4fe3f6450ba640f6, docs/v1.1/200-dsn-spec.md@sha256:998b76ebf72714706bca045d22f2b5b09ac655404f324cb904edcc241bc4f0ee, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:4ffe2b11c7ab7d90efc6e0d8a153e75960541b03d57396d39ab19719c3abb05c | pending | None | sdlc-200-dsn | 2026-09-07T11:21:26Z |
