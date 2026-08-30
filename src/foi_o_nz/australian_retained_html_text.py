"""Validate bounded AU-CTH text extracted from already retained HTML snapshots."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from foi_o_nz.australian_immutable_manifest import validate_manifest

MANIFEST_FILE_SHA256 = "c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393"
CLASSIFICATION_SHA256 = "98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab"
EXPECTED_HTML_COUNT = 517
_WHITESPACE = re.compile(r"\s+")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _jsonl(path: Path) -> list[dict[str, Any]]:
    values = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_number} is not an object")
        values.append(value)
    return values


class _CorrespondenceText(HTMLParser):
    """Collect human-readable text solely from correspondence-text containers."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._div_depth = 0
        self._active_depth: int | None = None
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "div":
            classes = dict(attrs).get("class", "") or ""
            if self._active_depth is None and "correspondence_text" in classes.split():
                self._active_depth = self._div_depth
            self._div_depth += 1

    def handle_data(self, data: str) -> None:
        if self._active_depth is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "div":
            self._div_depth -= 1
            if self._active_depth == self._div_depth:
                self._active_depth = None


def _extract(html: str) -> str:
    parser = _CorrespondenceText()
    parser.feed(html)
    parser.close()
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFC", " ".join(parser.parts))).strip()


def _bounded(root: Path, name: str) -> Path:
    path = root / name
    if (
        Path(name).name != name
        or path.is_symlink()
        or path.resolve(strict=False).parent != root.resolve()
    ):
        raise ValueError("artifact path escaped its approved root")
    return path


def build_candidate(
    *,
    manifest_path: Path,
    classification_summary: Path,
    replay_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Extract a non-final text candidate from the approved retained HTML subset."""
    if _sha256(manifest_path) != MANIFEST_FILE_SHA256:
        raise ValueError("immutable manifest stored-file SHA-256 mismatch")
    manifest = validate_manifest(manifest_path)
    if _sha256(classification_summary) != CLASSIFICATION_SHA256:
        raise ValueError("classification-summary SHA-256 mismatch")
    summary = json.loads(classification_summary.read_text(encoding="utf-8"))
    candidate_root = classification_summary.parent
    cth = summary["jurisdiction_outputs"]["AU-CTH"]
    cth_path = _bounded(candidate_root, cth["path"])
    if _sha256(cth_path) != cth["sha256"]:
        raise ValueError("AU-CTH classification artifact SHA-256 mismatch")
    index_meta = summary["replay_index"]
    index_path = _bounded(candidate_root, index_meta["path"])
    if _sha256(index_path) != index_meta["sha256"]:
        raise ValueError("replay-index SHA-256 mismatch")
    index = {row["canonical_slug"]: row for row in _jsonl(index_path)}
    records = [row for row in _jsonl(cth_path) if row.get("media_kind") == "html"]
    if len(records) != EXPECTED_HTML_COUNT:
        raise ValueError("approved AU-CTH retained HTML membership count mismatch")

    text_root = output_root / "text"
    text_root.mkdir(parents=True, exist_ok=True)
    output_rows: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda row: str(row["canonical_slug"])):
        slug = str(record["canonical_slug"])
        replay = index.get(slug)
        if replay is None or replay.get("raw_sha256") != record.get("raw_sha256"):
            raise ValueError("HTML classification membership escaped replay index")
        raw_path = _bounded(replay_root / "raw", str(replay["raw_filename"]))
        raw = raw_path.read_bytes()
        if _sha256_bytes(raw) != record["raw_sha256"]:
            raise ValueError("retained HTML raw SHA-256 mismatch")
        text = _extract(raw.decode("utf-8"))
        filename = f"{slug}.txt"
        if text:
            text_path = _bounded(text_root, filename)
            text_path.write_text(text + "\n", encoding="utf-8")
            text_bytes = text_path.read_bytes()
            output_rows.append({
                "canonical_slug": slug,
                "raw_sha256": record["raw_sha256"],
                "text_filename": filename,
                "text_sha256": _sha256_bytes(text_bytes),
                "text_byte_count": len(text_bytes),
                "source_spans": [
                    {
                        "start": 0,
                        "end": len(text),
                        "coordinate_system": "utf8_character_half_open",
                    }
                ],
                "accessibility": "accessible",
                "rights_disposition": "restricted_local_non_redistributable",
                "rights_eligible_for_empirical_use": False,
            })
        else:
            output_rows.append({
                "canonical_slug": slug,
                "raw_sha256": record["raw_sha256"],
                "text_filename": None,
                "text_sha256": None,
                "text_byte_count": 0,
                "source_spans": [],
                "accessibility": "missing_source_text",
                "rights_disposition": "restricted_local_non_redistributable",
                "rights_eligible_for_empirical_use": False,
            })
    jsonl_path = output_root / "retained-html-text.candidate.jsonl"
    jsonl_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8"
    )
    summary_path = output_root / "summary.json"
    value = {
        "schema": "foi-o.au-cth-retained-html-text-candidate.v1",
        "status": "candidate_text_validation_not_empirical",
        "immutable_manifest_sha256": manifest["manifest_sha256"],
        "classification_summary_sha256": CLASSIFICATION_SHA256,
        "approved_html_record_count": EXPECTED_HTML_COUNT,
        "accessible_text_record_count": sum(
            row["accessibility"] == "accessible" for row in output_rows
        ),
        "missing_source_text_record_count": sum(
            row["accessibility"] == "missing_source_text" for row in output_rows
        ),
        "candidate_jsonl_sha256": _sha256(jsonl_path),
        "network_accessed": False,
        "replay_performed": False,
        "empirical_freeze_authorized": False,
        "sampling_authorized": False,
        "annotation_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
    }
    summary_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def validate_candidate(
    summary_path: Path,
    *,
    text_root: Path,
    manifest_path: Path,
    classification_summary: Path,
    replay_root: Path,
) -> dict[str, Any]:
    """Verify a retained-HTML candidate report without converting it to a frame."""
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        summary.get("schema") != "foi-o.au-cth-retained-html-text-candidate.v1"
        or summary.get("status") != "candidate_text_validation_not_empirical"
        or summary.get("approved_html_record_count") != EXPECTED_HTML_COUNT
    ):
        raise ValueError("candidate summary is not the approved non-final operation")
    for key in (
        "network_accessed",
        "replay_performed",
        "empirical_freeze_authorized",
        "sampling_authorized",
        "annotation_authorized",
        "publication_authorized",
        "redistribution_authorized",
    ):
        if summary.get(key) is not False:
            raise ValueError("candidate summary crossed an unapproved boundary")
    jsonl_path = summary_path.parent / "retained-html-text.candidate.jsonl"
    rows = _jsonl(jsonl_path)
    if len(rows) != EXPECTED_HTML_COUNT or _sha256(jsonl_path) != summary.get(
        "candidate_jsonl_sha256"
    ):
        raise ValueError("candidate JSONL membership or SHA-256 mismatch")
    if _sha256(manifest_path) != MANIFEST_FILE_SHA256:
        raise ValueError("immutable manifest stored-file SHA-256 mismatch")
    if validate_manifest(manifest_path)["manifest_sha256"] != summary.get(
        "immutable_manifest_sha256"
    ):
        raise ValueError("immutable manifest self-pin mismatch")
    if _sha256(classification_summary) != CLASSIFICATION_SHA256:
        raise ValueError("classification-summary SHA-256 mismatch")
    classification = json.loads(classification_summary.read_text(encoding="utf-8"))
    candidate_root = classification_summary.parent
    cth_path = _bounded(candidate_root, classification["jurisdiction_outputs"]["AU-CTH"]["path"])
    index_path = _bounded(candidate_root, classification["replay_index"]["path"])
    index = {item["canonical_slug"]: item for item in _jsonl(index_path)}
    expected = {
        str(item["canonical_slug"]): item
        for item in _jsonl(cth_path)
        if item.get("media_kind") == "html"
    }
    actual = {str(item.get("canonical_slug")): item for item in rows}
    if len(actual) != len(rows) or set(actual) != set(expected):
        raise ValueError("candidate membership does not exactly match retained AU-CTH HTML")
    for slug, row in actual.items():
        source = expected[slug]
        replay = index.get(slug)
        if replay is None or row.get("raw_sha256") != source.get("raw_sha256"):
            raise ValueError("candidate raw provenance mismatch")
        raw = _bounded(replay_root / "raw", str(replay["raw_filename"])).read_bytes()
        if _sha256_bytes(raw) != row["raw_sha256"]:
            raise ValueError("retained raw HTML SHA-256 mismatch")
        if row["accessibility"] == "accessible":
            path = _bounded(text_root, str(row["text_filename"]))
            data = path.read_bytes()
            if _sha256_bytes(data) != row["text_sha256"] or row["text_byte_count"] != len(data):
                raise ValueError("extracted text artifact SHA-256 mismatch")
            text = data.decode("utf-8").rstrip("\n")
            if row["source_spans"] != [
                {"start": 0, "end": len(text), "coordinate_system": "utf8_character_half_open"}
            ]:
                raise ValueError("extracted text span is not exact")
            if text != _extract(raw.decode("utf-8")):
                raise ValueError("extracted text does not match retained HTML correspondence")
        if row["rights_eligible_for_empirical_use"] is not False:
            raise ValueError("candidate grants unapproved empirical rights")
    return {"ok": True, "record_count": len(rows), "summary_sha256": _sha256(summary_path)}
