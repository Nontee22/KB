同步 GitHub 的命令如下

```bash
# 1. 查看本地状态（确认有没有未提交的改动）
git status

# 2. 拉取远端最新信息（fetch 不会改动本地文件，只是获取远端状态）
git fetch origin

# 3. 把本地 main 更新到和远端一致（快进合并，无冲突）
git pull --ff-only origin main
```

如果你的流程是"先提交本地改动，再同步"，完整版是：

```bash
# 提交本地改动
git add .
git commit -m "你的提交说明"

# 拉取远端更新并合并（推荐 pull --rebase，保持提交历史线性）
git pull --rebase origin main

# 推送本地提交到 GitHub
git push origin main
```

几点说明：

- **只拉取（上面第一种）**：`git status` 显示 `nothing to commit, working tree clean` 时才安全。
- **有本地提交时**：用 `git pull --rebase` 而不是 `git pull`，可以避免产生多余的合并提交。
- 如果 `git pull --rebase` 出现冲突，需要手动解决冲突文件后执行 `git rebase --continue`，再推送。

刚才这次同步实际用到的就是第一段的三条命令。