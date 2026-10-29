# Chrome 定向清理

此步骤由代理使用浏览器设置或明确支持的存储接口执行，Python 脚本不自动修改浏览器数据库。

## 只读盘点

逐个资料检查 Default、Profile N，不假定所有资料均有 Claude 数据。只输出站点、Cookie 名称、存储类型、数量，不输出 Cookie 值。读取 SQLite 要用 mode=ro；遇锁停止，不用 immutable 强读或删除锁文件。

相关域名通常为 claude.ai、claude.com、anthropic.com 及其子域。不要通过字符串包含 claude 扩大为 GitHub 仓库、书签、其他应用记录。第三方社区站点另经用户确认。

Persona、Cloudflare、hCaptcha 可能服务多个网站：必须按顶层站点/分区判断，不能因 withpersona.com 匹配就删除 ChatGPT、Kraken 等站点分区。

## 授权、备份和清理

1. 明确用户是否允许退出 Claude 网页登录、清理扩展设置。仅检查请求不能授权删除。首次需要删除时列出具体站点及影响。
2. 正常关闭相关标签；不要自动修改全局启动设置或关闭无关未保存页面。
3. 正常退出 Chrome 后备份将修改的数据库和存储目录，校验内容。共享数据库的备份可能包含其他站点信息，只能本地保存并限制访问。
4. 优先使用 Chrome 原生站点数据设置清理指定站点；重新打开时避免恢复相关页面。操作前核对展开列表，尤其是第三方分区。
5. 若采用离线数据库操作，需要先确认当前版本 schema、精确选中记录，事务内验证所有未选中记录不变；不删整个 Cookies、Local Storage、Session Storage、QuotaManager 或 Service Worker 目录。
6. LevelDB 不通过文本搜索文件后整库删除。必须使用兼容库，按 origin/storage key 删除并比较其余键值；无法解析就标记未完成，不假称已清空。
7. Claude 扩展 ID 的已知示例为 fcoeoabgfenejglbffodgkkbkcdhcgfn；先核对当前扩展名称和 ID。清理存储不等于卸载。停用/卸载需要相应授权。

## 验收

- 逐资料复查目标 Cookie、IndexedDB、Local/Session Storage、配额登记和扩展存储。
- 明确哪些类型没有能力检查，不以几个查询为空证明所有浏览器数据均为空。
- 其他站点 Cookie 和共享分区内容应保持不变。
- 扩展或页面继续运行会重新生成记录。只确认当次检查时刻。
- 用户没有要求浏览器历史清理时，不删除 History、书签或标签恢复数据。
