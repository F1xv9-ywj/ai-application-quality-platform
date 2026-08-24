# EvalForge · AI Application Quality Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Test%20framework-pytest-0A9EDC?logo=pytest&logoColor=white" alt="pytest">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

## 中文

### 项目简介

EvalForge 是一个面向 **AI application、RAG pipeline 与 OpenAI-compatible API** 的可复现质量保障平台。它把功能测试、接口契约测试、RAG 检索与答案 grounding、多轮会话隔离、异常输入和基础性能测试统一到一条 evaluation pipeline 中，并输出可供人阅读、CI 消费和后续分析的证据。

默认使用 deterministic local RAG target，不需要付费 API 或外部模型即可运行完整演示；同时提供经过安全约束的 remote adapter，方便接入自有 OpenAI-compatible `/chat/completions` endpoint。

> **项目边界：** 仓库中的 cases、截图和报告都是 sample/synthetic 数据，用于演示测试方法，不代表生产系统表现或真实业务数据。

![EvalForge dashboard sample](docs/dashboard-sample.png)

截图由本地 synthetic sample evaluation 实际生成；视觉参考稿见 [`docs/assets/dashboard-concept.png`](docs/assets/dashboard-concept.png)。

### 为什么做这个项目

许多 LLM demo 能够“回答问题”，但难以回答以下工程问题：

- API contract 是否在异常参数、重复请求和超时下仍然稳定？
- RAG 是否真的检索到了正确文档，答案是否包含 unsupported claim？
- 多轮 history 是否发生会话串扰？
- 一次变更后，质量、延迟和错误率是否能在 CI 中被阻断？

EvalForge 将这些问题转化为 versioned JSONL cases、明确的 metrics 和可追溯 reports。

### 核心能力

| 能力 | 实现内容 |
| --- | --- |
| API contract testing | FastAPI target 覆盖文档入库、检索问答、history、idempotency、非法参数及 timeout/error simulation |
| RAG evaluation | retrieval `recall@k`、answer relevance、citation/unsupported claim 检查 |
| Robustness testing | 空输入、超长 prompt、非法文件、重复请求和错误响应路径 |
| Performance testing | `p50/p95 latency`、error rate、throughput；提供 Locust 与 k6 脚本 |
| Evidence & reporting | JSON、HTML、JUnit XML；Dashboard 直接消费 run API |
| Quality gate | pytest markers、coverage、ruff、mypy、CI workflow、Docker healthcheck |

### 30 秒开始

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

python -m pip install -e ".[dev]"
python -m evalforge evaluate --dataset datasets/sample.jsonl --output reports/sample
python -m evalforge serve
```

从 GitHub 下载项目不会自动启动服务。只有当最后一条命令保持运行时，下面的本地地址才可访问：

- Dashboard：<http://127.0.0.1:8000>
- API docs：<http://127.0.0.1:8000/docs>
- JSON report：[`reports/sample/report.json`](reports/sample/report.json)
- HTML report：[`reports/sample/report.html`](reports/sample/report.html)
- JUnit report：[`reports/sample/junit.xml`](reports/sample/junit.xml)

一条命令执行静态检查、类型检查、测试和 sample report：

```powershell
powershell -File scripts/check.ps1
```

GNU Make 环境也可以运行 `make check`。

### Remote target

```powershell
$env:EVALFORGE_REMOTE_ALLOWLIST = "api.example.com"
evalforge evaluate --target remote `
  --base-url https://api.example.com/v1 `
  --model your-model `
  --dataset datasets/sample.jsonl `
  --output reports/remote
```

macOS/Linux 使用 `export EVALFORGE_REMOTE_ALLOWLIST=api.example.com`。CLI 会向 `{base-url}/chat/completions` 发送 OpenAI-compatible request。

Remote adapter 默认启用以下安全约束：

- host 必须显式出现在 allowlist；
- 单次 DNS resolution 后，所有解析地址都必须是 public address；
- 连接固定到已验证的 IP，同时 HTTPS 仍使用原 hostname 完成 SNI 与证书验证；
- 拒绝 redirect、embedded credentials、本机、私网、link-local 与保留地址。

Remote adapter 当前只评估回答文本；如需 retrieval/citation metrics，应让被测系统提供可映射的 citation contract 并扩展 adapter。

### 测试与质量门禁

```bash
pytest -m unit
pytest -m contract
pytest -m eval
pytest -m integration
pytest -m "not e2e" --cov=evalforge
ruff check .
mypy src
```

可选 browser E2E：

```bash
python -m pip install -e ".[e2e]"
playwright install chromium
# 先启动服务，再执行
pytest -m e2e --browser chromium
```

Load testing 见 [`docs/testing-strategy.md`](docs/testing-strategy.md)。

本地验证记录：`29 passed, 1 skipped`，coverage `89.87%`；sample CLI evaluation 为 `5/5` 通过。这里的数字是本仓库当前 synthetic test suite 的结果，不是生产 SLA。

### 架构

```text
JSONL cases ──┐
              ├── Evaluator ── Metrics ── JSON / HTML / JUnit
Local RAG ────┤                    │
Remote API ───┘                    └── FastAPI Dashboard
```

```text
src/evalforge/       API、targets、evaluator、reporters、CLI、dashboard
datasets/            versioned synthetic JSONL cases
tests/               unit / contract / eval / integration / optional e2e
reports/sample/      reproducible sample evidence
docs/                architecture、metrics、testing、research、roadmap
```

### 文档导航

- [Architecture](docs/architecture.md)
- [Testing strategy](docs/testing-strategy.md)
- [Metrics](docs/metrics.md)
- [Research basis](docs/research-basis.md)
- [Roadmap](docs/roadmap.md)
- [Resume bullets](docs/resume-bullets.md)

### 限制

- 默认 evaluator 使用 deterministic local target，不能替代真实模型上的 statistical evaluation。
- LLM-as-a-judge、embedding-based retrieval metrics 和真实 provider latency 需要在接入目标系统后补充。
- Remote adapter 是最小 OpenAI-compatible client，不处理 streaming response 或厂商私有字段。
- Docker 与 CI 配置已提供；具体部署环境仍需根据组织网络、密钥和 runner policy 调整。

### License

[MIT](LICENSE)

---

英文版见 [`README_EN.md`](README_EN.md)。
