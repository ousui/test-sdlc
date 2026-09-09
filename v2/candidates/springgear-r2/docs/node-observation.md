# 节点观察器

观察器是每次执行可选的同步回调。已有 `SpringGearEngineParts` 构造器和不设置观察器的调用方式保持兼容。

```java
SpringGearEngineParts parts = new SpringGearEngineParts(
        request, args, "order", System.currentTimeMillis(), contextValue, "order-engine");
parts.setObserver(event -> {
    System.out.println(event.executionId() + " " + event.nodeIndex() + " " + event.stage());
});
Object response = executor.execute(parts);
```

执行器按原先配置的 handler 顺序运行。每个 `supports` 返回 true 的节点，在 `handle` 前发出 START，正常返回后发出 SUCCESS，抛出异常后发出 FAILURE。FAILURE 携带该节点抛出的原始 Throwable；另外两种事件的 failure 为 null。索引从零开始，表示原配置位置，因此不支持的节点会留下索引间隔。空流程或不支持的节点没有事件；`supports` 自身抛出的异常保留原先直接退出边界，没有虚构 START。

观察不会改写原有后续策略：Continue 异常发出 FAILURE 后继续下一节点；Interrupt、普通异常和其他领域异常停止后续节点。默认执行器保留原领域异常对象，Interrupt 仍可补入已产生的 response；普通异常的映射对象现在把原 Throwable 保存在 cause 中。接口默认映射同样保留 cause。SUCCESS 仅表示当前节点正常返回。

执行开始时捕获当前 parts 的观察器，当前调用期间换掉属性仅影响下一次调用。每次有观察器的执行获得独立 executionId，同一次执行中保持不变。事件不暴露可变上下文，执行器没有全局观察器或事件集合；不同 parts 可在同一执行器上并行使用自己的观察器。事件本身不可变，但 failure 是原 Throwable 引用，观察器应只读取它。

回调的 Exception 或 Error 被隔离并单独记录日志；不会替换业务异常、改变返回值或跳过节点。回调同步运行，应保持简短；阻塞回调仍会延迟业务调用。若复用同一观察器处理并行调用，观察器自身负责线程安全。R2 已加入每次调用的容器隔离与上下文引用释放，详见 [执行上下文与重复调用](context-lifecycle.md)；当前版本使用 `tools/verify_r2.py` 验证，下面保留 R1 交付时的验证说明。

验证命令：在 JDK 21 和已准备的 Maven 缓存下离线执行四模块 `mvn clean verify`，随后运行 `python3 -B tools/verify_r1.py`。保留原 10 项 JUnit 字节，新增 15 项观察行为测试，其中隔离测试用两个同时到达的真实执行调用验证事件归属。
