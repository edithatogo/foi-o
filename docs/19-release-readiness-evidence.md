# Release readiness evidence

This note records the repo-local evidence surface for the current release-readiness track.

## Repo-local proof

| Surface | Evidence | Validation command |
| --- | --- | --- |
| Python package and CLI | `src/foi_o_nz/`, `pyproject.toml`, tests | `uv run pytest -q` |
| JSON Schemas and examples | `schemas/json/`, `examples/` | `uv run pytest -q tests/test_validation.py tests/test_jsonl_validation.py` and `uv run python scripts/validate_examples.py` |
| Kernel fallback contract | `src/foi_o_nz/kernel_fallback.py`, `tests/test_kernel_fallback_native.py` | `uv run pytest -q tests/test_kernel_fallback_native.py` |
| Static Mojo audit and readiness | `src/foi_o_nz/mojo_audit.py`, `src/foi_o_nz/kernel_manifest.py`, `tests/test_mojo_audit_kernel_manifest.py` | `uv run pytest -q tests/test_mojo_audit_kernel_manifest.py` |
| Agent boundary and quality gates | `src/foi_o_nz/agent_policy.py`, `src/foi_o_nz/quality.py`, related tests | `uv run pytest -q tests/test_agent_policy.py tests/test_quality.py` |
| RDF/SHACL degraded-mode path | `src/foi_o_nz/rdf_export.py`, `src/foi_o_nz/shacl_validation.py`, related tests | `uv run pytest -q tests/test_rdf_export.py tests/test_schema_codegen_shacl.py` |
| Reproducibility and manifests | `src/foi_o_nz/reproducibility.py`, `examples/reproducibility-manifest.examples.json` | `uv run pytest -q tests/test_retrieval_redaction_diff_pack_repro.py` |

## Repeatable release validation sequence

Run these commands before claiming repo-local release readiness:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
uv run python scripts/validate_examples.py
```

If any command fails, the release is not repo-locally ready. If any optional live service or native toolchain is unavailable, record it under external gates rather than treating it as repo-local proof.

## External gates

| Gate | Current handling |
| --- | --- |
| Native Mojo/MAX release certification | Requires `pixi run mojo-format-check`, `pixi run mojo-test`, and `pixi run mojo-build` with the Modular toolchain available. Static Mojo audit is repo-local proof only, not a native release substitute. |
| Live Hugging Face/archive pulls | Not required for fixture-mode validation. Live access belongs to the corpus-profile track and must be documented separately from repo-local proof. |
| NZ Legislation/Ombudsman live source retrieval | Not required for current release readiness. Source-versioned legal references belong to the OIA process-rules track. |
| Publication registries | Not required for repo-local validation. Registry publication belongs to the publication/release track. |

## Claim audit

| Document | Status | Action |
| --- | --- | --- |
| `README.md` | Current for Track 7. Labels local/MAX extraction packs and LanceDB retrieval as experimental, candidate-only, and optional, with live MAX/model execution still external-gated. | Keep aligned with this evidence note as tracks complete. |
| `IMPLEMENTATION_REPORT.md` | Current through v0.8 and separates sandbox limitations from implemented fallback proof. | Use as historical evidence; avoid treating older validation counts as current test counts. |
| `docs/11-implementation-status.md` | Previously stale because it only described the v0.1 scaffold and listed later experimental surfaces as not implemented. | Updated in this track to distinguish implemented, experimental, planned, and external-gated surfaces. |
| `docs/18-implementation-delta-v0.8.md` | Current for static Mojo audit/kernel manifest scope. | Keep the native-release caveat. |
| `examples/kernel-readiness.fallback.json` | Repo-local readiness fixture. | Validate through kernel manifest/readiness tests. |
| `examples/mojo-audit.static.json` | Repo-local static audit fixture. | Validate through schema/example checks. |

## Release-readiness rule

A surface is release-ready only when the repository contains a deterministic validation command, committed schema/example evidence where applicable, and a clear external-gate note for any live service, optional dependency, or native toolchain requirement that cannot be proved locally.
