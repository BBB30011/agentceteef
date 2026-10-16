.PHONY: all setup install test build-sandbox report clean help

help:
	@echo "⚡ Agent CeTeEf (agentceteef) Makefile"
	@echo "  make run            - Run interactive CLI launcher wizard"
	@echo "  make demo           - Solve built-in sanity demo challenge"
	@echo "  make tokenless      - Run tokenless solver using Antigravity CLI"
	@echo "  make fast           - Run high-throughput fast multi-model swarm"
	@echo "  make setup          - Run setup script and prepare environment"
	@echo "  make install        - Sync dependencies with uv"
	@echo "  make test           - Run pytest test suite"
	@echo "  make lint           - Run ruff linter check"
	@echo "  make build-sandbox  - Build Docker ctf-sandbox image"
	@echo "  make report         - Show solve statistics from SQLite state DB"
	@echo "  make report-html    - Generate standalone dark mode HTML report"
	@echo "  make clean          - Clean temporary caches and logs"

run:
	./run.sh

demo:
	./run.sh demo

tokenless:
	uv run --offline ctf-solve --profile tokenless 2>/dev/null || uv run ctf-solve --profile tokenless

fast:
	uv run --offline ctf-solve --profile fast 2>/dev/null || uv run ctf-solve --profile fast

setup:
	./setup.sh

install:
	uv sync --offline 2>/dev/null || uv sync

test:
	uv run --offline pytest -v 2>/dev/null || uv run pytest -v

lint:
	uv run --offline ruff check backend tests 2>/dev/null || uv run ruff check backend tests

build-sandbox:
	docker build -f sandbox/Dockerfile.sandbox -t ctf-sandbox .

report:
	uv run --offline ctf-solve --report 2>/dev/null || uv run ctf-solve --report

report-html:
	uv run --offline ctf-solve --export-html ctf_report.html 2>/dev/null || uv run ctf-solve --export-html ctf_report.html

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

