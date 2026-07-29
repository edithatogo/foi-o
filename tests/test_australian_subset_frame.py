from __future__ import annotations

from foi_o_nz.australian_subset_frame import _canonical, _cluster_id


def test_canonical_duplicate_key_normalizes_unicode_and_whitespace() -> None:
    assert _canonical("  Caf\u00e9\n\t") == _canonical("cafe\u0301")


def test_cluster_id_changes_when_request_linked_text_changes() -> None:
    first = _cluster_id(title="Title", authority="Agency", text="First request")
    second = _cluster_id(title="Title", authority="Agency", text="Second request")
    assert first.startswith("exact:")
    assert first != second
