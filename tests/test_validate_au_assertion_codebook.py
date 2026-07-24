from scripts.validate_au_assertion_codebook import validate_codebook


def _codebook() -> dict:
    return {
        "schema_version": "foi-o.au-cth-assertion-codebook.v0.2.0",
        "status": "pending_human_approval",
        "codebook_id": "foio-au-pilot-assertion-v0.2.0",
        "revision": "a" * 40,
        "assertion": {"statement": "x", "evidence_window": "text"},
        "labels": [
            {"id": label, "positive_rule": "p", "negative_rule": "n"}
            for label in ("observed", "inferred", "candidate", "unknown")
        ],
        "span_policy": {
            "coordinate_system": "utf8_character_half_open",
            "maximum_span_characters": 1000,
        },
        "abstention": {
            "reasons": ["missing_evidence", "insufficient_evidence", "out_of_scope", "other"]
        },
        "serialization": {"one_primary_label": True},
        "registered_thresholds": {"raw_agreement_minimum": 0.8, "cohen_kappa_minimum": 0.6},
        "execution_allowed": False,
    }


def test_pending_codebook_contract_passes() -> None:
    assert validate_codebook(_codebook()) == []


def test_codebook_rejects_threshold_drift_and_missing_span_rule() -> None:
    value = _codebook()
    value["registered_thresholds"]["cohen_kappa_minimum"] = 0.5
    value["span_policy"].pop("coordinate_system")
    errors = validate_codebook(value)
    assert any("thresholds" in error for error in errors)
    assert any("coordinate" in error for error in errors)


def test_approved_codebook_requires_explicit_approval() -> None:
    value = _codebook()
    value["status"] = "approved"
    assert any("approval_present" in error for error in validate_codebook(value))
