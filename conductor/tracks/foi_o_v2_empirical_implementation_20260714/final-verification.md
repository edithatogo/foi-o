# Final repo-local verification

The FOI-O V2 empirical contracts are integrated into native repository surfaces
and all functional, schema, lint, format, repository-validation, Pixi quality,
and build checks pass. The package name, event/provenance systems, state mapper,
and `oia_rules` runtime remain intact.

The bounded fixture-only implementation is complete. It includes the approved
protocol, governed metadata-only NZ source pack, two bounded request mappings,
locked independent agent analyses, locked agent reconciliation, and deterministic
local inter-agent diagnostics (SHA-256
`fe2f9e29136fca68894bc3960b7a5cfcc4f97edc3e0a970d94b7fbc2a783bbc5`).
The diagnostics execution gate was hardened so every sanctioned entry point and
governed output write reacquires exact authorization at the current clean HEAD.

The track remains active because authentic empirical and external gates are not
satisfied. The metadata `gates` registry is authoritative for these dependencies:
an authentic rights-cleared archive population, archive-wide mapping evidence,
an authentic frozen sample, two independent analysts and a distinct reconciler
with exact actor provenance, empirical evaluation, promotion approval, immutable release
evidence, the paper prerequisite, and explicit remote-delivery authorization.
Agents may fill the analyst and reconciler roles under the v0.2 contract.
Synthetic fixture outputs remain non-empirical, while verified outputs from a
frozen authentic sample may support claims bounded to that sample. Agent work
does not become human-reviewed, gold, legal, release, or publication evidence.

Repository-wide coverage and type-check baselines are recorded in `audit.md` and
`release-gates.yaml`; neither was caused or hidden by this overlay.

## Current checkpoint — 2026-08-02

The repository-native recheck passed:

- `uv run pytest -q`: 1,233 passed, 4 skipped.
- `uv run python tests/validate_repo.py`: passed.
- `uv run python scripts/validate_requirements.py`: passed.
- `uv run python scripts/validate_workflows.py`: passed.
- `uv run ruff check src tests scripts`: passed.
- `uv run ruff format --check src tests scripts`: passed.
- `uv run ty check src tests scripts`: passed.
- `git diff --check`: passed.

No empirical or release gate changed status. The next unchecked empirical task
remains blocked because the available wider snapshot is not a rights-cleared,
content-bearing population and the bounded candidate still lacks independent
annotation/adjudication. No source capture, replay, external repository
mutation, publication, release, promotion, or legal certification was
performed.

## Conductor review checkpoint — 2026-08-02

Review found no local correctness, scope, provenance, security, schema, or
archive-integrity defect. The plan, metadata, release-gates registry, and
human-gated boundaries remain aligned. Full validation was rerun during review
with the same passing results above. The track remains active and must not be
archived or promoted while the blocked empirical and release gates remain
unsatisfied.

## Authorized pilot pre-execution check — 2026-08-02

The exact pre-materialization verifier was invoked against the approved
two-case batched authorization. It failed closed with:

`ValueError: HEAD does not equal authorization commit`

The authorization is anchored to repository commit `e9252ef`, while the
current clean branch is `c65ef46`. The authorized local source roots expected
under `/private/tmp` were also not present at the check. No HEAD change, source
restoration, context materialization, analyst execution, or reconciliation was
performed. A refreshed exact authorization at the current clean HEAD and
restored owner-private approved source roots are required before execution can
resume.

The first refresh record did not update a stale implementation pin. A corrected
inert authorization candidate has therefore been prepared at
`examples/v2/bounded-pilot-batched-execution-authorization.current-head.pending.json`,
SHA-256 `0f8499a508c1536c4072a7900b9260acc42242aab606c06c8d096a5161008b42`,
commit `2dcebb88223f0d01f38c108bfd909967c0e7c01d`. It updates only the
`scripts/build_submission_latex.py` implementation pin to SHA-256
`dd39f60d5178a0bb6aa67d5f6a87b239cda0a9b1f0ae47859b2e353c2a72f6aa` at commit
`fc6d650b40b245dec0bd084dd4cc58a9f4f49e06`. Exact approval of this corrected
candidate is required before it can replace the canonical authorization.
