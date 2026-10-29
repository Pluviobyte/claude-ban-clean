# claude-ban-clean

**中文优先的 Claude 本机清理 Skill，适用于 macOS。** 将缓存、旧账号字段、登录状态和设备记录分开处理，先备份和校验，再执行窄范围清理。

名称中的 `ban` 表示账号受限后的维护场景。该工具不能解除封禁、绕过 KYC，也不保证清理后无法关联设备；账号问题请通过官方支持处理。

## 能做什么

| 范围 | 内容 | 默认行为 |
| --- | --- | --- |
| `cache` | Claude Code 缓存、遥测目录，桌面图形缓存、日志、崩溃报告、窗口及兼容探测状态 | 只读审计 |
| `account` | 主配置、滚动备份和桌面配置中的指定账号/令牌字段，CLI 凭据文件、桌面配置 journal | 需明确选择，可能退出登录 |
| `device-records` | `ant-did`、`ant-device-registry.json` 两个本地文件 | 需单独选择，不更换底层设备密钥 |
| 浏览器 | 多资料、Cookie、IndexedDB、Local/Session Storage、扩展及第三方分区的定向操作流程 | 代理按参考文档处理；脚本不自动修改 Chrome |

仅使用 Python 3.10+ 标准库。Windows、Linux 尚不支持实际清理。不能由正在运行的 Claude Code 清理它自身使用的数据。

## 安装为 Codex Skill

```sh
git clone https://github.com/Pluviobyte/claude-ban-clean.git ~/.codex/skills/claude-ban-clean
```

目录已存在时先检查原内容，不要覆盖。安装后在新会话调用：

```text
使用 $claude-ban-clean 先只读检查 Claude 缓存与旧账号字段，列出清单。
不要动对话历史、Skills、Hooks、MCP、钥匙串、时区和其他应用数据。
```

其他支持 SKILL.md 的代理可将本仓库放入其对应的技能目录。浏览器操作能力和额外授权依宿主而定。

## 在终端使用

在本仓库目录执行：

```sh
# 默认只审计缓存，不写盘
python3 scripts/cleanup.py

# 审计缓存和账号字段；不显示字段值
python3 scripts/cleanup.py --scope cache --scope account

# 显示清单，输入 CONFIRM 后先备份再执行
python3 scripts/cleanup.py --scope cache --scope account --apply

# 仅在明确需要移除设备记录时使用
python3 scripts/cleanup.py --scope device-records --apply
```

没有 `--yes` 或跳过确认选项。`--apply` 需要真实终端；检测到 Claude 进程就停止，不替你结束任务。执行前请正常退出 Claude Desktop 和 Claude Code。

## 保护哪些数据

脚本不移除对话历史、projects、sessions、history.jsonl、file-history、Skills、Hooks、Plugins、Commands、Agents、MCP 或项目/Git 文件；不修改 settings.json、settings.local.json、claude_desktop_config.json。不会调用系统钥匙串接口，也不修改时区、代理、Shell 或 WebRTC。

`account` 仅移除这些顶层键：

```text
oauthAccount
accountUuid
oauth:tokenCache
oauth:tokenCacheV2
lastKnownAccountUuid
```

未知字段、嵌套项目内容、userID/machineID 和历史关联账号索引保留。因此不能宣称清除了所有账号痕迹。CLI `.credentials.json` 若存在会整体备份后移入废纸篓；桌面 `config.json.journal` 同样处理，避免旧登录状态被 journal 恢复。

移除遥测失败队列只是清理本机待处理文件，不代表已经关闭遥测，也不证明这些记录导致封禁。

## 备份、验证和恢复

- 第一项写操作是创建时间戳备份批次：`~/ClaudeBackups/claude-ban-clean-*`，批次权限为 `0700`。
- 对全部选中目标逐文件计算 SHA-256，并比较目录结构；全部通过后才开始清理。
- 移除项进入 `~/.Trash/claude-ban-clean-*`，不清空废纸篓。JSON 修改前的原件在备份中。
- 备份中有 `hashes.json` 和 `report.json`；报告只记录路径、键名、进度，不记录字段值。
- 中途出错会停止，报告状态为 `partial-or-stopped`。不会自动回滚覆盖当前文件。
- 符号链接和非普通文件会被拒绝。脚本不是对抗恶意并发写入的系统沙箱；操作时应保持相关应用关闭。

回滚前正常退出相关应用，另存当前状态，再从该批次备份恢复具体路径。不要整目录覆盖，避免覆盖新产生的历史或配置。备份可能含令牌、Cookie 或个人资料，应仅在本机妥善保管，不提交 GitHub。

## 设备密钥与浏览器限制

删除 `ant-did` 后，应用可能生成新值；删除登记 JSON 后，应用可能依靠保留的密钥和服务端登记恢复旧记录。删除缓存不等于撤销服务端设备登记。

受保护钥匙串读取报权限错误不能证明密钥不存在。本工具不注入程序、不重签名、不绕过访问组，也不修改密钥代次文件。

Chrome 的 Persona 等第三方存储可能属于 ChatGPT、Kraken 等其他站点。不能按关键词整库删除。浏览器清理需单独授权，并逐资料、逐 origin 和分区验证。详见 [浏览器流程](references/browser.md) 与 [验证和回滚](references/verification.md)。

## 验证

```sh
python3 -m unittest discover -s tests -v
```

测试使用临时目录中的模拟数据，覆盖只读审计、备份失败不清理、备份与废纸篓一致、账号字段修改保留历史/MCP/未知字段，以及符号链接拒绝。它们不对用户真实环境执行清理，不代表所有 Claude 版本及运行状态均已验证。

## 目录

```text
SKILL.md                     代理操作入口
scripts/cleanup.py           审计、备份与窄范围清理
agents/openai.yaml           Codex 展示信息
references/browser.md        浏览器存储与共享分区流程
references/verification.md   设备记录语义、复查与恢复
tests/test_cleanup.py        临时目录安全性测试
```

本仓库不包含任何个人清理日志、账号信息、Cookie、密钥或恢复备份。
