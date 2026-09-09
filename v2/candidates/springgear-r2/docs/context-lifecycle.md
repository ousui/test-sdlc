# 执行上下文与重复调用

每次 `execute(parts)` 都创建独立 Context、参数数组副本和 ContextValue Map 副本。同一次执行的各节点共享这份上下文；并行调用、重复使用同一个 parts、显式重试和嵌套调用分别使用自己的容器。执行器不使用全局锁或 ThreadLocal，也不会自动重试。失败后再次调用 `execute` 才是一次新的尝试，从调用者提供的种子重新复制，已有观察器为每次调用分配新的 executionId。

成功、handler 异常、Error、supports 异常和控制流程退出都会在 finally 中释放 Context 持有的 request、args、values、response 引用。Context 只在执行期间有效，执行结束后这些 getter 返回 null；source 和 timestamp 仍可用于识别。框架不关闭、不清空业务对象，因此直接返回 values Map、在结果中嵌套 Map 或参数数组、以及 Interrupt 携带的 response 均保留原对象和内容。调用者或 handler 自行保存的对象仍归其持有，释放引用不等于擦除数据。

原有五参数 Context 构造器保留。单独构造的 Context 不会自行释放；执行器管理它创建的 Context 生命周期。Continue 保留本次上下文并继续下一节点；Interrupt 和其他失败保持原来停止策略及 cause。supports 抛出异常仍直接退出，不虚构节点 START。观察器异常沿用 R1 的隔离策略，不能阻止 finally 清理或掩盖业务异常。

复制默认是浅复制：参数数组和 Map 容器独立，request 对象、Map 内对象及子类字段的对象引用不会被通用深复制。调用者应在调用期间保持 seed 和 args 输入稳定；共享的可变业务对象和 handler 自身字段仍由业务负责同步。若自定义 ContextValue 包含可变字段，可覆盖 `copyForExecution()` 为这些字段定义复制策略：

```java
@Override
public SpringGearContextValue copyForExecution() {
    MyValues copy = (MyValues) super.copyForExecution();
    copy.items = new ArrayList<>(items);
    return copy;
}
```

默认 HashMap clone 保留运行时子类。自定义 hook 必须返回非 null、不同实例且同一运行时类型的副本；不满足时执行器在进入 handler 和发送节点事件前拒绝调用。hook 自身的业务复制语义由提供者负责。null seed 继续允许不访问 values 的旧调用方式。

在 JDK 21 与已准备的隔离缓存下离线运行四模块 Maven `clean verify`，再运行 `python3 -B tools/verify_r2.py`。原始 10 项和 R1 的 15 项测试保留原字节；新增 18 项覆盖真实 barrier 并发、同 parts、观察事件和 cause 归属、子类复制、所有退出清理、嵌套返回对象、显式重试及重入。同步使用 barrier 和有界 Future 等待，不用 sleep 推测并发。
