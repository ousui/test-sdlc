# 并行上下文与执行生命周期

每次 execute 创建独立 SpringGearContext，克隆 args 数组并调用 SpringGearContextValue.copyForExecution() 创建浅层 value 容器。节点在同一调用内共享该 context；不同 parts、同一 parts 并发和重复调用均取得独立容器与观察 executionId。测试使用同步 barrier 确保交叠，不用 sleep 猜测。

默认 copyForExecution 使用 HashMap.clone，保留运行时子类及其普通字段，无需默认构造器，并重新建立容器视图。自定义可变字段须覆写 copyForExecution，先调用 super.copyForExecution 再复制这些字段。框架拒绝返回 null、原对象或不同运行时类型的无效副本；null seed 仍保持无 value 容器的兼容行为。

这是浅拷贝：args 元素、value 中的嵌套业务对象与其他自定义可变字段可能仍是调用者原引用。框架不深拷贝任意对象图；调用者负责这些共享业务对象、seed 并发修改和共享 handler/observer 内部状态的线程安全。各执行可独立修改容器键值和 args 元素，不修改原容器。

执行器用 finally 覆盖完整 context 生命周期，包括 supports、handle、异常策略与结束日志。无论正常返回、普通异常、Error、supports失败、自定义策略失败或全部节点不支持，结束时 releaseExecutionState 仅将本次 context 的 request、args、values、response 字段置 null；source/timestamp 保留。它不会调用 Map.clear、填空数组或遍历业务对象图。

返回值在 finally 前取得，直接或嵌套携带 value/args 的业务响应保持原对象和内容；interrupt 异常附带的 response 与原 cause 也保留。调用后仍持有 context 的代码只可检查已释放状态；调用者先前保存的业务对象引用不会被框架清空。原五参数构造器保留，可直接构造 context；执行器负责它创建的上下文生命周期。

框架不会自动重试。失败抛回调用者后，只有显式再次 execute 才开始新调用，新容器没有上次临时值或 response，新 executionId 与上次不同。Continue 在当前链继续，Interrupt 和其他终止异常停止当前链；R1观察顺序、观察器异常隔离与原cause规则不变。同步观察器的重入调用同样独立。

用 JDK21 和已经准备的隔离缓存运行当前四模块验收：

```sh
mvn -o -B -ntp -s .mvn/settings.xml -gs .mvn/settings.xml -Dmaven.repo.local=/path/to/isolated/repository clean verify
python3 -B tools/verify_r2.py
```

当前43项为原10、R1完整15和R2完整18；全部41生产class major65。继承的 verify_r0.py/verify_r1.py 是历史检查点，本轮使用 verify_r2.py。当前实际父包8417940f有125源文件，本轮新增4文件，交付129源文件。

本次本地Git专项先真实运行25项基线，通过后合入独立README文案提交，旧结果仍适用；公共执行组件真正变化后旧PASS必须拒绝，保留原条件并实际重跑最终43项。原始SHA、命令和回执在本次SDLC证据中，历史Q2结果不替代本次证明。完整工作区归档与源码交付包分别回读。
