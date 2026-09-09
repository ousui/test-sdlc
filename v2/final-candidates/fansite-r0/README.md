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
