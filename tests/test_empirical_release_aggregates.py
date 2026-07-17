from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
TRACK = ROOT / "conductor/tracks/foi_o_v2_empirical_implementation_20260714"


def test_release_gates_reflect_approved_source_and_bounded_mapping_state() -> None:
    gates = yaml.safe_load((TRACK / "release-gates.yaml").read_text())["gates"]
    source_pack = gates["nz_source_pack"]
    assert source_pack["status"] == "promoted_metadata_only"
    assert source_pack["missing"] == []
    assert source_pack["evidence"]["governed_pack"] == (
        "examples/v2/nz-source-pack.governed-metadata.json"
    )
    mapping = gates["raw_state_mapping_audit"]
    assert mapping["status"] == "bounded_mappings_human_approved"
    assert mapping["missing"] == ["archive_wide_evidence"]
    assert mapping["attachment_candidate"]["rights_status"] == "approved"
    assert mapping["attachment_candidate"]["ready_for_raw_state_mapping_audit"] is True


def test_output_ledger_reflects_completed_bounded_and_source_pack_work() -> None:
    outputs = yaml.safe_load((TRACK / "output-ledger.yaml").read_text())["outputs"]
    by_id = {item["id"]: item for item in outputs}
    assert by_id["O-FOIO-V2-REEXTRACTION-READINESS"]["status"] == (
        "bounded_run_complete_empirical_comparison_pending"
    )
    assert by_id["O-FOIO-V2-BOUNDED-RAW-STATE-AUDIT"]["status"] == (
        "two_bounded_mappings_human_approved"
    )
    assert by_id["O-FOIO-V2-FYI-ATTACHMENT-SNAPSHOT"]["status"] == (
        "local_snapshot_rights_approved"
    )
    assert by_id["O-FOIO-V2-NZ-SOURCE-PACK-REVIEW"]["status"] == (
        "metadata_only_source_pack_promoted"
    )
