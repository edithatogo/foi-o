"""Independent governed re-extraction verification and delta tests."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.governed_reextraction import (
    compare_reextraction_to_baseline,
    verify_governed_reextraction,
)


def _write_fixture(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    snapshot = root / "snapshot"
    (snapshot / "content").mkdir(parents=True)
    content = b"The agency must disclose.\n"
    content_path = snapshot / "content" / "page.html"
    content_path.write_bytes(content)
    content_digest = sha256(content).hexdigest()
    artifact = {
        "path": "content/page.html",
        "sha256": content_digest,
        "size": len(content),
    }
    source = {
        "artifacts": [artifact],
        "ready_for_processing": True,
        "rights_review": {
            "status": "approved",
            "purpose": "foi-o-candidate-extraction",
            "redistribution_allowed": False,
        },
        "requests": [
            {
                "request_id": "35076",
                "content_path": "content/page.html",
                "content_sha256": content_digest,
                "source_url": "https://fyi.org.nz/request/35076",
            }
        ],
    }
    source_path = snapshot / "manifest.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    contract = root / "contract.json"
    contract.write_text(json.dumps({"contract_version": "0.1.0"}), encoding="utf-8")
    contract_digest = sha256(contract.read_bytes()).hexdigest()
    source_digest = sha256(source_path.read_bytes()).hexdigest()
    start = content.decode().index("must")
    record = {
        "record_id": "nz:fyi:35076#obligation-0",
        "family": "obligation",
        "label": "must",
        "value": "must",
        "confidence": 0.5,
        "attributes": {"requires_human_review": True, "source_field": "content_text"},
        "source_trace": {
            "citation_path": "nz/fyi/request/35076",
            "source_sha256": content_digest,
            "source_url": "https://fyi.org.nz/request/35076",
            "retrieved_at": "2026-07-16T10:52:39Z",
            "spans": [{"start": start, "end": start + 4, "text": "must"}],
        },
    }
    candidate_payload = {
        "schema_version": "nlp-policy-nz.foio-raw-extraction.v0.2.0",
        "contract_version": "0.1.0",
        "review_status": "candidate",
        "human_promotion_required": True,
        "archive_revision": "a" * 40,
        "pipeline_revision": "b" * 40,
        "source_manifest_sha256": source_digest,
        "contract": {"manifest_sha256": contract_digest},
        "model": {
            "model_id": "nlpaueb/legal-bert-base-uncased",
            "revision": "d" * 40,
            "weights_sha256": "e" * 64,
            "applied_during_candidate_extraction": False,
        },
        "extraction_method": "deterministic_lexical_candidates_v0.1.0",
        "manifest": {"records": [record]},
    }
    baseline = root / "baseline.json"
    baseline.write_text(json.dumps(candidate_payload), encoding="utf-8")
    candidate = root / "candidate.json"
    candidate.write_bytes(baseline.read_bytes())
    packet_payload = {
        "schema_version": "foi-o.governed-reextraction-packet.v0.1.0",
        "packet_id": "foio-nz-35076-initial-baseline",
        "purpose": "foi-o-candidate-extraction",
        "source_request_id": "35076",
        "source_manifest_sha256": source_digest,
        "source_content_sha256": content_digest,
        "reviewed_pending_manifest_sha256": "f" * 64,
        "archive_revision": "a" * 40,
        "fyi_cli_revision": "c" * 40,
        "pipeline_revision": "b" * 40,
        "verifier_revision": "1" * 40,
        "baseline_schema_version": "nlp-policy-nz.foio-raw-extraction.v0.2.0",
        "baseline_sha256": sha256(baseline.read_bytes()).hexdigest(),
        "baseline_verification_sha256": "2" * 64,
        "contract_version": "0.1.0",
        "contract_sha256": contract_digest,
        "model_id": "nlpaueb/legal-bert-base-uncased",
        "model_revision": "d" * 40,
        "model_weights_sha256": "e" * 64,
        "model_applied_in_baseline": False,
        "rights_reviewer": "reviewer",
        "rights_reviewed_at": "2026-07-16T10:40:17Z",
        "storage": "local_only",
        "redistribution_allowed": False,
        "training_allowed": False,
        "fine_tuning_allowed": False,
        "release_allowed": False,
        "dataset_publication_allowed": False,
        "ready_for_candidate_reextraction": True,
        "ready_for_empirical_comparison": False,
        "comparison_blockers": ["independent_annotation_pending", "synthetic_fixture_only"],
        "human_promotion_required": True,
        "promotion_allowed": False,
        "reviewed_gold_label_promotion_allowed": False,
        "publication_allowed": False,
        "source_records_modified": False,
    }
    packet = root / "packet.json"
    packet.write_text(json.dumps(packet_payload), encoding="utf-8")
    return candidate, baseline, packet, snapshot, contract


def test_independent_verification_recomputes_all_governed_evidence(tmp_path: Path) -> None:
    candidate, baseline, packet, snapshot, contract = _write_fixture(tmp_path)
    report = verify_governed_reextraction(
        candidate,
        baseline_path=baseline,
        packet_path=packet,
        snapshot_dir=snapshot,
        contract_path=contract,
        expected_candidate_sha256=sha256(candidate.read_bytes()).hexdigest(),
        expected_packet_sha256=sha256(packet.read_bytes()).hexdigest(),
    )

    assert report.valid is True
    assert report.candidate_ids == ("nz:fyi:35076#obligation-0",)
    assert report.source_artifacts_verified == 1
    assert report.storage == "local_only"
    assert report.model_applied is False
    assert report.source_records_modified is False
    assert report.empirical_comparison is False


def test_non_empirical_delta_reports_bit_identical_reproduction(tmp_path: Path) -> None:
    candidate, baseline, packet, _, _ = _write_fixture(tmp_path)
    delta = compare_reextraction_to_baseline(candidate, baseline_path=baseline, packet_path=packet)

    assert delta.byte_identical is True
    assert delta.candidate_sets_identical is True
    assert delta.added_candidate_ids == ()
    assert delta.removed_candidate_ids == ()
    assert delta.changed_candidate_ids == ()
    assert delta.provenance_changed_candidate_ids == ()
    assert delta.empirical_comparison is False
    assert delta.empirical_claim_allowed is False


def test_delta_separates_timestamp_change_from_candidate_change(tmp_path: Path) -> None:
    candidate, baseline, packet, _, _ = _write_fixture(tmp_path)
    payload = json.loads(candidate.read_text())
    payload["manifest"]["records"][0]["source_trace"]["retrieved_at"] = "2026-07-16T11:00:00Z"
    candidate.write_text(json.dumps(payload), encoding="utf-8")

    delta = compare_reextraction_to_baseline(candidate, baseline_path=baseline, packet_path=packet)
    assert delta.byte_identical is False
    assert delta.candidate_sets_identical is True
    assert delta.changed_candidate_ids == ()
    assert delta.provenance_changed_candidate_ids == ("nz:fyi:35076#obligation-0",)


def test_delta_rejects_revision_drift(tmp_path: Path) -> None:
    candidate, baseline, packet, _, _ = _write_fixture(tmp_path)
    payload = json.loads(candidate.read_text())
    payload["pipeline_revision"] = "9" * 40
    candidate.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="candidate pipeline revision mismatch"):
        compare_reextraction_to_baseline(candidate, baseline_path=baseline, packet_path=packet)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("model", "model execution claim"),
        ("artifact", "source artifact SHA-256 mismatch"),
        ("candidate", "candidate SHA-256 mismatch"),
    ],
)
def test_independent_verification_fails_closed(tmp_path: Path, mutation: str, message: str) -> None:
    candidate, baseline, packet, snapshot, contract = _write_fixture(tmp_path)
    candidate_digest = sha256(candidate.read_bytes()).hexdigest()
    if mutation == "model":
        payload = json.loads(candidate.read_text())
        payload["model"]["applied_during_candidate_extraction"] = True
        candidate.write_text(json.dumps(payload), encoding="utf-8")
        candidate_digest = sha256(candidate.read_bytes()).hexdigest()
    elif mutation == "artifact":
        (snapshot / "content" / "page.html").write_text("changed", encoding="utf-8")
    else:
        candidate_digest = "0" * 64

    with pytest.raises(ValueError, match=message):
        verify_governed_reextraction(
            candidate,
            baseline_path=baseline,
            packet_path=packet,
            snapshot_dir=snapshot,
            contract_path=contract,
            expected_candidate_sha256=candidate_digest,
            expected_packet_sha256=sha256(packet.read_bytes()).hexdigest(),
        )
