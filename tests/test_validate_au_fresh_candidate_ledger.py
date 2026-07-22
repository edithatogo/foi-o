from scripts.validate_au_fresh_candidate_ledger import validate_ledger


def _ledger() -> dict:
    return {
        "schema": "foi-o.au-cth-fresh-candidate-ledger.v0.1.0",
        "source_cdx_sha256": "a" * 64,
        "calibration_excluded": True,
        "records": [
            {
                "source_url": "https://www.righttoknow.org.au/request/a",
                "archive_timestamp": "20200101000000",
                "archive_digest": "A",
            },
            {
                "source_url": "https://www.righttoknow.org.au/request/b",
                "archive_timestamp": "20200101000001",
                "archive_digest": "B",
            },
        ],
    }


def test_valid_ledger_passes() -> None:
    assert (
        validate_ledger(
            _ledger(),
            calibration_urls={"https://www.righttoknow.org.au/request/calibration"},
            expected_cdx_sha256="a" * 64,
        )
        == []
    )


def test_ledger_rejects_calibration_and_duplicate_urls() -> None:
    value = _ledger()
    value["records"][1]["source_url"] = value["records"][0]["source_url"]
    errors = validate_ledger(
        value, calibration_urls={value["records"][0]["source_url"]}, expected_cdx_sha256="a" * 64
    )
    assert any("calibration" in error for error in errors)
    assert any("unique" in error for error in errors)


def test_ledger_rejects_query_urls_and_wrong_cdx_hash() -> None:
    value = _ledger()
    value["records"][0]["source_url"] += "?utm_source=test"
    errors = validate_ledger(value, calibration_urls=set(), expected_cdx_sha256="b" * 64)
    assert any("canonicalized" in error for error in errors)
    assert any("CDX hash" in error for error in errors)
