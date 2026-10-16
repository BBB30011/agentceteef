.PHONY: all setup install test build-sandbox report clean help

help:
	@echo "CTF Agent Swarm Makefile"
	@echo "  make setup          - Run setup script and prepare environment"
	@echo "  make install        - Sync dependencies with uv"
	@echo "  make test           - Run pytest test suite"
	@echo "  make lint           - Run ruff linter check"
	@echo "  make build-sandbox  - Build Docker ctf-sandbox image"
	@echo "  make report         - Show solve statistics from SQLite state DB"
	@echo "  make clean          - Clean temporary caches and logs"

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

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

