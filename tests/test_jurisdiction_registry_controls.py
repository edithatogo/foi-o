"""Tests for the fail-closed jurisdiction registry controls."""

from __future__ import annotations

from pathlib import Path

from scripts.validate_jurisdiction_profiles import validate, validate_documents

ROOT = Path(__file__).resolve().parents[1]


def _documents() -> tuple[dict, dict, dict, dict]:
    registry = {
        "stages": ["discovered"],
        "profiles": [
            {
                "id": "p",
                "jurisdiction": "NZ",
                "regime": "OIA",
                "version": "1.0.0",
                "stage": "discovered",
                "status": "candidate",
                "source_pack": {"id": "p"},
                "capabilities": {},
                "human_gates": ["review"],
            }
        ],
    }
    maturity = {
        "dimensions": ["source_discovery"],
        "levels": [
            "unassessed",
            "discovered",
            "candidate",
            "implemented_candidate",
            "independently_evaluated",
            "human_promoted",
            "stable",
            "blocked",
        ],
        "aggregate_readiness_score": "prohibited",
        "profiles": {"p": {}},
    }
    template = {
        "platform": {},
        "archive": {},
        "normative": {},
        "nlp": {},
        "process": {},
        "conformance": {},
        "promotion": {"status": "blocked", "missing": ["review"]},
    }
    access = {
        "default_mode": "offline_fixture_replay",
        "network_capture": {
            "allowed_only_when": [
                "robots_reviewed",
                "terms_reviewed",
                "rate_limits_recorded",
                "operator_approval_recorded",
            ],
            "prohibited": [
                "access_control_bypass",
                "unbounded_scraping",
                "autonomous_live_capture",
            ],
        },
        "archive": {"immutable_digest_required": True},
        "foio": {"legal_interpretation": "prohibited"},
    }
    return registry, maturity, template, access


def test_canonical_jurisdiction_controls_validate() -> None:
    assert validate(ROOT) == {"ok": True, "profile_count": 3, "errors": []}


def test_profile_registry_rejects_missing_maturity_entry() -> None:
    registry, maturity, template, access = _documents()
    maturity["profiles"] = {}

    errors = validate_documents(registry, maturity, template, access)

    assert "p: missing capability maturity entry" in errors


def test_access_policy_rejects_incomplete_live_capture_controls() -> None:
    registry, maturity, template, access = _documents()
    access["network_capture"]["prohibited"] = []

    errors = validate_documents(registry, maturity, template, access)

    assert "operations/access-policy.yaml: live capture conditions are incomplete" not in errors
    assert "operations/access-policy.yaml: missing prohibition autonomous_live_capture" in errors
