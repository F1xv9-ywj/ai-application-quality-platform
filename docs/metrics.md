# Metrics

| Metric | 定义 | Sample gate |
| --- | --- | --- |
| Pass rate | 所有必需维度通过的 case / 全部 case | ≥ 0.80 |
| Retrieval recall@k | `expected_doc_ids ∩ retrieved_ids` / expected ids | ≥ 0.80 |
| Citation rate | 有 expected evidence 的 case 中命中 citation 的比例 | 观察项 |
| Unsupported claim rate | 返回 citation 但回答未出现首个 evidence marker 的比例 | ≤ 0.05 |
| p50 / p95 latency | evaluator 观察到的 wall-clock latency percentile | p95 ≤ 500 ms（local） |
| Error rate | target invocation exception / 全部 case | ≤ 0.25（含 expected timeout case） |

当前 answer metric 是 deterministic substring oracle，适合固定 regression fixture，不应被误解为 semantic correctness。真实项目可新增人工标注、embedding similarity 或 rubric judge，但 judge 自身也必须经过 calibration 与 drift monitoring。
