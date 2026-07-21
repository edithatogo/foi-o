.PHONY: help install sync lock lint format format-fix typecheck typecheck-basedpyright test test-fast test-full test-serial test-cov \
        quality validate smoke normalise quality-gate rdf embeddings agent-policy schema-drift duckdb-sql chunks ledger risk retrieval redactions agent-pack diff repro metadata openapi tool-manifest benchmark kernel-status kernel-conformance mojo-audit kernel-manifest kernel-fixtures kernel-readiness mojo-format mojo-test mojo-build \
        spell toml-check workflow-audit workflow-syntax security-audit sbom profile-quality clean

PKG := foi_o_nz
PYTHON ?= python

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install: ## Install dev environment with uv
	uv sync --extra dev --extra analytics --extra max --extra mcp --extra rdf

sync: ## Sync env from lockfile if present
	uv sync --extra dev --extra analytics --extra max --extra mcp --extra rdf --frozen

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
	uv run ty check src tests scripts

typecheck-basedpyright: ## basedpyright type check with tracked baseline
	uv run basedpyright

test: test-fast ## Run the complete Python suite using the fast parallel profile

test-fast: ## Run the complete Python suite with four work-stealing workers
	uv run pytest -q -n 4 --dist worksteal

test-full: lint format typecheck typecheck-basedpyright test-fast validate schema-drift ## Run the normal local quality and parallel test gate

test-serial: ## Run the complete Python suite serially for release evidence
	uv run pytest -q

test-cov: ## Run Python tests with coverage
	uv run pytest --cov=$(PKG) --cov-report=term-missing --cov-report=html

validate: ## Validate schemas, examples, RDF and mappings
	uv run python tests/validate_repo.py

profile-quality: ## Validate jurisdiction lifecycle, maturity, pack, and access controls
	uv run python scripts/validate_jurisdiction_profiles.py

smoke: ## Generate local smoke fixture and validate it
	uv run foi-o-nz smoke-fixture --output-dir data/smoke
	uv run foi-o-nz validate data/smoke/core-event.request-observed.json --schema schemas/json/core-event.schema.json

normalise: ## Normalise smoke manifest records
	uv run foi-o-nz normalise-manifest --input data/smoke/fyi-manifest.jsonl --requests-output data/smoke/requests.jsonl --events-output data/smoke/events.jsonl --parquet-dir data/smoke/parquet --run-manifest-output data/smoke/run-manifest.json
	uv run foi-o-nz validate-jsonl data/smoke/requests.jsonl --schema schemas/json/request-profile.schema.json
	uv run foi-o-nz validate-jsonl data/smoke/events.jsonl --schema schemas/json/core-event.schema.json

quality-gate: ## Run event-stream safety/certification quality gate
	uv run foi-o-nz event-summary data/smoke/events.jsonl --output data/smoke/event-summary.json
	uv run foi-o-nz quality-gate data/smoke/events.jsonl --output data/smoke/quality-report.json
	uv run foi-o-nz transition-audit data/smoke/events.jsonl --output data/smoke/transition-report.json

rdf: ## Export smoke request/events to RDF/Turtle and validate shapes
	uv run foi-o-nz export-rdf --requests-jsonl data/smoke/requests.jsonl --events-jsonl data/smoke/events.jsonl --output data/smoke/foi-o-nz.ttl
	uv run foi-o-nz validate-shacl data/smoke/foi-o-nz.ttl --shapes shacl/foi-o-nz.shapes.ttl

embeddings: ## Create smoke deterministic embedding JSONL
	uv run foi-o-nz embed-jsonl --input data/smoke/requests.jsonl --output data/smoke/request-embeddings.jsonl --kind request --dimensions 32

agent-policy: ## Generate and evaluate one bounded agent-action template
	uv run foi-o-nz agent-action-template map_state --output data/smoke/action.map-state.json
	uv run foi-o-nz evaluate-agent-action data/smoke/action.map-state.json

schema-drift: ## Compare generated Pydantic schema keys against committed schemas
	uv run foi-o-nz schema-drift

duckdb-sql: ## Write portable DuckDB bootstrap SQL
	uv run foi-o-nz write-duckdb-sql --output data/smoke/duckdb-bootstrap.sql

chunks: ## Create smoke request chunks
	uv run foi-o-nz chunk-jsonl --input data/smoke/requests.jsonl --output data/smoke/request-chunks.jsonl --kind request

ledger: ## Build and verify smoke event ledger
	uv run foi-o-nz build-ledger --input data/smoke/events.jsonl --output data/smoke/events.ledger.jsonl --record-type event
	uv run foi-o-nz verify-ledger --input data/smoke/events.jsonl --ledger data/smoke/events.ledger.jsonl --record-type event

risk: ## Run deterministic risk triage over smoke chunks
	uv run foi-o-nz risk-scan --input data/smoke/request-chunks.jsonl --output data/smoke/risk-assessments.jsonl

retrieval: ## Search smoke chunks with local deterministic retrieval
	uv run foi-o-nz search-chunks --input data/smoke/request-chunks.jsonl --query "example request" --output data/smoke/retrieval-results.json --top-k 3 --dimensions 16

redactions: ## Propose candidate sensitive spans for human review only
	uv run foi-o-nz propose-redactions --input data/smoke/request-chunks.jsonl --output data/smoke/redaction-candidates.jsonl

agent-pack: ## Build a request-scoped smoke agent context pack
	uv run foi-o-nz build-agent-pack --request-id 12345 --requests-jsonl data/smoke/requests.jsonl --events-jsonl data/smoke/events.jsonl --chunks-jsonl data/smoke/request-chunks.jsonl --risks-jsonl data/smoke/risk-assessments.jsonl --retrieval-json data/smoke/retrieval-results.json --redaction-candidates-jsonl data/smoke/redaction-candidates.jsonl --output data/smoke/agent-pack.12345.json

diff: ## Diff the smoke event stream against itself
	uv run foi-o-nz diff-jsonl --before data/smoke/events.jsonl --after data/smoke/events.jsonl --output data/smoke/events.diff.json

repro: ## Write a reproducibility manifest for smoke artefacts
	uv run foi-o-nz repro-manifest data/smoke/requests.jsonl data/smoke/events.jsonl data/smoke/request-chunks.jsonl --output data/smoke/reproducibility-manifest.json --base-dir .

metadata: ## Generate smoke dataset metadata
	uv run foi-o-nz dataset-metadata data/smoke/requests.jsonl data/smoke/events.jsonl data/smoke/request-chunks.jsonl --output data/smoke/dataset-metadata.json --base-dir .

openapi: ## Export bounded agent-facing OpenAPI contract
	uv run foi-o-nz export-openapi --output data/smoke/openapi.json

tool-manifest: ## Export bounded agent tool manifest
	uv run foi-o-nz export-tool-manifest --output data/smoke/tool-manifest.json

benchmark: ## Run dependency-light local microbenchmarks
	uv run foi-o-nz benchmark-local --output data/smoke/benchmarks.json --iterations 100


kernel-status: ## Report Mojo/MAX native-kernel availability and fallback mode
	uv run foi-o-nz kernel-status --output data/smoke/native-kernel-status.json

kernel-conformance: ## Run deterministic kernel parity/conformance checks
	uv run foi-o-nz kernel-conformance --output data/smoke/kernel-conformance.json

mojo-audit: ## Static audit that Mojo source declares every fallback kernel operation
	uv run foi-o-nz mojo-audit --output data/smoke/mojo-audit.json

kernel-manifest: ## Export deterministic kernel manifest
	uv run foi-o-nz export-kernel-manifest --output data/smoke/kernel-manifest.json

kernel-fixtures: ## Export JSONL kernel conformance fixtures for Mojo harnesses
	mkdir -p mojo/tests/fixtures
	uv run foi-o-nz export-kernel-fixtures --output mojo/tests/fixtures/kernel-conformance.jsonl

kernel-readiness: ## Report Mojo-first kernel readiness and remaining native blockers
	uv run foi-o-nz kernel-readiness --output data/smoke/kernel-readiness.json

mojo-format: ## Format Mojo sources
	pixi run mojo-format

mojo-test: ## Run native Mojo tests
	pixi run mojo-test

mojo-build: ## Build native Mojo smoke binary
	pixi run mojo-build

quality: lint format typecheck typecheck-basedpyright test-fast validate schema-drift mojo-audit kernel-manifest kernel-readiness ## Full Python/static quality gate

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
