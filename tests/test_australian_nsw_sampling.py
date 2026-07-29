from __future__ import annotations

from foi_o_nz.australian_nsw_sampling import POPULATION, SAMPLE_SIZE, _selection


def test_nsw_selection_is_deterministic_and_without_replacement() -> None:
    units = [
        {
            "text_sha256": f"{index:064x}",
            "unit_id": str(index),
            "canonical_slug": str(index),
            "duplicate_cluster_id": str(index),
        }
        for index in range(POPULATION)
    ]
    first = _selection(units)
    assert first == _selection(list(reversed(units)))
    assert len(first) == SAMPLE_SIZE
    assert len({row["text_sha256"] for row in first}) == SAMPLE_SIZE
