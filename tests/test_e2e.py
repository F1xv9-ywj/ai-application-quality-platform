import pytest

pytest.importorskip("pytest_playwright", reason="install the e2e extra to run browser tests")
pytestmark = pytest.mark.e2e


def test_dashboard_run_button(page) -> None:  # type: ignore[no-untyped-def]
    page.goto("http://127.0.0.1:8000")
    page.get_by_role("button", name="运行评测").click()
    page.wait_for_selector("text=评测完成")
    assert page.locator("#cases tr").count() >= 5
