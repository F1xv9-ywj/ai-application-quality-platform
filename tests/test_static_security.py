from pathlib import Path

import pytest


@pytest.mark.unit
def test_dashboard_escapes_api_identifiers_before_inner_html() -> None:
    script = Path("src/evalforge/static/app.js").read_text(encoding="utf-8")
    assert "escapeHtml(c.id)" in script
    assert "escapeHtml(r.run_id)" in script
    assert "${c.id}" not in script
    assert "${r.run_id}" not in script
