---
contract: sdlc-ai-spec/artifact/v1
phase: DSN
id: DSN-20260907112710-01
revision: 1
status: waiting_input
context: CTX-20260907112709-01@1
profile: full
inputs:
  - REQ-20260907112710-01@1
---
# Account availability and revocation design

## 摘要 Summary

Extend the existing app/model/admin forms; use transactional session-identifier rotation and additive SQLite migration.

## 范围 Scope

| Scope Item | Value |
|---|---|
| Design Boundary | Isolated Flask-Admin teaching application source and ephemeral local SQLite only; no upstream or production writes. |
| Requirement Scope Inputs | REQ-20260907112710-01@1 |
| Control Inputs | None |

## 设计基线与变更 Design Baseline and Change

| Change Type | Current Baseline References | Target State Summary | Impact Summary |
|---|---|---|---|
| incremental | CTX-20260907112709-01@1 | Enabled state is visible/editable, revoked sessions stay revoked, and persisted accounts survive restart/migration. | App/model/forms and isolated tests only; existing teaching authorization model retained. |

| Change ID | Object or Boundary | Change | Baseline References | Baseline State | Target State | Affected Domains |
|---|---|---|---|---|---|---|
| CHG-001 | resource:RSC-001 | modify | CTX-20260907112709-01@1 | No persisted availability switch or suspended-account access guard. | Working status edit/filter, immediate session revocation and additive migration. | DOM-110, DOM-120, DOM-130, DOM-220, DOM-230, DOM-240, DOM-310, DOM-330, DOM-340, DOM-410 |
| CHG-002 | resource:RSC-001 | add | CTX-20260907112709-01@1 | No regression for account suspension. | Deterministic tests and minimal local delivery documentation. | DOM-350, DOM-510 |

## 需求追踪 Requirement Traceability

| Source References | Design Item or Member References | Decision References | VFY Point or Objective References | N/A Reason |
|---|---|---|---|---|
| REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#AC-001 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#AC-002 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#AC-003 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#AC-004 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |
| REQ-20260907112710-01@1#R-005, REQ-20260907112710-01@1#AC-005 | CHG-001, CHG-002, DOM-510 | DEC-001 | VFO-001 | N/A |

## 设计决策 Design Decisions

| ID | Requirement or Constraint References | 决策问题 Decision Question | 候选方案 Options | 选择结果 Decision | 选择依据 Rationale | 影响 Domain Affected Domains |
|---|---|---|---|---|---|---|
| DEC-001 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | How should disabling invalidate outstanding sessions without deleting accounts? | Reject only fresh login, Rotate alternative login identity and reject disabled loads | Rotate identity on disable and reject disabled accounts on every protected load. | Meets immediate revocation and prevents old-session resurrection while retaining existing accounts. | DOM-110, DOM-220, DOM-240, DOM-310 |

## 设计总纲 Design Index

| 分组 Group | 设计领域 Design Domain | 处置 Disposition | 完成状态 Completion | 责任角色 Responsible Role | 内容引用 Content Reference | 适用性依据引用 Applicability Basis References | 不适用或豁免说明 N/A or Waiver Reason |
|---|---|---|---|---|---|---|---|
| 行为设计 Behavior | 流程与状态 Workflow and State | required | complete | Application developer | DSN-20260907112710-01@1/DOM-110 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 行为设计 Behavior | 用户体验与交互 UX and Interaction | required | complete | Application developer | DSN-20260907112710-01@1/DOM-120 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 行为设计 Behavior | 界面与内容 UI and Content | required | complete | Application developer | DSN-20260907112710-01@1/DOM-130 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 行为设计 Behavior | 可访问性与国际化 Accessibility and Internationalization | n/a | not_applicable | N/A | N/A | REQ-20260907112710-01@1 | No new accessibility or locale mechanism; reuse existing labeled form widgets. No claim of subjective usability, translation or accessibility certification. |
| 技术设计 Technical | 系统与架构 System and Architecture | n/a | not_applicable | N/A | N/A | REQ-20260907112710-01@1 | Existing single-process Flask application and dependency architecture retained; no service boundaries or new shared abstraction. |
| 技术设计 Technical | 组件与模块 Components and Modules | required | complete | Application developer | DSN-20260907112710-01@1/DOM-220 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 技术设计 Technical | 接口与集成 Interfaces and Integration | required | complete | Application developer | DSN-20260907112710-01@1/DOM-230 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 技术设计 Technical | 数据设计 Data Design | required | complete | Application developer | DSN-20260907112710-01@1/DOM-240 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 质量属性 Quality | 安全、隐私与合规 Security, Privacy and Compliance | required | complete | Application developer | DSN-20260907112710-01@1/DOM-310 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 质量属性 Quality | 性能与容量 Performance and Capacity | n/a | not_applicable | N/A | N/A | REQ-20260907112710-01@1 | No throughput/latency requirement or new workload; one indexed account load per protected request, no capacity certification. |
| 质量属性 Quality | 可靠性与恢复 Reliability and Recovery | required | complete | Application developer | DSN-20260907112710-01@1/DOM-330 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 质量属性 Quality | 兼容与迁移 Compatibility and Migration | required | complete | Application developer | DSN-20260907112710-01@1/DOM-340 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 质量属性 Quality | 可维护性与扩展性 Maintainability and Extensibility | required | complete | Application developer | DSN-20260907112710-01@1/DOM-350 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 运行设计 Operations | 部署与配置 Deployment and Configuration | required | complete | Application developer | DSN-20260907112710-01@1/DOM-410 | REQ-20260907112710-01@1#R-001, REQ-20260907112710-01@1#R-002, REQ-20260907112710-01@1#R-003, REQ-20260907112710-01@1#R-004, REQ-20260907112710-01@1#R-005 | N/A |
| 运行设计 Operations | 可观测性与可运维性 Observability and Operability | n/a | not_applicable | N/A | N/A | REQ-20260907112710-01@1 | No new operational telemetry or production incident workflow; retain existing server diagnostics without logging credentials. |
| 验证设计 Verification | 可验证性与 VFY 策略 Verifiability and VFY Strategy | required | complete | Verification designer | DSN-20260907112710-01@1/DOM-510 | REQ-20260907112710-01@1 | N/A |

### 复合 Domain 子领域适用性 Composite Domain Subdomain Applicability

| 复合 Domain 分类码 Composite Domain Catalog Code | 子领域 Subdomain | Disposition | Applicability Basis References | 不适用、豁免或待确认说明 N/A, Waiver or Pending Reason | Exception References |
|---|---|---|---|---|---|
| DOM-140 | 可访问性 Accessibility | n/a | REQ-20260907112710-01@1 | No new accessibility or locale mechanism; reuse existing labeled form widgets. No claim of subjective usability, translation or accessibility certification. | N/A |
| DOM-140 | 国际化 Internationalization | n/a | REQ-20260907112710-01@1 | No new accessibility or locale mechanism; reuse existing labeled form widgets. No claim of subjective usability, translation or accessibility certification. | N/A |
| DOM-310 | 安全 Security | required | REQ-20260907112710-01@1 | N/A | None |
| DOM-310 | 隐私 Privacy | n/a | REQ-20260907112710-01@1 | Only synthetic test accounts; no new personal-data collection or privacy workflow. | N/A |
| DOM-310 | 合规 Compliance | n/a | REQ-20260907112710-01@1 | No new regulated processing or jurisdictional change; preserve source license. | N/A |

## 产物集清单 Artifact Set Manifest

| Member ID | Type | Domain | Domain Spec Reference or Digest | Path or Reference | Media Type | Purpose | SHA-256 Digest | Empty Reason |
|---|---|---|---|---|---|---|---|---|
| DOM-110 | domain | 流程与状态 Workflow and State | docs/v1.1/200-dsn-domains/110-workflow-state.md@sha256:816a9c5144fa2980e5d9675c6b74bed74a7bb07c9cacab655a9ce57c64790f0c | domains/110-workflow-state.md | text/markdown | Domain Design | sha256:68f9f2196093710628c6e1799266992f3c44640455ebb7bcb8f131e6f54df246 | N/A |
| DOM-120 | domain | 用户体验与交互 UX and Interaction | docs/v1.1/200-dsn-domains/120-ux-interaction.md@sha256:dd46d3f9ab07702e65b776ef1e1a2036e8bf1413f36487334f85b7b525b21ca6 | domains/120-ux-interaction.md | text/markdown | Domain Design | sha256:78d828677be368accdb0b5e12f7355aebfb7f210f475468a0075aede65c6218f | N/A |
| DOM-130 | domain | 界面与内容 UI and Content | docs/v1.1/200-dsn-domains/130-ui-content.md@sha256:97c0733673fc7141dd704b6e254929ec08d2ba96d8e6818b69782e7160991386 | domains/130-ui-content.md | text/markdown | Domain Design | sha256:bfcbdfbcc3dc2f5117a126c21900cc2e68a08a45bd2521810ff68bec3676c8f4 | N/A |
| DOM-220 | domain | 组件与模块 Components and Modules | docs/v1.1/200-dsn-domains/220-components-modules.md@sha256:67d238cd54eccd896ad99111db2692676a5f504fd3c0114c1b296be4fa9dcd6c | domains/220-components-modules.md | text/markdown | Domain Design | sha256:9b2f5e21ac74e7cc43dd13713de16cb215fd9a55dbeebc842c6a15f541476f6e | N/A |
| DOM-230 | domain | 接口与集成 Interfaces and Integration | docs/v1.1/200-dsn-domains/230-interfaces-integration.md@sha256:db196e684b4d86ff6d1343633a368c34059b285524703dacebf47c23738af842 | domains/230-interfaces-integration.md | text/markdown | Domain Design | sha256:418b7cb5cd477cb7bcce9917375583f537590fea27da717ebf484cc0576480df | N/A |
| DOM-240 | domain | 数据设计 Data Design | docs/v1.1/200-dsn-domains/240-data-design.md@sha256:0d6383f895b1a43349c38a9fd22e5704451c451e66c3b4063938c098c22f4fef | domains/240-data-design.md | text/markdown | Domain Design | sha256:46c6acf8f2752668af6cf489c36751bdc78ec25db5db5003ecfe1fa27247a8b7 | N/A |
| DOM-310 | domain | 安全、隐私与合规 Security, Privacy and Compliance | docs/v1.1/200-dsn-domains/310-security-privacy-compliance.md@sha256:9b9c2764f57d96e0861ed7a5c841f622bc19f6ac1125ac538a6337978696d105 | domains/310-security-privacy-compliance.md | text/markdown | Domain Design | sha256:06591ec27119f25ebbe87c45c3d5199197ca2f39516ef3fc63ed6aaee3dfa8d9 | N/A |
| DOM-330 | domain | 可靠性与恢复 Reliability and Recovery | docs/v1.1/200-dsn-domains/330-reliability-recovery.md@sha256:7d3196dad795838f906f351aa462b06637f0c377cf5dd70c866a278b91db8a10 | domains/330-reliability-recovery.md | text/markdown | Domain Design | sha256:bcf12cd67258c9d73f4fdeeea8aa630d3cf3b1ac80d37686af6a7e17ee663401 | N/A |
| DOM-340 | domain | 兼容与迁移 Compatibility and Migration | docs/v1.1/200-dsn-domains/340-compatibility-migration.md@sha256:46ae3ddea5bd98930a065431e201e67bb81f404f42867a015bf0db8738430cb1 | domains/340-compatibility-migration.md | text/markdown | Domain Design | sha256:c3674c1a34947276575fadf298e057e858f7cf3041a84e57554f68dbd7983c5e | N/A |
| DOM-350 | domain | 可维护性与扩展性 Maintainability and Extensibility | docs/v1.1/200-dsn-domains/350-maintainability-extensibility.md@sha256:c419d0da292d36dbd1531d3305f753bfe2e67cc9750bcbe5db403d66d1555619 | domains/350-maintainability-extensibility.md | text/markdown | Domain Design | sha256:5963e7391db780367c31de52c8e7564eb909034650bd2997f5ceb891b97cd18b | N/A |
| DOM-410 | domain | 部署与配置 Deployment and Configuration | docs/v1.1/200-dsn-domains/410-deployment-configuration.md@sha256:8d5968912851696706c894c93c4319e122a0f527aa5035439ce33ac01d5b0291 | domains/410-deployment-configuration.md | text/markdown | Domain Design | sha256:b720147053914bcd9a9fdf7e917d1b0cf23a833073811789a9d7cc3ee5a43123 | N/A |
| DOM-510 | domain | 可验证性与 VFY 策略 Verifiability and VFY Strategy | docs/v1.1/200-dsn-domains/510-verifiability-vfy-strategy.md@sha256:30cea8dec4a69793a5bcc10ae9a6d4fa420fbff1b81e85bc4fe3f6450ba640f6 | domains/510-verifiability-vfy-strategy.md | text/markdown | Domain Design | sha256:e322d12523b9ffa75c12ef82598baf2d2def3a5e837040c3b835e4659de61b18 | N/A |

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
| PLN | required | N/A | Ordered implementation, whole-scope verification and authorized local sandbox delivery. |
| IMP | required | N/A | Ordered implementation, whole-scope verification and authorized local sandbox delivery. |
| VFY | required | N/A | Ordered implementation, whole-scope verification and authorized local sandbox delivery. |
| RLS | required | N/A | Ordered implementation, whole-scope verification and authorized local sandbox delivery. |

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
| DSN-DG-110-001 | DSN-DG-110-001 | pass | 流程与状态 Workflow and State 固定 Contract 已满足 |
| DSN-DG-110-002 | DSN-DG-110-002 | pass | 流程与状态 Workflow and State 固定 Contract 已满足 |
| DSN-DG-110-003 | DSN-DG-110-003 | pass | 流程与状态 Workflow and State 固定 Contract 已满足 |
| DSN-DG-120-001 | DSN-DG-120-001 | pass | 用户体验与交互 UX and Interaction 固定 Contract 已满足 |
| DSN-DG-120-002 | DSN-DG-120-002 | pass | 用户体验与交互 UX and Interaction 固定 Contract 已满足 |
| DSN-DG-120-003 | DSN-DG-120-003 | pass | 用户体验与交互 UX and Interaction 固定 Contract 已满足 |
| DSN-DG-130-001 | DSN-DG-130-001 | pass | 界面与内容 UI and Content 固定 Contract 已满足 |
| DSN-DG-130-002 | DSN-DG-130-002 | pass | 界面与内容 UI and Content 固定 Contract 已满足 |
| DSN-DG-130-003 | DSN-DG-130-003 | pass | 界面与内容 UI and Content 固定 Contract 已满足 |
| DSN-DG-220-001 | DSN-DG-220-001 | pass | 组件与模块 Components and Modules 固定 Contract 已满足 |
| DSN-DG-220-002 | DSN-DG-220-002 | pass | 组件与模块 Components and Modules 固定 Contract 已满足 |
| DSN-DG-220-003 | DSN-DG-220-003 | pass | 组件与模块 Components and Modules 固定 Contract 已满足 |
| DSN-DG-230-001 | DSN-DG-230-001 | pass | 接口与集成 Interfaces and Integration 固定 Contract 已满足 |
| DSN-DG-230-002 | DSN-DG-230-002 | pass | 接口与集成 Interfaces and Integration 固定 Contract 已满足 |
| DSN-DG-230-003 | DSN-DG-230-003 | pass | 接口与集成 Interfaces and Integration 固定 Contract 已满足 |
| DSN-DG-240-001 | DSN-DG-240-001 | pass | 数据设计 Data Design 固定 Contract 已满足 |
| DSN-DG-240-002 | DSN-DG-240-002 | pass | 数据设计 Data Design 固定 Contract 已满足 |
| DSN-DG-240-003 | DSN-DG-240-003 | pass | 数据设计 Data Design 固定 Contract 已满足 |
| DSN-DG-310-001 | DSN-DG-310-001 | pass | 安全、隐私与合规 Security, Privacy and Compliance 固定 Contract 已满足 |
| DSN-DG-310-002 | DSN-DG-310-002 | pass | 安全、隐私与合规 Security, Privacy and Compliance 固定 Contract 已满足 |
| DSN-DG-310-003 | DSN-DG-310-003 | pass | 安全、隐私与合规 Security, Privacy and Compliance 固定 Contract 已满足 |
| DSN-DG-310-004 | DSN-DG-310-004 | pass | 安全、隐私与合规 Security, Privacy and Compliance 固定 Contract 已满足 |
| DSN-DG-330-001 | DSN-DG-330-001 | pass | 可靠性与恢复 Reliability and Recovery 固定 Contract 已满足 |
| DSN-DG-330-002 | DSN-DG-330-002 | pass | 可靠性与恢复 Reliability and Recovery 固定 Contract 已满足 |
| DSN-DG-330-003 | DSN-DG-330-003 | pass | 可靠性与恢复 Reliability and Recovery 固定 Contract 已满足 |
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
| 1 | sha256:3a17af7bf845c7ef5618cfdf1faf23cd65005fce565f1177d9528bd738b17c8e | docs/v1.1/200-dsn-domains/110-workflow-state.md@sha256:816a9c5144fa2980e5d9675c6b74bed74a7bb07c9cacab655a9ce57c64790f0c, docs/v1.1/200-dsn-domains/120-ux-interaction.md@sha256:dd46d3f9ab07702e65b776ef1e1a2036e8bf1413f36487334f85b7b525b21ca6, docs/v1.1/200-dsn-domains/130-ui-content.md@sha256:97c0733673fc7141dd704b6e254929ec08d2ba96d8e6818b69782e7160991386, docs/v1.1/200-dsn-domains/140-accessibility-i18n.md@sha256:60a881cd1c69fbda8a02befb641f4dd8ab510c6147e02e892c3f9ba530319e01, docs/v1.1/200-dsn-domains/210-system-architecture.md@sha256:84a62b6f15542663e7ecf93cd6e12d96b1453e9a52a64cdd1f510a9076400eef, docs/v1.1/200-dsn-domains/220-components-modules.md@sha256:67d238cd54eccd896ad99111db2692676a5f504fd3c0114c1b296be4fa9dcd6c, docs/v1.1/200-dsn-domains/230-interfaces-integration.md@sha256:db196e684b4d86ff6d1343633a368c34059b285524703dacebf47c23738af842, docs/v1.1/200-dsn-domains/240-data-design.md@sha256:0d6383f895b1a43349c38a9fd22e5704451c451e66c3b4063938c098c22f4fef, docs/v1.1/200-dsn-domains/310-security-privacy-compliance.md@sha256:9b9c2764f57d96e0861ed7a5c841f622bc19f6ac1125ac538a6337978696d105, docs/v1.1/200-dsn-domains/320-performance-capacity.md@sha256:28928cb2d6dd99ccb98cb68e85a7c990e55c6590e5e6fa04207d8fa8df6bebc6, docs/v1.1/200-dsn-domains/330-reliability-recovery.md@sha256:7d3196dad795838f906f351aa462b06637f0c377cf5dd70c866a278b91db8a10, docs/v1.1/200-dsn-domains/340-compatibility-migration.md@sha256:46ae3ddea5bd98930a065431e201e67bb81f404f42867a015bf0db8738430cb1, docs/v1.1/200-dsn-domains/350-maintainability-extensibility.md@sha256:c419d0da292d36dbd1531d3305f753bfe2e67cc9750bcbe5db403d66d1555619, docs/v1.1/200-dsn-domains/410-deployment-configuration.md@sha256:8d5968912851696706c894c93c4319e122a0f527aa5035439ce33ac01d5b0291, docs/v1.1/200-dsn-domains/420-observability-operability.md@sha256:92b19fd4a50fe1e887f64a69d13c9713fdf64198e2bd9c6ef2f9da9456579c34, docs/v1.1/200-dsn-domains/510-verifiability-vfy-strategy.md@sha256:30cea8dec4a69793a5bcc10ae9a6d4fa420fbff1b81e85bc4fe3f6450ba640f6, docs/v1.1/200-dsn-spec.md@sha256:998b76ebf72714706bca045d22f2b5b09ac655404f324cb904edcc241bc4f0ee, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:edb9ba6770a68f6db3dd6964488673d6adce02fd1842baaeb4466b4149803587 | pending | N/A | N/A | N/A | N/A | None | N/A |

| Evaluated Revision | Control Input Digest | Evaluation Contract Set | Check Set Result Digest | Gate Result | Exception References | Evaluator | Evaluated At |
|---|---|---|---|---|---|---|---|
| 1 | sha256:3a17af7bf845c7ef5618cfdf1faf23cd65005fce565f1177d9528bd738b17c8e | docs/v1.1/200-dsn-domains/110-workflow-state.md@sha256:816a9c5144fa2980e5d9675c6b74bed74a7bb07c9cacab655a9ce57c64790f0c, docs/v1.1/200-dsn-domains/120-ux-interaction.md@sha256:dd46d3f9ab07702e65b776ef1e1a2036e8bf1413f36487334f85b7b525b21ca6, docs/v1.1/200-dsn-domains/130-ui-content.md@sha256:97c0733673fc7141dd704b6e254929ec08d2ba96d8e6818b69782e7160991386, docs/v1.1/200-dsn-domains/140-accessibility-i18n.md@sha256:60a881cd1c69fbda8a02befb641f4dd8ab510c6147e02e892c3f9ba530319e01, docs/v1.1/200-dsn-domains/210-system-architecture.md@sha256:84a62b6f15542663e7ecf93cd6e12d96b1453e9a52a64cdd1f510a9076400eef, docs/v1.1/200-dsn-domains/220-components-modules.md@sha256:67d238cd54eccd896ad99111db2692676a5f504fd3c0114c1b296be4fa9dcd6c, docs/v1.1/200-dsn-domains/230-interfaces-integration.md@sha256:db196e684b4d86ff6d1343633a368c34059b285524703dacebf47c23738af842, docs/v1.1/200-dsn-domains/240-data-design.md@sha256:0d6383f895b1a43349c38a9fd22e5704451c451e66c3b4063938c098c22f4fef, docs/v1.1/200-dsn-domains/310-security-privacy-compliance.md@sha256:9b9c2764f57d96e0861ed7a5c841f622bc19f6ac1125ac538a6337978696d105, docs/v1.1/200-dsn-domains/320-performance-capacity.md@sha256:28928cb2d6dd99ccb98cb68e85a7c990e55c6590e5e6fa04207d8fa8df6bebc6, docs/v1.1/200-dsn-domains/330-reliability-recovery.md@sha256:7d3196dad795838f906f351aa462b06637f0c377cf5dd70c866a278b91db8a10, docs/v1.1/200-dsn-domains/340-compatibility-migration.md@sha256:46ae3ddea5bd98930a065431e201e67bb81f404f42867a015bf0db8738430cb1, docs/v1.1/200-dsn-domains/350-maintainability-extensibility.md@sha256:c419d0da292d36dbd1531d3305f753bfe2e67cc9750bcbe5db403d66d1555619, docs/v1.1/200-dsn-domains/410-deployment-configuration.md@sha256:8d5968912851696706c894c93c4319e122a0f527aa5035439ce33ac01d5b0291, docs/v1.1/200-dsn-domains/420-observability-operability.md@sha256:92b19fd4a50fe1e887f64a69d13c9713fdf64198e2bd9c6ef2f9da9456579c34, docs/v1.1/200-dsn-domains/510-verifiability-vfy-strategy.md@sha256:30cea8dec4a69793a5bcc10ae9a6d4fa420fbff1b81e85bc4fe3f6450ba640f6, docs/v1.1/200-dsn-spec.md@sha256:998b76ebf72714706bca045d22f2b5b09ac655404f324cb904edcc241bc4f0ee, docs/v1.1/artifact-store-spec.md@sha256:b340ca2a38dfe0f7409acaa8f9ac559e8872bed44725037889528e3d167d4764, docs/v1.1/core-spec.md@sha256:1eefa7a138f2d221140137a5fac0f5429b7f847273fe9d70e891ace6c3b7a89b | sha256:edb9ba6770a68f6db3dd6964488673d6adce02fd1842baaeb4466b4149803587 | pending | None | sdlc-200-dsn | 2026-09-07T11:27:10Z |
