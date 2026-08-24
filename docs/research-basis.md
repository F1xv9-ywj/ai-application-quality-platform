# Research Basis

调研日期：2026-08-13。以下官方资料用于确定实现边界和测试接口；仓库没有复制第三方 benchmark 数据。

- FastAPI testing / TestClient: <https://fastapi.tiangolo.com/tutorial/testing/>
- pytest markers: <https://docs.pytest.org/en/stable/example/markers.html>
- OpenAI API chat completions reference: <https://platform.openai.com/docs/api-reference/chat>
- JUnit XML format support in pytest: <https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files>
- k6 thresholds: <https://grafana.com/docs/k6/latest/using-k6/thresholds/>
- Locust writing a locustfile: <https://docs.locust.io/en/stable/writing-a-locustfile.html>
- OWASP LLM Top 10: <https://genai.owasp.org/llm-top-10/>
- NIST AI Risk Management Framework: <https://www.nist.gov/itl/ai-risk-management-framework>

本项目据此将 functional contract、grounding/retrieval、robustness 与 operational latency/error 分开报告，避免用单一分数掩盖不同风险类型。
