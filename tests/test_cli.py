from argparse import Namespace

import pytest

from evalforge import cli


@pytest.mark.unit
def test_cli_evaluate_writes_reports(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    args = Namespace(
        dataset="datasets/sample.jsonl",
        output=str(tmp_path),
        target="local",
        base_url=None,
        api_key=None,
        model="demo-model",
        top_k=3,
        min_pass_rate=0.8,
    )
    cli.run_evaluation(args)
    assert (tmp_path / "report.json").exists()
    assert "passed" in capsys.readouterr().out


@pytest.mark.unit
def test_cli_returns_nonzero_when_gate_fails(tmp_path) -> None:  # type: ignore[no-untyped-def]
    args = Namespace(
        dataset="datasets/sample.jsonl",
        output=str(tmp_path),
        target="local",
        base_url=None,
        api_key=None,
        model="demo-model",
        top_k=3,
        min_pass_rate=1.1,
    )
    with pytest.raises(SystemExit, match="1"):
        cli.run_evaluation(args)
