# Flask-Admin 用户状态本地示例

基于 SOURCE.md 所列 BSD 示例，本轮从安全准备的轻量起点实现。设置 ADMIN_DEMO_SECRET 后用已有锁定环境运行 `python -B main.py`；不内置SECRET或演示账户，首次通过注册创建本地账户。

管理用户列表支持 enabled 筛选/编辑，停用立即撤销会话，旧SQLite增量迁移保留用户。详见 ACCOUNT-STATUS.md。

检查：`python -B -m unittest -v test_enabled test_final_r0`。这是本地示例，不包含生产RBAC或外部部署。

R1批量启停、Unicode过滤和稳定分页见BULK-STATUS.md。完整32项：`python -B -m unittest -v test_enabled test_final_r0 test_bulk_status test_final_r1`。

R2 adds transactionally consistent status audit and optional operation keys. See STATUS-AUDIT.md. Run all prior modules plus test_status_audit, test_sqlite_probe, test_final_r2 (59 methods); audit list is under /admin/users/audit/.
