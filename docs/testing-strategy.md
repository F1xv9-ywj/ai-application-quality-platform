# Testing Strategy

测试金字塔按反馈速度分层：unit 锁定 tokenizer/retrieval 与统计函数；contract 验证 FastAPI validation/response；eval 验证端到端指标阈值；integration 覆盖 session isolation、duplicate request、timeout/error；browser E2E 只覆盖最关键 UI path。

## Commands

- `pytest -m unit|contract|eval|integration`
- `locust -f locustfile.py --host http://127.0.0.1:8000`：交互式负载建模。
- `k6 run scripts/k6-smoke.js`：20 秒 smoke gate，要求 error rate <1%、p95 <500 ms、check rate >99%。这些是本地 sample gate，不是生产 SLO。
- E2E：启动 `evalforge serve` 后运行 `pytest -m e2e --browser chromium`。

CI 排除 optional e2e，避免在基础 pipeline 强制下载 browser；适合在 release workflow 或 nightly job 另行执行。
