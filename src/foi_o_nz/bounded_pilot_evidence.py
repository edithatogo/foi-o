"""Fail-closed verification for the local bounded-pilot evidence census."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any


def _digest_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_bounded_pilot_evidence(manifest_path: Path, snapshot_roots: dict[str, Path]) -> None:
    """Recompute local source, span, event/DOM, and attachment census pins."""
    manifest = _object(manifest_path)
    if manifest["context_presentation_allowed"] or manifest["execution_allowed"]:
        raise ValueError("evidence census cannot authorize presentation or execution")
    if set(snapshot_roots) != set(manifest["request_ids"]):
        raise ValueError("snapshot roots do not match approved request membership")
    for record in manifest["records"]:
        request_id = record["request_id"]
        root = snapshot_roots[request_id].resolve()
        source_manifest = _object(root / "manifest.json")
        if (
            _digest_bytes((root / "manifest.json").read_bytes())
            != record["snapshot_manifest_sha256"]
        ):
            raise ValueError(f"{request_id}: snapshot manifest mismatch")
        request_path = root / "content/request.json"
        page_path = root / "content/page.html"
        request_bytes = request_path.read_bytes()
        page_bytes = page_path.read_bytes()
        if _digest_bytes(request_bytes) != record["request_json_sha256"]:
            raise ValueError(f"{request_id}: request digest mismatch")
        if _digest_bytes(page_bytes) != record["page_html_sha256"]:
            raise ValueError(f"{request_id}: page digest mismatch")
        request_text = request_bytes.decode("utf-8", errors="strict")
        page_text = page_bytes.decode("utf-8", errors="strict")
        raw_state = record["raw_state"]
        raw_slice = request_text[raw_state["span"]["start"] : raw_state["span"]["end"]]
        if _digest_bytes(raw_slice.encode()) != raw_state["text_sha256"]:
            raise ValueError(f"{request_id}: raw-state span mismatch")
        request = json.loads(request_text)
        for block in record["correspondence"]["blocks"]:
            event_index = int(block["event_pointer"].rsplit("/", 1)[1])
            event = request["info_request_events"][event_index]
            message_key = f"{block['direction']}_message_id"
            if block["element_id"] != f"{block['direction']}-{event[message_key]}":
                raise ValueError(f"{request_id}: event/DOM join mismatch")
            for prefix in ("wrapper", "text"):
                span = block[f"{prefix}_span"]
                fragment = page_text[span["start"] : span["end"]]
                if _digest_bytes(fragment.encode()) != block[f"{prefix}_sha256"]:
                    raise ValueError(f"{request_id}: {prefix} span mismatch")
        inventory_path = root / "content/attachments.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        attachments = record["attachments"]
        if _digest_bytes(inventory_path.read_bytes()) != attachments["inventory_sha256"]:
            raise ValueError(f"{request_id}: attachment inventory mismatch")
        if len(inventory) != len(attachments["files"]):
            raise ValueError(f"{request_id}: attachment census mismatch")
        declared = {item["path"]: item for item in source_manifest["artifacts"]}
        for index, item in enumerate(attachments["files"]):
            if item["inventory_pointer"] != f"/{index}":
                raise ValueError(f"{request_id}: attachment pointer mismatch")
            artifact = declared[item["relative_path"]]
            path = (root / item["relative_path"]).resolve()
            if root not in path.parents or path.is_symlink():
                raise ValueError(f"{request_id}: unsafe attachment path")
            if (
                _digest_bytes(path.read_bytes()) != item["sha256"]
                or artifact["sha256"] != item["sha256"]
                or path.stat().st_size != item["size"]
            ):
                raise ValueError(f"{request_id}: attachment artifact mismatch")
