---
name: claude-ban-clean
description: 在 macOS 上审计、备份和定向清理 Claude Code、Claude Desktop 与 Chrome 的本地缓存、旧账号字段及站点数据。用于账号受限后的本机隐私整理、排障或卸载准备，保护对话历史、Skills、Hooks、MCP 和其他应用数据；不用于解除封禁或规避身份验证。
---

# Claude 本机安全清理

先区分用户需要的是检查、缓存清理、退出登录，还是设备记录移除。已有授权继续有效；不要从“清理缓存”推导出清理凭据、卸载扩展或更换设备密钥的授权。

## 工作流

1. 运行 `python3 scripts/cleanup.py`。默认只读，输出候选路径和字段名，不显示值，不访问钥匙串。macOS 以外仅说明尚不支持，不执行清理。
2. 根据用户范围选用下列 scope；先展示清单和实际影响，再执行 `--apply`。脚本要求终端输入一次 `CONFIRM`，不要管道代答。清理者如果正是 Claude Code，只做审计，交给 Codex 或普通终端执行。
   - `cache`：明确的缓存、日志、图形缓存及窗口/探测状态。不会删除功能配置。
   - `account`：指定 JSON 的明确账号/令牌字段、CLI 凭据文件和桌面配置 journal。会影响登录；不移除整个配置，不改 userID/machineID。
   - `device-records`：仅 `ant-did`、`ant-device-registry.json`；必须单独获得用户授权。不是底层密钥重置。
3. 让用户正常退出相关 Claude 应用。脚本检测到进程或无法确定进程状态时停止，不自动 kill。Chrome 清理单独按 [浏览器流程](references/browser.md) 处理，不因本机清理关闭其他应用。
4. 脚本把所有选中目标复制到权限为 0700 的 `~/ClaudeBackups/` 时间戳目录，逐文件 SHA-256 和目录树校验；再把移除项移入时间戳废纸篓目录，JSON 按字段修改。不要用全盘 rm、全删 JSON 或整个 Application Support/Claude 代替。
5. 阅读脚本报告；若中途失败，报告已完成部分及恢复位置，不声称全部成功。检查成功仅覆盖选中目标，不能宣称“全盘无痕”。
6. 用户要求时才正常启动应用复查；启动会产生数据。只比较标识是否相同，不显示完整值；不要为验证而登录、打开历史对话或调用 get-or-create 密钥接口。

示例：

```sh
python3 scripts/cleanup.py --scope cache
python3 scripts/cleanup.py --scope cache --scope account --apply
```

## 保留边界

- 不读取对话正文；不移除 projects、sessions、history.jsonl、file-history、skills、hooks、plugins、commands、agents、MCP、项目仓库、桌面 claude-code-sessions / local-agent-mode-sessions。
- `account` 只改白名单顶层字段；历史关联账号索引、MCP OAuth 和未知字段保留。`settings.json`、`settings.local.json`、`claude_desktop_config.json` 不改。
- 不修改 Shell、时区、代理、WebRTC 或其他应用数据。这些不是解除封禁的方法。
- 不自动删除钥匙串，包括 Claude Code-credentials、Claude Safe Storage、设备密钥；读取不到不代表不存在。需要此类操作时使用官方受支持流程并明确其影响。
- 不修改程序签名、注入进程、绕过钥匙串访问组或伪造设备身份。
- 不将备份、Cookie、令牌、日志或用户报告提交 GitHub。备份仍可能含秘密，不能称为彻底擦除。

## 特殊情况

浏览器 Cookie、扩展和共享分区：读 [browser.md](references/browser.md)。
设备记录语义、无法访问的密钥、复查和回滚：读 [verification.md](references/verification.md)。

名称中的 ban 表示使用场景，不表示可以解除账号封禁。账号状态通过官方支持/申诉处理；本地标识存在不能证明它是封禁原因。
