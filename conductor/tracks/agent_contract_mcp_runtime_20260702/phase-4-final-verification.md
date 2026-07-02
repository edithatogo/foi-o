# Phase 4 Final Verification: Agent Contract Closeout

Date: 2026-07-02

## Required Repo-Local Gate

Passed:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
```

Result: Ruff check passed, `97 files already formatted`, and `135 passed`.

Passed:

```bash
uv run python scripts/validate_examples.py
uv run foi-o-nz validate-repo
```

Result: examples ok and repository validation ok.

## Pixi/Mojo Gate

Passed:

```bash
pixi run mojo-format-check
```

Result: `20 files left unchanged`.

Passed:

```bash
pixi run mojo-test
```

Result: all Mojo tests passed across state, clock, text, retrieval, guardrail,
transition, hash, redaction, and epistemic suites.

Passed:

```bash
pixi run mojo-build
```

Result: `build/foi-o-nz-mojo` built successfully.

## Additional Type Check Attempt

An additional non-required check was attempted:

```bash
uv run ty check
```

Track 6 files initially contributed two diagnostics in descriptor code. These
were fixed in `f7afca5`. A rerun still reports 104 diagnostics in the broader
pre-existing baseline outside the Track 6 descriptor changes. The user-required
final gate does not include `ty check`.

## Manual Verification Steps

Autonomous verification substituted for an interactive pause because the user
explicitly requested comprehensive automatic execution.

Maintainer replay:

1. Run the required Python gate:
   `uv run ruff check src tests scripts && uv run ruff format --check src tests scripts && uv run pytest -q`
2. Validate examples and repository contracts:
   `uv run python scripts/validate_examples.py && uv run foi-o-nz validate-repo`
3. Run available Mojo checks:
   `pixi run mojo-format-check && pixi run mojo-test && pixi run mojo-build`

Expected outcome: all commands pass. The optional `ty check` remains a separate
baseline-hardening issue outside this completed track.

## External Gates

- Long-running MCP transport behavior remains operator-run.
- Native `conductor-review` command remains unavailable locally; manual
  skill-protocol review completed in `phase-4-review.md`.
