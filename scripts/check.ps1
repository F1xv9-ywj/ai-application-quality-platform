$ErrorActionPreference = "Stop"
python -m ruff check .
python -m mypy src
python -m pytest --cov=evalforge --cov-report=term-missing
python -m evalforge evaluate --dataset datasets/sample.jsonl --output reports/sample
