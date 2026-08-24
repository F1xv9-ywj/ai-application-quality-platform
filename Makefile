.PHONY: install test lint typecheck sample serve check
install:
	python -m pip install -e ".[dev]"
test:
	python -m pytest --cov=evalforge --cov-report=term-missing
lint:
	python -m ruff check .
typecheck:
	python -m mypy src
sample:
	python -m evalforge evaluate --dataset datasets/sample.jsonl --output reports/sample
serve:
	python -m evalforge serve
check: lint typecheck test sample
