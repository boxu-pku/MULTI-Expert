# 算例 tables/ 自指软链：复制会无限递归（打包/拷贝陷阱）

**日期**：2026-11-02（Be/Cawkwell 结果打包触发）

## 现象

`Shot*/tables/` 里除各表软链外，还有一条
`tables -> /home/.../r94/MULTI-IFE-2015/tables/tables`（r94 表库自身的
自指链）。`shutil.copytree(..., symlinks=False)`（默认）会跟随软链，
生成 `tables/tables/tables/...` 直到 `ELOOP`；一次打包把暂存目录写到
**64 GB**。

## 要点

- **`tar` 默认不跟随**软链，所以 `tar czf` 打包原始算例目录不会炸；
  炸的是 `cp -r`（GNU cp 默认也不跟随，但 `cp -rL` 会）和
  `shutil.copytree`（默认 follow）。
- 交付包也不应保留指向源机绝对路径的表软链（换机器即失效）。

## 正确做法

打包时**只实体化 data.in 引用的表**并重建 fort.12 相对软链：

    tabs = re.findall(r"_file\s*=\s*'tables/([^']+)'", open(data.in).read())
    for t in set(tabs):
        shutil.copy2(os.path.realpath(os.path.join(src, "tables", t)),
                     os.path.join(dst, "tables", t))
    os.symlink("data.in", os.path.join(dst, "fort.12"))

参考实现：`cases/HMX_simulation/pack_results_20261028.py::copy_case`
（Be 5 MB/例、Cawkwell 6 MB/例，12 例共 ~60 MB）。

## 验收

1. 解包到任意目录，`bash verify_all.sh` 全过；
2. 解包内 `sh RUN` 重跑一发，fort.10 与原文件 md5 一致。
