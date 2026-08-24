# Security Policy

当前维护版本为 `0.1.x`。请通过 GitHub private vulnerability reporting（启用后）报告漏洞；若不可用，联系仓库维护者的公开安全邮箱。不要在 public issue 中披露 exploit、credentials 或敏感样本。

EvalForge 是教育/作品集项目，不应直接暴露到公网。Remote target 的 API key 只应通过环境变量或 secret store 注入，禁止写入 dataset、report 或日志。维护者目标是在 7 天内确认报告，但不提供正式 SLA。
