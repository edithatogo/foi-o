# FOI-O next-generation implementation report — 2026-07-21

## Scope and audit

The root archive `foi-o-codex-autostart.zip` was inspected for traversal,
absolute paths and symlinks, safely extracted to `.codex/foio-nextgen-input/`,
and validated successfully. Archive SHA-256:
`4877122cf59b879d6121cd27054f99a3c9e1efee64771c22160fb487badfb528`.

The controlling prompt and all bundled reference files were read. The live
checkout is `edithatogo/foi-o` commit
`c4702380dfb50b0b856bbb1fc20953822dfaeee5` on the deleted remote branch
`codex/australia-profile-quality`; its uncommitted work was preserved. Exact
coordinated-repository state is in `workspace.lock.yaml` and the dated audit is
`workspace-audit.md`.

## Implemented

- Added `AGENTS.md` and modernised the FOI-O-specific Conductor product,
  workflow and track registry around global core/profile boundaries.
- Added a versioned `ContextPlan`/`ContextPack` compiler that fails closed on a
  missing request, filters request/profile mismatches before ranking, records
  exclusion reasons, blocks unauthorised cross-profile context, and hashes all
  material context canonically.
- Added negative/positive context isolation tests in `tests/test_context_pack.py`.
- Added `capabilities/registry.yaml`, multiaxial version registry/compatibility
  lock, schema, migration note and portable `scripts/version_tool.py`.
- Added paired workflow validation and a paper-update workflow in Markdown /
  Mermaid plus BPMN 2.0, with seven required Conductor tracks and their
  requirements, risks, decisions, ledgers and human gates.
- Added workspace lock/audit, MoSCoW requirements, ontology registry ledger,
  global namespace ADR, technology radar, paper claim/review/Sourceright/
  Authentext workflow contracts, paper ledger, and issue dry-run/creation
  ledgers.
- Regenerated ontology maturation inventory artifacts after adding the version
  schema; the existing Australian/profile and empirical edits remain intact.

The broader MCP/OpenAPI/MAX alignment, full global manuscript rewrite,
cross-repository workspace-doctor implementation, live jurisdiction packs,
formal-method prototypes and deep CI lane consolidation remain tracked work;
they are not represented as complete merely because local governance
scaffolding is present.

## Validation evidence

| Gate | Result |
| --- | --- |
| Bundle path/checksum validator | passed: 12 YAML, 2 JSON, 2 workflows, 45 checksummed files |
| Repository schema/RDF/example validator | passed |
| Workflow and BPMN/config validation | passed |
| Full managed pytest suite | passed: 295 passed, 2 skipped |
| Ruff check and format | passed |
| `git diff --check` | passed |
| BasedPyright | passed: repository baseline is now wired through `pyproject.toml`; 110 legacy errors are tracked and new errors fail `make typecheck-basedpyright` |
| `ty check` | blocked/failed: existing repository diagnostics, 70 errors; no suppression or false green was introduced |
| zizmor workflow audit | passed: all workflow action references are commit-pinned and checkout credentials are not persisted |
| Mojo/MAX, Sourceright, Authentext, registry quality, live capture | not run: unavailable or human/operator gated |

## GitHub coordination

After authenticated duplicate searches and this local dry-run, the programme
resolved 14 workstreams to 13 unique primary issues: ten existing issues were
linked and four genuine gaps were created:

- Existing FOI-O anchors: [#72](https://github.com/edithatogo/foi-o/issues/72),
  [#73](https://github.com/edithatogo/foi-o/issues/73),
  [#74](https://github.com/edithatogo/foi-o/issues/74), and
  [#24](https://github.com/edithatogo/foi-o/issues/24).
- New [foi-o #75](https://github.com/edithatogo/foi-o/issues/75) — exact release quality evidence.
- New [nlp-policy-nz #143](https://github.com/edithatogo/nlp-policy-nz/issues/143) — jurisdiction-neutral concept-pack feedback.
- New [sourceright #71](https://github.com/edithatogo/sourceright/issues/71) — paper source/citation integration.
- New [authentext #61](https://github.com/edithatogo/authentext/issues/61) — final editorial integration.
- Cross-repository linked issues include [rac-conformance #146](https://github.com/edithatogo/rac-conformance/issues/146), [fyi-cli #140](https://github.com/edithatogo/fyi-cli/issues/140), [fyi-archive #188](https://github.com/edithatogo/fyi-archive/issues/188), [legislation #62](https://github.com/edithatogo/legislation/issues/62), and [foi-process #37](https://github.com/edithatogo/foi-process/issues/37).

No PR was merged, no release/dataset/paper was published, and no sibling
repository was modified.

## Remaining blockers and human actions

- Continue reducing the pre-existing `ty` diagnostic debt (70 diagnostics).
  BasedPyright now has an executable 110-error no-regression baseline; new
  findings are blocking.
- Obtain operator/rights approval before any live capture; complete immutable
  source/archive packs and independent annotation/adjudication before profile
  promotion.
- Run Sourceright and Authentext with available tool versions and independent
  paper reviewers; human-approve any semantic/legal changes.
- Human-approve ontology registry submissions and any arXiv/OSF/Zenodo/GitHub
  release or publication. None was attempted.
- Decide whether to retain the environment-resolution changes in `pixi.lock`
  produced while invoking the managed tooling; they were not discarded.

## Next action

Review `issue-creation-ledger.json`, then run `./.venv/bin/python -m pytest -q`
from this preserved worktree before deciding whether to commit a coherent
task-sized slice. Do not push the deleted-branch checkout without an explicit
branch/recovery decision.

## Programme wiring continuation — 2026-07-21

- Re-audited the authenticated GitHub state after the ZIP-defined workstreams
  were reconciled. The private cross-repository programme board is [FOI-O
  Global Next-Generation Programme #29](https://github.com/users/edithatogo/projects/29)
  with 24 items, including the 14 unique workstream primaries and existing
  child issues.
- Linked existing work or created the four verified gaps across all 14
  workstreams: `foi-o#72`, `foi-o#73`, `foi-o#74`, `foi-o#24`, `foi-o#75`,
  `rac-conformance#146`, `fyi-cli#140`, `fyi-archive#188`, `legislation#62`,
  `nlp-policy-nz#143`, `foi-process#37`, `sourceright#71`, and `authentext#61`.
- Added local `issue-export.json` and hash-bound evidence records for each
  next-generation track, plus `issue-creation-ledger.json`,
  `issue-dry-run.json`, `prompt-traceability.yaml`, and
  `conductor/cross-repo-issue-map.yaml` as the reconciliation layer.
- The Conductor structural validator now passes in full mode. The two archived
  packages that had unchecked verification subtasks were rechecked with their
  focused tests and their existing phase evidence, then the subtasks and
  registry state were reconciled without changing archive contents.
- Additional repository-owned controls now include `profiles/registry.yaml`,
  `profiles/capability-maturity.yaml`, `operations/access-policy.yaml`,
  `scripts/workspace_doctor.py`, `scripts/validate_requirements.py`,
  `scripts/paper_governance.py`, `conductor-feature-radar.yaml`, and
  `.github/workflows/foio-programme-controls.yml`.
- The canonical manuscript was reframed from an NZ-first title to a global,
  jurisdiction-profiled contribution, and its limitations were converted into
  a threat/mitigation/independent-triangulation table. The text remains
  explicit that NZ is the reference profile and that comparative, legal, and
  publication claims remain gated.
- Managed validation after the additions: `uv run pytest -q` — 295 passed,
  2 skipped; focused archived-runtime tests — 36 passed, 2 skipped; Ruff
  check/format, repository validation, requirements, workflow, version,
  capability, bundle, full Conductor validation, `actionlint`, `zizmor`, and
  Pixi Mojo format/test/build all passed. BasedPyright now passes through the
  tracked no-regression baseline; `ty` remains failed by 70 broader
  diagnostics and is not represented as green. Schema-drift reports only the
  repository's existing warning-level top-level-key differences.
- Local execution artefacts are now ignored by `.gitignore` (`.codex/`,
  `.playwright-mcp/`, `output/`, and the ZIP input) without deleting them.
