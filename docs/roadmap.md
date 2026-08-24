# Roadmap

- 0.1：本地 deterministic RAG、OpenAI-compatible target、五维 evaluator、三种 report、dashboard、CI 与 load scripts。
- 0.2：pluggable citation normalizer、dataset schema version、baseline diff 与 flaky-case quarantine。
- 0.3：PostgreSQL run history、distributed workers、OIDC/RBAC、signed evidence artifacts。

路线图是候选方向，不是承诺或已实现能力。

## Current limitations

- In-memory documents/runs/sessions 会在进程重启后清空。
- Remote adapter 不解析 provider-specific citations，并要求 public DNS allowlist；本地私网 endpoint 需通过受控 proxy 暴露，不能绕过 SSRF guard。
- Dockerfile 已做静态 review，但当前验证环境未运行 Docker build；base image 使用可读 tag，发布流程可再由 Dependabot 管理 digest pinning。
- Dashboard 已完成浏览器交互与 responsive 检查；受当前浏览器会话截图输出限制，仓库 screenshot artifact 为 979×1024，而非设计稿原生 1536×1024。运行时页面本身在 1536px viewport 报告 `scrollWidth == innerWidth`。
