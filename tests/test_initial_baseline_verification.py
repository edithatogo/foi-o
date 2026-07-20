"""Independent verification tests for initial extraction baselines."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from foi_o_nz.baseline_verification import verify_initial_baseline


def _write_packet(root: Path) -> tuple[Path, Path, Path, str]:
    snapshot = root / "snapshot"
    (snapshot / "content").mkdir(parents=True)
    content = b"The agency must disclose.\r\n"
    (snapshot / "content" / "page.html").write_bytes(content)
    source = {
        "ready_for_processing": True,
        "rights_review": {
            "status": "approved",
            "purpose": "foi-o-candidate-extraction",
            "redistribution_allowed": False,
        },
        "requests": [
            {
                "request_id": "35076",
                "content_path": "content/page.html",
                "content_sha256": sha256(content).hexdigest(),
                "source_url": "https://fyi.org.nz/request/35076",
            }
        ],
    }
    source_path = snapshot / "manifest.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    contract = root / "contract.json"
    contract.write_text(json.dumps({"contract_version": "0.1.0"}), encoding="utf-8")
    start = content.decode().index("must")
    baseline = {
        "schema_version": "nlp-policy-nz.foio-raw-extraction.v0.2.0",
        "contract_version": "0.1.0",
        "review_status": "candidate",
        "human_promotion_required": True,
        "archive_revision": "a" * 40,
        "pipeline_revision": "b" * 40,
        "source_manifest_sha256": sha256(source_path.read_bytes()).hexdigest(),
        "contract": {"manifest_sha256": sha256(contract.read_bytes()).hexdigest()},
        "model": {"applied_during_candidate_extraction": False},
        "extraction_method": "deterministic_lexical_candidates_v0.1.0",
        "manifest": {
            "producer": "nlp-policy-nz",
            "schema_version": "1.0",
            "records": [
                {
                    "record_id": "nz:fyi:35076#obligation-0",
                    "family": "obligation",
                    "label": "must",
                    "value": "must",
                    "confidence": 0.5,
                    "attributes": {
                        "requires_human_review": True,
                        "source_field": "content_text",
                    },
                    "source_trace": {
                        "citation_path": "nz/fyi/request/35076",
                        "source_sha256": sha256(content).hexdigest(),
                        "source_url": "https://fyi.org.nz/request/35076",
                        "retrieved_at": "2026-07-16T10:52:39Z",
                        "spans": [{"start": start, "end": start + 4, "text": "must"}],
                    },
                }
            ],
        },
    }
    baseline_path = root / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    return baseline_path, snapshot, contract, sha256(baseline_path.read_bytes()).hexdigest()


def test_independent_verifier_recomputes_source_and_candidates(tmp_path: Path) -> None:
    baseline, snapshot, contract, digest = _write_packet(tmp_path)

    report = verify_initial_baseline(
        baseline,
        snapshot_dir=snapshot,
        contract_path=contract,
        expected_baseline_sha256=digest,
        expected_source_manifest_sha256=sha256(
            (snapshot / "manifest.json").read_bytes()
        ).hexdigest(),
        expected_contract_sha256=sha256(contract.read_bytes()).hexdigest(),
        expected_pipeline_revision="b" * 40,
        expected_archive_revision="a" * 40,
        expected_retrieved_at="2026-07-16T10:52:39Z",
    )

    assert report["valid"] is True
    assert report["record_count"] == 1
    assert report["candidate_ids"] == ["nz:fyi:35076#obligation-0"]


@pytest.mark.parametrize(
    ("drift", "message"),
    [
        ("artifact", "baseline SHA-256 mismatch"),
        ("source", "source content SHA-256 mismatch"),
        ("span", "trace spans mismatch"),
        ("pipeline", "pipeline mismatch"),
        ("source-pin", "source manifest SHA-256 mismatch"),
        ("contract-pin", "contract SHA-256 mismatch"),
        ("timestamp", "trace timestamp mismatch"),
    ],
)
def test_independent_verifier_fails_closed_on_drift(
    tmp_path: Path, drift: str, message: str
) -> None:
    baseline, snapshot, contract, digest = _write_packet(tmp_path)
    expected_pipeline = "b" * 40
    expected_source = sha256((snapshot / "manifest.json").read_bytes()).hexdigest()
    expected_contract = sha256(contract.read_bytes()).hexdigest()
    expected_retrieved_at = "2026-07-16T10:52:39Z"
    if drift == "artifact":
        digest = "0" * 64
    elif drift == "source":
        (snapshot / "content" / "page.html").write_text("changed", encoding="utf-8")
    elif drift == "span":
        payload = json.loads(baseline.read_text())
        payload["manifest"]["records"][0]["source_trace"]["spans"][0]["start"] = 0
        baseline.write_text(json.dumps(payload), encoding="utf-8")
        digest = sha256(baseline.read_bytes()).hexdigest()
    elif drift == "pipeline":
        expected_pipeline = "c" * 40
    elif drift == "source-pin":
        expected_source = "0" * 64
    elif drift == "contract-pin":
        expected_contract = "0" * 64
    else:
        expected_retrieved_at = "2026-07-16T00:00:00Z"

    with pytest.raises(ValueError, match=message):
        verify_initial_baseline(
            baseline,
            snapshot_dir=snapshot,
            contract_path=contract,
            expected_baseline_sha256=digest,
            expected_source_manifest_sha256=expected_source,
            expected_contract_sha256=expected_contract,
            expected_pipeline_revision=expected_pipeline,
            expected_archive_revision="a" * 40,
            expected_retrieved_at=expected_retrieved_at,
        )
