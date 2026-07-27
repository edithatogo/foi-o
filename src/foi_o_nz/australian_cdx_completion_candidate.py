"""Independent validation for the bounded AU RightToKnow CDX completion packet."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast
from urllib.parse import SplitResult, parse_qs, urlsplit

PINNED_SOURCE_CDX_SHA256 = "954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd"
PINNED_QUERY_PLAN_SHA256 = "ac402c3d69e6140772629e5ecb55f0138c891121a42c2fa7a180850260742d3b"
EXPECTED_SLUG_COUNT = 858
EXPECTED_QUERY_COUNT = 1_716
CDX_HEADER = ["original", "timestamp", "digest", "statuscode", "length"]
_SLUG = re.compile(r"^[a-z0-9_]+$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_TIMESTAMP = re.compile(r"^[0-9]{14}$")
_LENGTH = re.compile(r"^[0-9]+$")
_PLAN_KEYS = {
    "schema",
    "source_cdx_sha256",
    "missing_slug_count",
    "query_count",
    "queries",
}
_QUERY_KEYS = {"canonical_slug", "media_kind", "exact_url"}
_CANDIDATE_KEYS = {
    "schema",
    "status",
    "query_plan_sha256",
    "query_count",
    "complete_query_count",
    "failed_query_count",
    "pending_query_count",
    "circuit_open",
    "urls_with_captures",
    "publication",
    "redistribution",
    "replay_authorized",
    "results",
}
_RESULT_KEYS = {
    *_QUERY_KEYS,
    "status",
    "retrieved_at",
    "record_count",
    "records",
    "request_url",
    "response_body_filename",
    "response_byte_count",
    "response_sha256",
}
_SELECTION_KEYS = {
    "schema",
    "status",
    "source_cdx_sha256",
    "completion_candidate_sha256",
    "queried_slug_count",
    "selected_slug_count",
    "json_count",
    "html_fallback_count",
    "no_capture_slug_count",
    "no_capture_slugs",
    "records",
    "replay_authorized",
    "publication",
    "redistribution",
    "manifest_finalization_authorized",
}
_SELECTION_RECORD_KEYS = {
    "canonical_slug",
    "media_kind",
    "source_url",
    "archive_timestamp",
    "archive_digest",
    "statuscode",
    "length",
    "selection_reason",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} is not a JSON object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} fields do not match the independent contract")


def _default_authority(parsed: SplitResult) -> bool:
    try:
        port = parsed.port
    except ValueError:
        return False
    expected_port = 80 if parsed.scheme == "http" else 443
    return parsed.username is None and parsed.password is None and port in {None, expected_port}


def _canonical_url(slug: str, media_kind: str) -> str:
    suffix = ".json" if media_kind == "json" else ""
    return f"https://www.righttoknow.org.au/request/{slug}{suffix}"


def _validate_identity(value: Mapping[str, Any], label: str) -> tuple[str, str, str]:
    slug = value.get("canonical_slug")
    media_kind = value.get("media_kind")
    exact_url = value.get("exact_url")
    if not isinstance(slug, str) or _SLUG.fullmatch(slug) is None:
        raise ValueError(f"{label} has an invalid canonical slug")
    if media_kind not in {"json", "html"}:
        raise ValueError(f"{label} has an invalid media kind")
    expected_url = _canonical_url(slug, media_kind)
    if exact_url != expected_url:
        raise ValueError(f"{label} escaped its exact canonical URL")
    return slug, media_kind, expected_url


def _validate_source_url(value: object, expected_url: str, label: str) -> None:
    actual = urlsplit(str(value or ""))
    expected = urlsplit(expected_url)
    if (
        actual.scheme not in {"http", "https"}
        or not _default_authority(actual)
        or (actual.hostname or "").lower() != (expected.hostname or "").lower()
        or actual.path != expected.path
        or actual.query
        or actual.fragment
    ):
        raise ValueError(f"{label} escaped its exact canonical URL")


def _validate_rows(
    rows: object,
    *,
    expected_url: str,
    label: str,
) -> list[list[str]]:
    if not isinstance(rows, list):
        raise ValueError(f"{label} rows are not an array")
    validated: list[list[str]] = []
    for row in rows:
        if (
            not isinstance(row, list)
            or len(row) != len(CDX_HEADER)
            or not all(isinstance(item, str) for item in row)
        ):
            raise ValueError(f"{label} contains a malformed CDX row")
        typed_row = cast("list[str]", row)
        _validate_source_url(typed_row[0], expected_url, label)
        if _TIMESTAMP.fullmatch(typed_row[1]) is None:
            raise ValueError(f"{label} contains an invalid capture timestamp")
        if not typed_row[2]:
            raise ValueError(f"{label} contains an empty capture digest")
        if typed_row[3] != "200":
            raise ValueError(f"{label} contains a capture without statuscode 200")
        if _LENGTH.fullmatch(typed_row[4]) is None:
            raise ValueError(f"{label} contains an invalid capture length")
        validated.append(typed_row)
    return validated


def _validate_request_url(value: object, expected_url: str) -> None:
    parsed = urlsplit(str(value or ""))
    expected_parameters = {
        "url": [expected_url],
        "matchType": ["exact"],
        "output": ["json"],
        "fl": [",".join(CDX_HEADER)],
        "filter": ["statuscode:200"],
    }
    if (
        parsed.scheme != "https"
        or not _default_authority(parsed)
        or (parsed.hostname or "").lower() != "web.archive.org"
        or parsed.path != "/cdx/search/cdx"
        or parsed.fragment
        or parse_qs(parsed.query, keep_blank_values=True) != expected_parameters
    ):
        raise ValueError("result CDX request parameter multimap is not exact")


def _response_body(
    root: Path,
    result: Mapping[str, Any],
    *,
    slug: str,
    media_kind: str,
    expected_url: str,
) -> list[list[str]]:
    filename = result.get("response_body_filename")
    expected_filename = f"{slug}.{media_kind}.json"
    if not isinstance(filename, str) or filename != expected_filename:
        raise ValueError("result response-body path is not exact")
    path = root / filename
    resolved_root = root.resolve()
    if (
        path.is_symlink()
        or not path.is_file()
        or path.resolve(strict=False).parent != resolved_root
    ):
        raise ValueError("result response-body path escaped its approved root")
    body = path.read_bytes()
    if (
        type(result.get("response_byte_count")) is not int
        or result["response_byte_count"] != len(body)
        or not isinstance(result.get("response_sha256"), str)
        or _SHA256.fullmatch(result["response_sha256"]) is None
        or hashlib.sha256(body).hexdigest() != result["response_sha256"]
    ):
        raise ValueError("result response body bytes or SHA-256 mismatch")
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("result response body is not valid JSON") from error
    if not isinstance(payload, list) or not payload or payload[0] != CDX_HEADER:
        raise ValueError("result response body CDX header mismatch")
    return _validate_rows(payload[1:], expected_url=expected_url, label="response body")


def _validate_plan(plan_path: Path) -> dict[tuple[str, str], str]:
    if _sha256(plan_path) != PINNED_QUERY_PLAN_SHA256:
        raise ValueError("pinned query-plan SHA-256 mismatch")
    plan = _object(plan_path, "query plan")
    _exact_keys(plan, _PLAN_KEYS, "query plan")
    if (
        plan.get("schema") != "fyi-archive.au-rtk-canonical-cdx-query-plan.v1"
        or plan.get("source_cdx_sha256") != PINNED_SOURCE_CDX_SHA256
        or plan.get("missing_slug_count") != EXPECTED_SLUG_COUNT
        or plan.get("query_count") != EXPECTED_QUERY_COUNT
        or not isinstance(plan.get("queries"), list)
        or len(plan["queries"]) != EXPECTED_QUERY_COUNT
    ):
        raise ValueError("query plan is not pinned to the approved source and population")
    queries: dict[tuple[str, str], str] = {}
    slugs: set[str] = set()
    for query in plan["queries"]:
        if not isinstance(query, dict):
            raise ValueError("query plan contains a non-object query")
        _exact_keys(query, _QUERY_KEYS, "query")
        slug, media_kind, exact_url = _validate_identity(query, "query")
        identity = (slug, media_kind)
        if identity in queries:
            raise ValueError("query plan contains duplicate query membership")
        queries[identity] = exact_url
        slugs.add(slug)
    expected_membership = {(slug, media_kind) for slug in slugs for media_kind in ("json", "html")}
    if len(slugs) != EXPECTED_SLUG_COUNT or set(queries) != expected_membership:
        raise ValueError("query plan does not contain exactly two media kinds per slug")
    return queries


def _validate_candidate(
    candidate_path: Path,
    *,
    queries: Mapping[tuple[str, str], str],
    response_bodies_root: Path,
) -> dict[tuple[str, str], list[list[str]]]:
    candidate = _object(candidate_path, "completion candidate")
    _exact_keys(candidate, _CANDIDATE_KEYS, "completion candidate")
    if (
        candidate.get("schema") != "fyi-archive.au-rtk-canonical-cdx-completion-candidate.v1"
        or candidate.get("status") != "candidate_pending_replay_approval"
        or candidate.get("query_plan_sha256") != PINNED_QUERY_PLAN_SHA256
        or candidate.get("query_count") != EXPECTED_QUERY_COUNT
        or candidate.get("complete_query_count") != EXPECTED_QUERY_COUNT
        or candidate.get("failed_query_count") != 0
        or candidate.get("pending_query_count") != 0
        or candidate.get("circuit_open") is not False
    ):
        raise ValueError("completion candidate is incomplete or not pinned")
    for field in ("publication", "redistribution", "replay_authorized"):
        if candidate.get(field) is not False:
            raise ValueError(f"completion candidate {field} must be false")
    results = candidate.get("results")
    if not isinstance(results, list) or len(results) != EXPECTED_QUERY_COUNT:
        raise ValueError("completion candidate does not contain exactly 1,716 results")
    validated: dict[tuple[str, str], list[list[str]]] = {}
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("completion candidate contains a non-object result")
        _exact_keys(result, _RESULT_KEYS, "completion result")
        slug, media_kind, expected_url = _validate_identity(result, "completion result")
        identity = (slug, media_kind)
        if identity not in queries or expected_url != queries[identity] or identity in validated:
            raise ValueError("completion result membership does not exactly match the plan")
        if result.get("status") != "complete":
            raise ValueError("completion result is not complete")
        _validate_request_url(result.get("request_url"), expected_url)
        body_rows = _response_body(
            response_bodies_root,
            result,
            slug=slug,
            media_kind=media_kind,
            expected_url=expected_url,
        )
        candidate_rows = _validate_rows(
            result.get("records"),
            expected_url=expected_url,
            label="completion result",
        )
        if body_rows != candidate_rows:
            raise ValueError("result response body rows do not match candidate rows")
        if type(result.get("record_count")) is not int or result["record_count"] != len(
            candidate_rows
        ):
            raise ValueError("completion result record count mismatch")
        validated[identity] = candidate_rows
    if set(validated) != set(queries):
        raise ValueError("completion results do not exactly cover the query plan")
    if type(candidate.get("urls_with_captures")) is not int or candidate[
        "urls_with_captures"
    ] != sum(bool(rows) for rows in validated.values()):
        raise ValueError("completion candidate capture count mismatch")
    return validated


def _expected_selection(
    rows: Mapping[tuple[str, str], list[list[str]]],
) -> tuple[list[dict[str, str]], list[str]]:
    records: list[dict[str, str]] = []
    no_capture: list[str] = []
    slugs = sorted({slug for slug, _ in rows})
    for slug in slugs:
        json_rows = rows[(slug, "json")]
        html_rows = rows[(slug, "html")]
        media_kind = "json" if json_rows else "html"
        choices = json_rows or html_rows
        if not choices:
            no_capture.append(slug)
            continue
        latest = max(choices, key=lambda row: row[1])
        records.append(
            {
                "canonical_slug": slug,
                "media_kind": media_kind,
                "source_url": latest[0],
                "archive_timestamp": latest[1],
                "archive_digest": latest[2],
                "statuscode": latest[3],
                "length": latest[4],
                "selection_reason": (
                    "latest_successful_canonical_json"
                    if media_kind == "json"
                    else "latest_successful_canonical_html_fallback"
                ),
            }
        )
    return records, no_capture


def _validate_selection(
    selection_path: Path,
    *,
    candidate_sha256: str,
    expected_records: list[dict[str, str]],
    expected_no_capture: list[str],
) -> dict[str, Any]:
    selection = _object(selection_path, "replay selection")
    _exact_keys(selection, _SELECTION_KEYS, "replay selection")
    if (
        selection.get("schema") != "fyi-archive.au-rtk-canonical-completion-replay-selection.v1"
        or selection.get("status") != "candidate_pending_replay_approval"
        or selection.get("source_cdx_sha256") != PINNED_SOURCE_CDX_SHA256
        or selection.get("completion_candidate_sha256") != candidate_sha256
        or selection.get("queried_slug_count") != EXPECTED_SLUG_COUNT
    ):
        raise ValueError("selection or candidate SHA-256 binding is invalid")
    for field in (
        "replay_authorized",
        "publication",
        "redistribution",
        "manifest_finalization_authorized",
    ):
        if selection.get(field) is not False:
            raise ValueError(f"replay selection {field} must be false")
    records = selection.get("records")
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError("replay selection records are malformed")
    for record in records:
        _exact_keys(record, _SELECTION_RECORD_KEYS, "replay selection record")
    if records != expected_records:
        raise ValueError("replay selection records are not the latest JSON-preferred selection")
    no_capture = selection.get("no_capture_slugs")
    if no_capture != expected_no_capture:
        raise ValueError("replay selection no-capture membership is not exact")
    expected_json = sum(record["media_kind"] == "json" for record in expected_records)
    expected_html = len(expected_records) - expected_json
    if (
        selection.get("selected_slug_count") != len(expected_records)
        or selection.get("json_count") != expected_json
        or selection.get("html_fallback_count") != expected_html
        or selection.get("no_capture_slug_count") != len(expected_no_capture)
        or len(expected_records) + len(expected_no_capture) != EXPECTED_SLUG_COUNT
    ):
        raise ValueError("replay selection counts are inconsistent")
    return selection


def validate_completion_candidate(
    candidate_path: Path,
    *,
    selection_path: Path,
    query_plan_path: Path,
    response_bodies_root: Path,
    expected_candidate_sha256: str | None = None,
    expected_selection_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate a complete, non-final AU RightToKnow canonical CDX packet."""
    queries = _validate_plan(query_plan_path)
    rows = _validate_candidate(
        candidate_path,
        queries=queries,
        response_bodies_root=response_bodies_root,
    )
    candidate_sha256 = _sha256(candidate_path)
    expected_records, expected_no_capture = _expected_selection(rows)
    _validate_selection(
        selection_path,
        candidate_sha256=candidate_sha256,
        expected_records=expected_records,
        expected_no_capture=expected_no_capture,
    )
    selection_sha256 = _sha256(selection_path)
    if expected_candidate_sha256 is not None and (
        _SHA256.fullmatch(expected_candidate_sha256) is None
        or expected_candidate_sha256 != candidate_sha256
    ):
        raise ValueError("expected candidate SHA-256 mismatch")
    if expected_selection_sha256 is not None and (
        _SHA256.fullmatch(expected_selection_sha256) is None
        or expected_selection_sha256 != selection_sha256
    ):
        raise ValueError("expected selection SHA-256 mismatch")
    return {
        "ok": True,
        "source_cdx_sha256": PINNED_SOURCE_CDX_SHA256,
        "query_plan_sha256": PINNED_QUERY_PLAN_SHA256,
        "candidate_sha256": candidate_sha256,
        "selection_sha256": selection_sha256,
        "query_count": len(rows),
        "slug_count": EXPECTED_SLUG_COUNT,
        "selected_slug_count": len(expected_records),
        "no_capture_slug_count": len(expected_no_capture),
        "replay_authorized": False,
        "publication": False,
        "redistribution": False,
        "manifest_finalization_authorized": False,
    }
