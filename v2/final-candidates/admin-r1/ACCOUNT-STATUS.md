# 用户状态

本地示例允许已登录且启用的账户使用管理后台。用户列表可筛选enabled，并通过真实Flask-Admin表单修改状态。停用时在同一事务旋转alternative_id，user_loader每次请求检查启用状态；重新启用保留已旋转标记，旧cookie不能复活。

create_app配置数据库和SECRET_KEY，启动只增量补enabled列，不重建用户表或写入示例账户。密码、认证标记不展示在管理列表/编辑字段；登录、注册、编辑与POST登出受CSRF保护。此处不建设生产RBAC。

验证：现有Python环境执行 python -B -m unittest -v test_enabled test_final_r0。原13项文件保持冻结SHA；本轮另增加安全配置与新用户标记检查。使用临时SQLite，不触碰用户现有数据库。
