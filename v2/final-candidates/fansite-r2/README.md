# 非官方粉丝站

这是本地 Go 与原生 JavaScript 示例，包含首页、粉丝账户、个人资料、试听、相册和管理员后台。媒体仅使用自产测试音与色块图，无真实身份或艺人素材。

首次启动设置 `FAN_ADMIN_EMAIL` 与 `FAN_ADMIN_PASSWORD`（12–72 字节），再运行 `go run -mod=vendor .`。默认监听 `127.0.0.1:8080`，数据存于 `data/state.json`。可用 `FAN_ADDR`、`FAN_DATA_DIR` 更换本地端口和目录；真实 HTTPS 反向代理后才设置 `FAN_SECURE_COOKIE=1`。没有部署到任何远端。

管理员登录 `/login` 后访问 `/admin`。可编辑站点、添加/编辑/发布音乐和相册、上传照片、删除内容及停用粉丝。新内容默认草稿；撤下与删除后既有媒体 URL 失效。普通粉丝只能编辑自己的昵称和简介。会话重启失效，停用后旧会话永久失效。

运行 `python3 sample_media.py --output demo-media` 生成两秒 8000 Hz 单声道 16 位 PCM WAV 与 32×32 PNG。音频与图片单个最多 1 MiB；目前仅支持标准 44 字节头 PCM WAV、PNG/JPEG。图片最多 400 万像素。不支持外部媒体抓取。

验证：

- `go test -count=1 -v ./...`：原 24 项 HTTP、权限、媒体、并发和持久化断言。
- `node --check web/app.js`：原生脚本语法。
- `python3 -B check_ui.py`：原始测试字节、七区七表单、vendor 和自产媒体。
- `python3 -B verify_format.py`：本轮新写源文件格式；原始 site_test.go 保持完整旧字节。
- `go build -o .build/fansite .`：独立二进制。

依赖已附 vendor，可设 `GOFLAGS=-mod=vendor GOPROXY=off GOTOOLCHAIN=local` 离线执行。仅支持一个进程持有数据目录；写入先完成临时文件同步与原子替换再发布内存，失败保留旧值。请勿同时启动两个服务操作同一个目录。密码采用独立随机盐 PBKDF2，详情见 SOURCE.md。没有生产或原生浏览器认证声明。

R1 增加公共及管理目录搜索/过滤/排序/分页。公共目录只返回 published；管理员可筛选 draft、published、withdrawn。标题采用 Unicode 简单大小写等价，标题同键按 ID 升序；相册也匹配描述。默认每页10，最大100，页码从1开始，超界返回空数组。旧 Published 布尔写法继续支持，从已发布取消发布会成为 withdrawn。数据自动从实际 schema_version1 或历史 version1 原子迁移到 version2，重启不改变结果。

新增验证：`node ui_catalog_test.js` 原47交互/HTML断言，`node ui_reset_test.js` 保留编辑后新建不覆写；Go 原24加R1十项（包含 Unicode final sigma）。这些是 Handler/文件与原生脚本模型证据，不是生产部署或完整客户端认证。

R2 内容更新与删除须带当前 `Version`，上传照片须带 `AlbumVersion`；GET返回revision。缺失428、过时409，成功仅增加一次。409/500保留输入，点击重新读取后自主决定修改；删除的上传目标保持空白直到手选。原24项业务断言完整保留，client.post仅适配缺省传输版本且不重试；明确旧/null版本由独立原始请求验证。44项Go、47目录JS、49版本JS、照片连续重读与reset模型：`node ui_version_test.js`、`node ui_photo_test.js web/app.js`。`python3 verify_recovery.py`核验本轮真实中断附件；恢复前先诊断unknown和原进程。

独立评审补充：`helper_case_test.go`在原44项之外新增1项顶层回归，覆盖Version/AlbumVersion四种大小写的旧值与null，共16次明确拒绝；因此最终Go合计45项。
