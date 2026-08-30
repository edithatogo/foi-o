"""Memory-budget tests (trial: pytest-memray).

Opt-in via ``make test-memray`` (which passes ``--memray``); skipped entirely
in the normal suite. Budgets bound the archive checkpoint manager, which is
executed over large unit batches in production rollout runs.
"""

from __future__ import annotations

import pytest

from foi_o_nz.archive_adapters import ArchiveCheckpointManager

pytest.importorskip("pytest_memray")


@pytest.mark.memray
@pytest.mark.limit_memory("8 MB")
def test_checkpoint_manager_batch_memory_budget(tmp_path, monkeypatch) -> None:
    """Saving a 5,000-unit batch must stay within a bounded memory envelope."""
    manager = ArchiveCheckpointManager(tmp_path, definition_sha256="d" * 64)
    units = [
        {"request_id": f"r{index}", "url": f"https://example.test/f/{index}", "state": "Received"}
        for index in range(5_000)
    ]
    path = manager.save_checkpoint("stage_memory", units, "a" * 64)
    assert path.exists()
    loaded = manager.load_latest_checkpoint("stage_memory")
    assert loaded is not None and loaded["processed_count"] == 5_000
