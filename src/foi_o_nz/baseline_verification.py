"""Independent, fail-closed verification for initial FOI-O baselines."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

_PATTERNS = (
    ("prohibition", "must not", re.compile(r"\bmust\s+not\b", re.IGNORECASE)),
    ("obligation", "must", re.compile(r"\bmust\b(?!\s+not\b)", re.IGNORECASE)),
    ("permission", "may", re.compile(r"\bmay\b", re.IGNORECASE)),
)


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_initial_baseline(
    baseline_path: Path,
    *,
    snapshot_dir: Path,
    contract_path: Path,
    expected_baseline_sha256: str,
    expected_source_manifest_sha256: str,
    expected_contract_sha256: str,
    expected_pipeline_revision: str,
    expected_archive_revision: str,
    expected_retrieved_at: str,
) -> dict[str, Any]:
    """Recompute baseline provenance and lexical candidates without producer code."""
    _require(_digest(baseline_path) == expected_baseline_sha256, "baseline SHA-256 mismatch")
    baseline = _load_object(baseline_path)
    _require(
        baseline.get("schema_version") == "nlp-policy-nz.foio-raw-extraction.v0.2.0",
        "unsupported baseline schema",
    )
    _require(baseline.get("pipeline_revision") == expected_pipeline_revision, "pipeline mismatch")
    _require(baseline.get("archive_revision") == expected_archive_revision, "archive mismatch")
    _require(baseline.get("contract_version") == "0.1.0", "contract version mismatch")
    _require(baseline.get("review_status") == "candidate", "baseline must remain candidate")
    _require(baseline.get("human_promotion_required") is True, "human promotion gate missing")
    _require(
        baseline.get("extraction_method") == "deterministic_lexical_candidates_v0.1.0",
        "unsupported extraction method",
    )
    _require(
        baseline.get("model", {}).get("applied_during_candidate_extraction") is False,
        "baseline cannot claim model execution",
    )
    _require(
        _digest(contract_path) == expected_contract_sha256
        and baseline.get("contract", {}).get("manifest_sha256") == expected_contract_sha256,
        "contract SHA-256 mismatch",
    )

    source_manifest_path = snapshot_dir / "manifest.json"
    _require(
        _digest(source_manifest_path) == expected_source_manifest_sha256
        and baseline.get("source_manifest_sha256") == expected_source_manifest_sha256,
        "source manifest SHA-256 mismatch",
    )
    source = _load_object(source_manifest_path)
    rights = source.get("rights_review", {})
    _require(source.get("ready_for_processing") is True, "source is not processing-ready")
    _require(rights.get("status") == "approved", "source rights review is not approved")
    _require(rights.get("purpose") == "foi-o-candidate-extraction", "source purpose mismatch")
    _require(rights.get("redistribution_allowed") is False, "source redistribution must be false")
    requests = source.get("requests")
    _require(isinstance(requests, list) and len(requests) == 1, "expected one source request")
    requests = cast("list[dict[str, Any]]", requests)

    root = snapshot_dir.resolve()
    expected_records: list[dict[str, Any]] = []
    for request in requests:
        _require(isinstance(request, dict), "source request must be an object")
        request_id = str(request.get("request_id") or "")
        content_path = (root / str(request.get("content_path") or "")).resolve()
        _require(root in content_path.parents, "content path escapes snapshot")
        content_bytes = content_path.read_bytes()
        content_digest = sha256(content_bytes).hexdigest()
        _require(content_digest == request.get("content_sha256"), "source content SHA-256 mismatch")
        text = content_bytes.decode("utf-8")
        for family, label, pattern in _PATTERNS:
            for index, match in enumerate(pattern.finditer(text)):
                expected_records.append(
                    {
                        "record_id": f"nz:fyi:{request_id}#{family}-{index}",
                        "family": family,
                        "label": label,
                        "value": match.group(0),
                        "confidence": 0.5,
                        "attributes": {
                            "requires_human_review": True,
                            "source_field": "content_text",
                        },
                        "source_trace": {
                            "citation_path": f"nz/fyi/request/{request_id}",
                            "source_sha256": content_digest,
                            "source_url": str(request.get("source_url") or ""),
                            "spans": [
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ],
                        },
                    }
                )

    manifest = baseline.get("manifest", {})
    records = manifest.get("records")
    _require(isinstance(records, list), "baseline records must be a list")
    _require(len(records) == len(expected_records), "baseline record count mismatch")
    for actual, expected in zip(records, expected_records, strict=True):
        for field in ("record_id", "family", "label", "value", "confidence", "attributes"):
            _require(actual.get(field) == expected[field], f"candidate {field} mismatch")
        actual_trace = actual.get("source_trace", {})
        for field in ("citation_path", "source_sha256", "source_url", "spans"):
            _require(
                actual_trace.get(field) == expected["source_trace"][field],
                f"trace {field} mismatch",
            )
        _require(
            actual_trace.get("retrieved_at") == expected_retrieved_at, "trace timestamp mismatch"
        )

    return {
        "schema_version": "foi-o.initial-baseline-verification.v0.1.0",
        "valid": True,
        "baseline_sha256": expected_baseline_sha256,
        "source_manifest_sha256": expected_source_manifest_sha256,
        "pipeline_revision": expected_pipeline_revision,
        "archive_revision": expected_archive_revision,
        "contract_sha256": expected_contract_sha256,
        "retrieved_at": expected_retrieved_at,
        "record_count": len(records),
        "candidate_ids": [record["record_id"] for record in records],
        "model_applied": False,
        "review_status": "candidate",
    }
