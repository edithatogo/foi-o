import json
from pathlib import Path

import pytest

from foi_o_nz.bounded_pilot_evidence import verify_bounded_pilot_evidence
from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "examples/v2/bounded-pilot-evidence-manifest.pending.json"
SCHEMA = ROOT / "schemas/json/bounded-pilot-evidence-manifest.schema.json"


def test_manifest_is_valid_and_fail_closed() -> None:
    result = validate_json_schema(MANIFEST, SCHEMA)
    assert not result.errors, result.errors
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["request_ids"] == ["11872", "35076"]
    assert manifest["authentic_input"] is True
    assert manifest["empirical_evidence"] is False
    assert manifest["context_presentation_allowed"] is False
    assert manifest["execution_allowed"] is False


def test_manifest_pins_raw_state_pointer_span_and_recurrence() -> None:
    manifest = json.loads(MANIFEST.read_text())
    records = {record["request_id"]: record for record in manifest["records"]}
    assert records["11872"]["raw_state"]["span"] == {"start": 102, "end": 122}
    assert records["35076"]["raw_state"]["span"] == {"start": 102, "end": 118}
    for record in records.values():
        assert record["raw_state"]["json_pointer"] == "/described_state"
        assert record["raw_state"]["coordinate_system"] == "unicode_code_points_half_open"
        assert record["raw_state"]["repeated_elsewhere"] is True


def test_manifest_preserves_correspondence_and_attachment_boundaries() -> None:
    manifest = json.loads(MANIFEST.read_text())
    records = {record["request_id"]: record for record in manifest["records"]}
    assert records["11872"]["correspondence"]["block_count"] == 4
    assert records["11872"]["attachments"]["canonical_inventory_empty"] is True
    assert records["11872"]["attachments"]["supplemental_file_count"] == 3
    assert records["35076"]["correspondence"]["block_count"] == 1
    assert records["35076"]["attachments"]["verified_empty"] is True


def test_manifest_recomputes_against_approved_local_snapshots() -> None:
    roots = {
        "11872": Path("/private/tmp/fyi-attachment-snapshot-11872-approved"),
        "35076": Path("/private/tmp/fyi-content-snapshot-35076-approved"),
    }
    if not all(path.is_dir() for path in roots.values()):
        pytest.skip("restricted approved local snapshots are not available")
    verify_bounded_pilot_evidence(MANIFEST, roots)


def test_local_verifier_rejects_span_drift(tmp_path: Path) -> None:
    roots = {
        "11872": Path("/private/tmp/fyi-attachment-snapshot-11872-approved"),
        "35076": Path("/private/tmp/fyi-content-snapshot-35076-approved"),
    }
    if not all(path.is_dir() for path in roots.values()):
        pytest.skip("restricted approved local snapshots are not available")
    manifest = json.loads(MANIFEST.read_text())
    manifest["records"][0]["correspondence"]["blocks"][0]["text_span"]["start"] += 1
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="text span mismatch"):
        verify_bounded_pilot_evidence(changed, roots)
