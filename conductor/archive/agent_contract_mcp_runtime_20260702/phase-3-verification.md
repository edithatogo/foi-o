# Phase 3 Verification: Agent Guardrail Replay

Date: 2026-07-02

## Scope

Phase 3 connected the action policy, replay guardrails, and descriptor safety
checks so proposed follow-on actions can be blocked or routed to review while
safe preparatory actions retain provenance in replay findings.

Changed implementation surfaces:

- `src/foi_o_nz/models.py`
- `src/foi_o_nz/agent_policy.py`
- `src/foi_o_nz/replay.py`
- `schemas/json/agent-action.schema.json`
- `tests/test_guardrail_replay_agent_contract.py`
- `docs/04-agent-boundaries.md`

## Automated Verification

Passed:

```bash
uv run pytest -q tests/test_guardrail_replay_agent_contract.py tests/test_agent_policy.py tests/test_mcp_runtime.py tests/test_agent_descriptors.py tests/test_quality.py
```

Result: `20 passed`.

Passed:

```bash
uv run foi-o-nz schema-drift
```

Result: `ok: true`. Warning-level top-level drift remains for pre-existing,
unrelated `core-event`, `reporting-metric`, and `request-profile` schemas.

Passed:

```bash
tmpdir=$(mktemp -d)
uv run python - <<'PY' "$tmpdir/actions.jsonl"
import json, sys
from pathlib import Path
from foi_o_nz.agent_policy import build_agent_action
path = Path(sys.argv[1])
action = build_agent_action('map_state').model_dump(mode='json')
action['requested_follow_on_actions'] = ['treat_state_as_legal_outcome']
path.write_text(json.dumps(action) + '\n', encoding='utf-8')
PY
uv run foi-o-nz replay-guardrails --actions-jsonl "$tmpdir/actions.jsonl" --output "$tmpdir/replay.json"
```

Result: command exited `1` as expected for an unsafe requested follow-on action
and wrote `prohibited_follow_on_action_requested`.

Passed:

```bash
uv run python scripts/validate_examples.py
uv run foi-o-nz validate-repo
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

Result: examples ok, repository validation ok, Ruff check passed, and
`97 files already formatted`.

## Conductor Review

`conductor-review` is not installed on PATH in this workspace, so the review was
performed using the `conductor-review` skill protocol as a manual fallback.

Review inputs:

- `conductor/tracks/agent_contract_mcp_runtime_20260702/spec.md`
- `conductor/tracks/agent_contract_mcp_runtime_20260702/plan.md`
- `conductor/workflow.md`
- Phase diff from checkpoint `be3aae6`
- Focused guardrail, policy, replay, schema, CLI, example, repo, and style
  checks

Findings applied: none.

Unresolved findings: none.

## Runtime Boundaries Verified

- Requested follow-on actions matching `prohibited_follow_on_actions` produce an
  error finding and make the replay report fail.
- Unsafe tool descriptors attached to actions are routed into policy findings.
- Invalid action records are reported as replay findings instead of raising.
- Safe preparatory actions with `audit_trace` emit provenance-preserving info
  findings.
- Preparatory actions missing provenance emit warnings.
- Replay remains guardrail metadata only and does not certify legal correctness.

## Manual Verification Steps

Autonomous verification substituted for an interactive pause because the user
explicitly requested comprehensive automatic execution.

Maintainer replay:

1. Run replay contract tests:
   `uv run pytest -q tests/test_guardrail_replay_agent_contract.py`
2. Run replay against an action JSONL:
   `uv run foi-o-nz replay-guardrails --actions-jsonl data/processed/agent-actions.jsonl --output data/processed/guardrail-replay.json`
3. Confirm unsafe requested follow-ons appear as
   `prohibited_follow_on_action_requested`.
4. Confirm preparatory actions include `audit_trace` provenance or receive a
   `preparatory_action_missing_audit_trace` warning.

Expected outcome: unsafe requested follow-on actions are blocked or routed to
human review, while safe preparatory actions retain provenance and warnings.

## External Gates

- Native `conductor-review` command: unavailable locally; manual skill-protocol
  review completed.
