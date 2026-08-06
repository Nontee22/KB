## 组合示例（一条龙）

```bash
# 日常提交 + 推送
git add -A && git commit -m "更新笔记" && git push

# 提交全部已跟踪文件（跳过 add）
git commit -am "更新算法笔记" && git push

# 首次推送到 GitHub
git remote add origin https://github.com/用户名/仓库.git
git push -u origin main
```

## 初始化与配置

```bash
git init
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"   # 提交身份，首次必须配置
git config --global core.autocrlf true      # Windows 建议开启，避免换行符问题
```

## 查看状态

```bash
git status              # 查看工作区/暂存区状态
git status -sb          # 简略状态 + 分支跟踪信息（ahead/behind）
git diff                # 查看未暂存的改动
git diff --staged       # 查看已暂存待提交的改动
```

## 暂存与提交

```bash
git add <文件>          # 暂存指定文件
git add -A              # 暂存所有改动（含新增、删除）
git commit -m "提交信息" # 提交暂存内容
git commit -am "信息"    # 跳过 add，直接提交所有已跟踪文件的改动
git commit --amend      # 修改上一次提交（未推送时使用）
```

## 推送与拉取（重点）

```bash
git push                          # 推送到当前分支的上游
git push -u origin main           # 首次推送并建立上游跟踪
git push --force-with-lease       # 覆盖远端（带保护，比 --force 安全）
git pull                          # 拉取并合并（= fetch + merge）
git pull --rebase                 # 拉取并以 rebase 方式合并，历史更干净
git fetch                         # 只拉取远端状态，不合并
```

## 分支操作

```bash
git branch                    # 查看本地分支（* 为当前分支）
git branch -a                 # 查看所有分支（含远端）
git branch <name>             # 新建分支
git checkout <name>           # 切换分支
git checkout -b <name>        # 新建并切换
git merge <name>              # 合并指定分支到当前分支
git branch -d <name>          # 删除本地分支
git push origin --delete <name>  # 删除远端分支
```

## 撤销与回退

```bash
git restore <文件>            # 丢弃工作区改动（危险，不可恢复）
git restore --staged <文件>   # 取消暂存，保留改动
git reset --soft HEAD~1       # 撤销最近一次提交，保留改动在暂存区
git reset --hard HEAD~1       # 撤销最近一次提交并丢弃改动（危险）
git revert <commit>           # 生成一个反向提交来撤销（适合已推送）
```

## 日志

```bash
git log --oneline            # 一行一条提交历史
git log --oneline -10        # 最近 10 条
git log --oneline --graph    # 图形化分支历史
git log -p                   # 带每次提交的 diff
git show <commit>            # 查看某次提交详情
```

## 遇到冲突时

```bash
git status
# 手动编辑文件解决冲突后：
git add <文件>
git commit -m "解决冲突"
```
