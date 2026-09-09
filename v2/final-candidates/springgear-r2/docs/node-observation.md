# 节点观察

此文保留R1观察器契约及该检查点命令；当前R2的上下文生命周期和43项验收见 [上下文隔离](context-isolation.md)。

在现有 SpringGearEngineParts 上调用 setObserver(event -> ...) 可选开启同步观察。未设置时保持原流程；六字段构造器和 ToString 保持原样。执行器在每次调用开始固定观察器，随后改变 parts 的回调只影响下一次调用。每次有观察器的调用生成独立 executionId，同次所有事件共用该标识。

事件包含 source、beanName、nodeIndex、nodeType 和 stage。supports 返回 true 后、handle 前发 START；handle 正常返回发 SUCCESS；handle 抛出任何 Throwable 时先发 FAILURE，其 failure 保持原对象。空链、未支持节点及 supports 自身失败不发节点事件；supports 异常沿原路径直接抛出。

默认策略保持继续/停止边界：SpringGearContinueException 记 FAILURE 后执行下一节点；SpringGearInterruptException 保持同一异常并附上已有 response，然后停止；其他领域异常保持身份，普通异常保留原映射消息/状态且 cause 指向原异常，然后停止。接口默认策略同样保留原因。框架不自动重试节点。

观察器抛出的 Exception 或 Error 在所有阶段都被隔离，连观察器错误日志失败也不会替代业务结果、改变后续节点策略或覆盖 cause。回调同步执行，慢回调会延长调用时间；调用者负责共享观察器内部的线程安全。事件不暴露 context，但仍持有原 Throwable 引用。

R2继续保证观察器选择与执行标识隔离，并已增加每调用浅层 args/contextValue 容器复制及结束后的上下文引用清理；调用者共享嵌套业务可变对象的并发责任不变。观察器契约保持R1语义。

用 JDK21 执行离线四模块验收：

```sh
mvn -o -B -ntp -s .mvn/settings.xml -gs .mvn/settings.xml -Dmaven.repo.local=/path/to/isolated/repository clean verify
python3 -B tools/verify_r1.py
```

本轮当前验收为原10加完整15观察器测试，共25项；全41个生产类major65。继承的 verify_r0.py 和 jdk21-migration.md 描述R0检查点，本轮使用上述 verify_r1.py。本地交付包含全部125源文件，完整SDLC归档单独保留依赖资产与原始回执。
