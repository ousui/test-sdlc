# 杨千嬅 · 非官方个人粉丝站

Go + HTML + 原生 JavaScript：主页、粉丝注册/登录/资料/注销、WAV试听、相册、用户及内容后台。仅供本地SDLC验证，不是艺人官方网站或生产安全/可用性认证。

## 本地运行

语言下限Go1.23，全部依赖在vendor，无需npm、数据库服务器或网络。

```sh
GOPROXY=off GOTOOLCHAIN=local go test -count=1 -v ./...
GOPROXY=off GOTOOLCHAIN=local go build -o fansite .
export FAN_DATA_DIR="$PWD/data"
export FAN_ADMIN_EMAIL='your-local-admin@example.invalid'
read -r -s -p 'Choose local admin password (10–72 bytes): ' FAN_ADMIN_PASSWORD
export FAN_ADMIN_PASSWORD
./fansite
```

访问 http://127.0.0.1:8080。管理员仅在空用户库、显式设置上述环境变量时创建；重启不重置账户。未设置时仍能浏览/注册，但不会暗设管理员。不要将密码写入源码、日志或共享文件。默认FAN_ADDR=127.0.0.1:8080；FAN_SECURE_COOKIE=true只在HTTPS接入时配置，本轮不提供公网部署。

## 功能使用

管理员后台可以编辑首页，新增/编辑/发布/下架/删除音乐和相册，上传/删除相片，列出并启用/禁用粉丝。编辑时填写列表显示的ID；新增留空。禁止禁用管理员。普通粉丝仅编辑自己的资料。禁用使当前和过期代数会话失效，重新启用需新登录；重启后所有人重新登录。

```sh
python3 sample_media.py
```

上述命令生成自产440Hz测试音和色块图片。通过后台上传sample-media/generated-tone.wav和generated-swatch.png。它们绝非杨千嬅录音/照片。试听限PCM WAV≤1MiB；图片限PNG/JPEG≤1MiB、单边≤4096、总像素≤1600万。JSON接口限制2MiB。

公开GET：/api/site、/api/tracks、/api/albums、/api/albums/{id}。媒体GET/HEAD：/media/tracks/{id}；相片/media/photos/{id}。音频支持Range；草稿/下架/删除后旧URL不能获取媒体。

账户：GET /api/session取得会话绑定CSRF；POST /api/register、/api/login、/api/logout；GET/POST /api/me。POST必须JSON、会话及X-CSRF-Token，存在Origin时必须同站；未知字段拒绝。

管理：GET /api/admin/users、/api/admin/content；POST /api/admin/site、/api/admin/user-state、/api/admin/tracks、/api/admin/albums、/api/admin/photos、/api/admin/delete。服务端统一检查角色，注册不能自行分配管理员。

## 持久化和验证边界

本地state.json以0600文件、单进程互斥clone→validate→persist→rename→publish保存完整用户/内容。写入失败不公开半成品内存状态；不声称多进程数据库或断电级事务持久性。不要让多个实例共享目录，也不要把实际数据目录提交仓库。

24项实际Go功能测试见CASE-TRACEABILITY。它们使用真实HTTP Handler与临时文件，不依赖远端数据库或浏览器。页面、DOM和原生JS语法另行检查，不冒称主观UI/UX验收。

密码用随机盐PBKDF2-HMAC-SHA256600000轮，复用带BSD许可证的官方Go x/crypto代码（SOURCE.md），非自行实现算法。会话原值不持久化、带过期及撤销代数。这不代表生产渗透/负载合规认证。RLS是本地Sandbox版本状态，不是应用部署。
