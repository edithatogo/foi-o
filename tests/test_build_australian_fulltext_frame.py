import json
from pathlib import Path

from scripts.build_australian_fulltext_frame import build_frame


def test_fulltext_frame_preserves_capture_disposition(tmp_path: Path) -> None:
    artifact = tmp_path / "fulltext.json"
    artifact.write_text(
        json.dumps(
            {
                "schema": "fyi-archive.historical-fulltext.v1",
                "records": [
                    {
                        "source_url": "https://example.test/request/a?utm_source=x",
                        "status": "captured",
                        "text": "A",
                        "text_sha256": "a" * 64,
                    },
                    {
                        "source_url": "https://example.test/request/b",
                        "status": "failed",
                        "diagnostic": "403",
                        "text": "",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    frame = build_frame(artifact, jurisdiction="AU-CTH", output=tmp_path / "frame.json")
    assert frame["record_count"] == 2
    assert frame["captured_count"] == 1
    assert frame["failed_count"] == 1
    assert frame["fulltext_available"] is True
    assert frame["rights_eligible"] is False
    assert (
        frame["units"][0]["source_ref"]["canonical_source_url"]
        == "https://example.test/request/a?utm_source=x"
    )
    assert frame["units"][1]["text"] is None
