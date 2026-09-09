# v2 GitHub 共享专项结果

配套实现：[sdlc-ai-spec PR #23](https://github.com/ousui/sdlc-ai-spec/pull/23)。本实验室分支从 `dde73bc4525522ed8298396b2f129bb884db64b5` 接续，只增加当前专项，不改变历史9条Agent产品链。

## 实际执行

- Runtime 精确源码：`f8b4765e46fd440d8e95d0c065b5ccc7b115b0af`。
- 实验室执行源码：`bf0ce1c2b55a69f797bf6d047cba1df527406b96`。
- Workflow：[34351132793](https://github.com/ousui/test-sdlc/actions/runs/34351132793)，实际success。
- 原始证据：[artifact10103739045](https://github.com/ousui/test-sdlc/actions/runs/34351132793/artifacts/10103739045)，14天保留；包含12次公共CLI请求/回执、源码SHA、安装包及合成工作区导出。
- 实际评论：[Issue #21 comment5601819414](https://github.com/ousui/test-sdlc/issues/21#issuecomment-5601819414)。该评论由安装后的Runtime调用gh真实创建；不是连接器代写内容。

## 判定

合成REQ通过共享Runtime创建并提交。github.preview生成可读Markdown；github.publish真实POST并GET回读confirmed；重复publish返回idempotent=true且comment_id未变；github.reconcile再次核对同一评论；本地status与workspace.export成功。另由Web连接器独立读取Issue，确认仅一条测试快照评论。

publication_id：`github-6cf51659838b6a1da3134bc05601ee26db1ebf9eb58ac0147453e580248e557a`。
导出逻辑摘要：`851acc13bcb8b4b8c13ae7c5724df3f7b1d28191b5f7ed5b6abd19d99c145a9d`。
导出ZIP SHA256：`e581571a19f0711ea9a28592ab37db11197f2777d953f9224f24173a8399d075`。

## 边界

只证明已安装公共CLI→gh→真实Issue读写/去重/回查链；不证明自然语言宿主加载或另一次业务需求闭环。使用标准Actions目标仓库Issue权限、合成输入，不上传生产资料或凭据。

`sdlc-ai-spec` 自身Issues关闭，创建返回410；因此选择启用Issues的实验室。没有修改仓库设置。当前能力向已有Issue追加快照评论，不创建Issue、不覆盖人工正文、不推送仓库文件。

原测试Issue完成后关闭，保留原评论。历史test-sdlc PR #20继续保存原v2三项目三轮证据，不把本专项当成那些场景复验。
