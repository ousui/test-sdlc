# SDLC 真实项目回归实验室

目标是以真实需求验证 `ousui/sdlc-ai-spec` 的通用 Skill/Runtime 衔接，而非生产发布或 UI 美观认证。原始失败与旧范围保留，但 JDK26 不计入当前 JDK21 验收。

## 已核验的两个闭环

共同 Runtime SHA：`0102b8f42a87809f58f978e2c2611705b30e7869`。

固定基线：[verified/admin-springgear-20260907](https://github.com/ousui/sdlc-ai-spec/tree/verified/admin-springgear-20260907)。本基线不随第三项目修复前进。

| 场景 | 结果 | 全部产物、源码与证据 |
|---|---|---|
| 极简 Admin：用户启用/禁用、筛选修改、会话撤销、旧库兼容 | CLOSED；13项实际测试，VFY重新执行；RLS成功、Status无阻塞 | [Admin完整入口](runs/ADMIN-34116649433/README.md) |
| SpringGear：原四模块升级适配JDK21 | CLOSED；10项JUnit测试、class major65；离线Maven与VFY通过；RLS成功、Status无阻塞 | [SpringGear完整入口](runs/SPRINGGEAR-34116147376/README.md) |

准确源码的strict仓库回归：**1082/1082**，零failure/error/skip/expectedFailure；VFY真实OS执行PASS，IMP82、VFY80、RLS87、Status14注册案例全部有真实执行覆盖。[完整执行证据](https://github.com/ousui/sdlc-ai-spec/actions/runs/34116067464)。此运行内部冻结并在独立job验证的源码是上述0102b8f，不是触发提交1ebc453。

## 第三个项目

杨千嬅主题非官方粉丝站，Go使用既有版本（1.23.2）、HTML和原生JavaScript；展示、粉丝账户、音乐试听、相册及简单后台。后续工作基于上述固定基线，代码与产物归集到 `verify/fansite-closure-v1`，尚未验收。不得把此项标为已完成。

## 闭环的准确含义

AI编写正常需求、设计与候选实现，经各Skill规定的正式Runtime CLI顺序执行，保留准确Artifact/Revision、成员、Claim、Evidence和独立进程客观合规复核。不是原生Codex Discovery/安装认证，不冒称独立AI语义审查。

RLS为当前支持的**本地Sandbox版本状态转换**，不等同于应用部署或Java库发布安装。无生产、无上游维护分支写入，无真实用户资料、凭据、未经授权的艺人音频或照片。

每个结果入口包含完整可读正文、最终源码、测试和调用记录。原始恢复包随对应Actions附件保留30天；固定源码和可读证据在Git中保留。总控与缺陷见 [Issue #1](https://github.com/ousui/test-sdlc/issues/1)。
