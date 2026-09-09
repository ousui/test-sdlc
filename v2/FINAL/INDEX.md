# FINAL 同版本证据索引

冻结 Runtime：`495177acf777251d378652e2a50e47a1b5c4c41a`。安装包摘要：`a3ecb85d9286fe61b80f98882da4e4f6b91ca33aa25616401d0b043967f9a310`。

本索引仅登记已经根回读的场景；完整执行进度以实现仓库 `docs/work-items/sdlc-v2/PROGRESS.md` 为准。其他场景尚未验收，不预填通过。

| 场景 | 当前已验证结果 | 来源 |
|---|---|---|
| Admin R0 | 原13保留，最终16通过；独立19次含1重叠；两轮产品修复后本地RLS及完整归档通过 | [索引](admin-r0.json) |
| SpringGear R0 | 原四模块/10测试、38类major65；一次离线依赖选型修复后本地RLS及完整归档通过 | [索引](springgear-r0.json) |
| fansite R0 | 原24及原UI检查保留，新增4条reset断言与独立DOM红绿；两轮产品修复后本地RLS及完整归档通过 | [索引](fansite-r0.json) |
| Admin R1 | 32通过，独立35次含重叠；一次页面修复，真实切分支后两需求保持 | [索引](admin-r1.json) |
| SpringGear R1 | 25通过及3项独立边界；41类major65；无产品修复 | [索引](springgear-r1.json) |
| fansite R1 | 34Go、47JS及4reset通过；独立迁移/Unicode/分页/绑定验证，无产品修复 | [索引](fansite-r1.json) |

候选源码在 `../final-candidates/`，逐字节提取自各自本轮本地RLS包；旧 `../candidates/` 与 Q0/Q1/Q2 证据保持原版本。源码之外的数据库、日志、资产和完整ZIP保留在忽略的 `.local-runs/sdlc-v2/`，不进入Git。

三个R0场景均由当前Agent按安装版Skill真实逐阶段形成输入与代码，运行真实验证并完成交付。根单独复核全部ZIP成员、资产字节、源文件、六阶段回执和对应归档操作，不把归档回读计作新增业务测试。SpringGear R0没有独立产品Git；其Git探测向上读取Lab HEAD，产品来源由原e855096本地Git archive及精确源码清单证明。

本批共149份源码；fansite生成二进制留在原始RLS包，不入Git。Spring原有3份含历史空白的文件从原始来源逐字节保留，仅对这些已核对文件使用命令级空白例外；其余新增文件严格diff检查。Admin及fansite的Agent输入纠正、Spring离线依赖选型修复均见逐场景索引，不伪称首次零错误。

R1批次另保存163份本轮交付源码。额外7组公共CLI确定性回归的5个脚本原字节与依赖闭包保存在[回归源码](regression-sources/README.md)，原运行346请求在忽略目录中；复制后未重复执行，不把它们当作真实Agent链或加入159测试数。

独立当前客户端来源审阅见`.local-runs/sdlc-v2/reviews/final-acceptance-46/real-chain-r0-audit/REPORT.md`：三R0实际六Skill完整正文、当场代码形成与IMP时序、265请求/185归档操作、独立review和真实RLS对应。客户端日志记录Codex Desktop0.153.4及gpt-6-astra/xhigh；这不是服务端effective model认证。子任务delegation正文在本地日志加密，总授权仍以用户目标原文和根会话为准。Spring R0报告后来仅补Git边界字段，原根回读绑定的是补记前报告SHA，独立审阅精确核对了这项文案差异。
