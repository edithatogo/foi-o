from __future__ import annotations

from pathlib import Path

import pytest

from foi_o_nz.archive_adapters import (
    ArchiveCheckpointManager,
    MetadataFirstSelector,
    RetryPolicy,
)


def test_retry_policy_delays_and_status() -> None:
    policy = RetryPolicy(base_delay_seconds=1.0, max_delay_seconds=10.0, backoff_multiplier=2.0)

    assert policy.is_retryable(429) is True
    assert policy.is_retryable(503) is True
    assert policy.is_retryable(404) is False
    assert policy.is_retryable(200) is False

    assert policy.compute_backoff(1) == 1.0
    assert policy.compute_backoff(2) == 2.0
    assert policy.compute_backoff(3) == 4.0
    assert policy.compute_backoff(5) == 10.0  # capped at max_delay


def test_checkpoint_manager_save_and_load(tmp_path: Path) -> None:
    def_sha = "a" * 64
    mgr = ArchiveCheckpointManager(tmp_path / "checkpoints", def_sha)

    units = [{"unit_id": "u1", "status": "ok"}, {"unit_id": "u2", "status": "ok"}]
    output_sha = "b" * 64
    cp_path = mgr.save_checkpoint("discover", units, output_sha)
    assert cp_path.exists()

    loaded = mgr.load_latest_checkpoint("discover")
    assert loaded is not None
    assert loaded["stage_name"] == "discover"
    assert loaded["processed_count"] == 2
    assert loaded["stage_output_sha256"] == output_sha


def test_checkpoint_manager_rejects_definition_mismatch(tmp_path: Path) -> None:
    def_sha1 = "a" * 64
    mgr1 = ArchiveCheckpointManager(tmp_path / "checkpoints", def_sha1)
    mgr1.save_checkpoint("discover", [{"u": 1}], "b" * 64)

    def_sha2 = "c" * 64
    mgr2 = ArchiveCheckpointManager(tmp_path / "checkpoints", def_sha2)
    with pytest.raises(ValueError, match="checkpoint definition mismatch"):
        mgr2.load_latest_checkpoint("discover")


def test_metadata_first_selector() -> None:
    selector = MetadataFirstSelector("AU-ACT", max_fulltext_units=2)
    records = [
        {"request_id": "req-1", "jurisdiction": "AU-ACT", "http_status": 200},
        {"request_id": "req-2", "jurisdiction": "AU-NSW", "http_status": 200},
        {"request_id": "req-3", "jurisdiction": "AU-ACT", "http_status": 404},
        {"request_id": "req-4", "jurisdiction": "AU-ACT", "http_status": 200},
        {"request_id": "req-5", "jurisdiction": "AU-ACT", "http_status": 200},
    ]
    eligible = selector.filter_metadata_rows(records)
    assert len(eligible) == 3

    selected, backlog = selector.select_for_fulltext(eligible)
    assert len(selected) == 2
    assert len(backlog) == 1
    assert selected[0]["request_id"] == "req-1"
    assert selected[1]["request_id"] == "req-4"
    assert backlog[0]["request_id"] == "req-5"
