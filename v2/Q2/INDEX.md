# Q2 三项目第二复杂需求闭环

三项目均从各自 R1 真实产品终态开始，当前 Agent 实际读取安装版 Skill，通过公开 CLI 形成需求、设计、计划、代码、验证与本地交付。源码候选仅从最终原生交付 ZIP 回读提取，不是事前预制候选或补造阶段记录。

| 项目 | 实际业务回归 | 独立补证 | 源码文件 |
|---|---|---|---:|
| Admin | 53 项：原13、R1十五及Q2审计/幂等/迁移/准备探针 | 58 次执行含重复4项及新增迁移边界；真实原库collect恢复 | 18 |
| SpringGear | 四模块43 JUnit：原10、R1十五、Q2十八；JDK21、41类major65 | 额外5项隔离/重试/失败清理边界；真实Git合入与适用性 | 128 |
| fansite | Go44：原24、R1十、Q2九及迁移一；race；JS47/49及UI | 独立连续相册重载、真实中断和复制恢复、Header脱敏复验 | 24 |

共170份源码。fansite交付的额外生成二进制保留在原包；Admin原交付的空Runtime协调锁保留在原包，均未作为源码提交。Spring继承的doc-change.md、doc-example-01.md和HttpStatus.java与R1字节相同，保留原有空白；其他路径执行严格空白检查。

主业务链使用 q2-entry（7d71793）。fansite中断专项保留该版本原始红，再使用 q2-headerfix（fc07245）实际完成脱敏/unknown/复制恢复补证。Admin分叉归档原row_conflict确认为Runtime缺陷，修补后以q2-collectfix（6214e5c）在原目标恢复原439行归档，实际完成正常内容checkpoint、change.resolve及再导出；原失败回执、源码和来源ZIP不改写。版本与包摘要见三个JSON索引。

业务与测试修复均保留原失败：Admin身份ID复用及一次迁移SQL错误；fansite版本冲突恢复、旧空库迁移、删除相册连续重载及修复验证；Spring仅一轮测试泛型重载编译修正。人工SQL/Store/Authority/协议绕过0。Agent请求纠正、读回脚本纠正和预期边界单独记账，不混为正常全绿。

大型证据保留于忽略目录.local-runs/sdlc-v2/q2-*与reviews。三份索引定位精确Run/Revision、实际交付与完整归档、独立报告和原始需求。安装版显式读取+公共CLI属于当前客户端真实执行，不冒称其他客户端原生认证。

本轮本地提交后进入FINAL：冻结H_final及安装包，在同版本重做全部九条真实Agent链和公共入口/业务回归，补齐46项映射。本轮多版本证据保持真实边界。
