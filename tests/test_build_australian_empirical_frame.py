import json
from pathlib import Path

from scripts.build_australian_empirical_frame import build_frame


def test_build_frame_is_authentic_but_fail_closed_for_annotation(tmp_path: Path) -> None:
    core = tmp_path / "core.json"
    core.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "extraction_status": "extracted",
                        "request_key": "example",
                        "source_url": "https://example.test/request/example",
                        "archive_url": "https://web.archive.org/example",
                        "archive_digest": "digest",
                        "content_sha256": "a" * 64,
                        "title": "Request title",
                        "state": "The request is open.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    frame = build_frame(core, jurisdiction="AU-CTH", output=tmp_path / "frame.json")
    assert frame["status"] == "authentic_pending_rights_and_fulltext_review"
    assert frame["rights_eligible"] is False
    assert frame["annotation_execution_authorized"] is False
    assert frame["units"][0]["unit_id"] == "AU-CTH:example"
