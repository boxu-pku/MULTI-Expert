# pkill 按名杀不掉算例内 multi 进程（产物持续被写、mv 假象失败）

**日期**：2026-09-10
**状态**：已确认并修复（hBNCpx T150 事故）
**场景**：hugoniot 算例 dt 塌缩后想中止运行，用 `pkill -f "hugoniot_T150"`
杀进程。

## 事故链

1. RUN 脚本启动的进程命令行是 `multi`（或 `/usr/bin/time multi`）与
   `sh proceso`——**命令行不含算例目录名**，`pkill -f "<目录名>"`
   匹配不到任何进程，返回 1；
2. 但同一复合命令里的 `mv output <归档名> && rm ktag` 仍执行，产生
   "已归档、已清理"假象；
3. multi 继续锁死步进并**持续写 output/fort.10/fort.11**（fd 追加模式
   会重建被 mv 走的 output），ktag 被 RUN 期 proceso 逻辑残留；
4. 后续基于"产物已固定"的提取/汇总可能读到仍在变化的文件。

## 正确做法

```bash
# 用 lsof/ps 定位具体 PID（按可执行名 + 启动时间识别），kill PID：
ps aux | grep -E "(^| )multi( |$)" | grep -v grep
kill <PID_of_multi> <PID_of_/usr/bin/time>
```

杀完后**核验**：`ps -p <PID>` 无输出 + 产物 mtime 不再变化 +
`ls ktag` 确认状态，才可 mv 归档/重提取。

## 关联

- hBNCpx T150 两次 dt 塌缩的处置记录：
  `validation_cases/hBNCpx/材料表信息.md`（含三份失败 output 备查）；
- 2026-09-10 cBNCpx/hBNCpx 迁移验收中由子 agent 发现（output 与文档
  叙述不符→追溯出残留进程）。
