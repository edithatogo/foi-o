import json
from pathlib import Path

from scripts.extract_au_cth_assertion_candidate import extract


def test_candidate_extractor_requires_explicit_commonwealth_foi_phrase(tmp_path: Path) -> None:
    frame = tmp_path / "frame.json"
    frame.write_text(
        json.dumps(
            {
                "source_population_sha256": "a" * 64,
                "units": [
                    {"unit_id": "u1", "unit_sha256": "b" * 64, "text": "Commonwealth FOI request"},
                    {"unit_id": "u2", "unit_sha256": "c" * 64, "text": "Australian request"},
                ],
            }
        )
    )
    result = extract(frame, extractor_revision="test")
    assert result["units"][0]["label"] == "observed"
    assert result["units"][0]["abstention"] is False
    assert result["units"][1]["label"] == "unknown"
    assert result["units"][1]["abstention"] is True
