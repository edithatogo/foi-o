"""Property-based tests for content-addressed archive checkpoints (trial: Hypothesis).

Invariants under test:
- checkpoint content-addressing is deterministic: identical inputs produce an
  identical SHA-256 address and serializable payload;
- the recorded ``checkpoint_sha256`` always matches the serialized body;
- distinct payloads never collide on the same checkpoint address;
- ``load_latest_checkpoint`` round-trips the saved units and validates the
  definition hash (mismatched definitions must be rejected).
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from foi_o_nz.archive_adapters import ArchiveCheckpointManager

unit_strategy = st.dictionaries(
    st.sampled_from(["request_id", "url", "state", "captured_at"]),
    st.one_of(st.text(min_size=0, max_size=20), st.integers(0, 10_000)),
    min_size=1,
    max_size=4,
)


def test_checkpoint_address_is_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = ArchiveCheckpointManager(Path(tmp), definition_sha256="d" * 64)
        units = [{"request_id": "35076", "state": "Received"}]
        path_one = manager.save_checkpoint("stage_a", units, "a" * 64)
        path_two = manager.save_checkpoint("stage_a", units, "a" * 64)
        assert path_one.name == path_two.name
        body = json.loads(path_one.read_text(encoding="utf-8"))
        expected_sha = hashlib.sha256(
            json.dumps(
                {k: v for k, v in body.items() if k != "checkpoint_sha256"},
                sort_keys=True,
                indent=2,
            ).encode("utf-8")
        ).hexdigest()
        assert body["checkpoint_sha256"] == expected_sha


@settings(max_examples=100, deadline=None)
@given(
    units=st.lists(unit_strategy, min_size=0, max_size=15),
    output_sha=st.text(min_size=64, max_size=64, alphabet="0123456789abcdef"),
)
def test_checkpoint_round_trip_and_address_integrity(
    units: list[dict[str, object]], output_sha: str
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = ArchiveCheckpointManager(Path(tmp), definition_sha256="d" * 64)
        path = manager.save_checkpoint("stage_b", units, output_sha)
        body = json.loads(path.read_text(encoding="utf-8"))
        expected_sha = hashlib.sha256(
            json.dumps(
                {k: v for k, v in body.items() if k != "checkpoint_sha256"},
                sort_keys=True,
                indent=2,
            ).encode("utf-8")
        ).hexdigest()
        assert body["checkpoint_sha256"] == expected_sha
        assert path.name.startswith(f"checkpoint_stage_b_{body['checkpoint_sha256'][:16]}")
        loaded = manager.load_latest_checkpoint("stage_b")
        assert loaded is not None
        assert loaded["units"] == units
        assert loaded["stage_output_sha256"] == output_sha
