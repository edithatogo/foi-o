"""Validate a paper-review run without inventing external tool or human evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return value


def audit(run_dir: Path | None = None) -> dict[str, Any]:
    """Return `blocked` until independent reports and human gates are evidenced."""
    contract = load(ROOT / "submission/PAPER_REVIEW_SCORE_CONTRACT.yaml")
    matrix = load(ROOT / "submission/PAPER_AGENT_MATRIX.yaml")
    roles = [str(item["id"]) for item in matrix["roles"]]
    present = sorted(
        path.stem
        for path in (run_dir.iterdir() if run_dir and run_dir.exists() else [])
        if path.suffix in {".json", ".yaml", ".yml", ".md"} and path.stem in roles
    )
    missing = sorted(set(matrix["minimum_reports_before_candidate"]) - set(present))
    score = None
    critical_gates = {str(gate["id"]): "missing" for gate in contract["hard_gates"]}
    if run_dir is not None and (run_dir / "scorecard.yaml").exists():
        scorecard = load(run_dir / "scorecard.yaml")
        score = scorecard.get("score")
        for gate in scorecard.get("gates", []):
            if isinstance(gate, dict) and gate.get("id") in critical_gates:
                critical_gates[str(gate["id"])] = str(gate.get("status", "unverified"))
    threshold_pass = isinstance(score, (int, float)) and score > contract["threshold"]
    complete = (
        not missing and threshold_pass and all(value == "pass" for value in critical_gates.values())
    )
    return {
        "status": "candidate_ready" if complete else "blocked",
        "threshold": contract["threshold"],
        "score": score,
        "required_roles": roles,
        "present_reports": present,
        "missing_required_reports": missing,
        "critical_gates": critical_gates,
        "human_submission_gate": "pending",
        "external_tools": {"sourceright": "not_run", "authentext": "not_run"},
        "publication_authorised": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    result = audit(args.run_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "candidate_ready":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
