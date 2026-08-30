"""Generic public governance metadata and provenance reference contracts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from foi_o_nz.validation import validate_json_schema

ROOT = Path(__file__).parents[2]
GENERIC_GOVERNANCE_SCHEMA = ROOT / "schemas/json/generic-governance-metadata.schema.json"
PROVENANCE_REFERENCE_SCHEMA = ROOT / "schemas/json/provenance-reference.schema.json"

_INVALID_PATH_PATTERNS = re.compile(
    r"^/|^(?:private/tmp|tmp|opt|Users)/|/(?:tmp|opt|Users|private)/|\b(?:35076|11872)\b"
)


def validate_generic_governance_metadata(
    metadata_path_or_dict: Path | dict[str, Any],
) -> dict[str, Any]:
    """Validate generic governance metadata against schema and public-safety constraints."""
    if isinstance(metadata_path_or_dict, Path):
        schema_result = validate_json_schema(metadata_path_or_dict, GENERIC_GOVERNANCE_SCHEMA)
        if schema_result.errors:
            raise ValueError(f"schema validation failed: {'; '.join(schema_result.errors)}")
        data = json.loads(metadata_path_or_dict.read_text(encoding="utf-8"))
    else:
        data = metadata_path_or_dict

    for pin in data.get("provenance_pins", []):
        rel_path = pin.get("relative_path", "")
        if _INVALID_PATH_PATTERNS.search(rel_path):
            raise ValueError(
                f"invalid provenance path contains restricted location or case ID: {rel_path}"
            )
        sha = pin.get("sha256", "")
        if not re.fullmatch(r"[a-f0-9]{64}", sha):
            raise ValueError(f"invalid SHA-256 pin: {sha}")

    return {"ok": True, "contract_id": data.get("contract_id")}


def validate_provenance_reference(
    reference_path_or_dict: Path | dict[str, Any],
) -> dict[str, Any]:
    """Validate opaque provenance reference against schema and public-safety constraints."""
    if isinstance(reference_path_or_dict, Path):
        schema_result = validate_json_schema(reference_path_or_dict, PROVENANCE_REFERENCE_SCHEMA)
        if schema_result.errors:
            raise ValueError(f"schema validation failed: {'; '.join(schema_result.errors)}")
        data = json.loads(reference_path_or_dict.read_text(encoding="utf-8"))
    else:
        data = reference_path_or_dict

    rel_path = data.get("relative_path", "")
    if _INVALID_PATH_PATTERNS.search(rel_path):
        raise ValueError(
            f"invalid provenance path contains restricted location or case ID: {rel_path}"
        )
    sha = data.get("content_sha256", "")
    if not re.fullmatch(r"[a-f0-9]{64}", sha):
        raise ValueError(f"invalid content SHA-256: {sha}")

    return {"ok": True, "reference_id": data.get("reference_id")}


def is_public_safe_manifest(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    """Audit a release manifest or metadata structure for restricted path leakage or case IDs."""
    errors: list[str] = []
    manifest_str = json.dumps(manifest)

    # Check for direct presence of restricted path keywords
    if "/private/tmp" in manifest_str or "/tmp/" in manifest_str:
        errors.append("manifest contains temporary path reference (/tmp or /private/tmp)")
    if "/opt/homebrew" in manifest_str or "/opt/" in manifest_str:
        errors.append("manifest contains local package-manager path reference (/opt)")
    if "/Users/" in manifest_str:
        errors.append("manifest contains user home directory path reference (/Users/)")

    # Check files list if present
    files = manifest.get("files", [])
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict):
                path = item.get("path", "")
                if _INVALID_PATH_PATTERNS.search(path):
                    errors.append(f"restricted path pattern detected in file entry: {path}")

    return len(errors) == 0, errors


def build_public_governance_provenance_map(
    repo_root: Path, file_paths: list[str]
) -> list[dict[str, Any]]:
    """Build opaque, hash-pinned provenance reference entries for a list of repo files."""
    results: list[dict[str, Any]] = []
    for rel_path in sorted(file_paths):
        if _INVALID_PATH_PATTERNS.search(rel_path):
            raise ValueError(f"file path violates public governance safety: {rel_path}")
        target = repo_root / rel_path
        if not target.is_file():
            raise FileNotFoundError(f"target file not found: {target}")
        sha = hashlib.sha256(target.read_bytes()).hexdigest()
        sanitized_id = re.sub(r"[^a-z0-9-]", "-", rel_path.lower().replace(".", "-"))
        results.append(
            {
                "schema_version": "foi-o.provenance-reference.v0.1.0",
                "reference_id": f"ref-{sanitized_id}",
                "relative_path": rel_path,
                "content_sha256": sha,
                "classification": "public_asset",
                "redacted": False,
            }
        )
    return results
