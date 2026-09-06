# SDLC 真实项目回归实验室

本仓库由维护者授权用于 `ousui/sdlc-ai-spec` 的真实场景回归。业务源码、可读流程产物和证据在独立 `verify/web-realflow-v1` 分支交付，主分支仅保留入口。

本轮：`WEB-RF-20260907-01`。

- SpringGear：升级并适配当前正式 JDK 26。
- Minimal Admin：基于 Flask-Admin 官方示例增加用户启用/禁用与权限回归。
- 粉丝站：Go + jQuery + HTML，实现展示、粉丝账户、音乐试听、相册和后台。

结果必须区分业务功能测试、真实 Runtime 运行、Artifact Gate、独立确认与宿主原生加载；未运行或受阻不得描述为 PASS。

本仓库不包含真实用户资料、真实凭据或未经授权的歌曲/照片。原始上游许可证和来源声明保留。
