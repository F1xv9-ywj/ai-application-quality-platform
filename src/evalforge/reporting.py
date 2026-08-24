from __future__ import annotations

import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import EvalSummary


def write_reports(summary: EvalSummary, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    html_path = output_dir / "report.html"
    junit_path = output_dir / "junit.xml"
    json_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    rows = "".join(
        f"<tr><td>{html.escape(case.id)}</td><td class='{('pass' if case.passed else 'fail')}'>{'PASS' if case.passed else 'FAIL'}</td><td>{case.latency_ms:.1f} ms</td><td>{html.escape(case.error or '')}</td></tr>"
        for case in summary.cases
    )
    metrics = "".join(f"<li><b>{html.escape(key)}</b><span>{value}</span></li>" for key, value in summary.metrics.items())
    html_path.write_text(f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>EvalForge sample report</title><style>body{{font:15px system-ui;margin:40px;color:#17213d;background:#f7f9fc}}main{{max-width:980px;margin:auto;background:white;padding:32px;border:1px solid #dfe5ef}}h1{{margin-top:0}}ul{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;padding:0}}li{{list-style:none;border:1px solid #dfe5ef;padding:16px;display:flex;justify-content:space-between}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #e6eaf1;text-align:left}}.pass{{color:#07865c}}.fail{{color:#d9363e}}small{{color:#68738d}}</style></head><body><main><h1>EvalForge Evaluation Report</h1><small>Sample/synthetic data · {html.escape(summary.created_at)}</small><h2>Metrics</h2><ul>{metrics}</ul><h2>Cases</h2><table><thead><tr><th>ID</th><th>Result</th><th>Latency</th><th>Error</th></tr></thead><tbody>{rows}</tbody></table></main></body></html>""", encoding="utf-8")
    suite = ET.Element("testsuite", name="EvalForge", tests=str(summary.total), failures=str(summary.total - summary.passed))
    for case in summary.cases:
        node = ET.SubElement(suite, "testcase", name=case.id, time=str(case.latency_ms / 1000))
        if not case.passed:
            ET.SubElement(node, "failure", message=case.error or "quality threshold failed").text = json.dumps(case.dimension_results)
    ET.ElementTree(suite).write(junit_path, encoding="utf-8", xml_declaration=True)
    return [json_path, html_path, junit_path]
