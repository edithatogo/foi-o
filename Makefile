.PHONY: help install sync lock lint format format-fix typecheck test test-cov \
        quality validate smoke normalise mojo-format mojo-test mojo-build \
        spell toml-check workflow-audit workflow-syntax security-audit sbom clean

PKG := foi_o_nz
PYTHON ?= python

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install: ## Install dev environment with uv
	uv sync --extra dev --extra analytics --extra max

sync: ## Sync env from lockfile if present
	uv sync --extra dev --extra analytics --extra max --frozen

lock: ## Regenerate uv lockfile
	uv lock

lint: ## Ruff lint
	uv run ruff check src tests scripts

format: ## Check formatting
	uv run ruff format --check src tests scripts

format-fix: ## Apply formatting + lint fixes
	uv run ruff check --fix src tests scripts
	uv run ruff format src tests scripts

typecheck: ## ty type check
	uv run ty check src tests

test: ## Run Python tests
	uv run pytest -q

test-cov: ## Run Python tests with coverage
	uv run pytest --cov=$(PKG) --cov-report=term-missing --cov-report=html

validate: ## Validate schemas, examples, RDF and mappings
	uv run python tests/validate_repo.py

smoke: ## Generate local smoke fixture and validate it
	uv run foi-o-nz smoke-fixture --output-dir data/smoke
	uv run foi-o-nz validate data/smoke/core-event.request-observed.json --schema schemas/json/core-event.schema.json

normalise: ## Normalise smoke manifest records
	uv run foi-o-nz normalise-manifest --input data/smoke/fyi-manifest.jsonl --requests-output data/smoke/requests.jsonl --events-output data/smoke/events.jsonl --parquet-dir data/smoke/parquet

mojo-format: ## Format Mojo sources
	pixi run mojo-format

mojo-test: ## Run native Mojo tests
	pixi run mojo-test

mojo-build: ## Build native Mojo smoke binary
	pixi run mojo-build

quality: lint format typecheck test validate ## Full Python quality gate

spell: ## typos spelling check
	uv run typos src tests scripts docs README.md || true

toml-check: ## taplo TOML check
	uv run taplo check pyproject.toml pixi.toml || true

workflow-audit: ## zizmor GitHub Actions audit
	zizmor --min-severity medium .github/workflows || true

workflow-syntax: ## actionlint workflow syntax
	actionlint || true

security-audit: ## pip-audit over installed env
	uv run --extra dev pip-audit || true

sbom: ## Generate CycloneDX SBOM
	mkdir -p dist
	uv run cyclonedx-py environment --output-format json --output-file dist/sbom.cdx.json

clean: ## Remove local caches and generated artifacts
	rm -rf .pytest_cache .ruff_cache .ty_cache .mypy_cache .coverage coverage.xml htmlcov build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
