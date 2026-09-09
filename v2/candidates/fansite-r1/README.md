# 杨千嬅 · 非官方粉丝站

一个本地 Go + HTML + 原生 JavaScript 项目，包含公开主页、粉丝注册登录与资料、WAV 试听、PNG/JPEG 相册和简单后台。与艺人官方无关联；请只使用合成账户与自产示例媒体。

需要 Go 1.23+；依赖已在 vendor，不需要 npm、数据库服务或联网下载。Node 仅用于 JS 语法检查，Python 3.11+ 用于媒体生成与辅助验收。

```sh
GOPROXY=off GOTOOLCHAIN=local go test -count=1 -v ./...
GOPROXY=off GOTOOLCHAIN=local go build -o .build/fansite .
node --check web/app.js
python3 -B check_ui.py
python3 -B sample_media.py
```

运行 `.build/fansite` 后访问 `http://127.0.0.1:8080`。默认数据目录为 `data`，可通过 `FAN_DATA_DIR` 指定新建的可丢弃目录；`FAN_ADDR` 可配置本地监听地址。Go 的 `GOCACHE` 和 `GOPATH` 可以设置到隔离目录，标准库临时构建和缓存是测试必需的本地写入。

首次建立管理员时，在启动前设置 `FAN_ADMIN_EMAIL` 和 `FAN_ADMIN_PASSWORD` 环境变量。密码需 10–72 字节；请通过终端安全输入机制提供，不写入源码或命令历史。只在用户库为空时引导管理员；已有用户库绝不会被重置或补设管理员。未设置管理员环境变量也能浏览和注册，但注册账户始终是普通粉丝。重启后所有用户需重新登录。

后台可编辑主页、列出并启用/禁用粉丝，新增/编辑/发布/下架/删除音乐和相册，以及上传/删除相片。点击列表的“编辑”会填入表单；清空 ID 表示新增。管理员不能被禁用。粉丝只能编辑自己的资料；禁用后旧会话即时失效，重新启用必须新登录。

`sample_media.py` 生成 `sample-media/generated-tone.wav`（自产 440 Hz 测试音）和 `generated-swatch.png`（自产色块），没有使用艺人录音、照片或真实个人资料。音频只接受有效 PCM WAV、图片只接受有效 PNG/JPEG；文件最多 1 MiB，图片单边最多 4096、总像素最多 1600 万，JSON 请求最多 2 MiB。

公开 API：`/api/site`、`/api/tracks`、`/api/albums`、`/api/albums/{id}`。WAV 媒体支持 GET/HEAD/Range；草稿、下架、删除的媒体 URL 返回 404。写操作使用 JSON、会话绑定 CSRF 与同站 Origin 检查；未知字段拒绝。动态文本使用原生 DOM 文本节点，模板自动转义。

本地 JSON 在单进程互斥锁内复制、校验、持久化、原子替换后才发布内存；失败保留已有状态，坏库/符号链接拒绝启动。账户密码使用带许可证的官方 vendor PBKDF2-HMAC-SHA256、600000 轮与独立随机盐。会话不落盘，最长 24 小时，并绑定持久化撤销代数。`FAN_SECURE_COOKIE=true` 只用于自行配置的 HTTPS 接入；本轮没有公网部署。

原 `site_test.go` 的 24 个测试及断言保持原字节；它们实际调用 HTTP Handler 并使用临时文件。`check_ui.py` 检查页面/JS连接结构、许可、原断言摘要与自产媒体；它不是主观视觉或浏览器兼容认证。辅助测试的 `.check-work` 会清理。不要让多个实例共享一个数据目录，不承诺分布式一致性、生产安全认证、性能 SLA 或断电级持久性。


## Q1 目录搜索与发布状态

音乐/相册页可按标题搜索、升降序排序和翻页；相册还搜索描述。后台目录另可筛选草稿、已发布、已下架或全部，并可在列表中显式改变状态。筛选变化回到第一页；页面显示过滤后总数。旧 Published 复选框继续工作：从发布改为未发布表示下架。

新增查询 API `/api/catalog/tracks`、`/api/catalog/albums` 和仅管理员的 `/api/admin/catalog/tracks`、`/api/admin/catalog/albums`。参数为 `q`、`sort=title|-title`、`page`（默认1）、`page_size`（默认10，1–100）；管理 `state=draft|published|withdrawn|all` 默认all，公开只允许published。响应为 `{items,total,page,page_size}`，total在过滤后、分页前计算；超尾页返回空items。标题忽略大小写排序，相同标题按持久ID升序，降序时仍保持同标题ID升序。非法、重复和未知参数400；公开请求非发布状态403。

原 `/api/tracks` 与 `/api/albums` 仍返回数组。新增 `/api/tracks/{id}` 详情。公开列表、详情和媒体均只显示当前published内容；草稿、下架和删除的旧媒体URL对GET/HEAD/Range均404，重新发布恢复当前有效媒体。没有管理员的公开URL绕过。

R0 `state.json` schema v1 首次载入时原子迁移为v2：Published=true映射published，其余映射draft，保留账号/ID/媒体。之后发布状态持久保存。已有数据目录须由单实例使用；迁移时请保留自己的备份。旧版本程序不应回读v2文件。重启保留目录顺序与状态，用户需重新登录。

额外前端行为测试：`node ui_catalog_test.js`。它执行实际原生目录控制器的DOM事件与fetch契约，覆盖页码重置、筛选、total/边界、错误、晚到响应和末页删除；它与原 `node --check web/app.js`、`python3 -B check_ui.py` 一起运行。Go `go test -count=1 -v ./...` 包含原24项和独立R1分页、发布可见性、旧数据迁移/重启测试，无需网络/socket监听。Node DOM fixture不是浏览器视觉或跨浏览器认证。
