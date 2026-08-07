# Reasonix 快捷方式修复全流程复盘（首个开源贡献 PR #7752）

> 2026-08 · Windows 11 25H2 · 从 0 到合并上游的完整记录，重点标注**每一步能学到什么**

---

## 一、问题

Reasonix 从 v1.19.6 应用内更新到 v1.20.0 后，开始菜单里的 Reasonix 快捷方式失效：点击报"找不到应用"，随后图标自动消失。删除快捷方式重新创建后恢复正常。

## 二、诊断过程

1. **查文档**：v1.20.0 起 Windows 改用版本化安装布局（`versions/<v>/` + `current.json` + 薄启动器 `reasonix-launcher.exe`），开始菜单快捷方式应指向稳定的 `Reasonix.exe`（launcher 别名）。
2. **本机取证**（`<Reasonix 安装目录>`）：
   - `current.json` → `v1.20.0`（激活正常）
   - 重建后的快捷方式 TargetPath = `<Reasonix 安装目录>\Reasonix.exe`（存在，正常）
   - `versions/` 里只剩 `v1.19.5` 和 `v1.20.0` → 旧版本目录确实被更新器清理过
3. **定位代码**：`desktop/icon_repair_windows.go` 的启动自修复逻辑（`repairDesktopIconIntegration` → `repairWindowsShortcut`）。

## 三、根因

升级前快捷方式的 TargetPath 指向 `versions/<旧版本>/reasonix-desktop.exe`；升级时更新器清理了旧版本目录，TargetPath 悬空。而 v1.20.0 的快捷方式自修复**只重写 IconLocation（图标），从不重写 TargetPath**——尽管 `reasonixWindowsShortcutTarget` 已把版本化路径判定为"Reasonix 自有"，却只修图标不修目标，快捷方式继续失效。

## 四、解决方案

**提交 issue**：中文 issue 全文（复现步骤、OS、根因假设、声明自己来修）。

**写补丁**（`desktop/icon_repair_windows.go`）：
- 新增 `reasonixWindowsVersionedTarget`：识别指向 `versions/<v>/reasonix-desktop.exe` 的目标
- 新增 `repairWindowsShortcutPlan`：决定需重写哪些属性（target / icon / 都不动）
- `repairWindowsShortcut`：检测到版本化 TargetPath 时重写为稳定 `reasonix-launcher.exe` + 修正 `WorkingDirectory`，再按需修图标，统一 Save
- 不误伤用户自定义指向别处的快捷方式

**写测试**（`desktop/icon_repair_windows_test.go`）：2 个测试函数共 14 个用例（版本化路径判定、大小写、不同盘/目录拒绝、target×icon 组合）。

**验证**：`go test` ✅（ok reasonix/desktop 26.4s）、`gofmt` ✅、`go vet` ✅；提交前独立 review 提的大小写疑虑经本机 8 组路径实测为误报。

## 五、环境搭建（最终状态）

- Go 1.26.5 便携版：`<Go 工具链目录>`（非 C 盘，SHA256 校验通过，User PATH 持久化）
- GOPATH / 模块缓存：`<Go 工具链目录>\gopath`（原 C 盘缓存已删，释放 ~158MB）
- 仓库：`<本地仓库目录>`（origin = 自己的 fork `Nontee22`，upstream = esengine）

## 六、提交与合并

建分支 `fix/windows-shortcut-target` → Conventional Commits 提交 → push → 开 PR（按官方模板填 `Documentation-impact: none` / `Cache-impact: none`）→ CI 23 项检查全过 → **SivanCola 合并进 `esengine:main-v2`（PR #7752）**，issue #7750 自动关闭。修复将随 v1.21.0 发布。

---

# 🌟 重点：这个流程能学到什么

## 1. GitHub 开源协作的完整闭环（最值钱的一课）

| 概念 | 学到什么 |
|---|---|
| fork | 把别人的仓库复制到自己的账号下，获得"可写副本" |
| remote | `origin` = 自己的 fork（push 目标），`upstream` = 上游（拉更新源）。克隆别人的仓库时 origin 是上游，要 `git remote set-url` 改成自己的 |
| 功能分支 | 不在 main 上直接改：`git checkout -b fix/xxx`，每个修复一个分支 |
| Conventional Commits | 提交信息有规范：`fix(desktop): 描述`（type(scope): subject） |
| push 认证 | HTTPS 推送要 Personal Access Token（PAT），不是登录密码；勾 `repo` 权限 |
| PR | 分支推到 fork 后点链接开 PR；base 选上游 `main-v2`，compare 选自己的分支 |
| `Fixes #7750` | 单独一行写，合并时 GitHub **自动关闭关联 issue** |
| 等 CI | fork 的 PR 首次跑 workflow 需维护者批准（安全机制）；批准后 lint/race/test 自动跑 |
| 合并后 | 本地 `git pull upstream main-v2` 同步，删除旧分支 |

## 2. 写 issue 的正确姿势

- 用官方模板（`bug_report.yml`），字段：版本线、精确版本、现象、**复现步骤**、OS、日志
- 现象描述要具体："点击报找不到应用 → 图标自动消失" 比"快捷方式坏了"有用 100 倍
- 附上自己的**证据**（current.json 内容、TargetPath、目录列表）——维护者一眼能确认问题
- 给出**根因假设**（哪怕不确定）——显示你认真查过，也引导修复方向
- 结尾声明"这个 bug 我来修"——开源社区非常欢迎"报告 + 自修"的贡献者

## 3. 定位问题的方法论：先文档，再取证，后代码

```
查文档/changelog（机制是什么样）
   ↓
本机取证（实际状态 vs 应有状态，找差异）
   ↓
差异即线索 → 定位到具体代码文件/函数
```

这次就是：文档说"快捷方式应指向 launcher" → 实测 current.json 正常、快捷方式 TargetPath 正常（重建后）→ 反推**升级时**的旧快捷方式指向版本化目录 → 代码里找到只修图标不修目标的函数。**证据链思维**是排障的核心技能。

## 4. 工程化改代码

- **最小 diff**：只改必要的文件/函数，不顺手重构无关代码（review 提到的 pre-existing 问题选择不动，避免扩大改动面）
- **纯逻辑抽函数**：把"决定要不要修、修什么"抽成无副作用的纯函数（`repairWindowsShortcutPlan`），让没有 COM 依赖的逻辑能被单测——**可测试性设计**
- **测试用例设计**：正例（版本化路径）、反例（其他安装/其他文件/空值）、边界（大小写、深层路径）都要覆盖
- **工具链纪律**：`gofmt`（格式）、`go vet`（静态检查）、`go test`（测试）——CI 也会跑，本地先过一遍

## 5. 环境与工具管理

- 便携版工具链（Go zip 解压即用）可放任意盘、不污染系统；`go env -w GOPATH=...` 可迁移缓存
- **SHA256 校验**下载文件（`Get-FileHash` 对比官方值），防止下载损坏/被篡改
- 证书吊销检查失败（`CRYPT_E_REVOCATION_OFFLINE`）时用 `curl --ssl-no-revoke` 或国内镜像
- PATH 修改写入 User 级（`[Environment]::SetEnvironmentVariable`）持久生效，但**每个新 shell 进程要重新加载**才能用

## 6. 协作与心态

- 新手完全可以贡献：不需要多强，**认真查证 + 规范流程 + 愿意改**就够
- 等 review/CI 是常态，不是卡住；反馈意见改完 `git push` 即可自动更新 PR
- CI 23 项全绿（含 Windows/macOS/Linux 三平台、race、漏洞扫描）是对改动质量的强背书
- 第一次合并的感觉：你的代码进入了别人每天都在用的软件

## 7. 顺带学到的领域知识

- **Windows 快捷方式机制**：.lnk 的 TargetPath / IconLocation / WorkingDirectory，悬空目标会被系统自动清理图标
- **版本化安装布局**：`versions/<v>/` + `current.json` 指针 + 薄启动器，支持回滚和原子更新
- **AI agent 是什么**：模型（想）× 工具（做）× loop（决策）× harness（可靠外壳）；DeepSeek 官方强化模型/API 层，Reasonix 这类工具做外壳

---

# 下次贡献 checklist

- [ ] `git checkout main-v2 && git pull upstream main-v2`（先同步）
- [ ] 查 changelog / 文档，确认机制
- [ ] 本机取证，形成证据链
- [ ] `git checkout -b fix/xxx` 建分支
- [ ] 最小改动 + 补测试（正/反/边界）
- [ ] `gofmt` / `go vet` / `go test` 本地全过
- [ ] Conventional Commits 提交
- [ ] `git push -u origin fix/xxx`
- [ ] 开 PR：官方模板 + `Fixes #issue号`（单独一行）
- [ ] 等 CI / review，有意见改完再 push
