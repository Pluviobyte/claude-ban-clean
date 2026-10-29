# 验证、设备记录与恢复

## 设备记录

已检查过的某版本桌面端中，ant-did 是随机 UUID 的 Base64 编码，删除后可生成不同值。版本变化需重新验证，不能把这一观察推广为任何版本的承诺。

ant-device-registry.json 曾包含按账号索引的公钥指纹及服务端设备记录 ID。原设备密钥与服务端登记仍有效时，缓存可能恢复。删除这两个文件不等于撤销服务端登记，不等于更换硬件或底层密钥。

本机程序发现过 Q6L2SF6YDW.com.anthropic.claude.hwkey 访问组和 hardwareKeyGetOrCreate 接口。接口可能创建密钥，不能用它做严格只读存在性检查。-34018 表示权限缺失，不表示不存在。原生模块具有 Secure Enclave API 不足以证明某条实际密钥是硬件保护的。

某版本的内部 rotateKey 要求已登录账号；未找到未登录时的专用正式入口。不要写成“绝对不存在”。官方 Reset App Data 会影响设置、登录和 Cowork 本地任务，不适用于保留历史的清理。Trusted devices 撤销也不能直接等同于上述硬件密钥轮换。

## 复查

先在应用关闭时复查目标。账号模式检查活跃配置和滚动备份中的白名单字段，不递归搜索历史正文。对话及项目索引仍可能保有账号关联，这是保护历史的必要范围限制。

单独授权启动应用后，记录检查时间、哪些数据重建及新旧值是否一致。保持原登录状态，不为测试主动登录。不要把恢复备份当成仍被应用使用的活跃数据。

## 回滚

每次报告包含源路径、备份、废纸篓路径与修改字段名。正常退出相关应用，先保存当前文件，然后从该批次备份恢复指定路径。JSON 恢复前比较后续新增配置；不要整目录覆盖 ~/.claude 或桌面数据目录，不要覆盖新历史。

校验备份的 SHA-256，恢复后核验格式、权限和目标内容。校验相同不等于完成恢复演练。备份和废纸篓仍含旧值，不自动清空；需要销毁备份时另行确认。

## 参考

- https://developer.apple.com/documentation/technotes/tn3137-on-mac-keychains
- https://code.claude.com/docs/en/remote-control#manage-enrolled-devices
- https://support.claude.com/en/articles/14328960-identity-verification-on-claude

这些资料用于解释权限和产品机制，不证明具体封禁原因。
