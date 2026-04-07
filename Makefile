.PHONY: help install install-dev sync test test-unit test-e2e test-cov lint format type-check check clean run server

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync

install-dev: ## Install dev + test dependencies
	uv sync --group dev --group test

sync: install-dev ## Alias for install-dev

test: ## Run unit tests (no e2e)
	uv run pytest tests/ -m "not e2e" -v

test-unit: test ## Alias for test

test-e2e: ## Run e2e tests (requires AUSPOST_API_KEY)
	uv run pytest tests/e2e/ -v -m e2e

test-cov: ## Run tests with coverage report
	uv run pytest tests/ -m "not e2e" --cov=src/auspost_blade_mcp --cov-report=term-missing

lint: ## Run linter
	uv run ruff check src/ tests/

format: ## Format code
	uv run ruff format src/ tests/

type-check: ## Run type checker
	uv run mypy src/auspost_blade_mcp

check: lint type-check ## Run all quality checks
	@echo "All quality checks passed!"

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

run: ## Run the MCP server (stdio)
	uv run auspost-blade-mcp

server: run ## Alias for run
