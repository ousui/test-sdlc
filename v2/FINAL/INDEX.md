# FINAL 同版本证据索引

冻结 Runtime：`495177acf777251d378652e2a50e47a1b5c4c41a`。安装包摘要：`a3ecb85d9286fe61b80f98882da4e4f6b91ca33aa25616401d0b043967f9a310`。

九个产品场景均已完成实际当前Agent执行、本地交付和根回读；fansite R2按原实施链与另建验证交付链联合计入。完整进度与报告见实现仓库 `docs/work-items/sdlc-v2/PROGRESS.md`、`FINAL-RESULTS.md`。

| 场景 | 当前已验证结果 | 来源 |
|---|---|---|
| Admin R0 | 原13保留，最终16通过；独立19次含1重叠；两轮产品修复后本地RLS及完整归档通过 | [索引](admin-r0.json) |
| SpringGear R0 | 原四模块/10测试、38类major65；一次离线依赖选型修复后本地RLS及完整归档通过 | [索引](springgear-r0.json) |
| fansite R0 | 原24及原UI检查保留，新增4条reset断言与独立DOM红绿；两轮产品修复后本地RLS及完整归档通过 | [索引](fansite-r0.json) |
| Admin R1 | 32通过，独立35次含重叠；一次页面修复，真实切分支后两需求保持 | [索引](admin-r1.json) |
| SpringGear R1 | 25通过及3项独立边界；41类major65；无产品修复 | [索引](springgear-r1.json) |
| fansite R1 | 34Go、47JS及4reset通过；独立迁移/Unicode/分页/绑定验证，无产品修复 | [索引](fansite-r1.json) |
| Admin R2 | 59通过及独立1项COMMIT边界；本地RLS完成，同需求冲突公开恢复；独立新需求交回专项亦已完成，见admin-v22 | [索引](admin-r2.json) |
| SpringGear R2 | 43通过及5项独立边界；无关基线合入后继续，公共组件改变后拒绝旧PASS并真实复验 | [索引](springgear-r2.json) |
| fansite R2 | 45Go、47/49JS、4reset及原UI；独立4探针/29绑定；原RLS超限，新验证链完成实际交付 | [索引](fansite-r2.json) |

候选源码在 `../final-candidates/`，逐字节提取自各自本轮本地RLS包；旧 `../candidates/` 与 Q0/Q1/Q2 证据保持原版本。源码之外的数据库、日志、资产和完整ZIP保留在忽略的 `.local-runs/sdlc-v2/`，不进入Git。

三个R0场景均由当前Agent按安装版Skill真实逐阶段形成输入与代码，运行真实验证并完成交付。根单独复核全部ZIP成员、资产字节、源文件、六阶段回执和对应归档操作，不把归档回读计作新增业务测试。SpringGear R0没有独立产品Git；其Git探测向上读取Lab HEAD，产品来源由原e855096本地Git archive及精确源码清单证明。

R0批次共149份源码；fansite生成二进制留在原始RLS包，不入Git。Spring原有3份含历史空白的文件从原始来源逐字节保留，仅对这些已核对文件使用命令级空白例外；其余新增文件严格diff检查。Admin及fansite的Agent输入纠正、Spring离线依赖选型修复均见逐场景索引，不伪称首次零错误。

R1批次另保存163份本轮交付源码。额外7组公共CLI确定性回归的5个脚本原字节与依赖闭包保存在[回归源码](regression-sources/README.md)，原运行346请求在忽略目录中；复制后未重复执行，不把它们当作真实Agent链或加入159测试数。

独立当前客户端来源审阅见`.local-runs/sdlc-v2/reviews/final-acceptance-46/real-chain-r0-audit/REPORT.md`：三R0实际六Skill完整正文、当场代码形成与IMP时序、265请求/185归档操作、独立review和真实RLS对应。客户端日志记录Codex Desktop0.153.4及gpt-6-astra/xhigh；这不是服务端effective model认证。子任务delegation正文在本地日志加密，总授权仍以用户目标原文和根会话为准。Spring R0报告后来仅补Git边界字段，原根回读绑定的是补记前报告SHA，独立审阅精确核对了这项文案差异。


R2批次新增178份源码：Admin22、SpringGear129、fansite27；三轮共490份实际交付源码。生成二进制保留在各原ZIP。额外[Admin V2-022专项](admin-v22.json)只有一份新验证说明，原22业务源码不变，不计作第十个产品场景。

同一H_final的159项内核测试通过；[最终46项映射](ACCEPTANCE-MAP.md)裁决43项批准本地范围已证，040其他客户端原生认证、045Rust、046SpecKit延期。MySQL为本次明确非范围。7组/346请求重放与实际九产品链分开记录，不合并测试数字。机器明细含当前代码/测试名/日志行/历史SHA和实际客户端证据，见[ACCEPTANCE-MAP.json](ACCEPTANCE-MAP.json)。

四组独立实际客户端审阅及原请求、归档、断言字节证明均由根复核；入口及SHA见[PROVENANCE.json](PROVENANCE.json)。Admin R1复用同Agent此前完整读取的同H Skill；fansite恢复DSN的新读取输出截断，完整正文以同Agent原实施链已实际读取为据，不声称再次消费了不可见全文。Admin R2为REQ先完成、随后clone，实施Run完成DSN至RLS。

必须保留的恢复边界：Admin原main collect仍因共有Run状态冲突失败；新同change内容pair成功保留版本并resolve。V2-022另以真实completed新需求证明new_change交回，6旧需求/21原Run/配置/22源码保持，原ZIP独立保存、135展开成员字节一致；额外自拟的嵌套ZIP格式没有发生，未进入正式criterion且不属于批准022要求。fansite原91.5MB祖先附件组合触发64MiB原生包上限；保留原failed Run/归档/真实IMP写入，新Change对相同27源码真实复验并交付，不能称原Run成功或另一次从零实施。

所有Agent输入错误、预期负例、产品红绿与读回辅助脚本纠正均保留；人工SQL/Store/Authority绕过0。原审批与执行记录不变为本机能力，逻辑交回不覆盖产品代码。没有push、merge、tag、release；/tmp用于隔离测试和提交消息。最终HEAD与清洁状态另存忽略证据CLOSEOUT.json，执行H_final始终不改标。
