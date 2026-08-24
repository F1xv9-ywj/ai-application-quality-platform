from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import uvicorn

from .evaluation import EvaluationEngine
from .models import EvalRunRequest
from .reporting import write_reports
from .service import build_sample_service


def run_evaluation(args: argparse.Namespace) -> None:
    request = EvalRunRequest(target=args.target, base_url=args.base_url, api_key=args.api_key, model=args.model, top_k=args.top_k, dataset_path=args.dataset)
    summary = asyncio.run(EvaluationEngine(build_sample_service()).run(Path(args.dataset), request))
    paths = write_reports(summary, Path(args.output))
    print(f"{summary.run_id}: {summary.passed}/{summary.total} passed ({summary.metrics['pass_rate']:.1%})")
    print("Reports: " + ", ".join(str(path) for path in paths))
    if summary.metrics["pass_rate"] < args.min_pass_rate:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(prog="evalforge", description="Evaluate AI applications reproducibly")
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve = subparsers.add_parser("serve", help="serve API and dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    evaluate = subparsers.add_parser("evaluate", help="run a JSONL evaluation")
    evaluate.add_argument("--dataset", default="datasets/sample.jsonl")
    evaluate.add_argument("--output", default="reports/sample")
    evaluate.add_argument("--top-k", type=int, default=3)
    evaluate.add_argument("--target", choices=("local", "remote"), default="local")
    evaluate.add_argument("--base-url")
    evaluate.add_argument("--api-key")
    evaluate.add_argument("--model", default="demo-model")
    evaluate.add_argument("--min-pass-rate", type=float, default=0.8)
    args = parser.parse_args()
    if args.command == "serve":
        uvicorn.run("evalforge.app:app", host=args.host, port=args.port, reload=False)
    else:
        run_evaluation(args)


if __name__ == "__main__":
    main()
