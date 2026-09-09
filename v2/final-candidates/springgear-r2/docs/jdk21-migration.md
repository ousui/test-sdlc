# JDK21 构建

本次只调整 build/parent 的编译与依赖配置，保留原 core/BOM 模块及其余源文件。编译 release 固定21；Spring5.3.31、Lombok1.18.30 和 JUnit5.10.5 配合已固定的 Maven 插件执行原十项验收。没有启用旧扩展模块，也没有执行发布。

在 JDK21 和预先准备的独立 Maven 缓存下，从本目录执行：

```sh
mvn -o -B -ntp -s .mvn/settings.xml -gs .mvn/settings.xml -Dmaven.repo.local=/path/to/isolated/repository clean verify
python3 -B tools/verify_r0.py
```

该命令真实运行四模块和原十项测试，随后检查实际 XML、全部38个生产class的major65、原始114文件范围和三份历史空白文件的原字节。缓存路径由使用者选择；不要把示例路径当作现有目录。单独的settings不读取用户凭证。后续观察器和上下文并行功能属于R1/R2，未包含于本轮。
