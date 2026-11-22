---
title: r94 模块体系与编译链 — MODINFO/DEPENDENCES、.s96_base 别名、x.2.* 脚本
skill: multi-architecture
category: internals
source_anchors:
  - .s96_base:L1-L10
  - r94/boot-3.2/x.2.libgen:L29-L40
  - r94/boot-3.2/x.2.build:L15-L29
  - r94/boot-3.2/x.sys.ld:L4
  - r94/boot-3.2/x.0.find:L11-L51
  - MULTI-2D_梳理文档.md §3
doc_ref: "MULTI-2D_梳理文档.md §3, §8.2"
created: 2026-08-11
last_verified: 2026-08-11
verifier: claude
status: stable
tags:
  - r94
  - 模块
  - .s96_base
  - x.2.library
  - x.2.build
  - 编译链
---

# r94 模块体系与编译链

> **TL;DR**：约 50 个模块目录，每个含 MODINFO/DEPENDENCES/FILELIST/*.r/lib.a。`.s96_base` 是"模块名→路径"映射表（含别名）。编译 = r94 翻译 .r→.c → gcc -c → ar 归档 lib.a → x.2.build 生成 main.c 链接全部依赖。

## 1. 模块目录构成（梳理文档 §3）

| 文件 | 作用 |
|---|---|
| `MODINFO` | 元信息：name/author/info/parent/cdate/ldate |
| `DEPENDENCES` | 依赖模块名（每行一个），链接时自动递归 |
| `FILELIST` | 打包清单（tar 归档用） |
| `CHECKSUM`、`LOCK` | 校验和与安装锁（删 LOCK 可触发重装） |
| `*.r` | r94 脚本源代码（用户/物理逻辑） |
| `*.c`、`*.o`、`*.t` | 翻译生成的 C 源、目标文件、引用表 |
| `lib.a` | 本模块编译归档的静态库 |
| `D.h` | 内核头文件（从 kernel-4.4 拷贝，所有 .c 都 #include） |

## 2. 编译流水（梳理文档 §3.2-3.3）

```
User.r ──(transl-4.3 的 r94 翻译器)──> User.c ──(gcc -c)──> User.o ──(ar)──> lib.a
                                                                              │
   x.2.build multi2d: 自动生成 main.c（DStart/DLibera/DStop），               │
   链接本目录 lib.a + DEPENDENCES 递归收集的全部模块 lib.a ──> 可执行 multi2d  │
```

脚本实现（`r94/boot-3.2/`）：

| 命令 | 关键行 | 作用 |
|---|---|---|
| `x.2.library [dir]` | `x.2.library:12` → `x.2.libgen r94 $dir` | 翻译+编译+归档 lib.a |
| `x.2.libgen` | `:29-31`（for i in *.r; `$1 $i` 调翻译器）; `:34-37`（x.sys.compile）; `:40`（x.sys.archive） | 实际执行者 |
| `x.sys.compile` | `:4` `gcc -c -O -DLinux $*` | 编译 .c |
| `x.sys.archive` | `:4` `ar r lib.a $*` | 归档 |
| `x.2.build <name>` | `:15-27` 生成 main.c（DStart/DLibera($code())/DStop）；`:7` linklist；`:29` x.sys.ld | 链接可执行 |
| `x.sys.ld` | `:4` `gcc -o $name $* -L/usr/X11R6/lib -lX11 -lgfortran -lm` | 链接（含 X11/gfortran 运行时） |
| `x.2.linklist [dir]` | — | 输出依赖 lib.a 完整路径列表（递归 DEPENDENCES） |
| `x.0.find <module>` | `:11` base=$MULTI/.s96_base；`:36/:51` `fgrep ":$key:" $base` | 查模块路径 |

**入口约定**：源文件中至少一个 `entry multi2d()` 或 `entry multi()`，编译器据此生成
`_multi2d0`/`_multi0` C 函数，由 main.c 调用（梳理文档 §3.2）。

## 3. .s96_base 路径表与别名

格式：`类型:挂载目录:模块名:`（每行一条）。前 10 行实例（`.s96_base:1-10`）：

```
pathto:$MULTI/r94/boot-3.2:boot-3.2:
default:$MULTI/r94/kernel-4.4:kernel-4.4:
alias:$MULTI/r94/kernel-4.4:kernel-4.3:
alias:$MULTI/r94/kernel-4.4:kernel-4.2:
...
```

- `default` = 当前版本；`alias` = 旧版本号→当前路径（kernel 的 5 个别名在 :3-7）
- m2d-core-9.1 条目在 `:29-34`（含 m2d-core-9.0/7.0.9 等别名）；
  MULTI-IFE-2015 在 `:82`
- 效果：User.r 的 DEPENDENCES 写 `m2d-core-7.0.7` 也透明映射到 9.1
- 环境变量 `$MULTI` = 根目录绝对路径（由 `R94:L7-L12` 设置并导出；
  PATH 由 `x.1.path` 拼入 boot-3.2）

## 4. 算例 RUN 脚本（编译链的实际使用）

2D 算例（`cases/M2D_Radia_110/RUN`，16 行）：
```
:1  echo "nada" >ktag          # 运行标记
:3  x.2.library                # 编译本目录
:10 x.2.build multi            # 链接出 multi
:11 mv multi a.out
:13-15 生成 proceso: /usr/bin/time a.out>>output 2>>cputime;rm ktag
:16 nohup sh proceso &
```
1D 算例不同：直接 gfortran 编译 m150304.f95（`cases/2015CPC/RUN:L2-L8`）。
详见 multi-case-runner skill。

## 5. 常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| `can't translate User.r` | r94 语法错 | 看翻译器报错行；r94 例程引用写法是 `'name(N)'`（梳理文档 §12） |
| 链接缺 lib | DEPENDENCES 缺模块或该模块未编译 | 先 `x.2.library` 编译依赖模块；`x.0.find <mod>` 确认路径 |
| `x.2.*: command not found` | $MULTI/PATH 未设 | `export MULTI=<根>`; `export PATH=$PATH:$MULTI/r94/boot-3.2:.`（梳理文档 §12） |
| 改了 Material.r 算例没生效 | 未重编译 | `cd r94/m2d-core-9.1 && x.2.library` 后重编算例 |

## 6. 延伸阅读

- `MULTI-2D_梳理文档.md §3`（模块体系）、§8（运行方式）
- `r94/26_MULTI_documents/2009_r94_manual.pdf`（r94 语言手册）

## 7. 变更日志

| 日期 | 改动 | 改动人 |
|---|---|---|
| 2026-08-11 | 初始创建 | claude |
