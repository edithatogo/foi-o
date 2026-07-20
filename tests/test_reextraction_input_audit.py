"""Fail-closed tests for governed re-extraction input auditing."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.reextraction import (
    audit_reextraction_input,
    build_governed_reextraction_packet,
)
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schemas" / "json" / "reextraction-input-audit.schema.json"
REPORT = ROOT / "examples" / "v2" / "reextraction-input-audit.fc27.json"
READINESS = ROOT / "examples" / "v2" / "upstream-extraction-readiness.2026-07-16.json"
PACKET = ROOT / "examples" / "v2" / "governed-reextraction-packet.35076.json"
PACKET_SCHEMA = ROOT / "schemas" / "json" / "governed-reextraction-packet.schema.json"
REVISION = "fc27bfa471c598a31d975cfa2b603b1a11408e55"


def _write_manifest(path: Path, requests: list[dict[str, object]]) -> str:
    path.write_text(
        json.dumps(
            {
                "meta": {
                    "record_count": len(requests),
                    "generated_at": "2026-07-13T01:57:41Z",
                    "version": "0.10.3",
                },
                "requests": requests,
            }
        ),
        encoding="utf-8",
    )
    return sha256(path.read_bytes()).hexdigest()


def _request(request_id: int, *, license_value: str | None = "CC-BY-4.0") -> dict[str, object]:
    return {
        "request_id": request_id,
        "content_sha256": f"{request_id:064x}",
        "license": license_value,
    }


def test_complete_rights_and_integrity_input_is_ready(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    digest = _write_manifest(manifest, [_request(1), _request(2)])
    report = audit_reextraction_input(
        manifest,
        dataset_repository="edithatogo/fyi-archive-nz",
        dataset_revision=REVISION,
        configuration="default",
        split="requests",
        expected_manifest_sha256=digest,
    )
    assert report.ready_for_reextraction is True
    assert report.blockers == []
    assert report.source_records_modified is False


def test_null_rights_missing_digest_and_duplicates_fail_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    records = [_request(1, license_value=None), _request(1)]
    records[1]["content_sha256"] = "not-a-digest"
    digest = _write_manifest(manifest, records)
    report = audit_reextraction_input(
        manifest,
        dataset_repository="edithatogo/fyi-archive-nz",
        dataset_revision=REVISION,
        configuration="default",
        split="requests",
        expected_manifest_sha256=digest,
    )
    assert report.ready_for_reextraction is False
    assert report.records_without_declared_license == 1
    assert report.records_with_invalid_content_sha256 == 1
    assert report.duplicate_request_ids == ["1"]
    assert report.blockers == [
        "duplicate_request_ids",
        "invalid_content_sha256",
        "missing_declared_license",
    ]


def test_manifest_digest_mismatch_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, [_request(1)])
    with pytest.raises(ValueError, match="manifest SHA-256"):
        audit_reextraction_input(
            manifest,
            dataset_repository="edithatogo/fyi-archive-nz",
            dataset_revision=REVISION,
            configuration="default",
            split="requests",
            expected_manifest_sha256="0" * 64,
        )


def test_committed_fc27_report_is_schema_valid_and_blocked_on_rights() -> None:
    result = validate_json_schema(REPORT, SCHEMA)
    assert not result.errors, result.errors
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["dataset_revision"] == REVISION
    assert report["manifest_sha256"] == (
        "23cab9ee0ac6986326d67c91a91e415456a1d0589c90ec1c1628556e0d0d6e1e"
    )
    assert report["record_count"] == 33217
    assert report["records_with_valid_content_sha256"] == 33217
    assert report["records_without_declared_license"] == 33217
    assert report["ready_for_reextraction"] is False
    assert report["blockers"] == ["missing_declared_license"]


def test_governed_packet_returns_exact_immutable_revisions() -> None:
    packet = build_governed_reextraction_packet(READINESS)

    assert packet.source_request_id == "35076"
    assert packet.source_manifest_sha256 == (
        "c929b312f4b627049b7867e46fa74b08ed8e9a43c35ba866871bead6f8a19b7d"
    )
    assert packet.baseline_sha256 == (
        "90550ce084be684ee493e2ce7470cbe0b01dee13b6253c50f91c7de9974d6007"
    )
    assert packet.pipeline_revision == "7fc78f14c1da6c1b165c0984c2173ae96307a3f6"
    assert packet.verifier_revision == "baf1b229e248c19d0922c0e75ef395ba22858b33"
    assert packet.ready_for_candidate_reextraction is True
    assert packet.ready_for_empirical_comparison is False
    assert packet.storage == "local_only"
    assert packet.redistribution_allowed is False
    assert packet.training_allowed is False
    assert packet.fine_tuning_allowed is False
    assert packet.release_allowed is False
    assert packet.dataset_publication_allowed is False
    assert packet.promotion_allowed is False
    assert packet.reviewed_gold_label_promotion_allowed is False
    assert packet.publication_allowed is False
    assert packet.source_records_modified is False


def test_governed_packet_is_schema_valid_and_matches_builder() -> None:
    result = validate_json_schema(PACKET, PACKET_SCHEMA)
    assert not result.errors, result.errors
    assert json.loads(PACKET.read_text(encoding="utf-8")) == build_governed_reextraction_packet(
        READINESS
    ).model_dump(mode="json")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("upstreams", "fyi_archive", "approved_local_content_snapshot", "published"), "published"),
        (("upstreams", "nlp_policy_nz", "initial_baseline", "review_status"), "candidate"),
        (("upstreams", "nlp_policy_nz", "initial_baseline", "model_applied"), "model"),
    ],
)
def test_governed_packet_rejects_unsafe_readiness(
    tmp_path: Path, mutation: tuple[str, ...], message: str
) -> None:
    payload = json.loads(READINESS.read_text(encoding="utf-8"))
    target = payload
    for key in mutation[:-1]:
        target = target[key]
    field = mutation[-1]
    target[field] = True if field != "review_status" else "reviewed"
    path = tmp_path / "readiness.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        build_governed_reextraction_packet(path)


def test_governed_packet_rejects_reintroduced_input_blocker(tmp_path: Path) -> None:
    payload = json.loads(READINESS.read_text(encoding="utf-8"))
    payload["blockers"].append("rights_metadata_incomplete")
    path = tmp_path / "readiness.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unresolved governed input blockers"):
        build_governed_reextraction_packet(path)


def test_governed_packet_rejects_archive_revision_drift(tmp_path: Path) -> None:
    payload = json.loads(READINESS.read_text(encoding="utf-8"))
    payload["upstreams"]["nlp_policy_nz"]["initial_baseline"]["archive_revision"] = "0" * 40
    path = tmp_path / "readiness.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="baseline archive revision mismatch"):
        build_governed_reextraction_packet(path)
