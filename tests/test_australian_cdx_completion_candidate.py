from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

import pytest

from foi_o_nz import australian_cdx_completion_candidate as validator
from scripts import validate_australian_cdx_completion_candidate as cli


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _fixture(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path, Path]:
    body_root = tmp_path / "response-bodies"
    body_root.mkdir()
    queries = []
    results = []
    selected = []
    no_capture = []
    for index in range(validator.EXPECTED_SLUG_COUNT):
        slug = str(index)
        options = {}
        for media_kind, suffix in (("json", ".json"), ("html", "")):
            exact_url = f"https://www.righttoknow.org.au/request/{slug}{suffix}"
            query = {
                "canonical_slug": slug,
                "media_kind": media_kind,
                "exact_url": exact_url,
            }
            queries.append(query)
            rows = []
            if index == 0:
                rows = [
                    [exact_url, "20200101000000", f"{media_kind}-old", "200", "1"],
                    [exact_url, "20210101000000", f"{media_kind}-new", "200", "2"],
                ]
                options[media_kind] = rows[-1]
            elif index == 1 and media_kind == "html":
                rows = [[exact_url, "20220101000000", "html-only", "200", "3"]]
                options[media_kind] = rows[-1]
            body_path = body_root / f"{slug}.{media_kind}.json"
            _write_json(body_path, [validator.CDX_HEADER, *rows])
            request_url = "https://web.archive.org/cdx/search/cdx?" + urlencode([
                ("url", exact_url),
                ("matchType", "exact"),
                ("output", "json"),
                ("fl", ",".join(validator.CDX_HEADER)),
                ("filter", "statuscode:200"),
            ])
            results.append({
                **query,
                "status": "complete",
                "retrieved_at": "2026-07-27T00:00:00+00:00",
                "record_count": len(rows),
                "records": rows,
                "request_url": request_url,
                "response_body_filename": body_path.name,
                "response_byte_count": body_path.stat().st_size,
                "response_sha256": _sha256(body_path),
            })
        chosen_kind = "json" if "json" in options else "html"
        if chosen_kind in options:
            row = options[chosen_kind]
            selected.append({
                "canonical_slug": slug,
                "media_kind": chosen_kind,
                "source_url": row[0],
                "archive_timestamp": row[1],
                "archive_digest": row[2],
                "statuscode": row[3],
                "length": row[4],
                "selection_reason": (
                    "latest_successful_canonical_json"
                    if chosen_kind == "json"
                    else "latest_successful_canonical_html_fallback"
                ),
            })
        else:
            no_capture.append(slug)

    plan = {
        "schema": "fyi-archive.au-rtk-canonical-cdx-query-plan.v1",
        "source_cdx_sha256": validator.PINNED_SOURCE_CDX_SHA256,
        "missing_slug_count": validator.EXPECTED_SLUG_COUNT,
        "query_count": validator.EXPECTED_QUERY_COUNT,
        "queries": queries,
    }
    plan_path = tmp_path / "query-plan.json"
    _write_json(plan_path, plan)
    monkeypatch.setattr(validator, "PINNED_QUERY_PLAN_SHA256", _sha256(plan_path))

    candidate = {
        "schema": "fyi-archive.au-rtk-canonical-cdx-completion-candidate.v1",
        "status": "candidate_pending_replay_approval",
        "query_plan_sha256": _sha256(plan_path),
        "query_count": validator.EXPECTED_QUERY_COUNT,
        "complete_query_count": validator.EXPECTED_QUERY_COUNT,
        "failed_query_count": 0,
        "pending_query_count": 0,
        "circuit_open": False,
        "urls_with_captures": 3,
        "publication": False,
        "redistribution": False,
        "replay_authorized": False,
        "results": results,
    }
    candidate_path = tmp_path / "completion-candidate.json"
    _write_json(candidate_path, candidate)
    selection = {
        "schema": "fyi-archive.au-rtk-canonical-completion-replay-selection.v1",
        "status": "candidate_pending_replay_approval",
        "source_cdx_sha256": validator.PINNED_SOURCE_CDX_SHA256,
        "completion_candidate_sha256": _sha256(candidate_path),
        "queried_slug_count": validator.EXPECTED_SLUG_COUNT,
        "selected_slug_count": len(selected),
        "json_count": 1,
        "html_fallback_count": 1,
        "no_capture_slug_count": len(no_capture),
        "no_capture_slugs": sorted(no_capture),
        "records": selected,
        "replay_authorized": False,
        "publication": False,
        "redistribution": False,
        "manifest_finalization_authorized": False,
    }
    selection_path = tmp_path / "completion-replay-selection.candidate.json"
    _write_json(selection_path, selection)
    return candidate_path, selection_path, plan_path, body_root


def _validate(paths: tuple[Path, Path, Path, Path]) -> dict[str, object]:
    candidate, selection, plan, bodies = paths
    return validator.validate_completion_candidate(
        candidate,
        selection_path=selection,
        query_plan_path=plan,
        response_bodies_root=bodies,
    )


def test_validates_complete_candidate_and_non_final_selection(tmp_path, monkeypatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    result = _validate(paths)
    assert result["ok"] is True
    assert result["query_count"] == 1_716
    assert result["slug_count"] == 858
    assert result["selected_slug_count"] == 2
    assert result["no_capture_slug_count"] == 856
    assert result["candidate_sha256"] == _sha256(paths[0])
    assert result["selection_sha256"] == _sha256(paths[1])


def test_cli_emits_hash_pinned_validation_result(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    candidate, selection, plan, bodies = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate-australian-cdx-completion-candidate",
            str(candidate),
            "--selection",
            str(selection),
            "--query-plan",
            str(plan),
            "--response-bodies-root",
            str(bodies),
            "--candidate-sha256",
            _sha256(candidate),
            "--selection-sha256",
            _sha256(selection),
        ],
    )
    assert cli.main() == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_rejects_changed_request_parameter_multimap(tmp_path, monkeypatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    payload = json.loads(paths[0].read_text())
    payload["results"][0]["request_url"] += "&filter=mimetype:application/json"
    _write_json(paths[0], payload)
    with pytest.raises(ValueError, match="CDX request parameter multimap"):
        _validate(paths)


def test_rejects_response_body_escape(tmp_path, monkeypatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    payload = json.loads(paths[0].read_text())
    payload["results"][0]["response_body_filename"] = "../outside.json"
    _write_json(paths[0], payload)
    with pytest.raises(ValueError, match="response-body path"):
        _validate(paths)


def test_rejects_changed_response_body_rows(tmp_path, monkeypatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    (paths[3] / "0.json.json").write_text("[]")
    with pytest.raises(ValueError, match="response body"):
        _validate(paths)


def test_accepts_empty_cdx_array_for_no_capture_exact_url(tmp_path, monkeypatch) -> None:
    candidate, selection, _plan, bodies = _fixture(tmp_path, monkeypatch)
    payload = json.loads(candidate.read_text())
    result = next(
        row
        for row in payload["results"]
        if row["canonical_slug"] == "2" and row["media_kind"] == "json"
    )
    body = bodies / result["response_body_filename"]
    body.write_text("[]")
    result["response_byte_count"] = body.stat().st_size
    result["response_sha256"] = _sha256(body)
    _write_json(candidate, payload)
    selection_payload = json.loads(selection.read_text())
    selection_payload["completion_candidate_sha256"] = _sha256(candidate)
    _write_json(selection, selection_payload)
    assert _validate((candidate, selection, _plan, bodies))["ok"] is True


def test_rejects_non_200_capture_row(tmp_path, monkeypatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    payload = json.loads(paths[0].read_text())
    payload["results"][0]["records"][0][3] = "302"
    _write_json(paths[0], payload)
    with pytest.raises(ValueError, match="statuscode 200"):
        _validate(paths)


def test_rejects_html_when_json_capture_exists(tmp_path, monkeypatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    selection = json.loads(paths[1].read_text())
    selection["records"][0] = {
        **selection["records"][0],
        "media_kind": "html",
        "source_url": "https://www.righttoknow.org.au/request/0",
        "archive_digest": "html-new",
        "selection_reason": "latest_successful_canonical_html_fallback",
    }
    _write_json(paths[1], selection)
    with pytest.raises(ValueError, match="selection records"):
        _validate(paths)


def test_rejects_inexact_no_capture_membership(tmp_path, monkeypatch) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    selection = json.loads(paths[1].read_text())
    selection["no_capture_slugs"][0] = "0"
    _write_json(paths[1], selection)
    with pytest.raises(ValueError, match="no-capture membership"):
        _validate(paths)


@pytest.mark.parametrize(
    ("document_index", "field"),
    [
        (0, "publication"),
        (0, "redistribution"),
        (0, "replay_authorized"),
        (1, "publication"),
        (1, "redistribution"),
        (1, "replay_authorized"),
        (1, "manifest_finalization_authorized"),
    ],
)
def test_rejects_any_authorization_boolean_true(
    tmp_path,
    monkeypatch,
    document_index,
    field,
) -> None:
    paths = _fixture(tmp_path, monkeypatch)
    path = paths[document_index]
    payload = json.loads(path.read_text())
    payload[field] = True
    _write_json(path, payload)
    with pytest.raises(ValueError, match=r"must be false|candidate SHA-256"):
        _validate(paths)
