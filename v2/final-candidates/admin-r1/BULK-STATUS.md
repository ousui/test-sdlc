# 批量启停与查询

登录且启用的管理用户可访问 /admin/users/bulk/，按用户名、enabled过滤并按id稳定分页；HTML与 /admin/users/data/ 的total是相同过滤后的总数。Unicode搜索使用每连接注册的casefold函数，百分号/下划线按字面匹配。

POST /admin/users/status/ 受CSRF保护。JSON为 ids正整数列表与enabled布尔值，原始数量1至100，去重后处理；HTML接受同样的SQLite int64范围。任何非法、未知或当前账户混入都整体拒绝。事务提交成功返回requested/changed/enabled；数据库失败503/storage_failure并回滚所有目标和会话标记。同状态不重复旋转，重新启用不复活旧cookie。

保留原13、FINAL R0三项与冻结R1十五项，另增加Unicode展开/Greek新连接回归，总32方法。运行 python -B -m unittest -v test_enabled test_final_r0 test_bulk_status test_final_r1。

本轮无R2操作键或审计；同目录Git分支切换需求身份专项保存在Runtime证据链和本轮独立归档。来源许可证与原SQLite增量迁移继续保持。
