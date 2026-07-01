"""Content-addressed storage helpers for FOI-O NZ artifacts.

The functions in this module intentionally use only the standard library plus
Pydantic. They provide small, auditable primitives for turning JSON/JSONL and
other repo artifacts into content-addressed records that can later be mirrored to
Hugging Face/Xet, OCI artifacts, IPFS-like stores, or a local CAS directory.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from hashlib import sha256
from mimetypes import guess_type
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.constants import CAS_MANIFEST_SCHEMA_VERSION
from foi_o_nz.encoding import dumps_json, loads_json
from foi_o_nz.io import iter_jsonl, write_json, write_jsonl


class CasEntry(BaseModel):
    """One content-addressed file or record entry."""

    model_config = ConfigDict(extra="forbid")

    uri: str
    sha256: str = Field(min_length=64, max_length=64)
    media_type: str
    byte_size: int = Field(ge=0)
    path: str | None = None
    source_path: str | None = None
    record_count: int | None = Field(default=None, ge=0)
    record_type: Literal["file", "json_record"] = "file"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CasManifest(BaseModel):
    """Content-addressed manifest for a set of artifacts."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.cas-manifest.v0.1.0"] = CAS_MANIFEST_SCHEMA_VERSION
    generated_at: datetime
    root_digest: str = Field(min_length=64, max_length=64)
    entry_count: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    entries: list[CasEntry]
    limitations: list[str] = Field(default_factory=list)


def canonical_record_bytes(record: dict[str, Any]) -> bytes:
    """Return canonical UTF-8 JSON bytes for one record."""
    return dumps_json(record, pretty=False, sort_keys=True).encode("utf-8")


def digest_bytes(data: bytes) -> str:
    """Return a SHA-256 hex digest."""
    return sha256(data).hexdigest()


def digest_file(path: Path) -> tuple[str, int]:
    """Hash a file using bounded chunks and return digest plus byte count."""
    hasher = sha256()
    byte_count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
            byte_count += len(chunk)
    return hasher.hexdigest(), byte_count


def infer_media_type(path: Path) -> str:
    """Infer a conservative media type from the path suffix."""
    if path.suffix == ".jsonl":
        return "application/x-ndjson"
    if path.suffix == ".jsonld":
        return "application/ld+json"
    guessed, _ = guess_type(str(path))
    return guessed or "application/octet-stream"


def count_jsonl_records(path: Path) -> int | None:
    """Count JSONL records, returning None for non-JSONL files."""
    if path.suffix != ".jsonl":
        return None
    return sum(1 for _ in iter_jsonl(path))


def build_file_entry(path: Path, *, base_dir: Path | None = None) -> CasEntry:
    """Build one CAS entry for a file."""
    digest, size = digest_file(path)
    rel = str(path.relative_to(base_dir)) if base_dir is not None and path.is_relative_to(base_dir) else str(path)
    return CasEntry(
        uri=f"sha256:{digest}",
        sha256=digest,
        media_type=infer_media_type(path),
        byte_size=size,
        path=rel,
        source_path=str(path),
        record_count=count_jsonl_records(path),
        record_type="file",
    )


def root_digest_for_entries(entries: Iterable[CasEntry]) -> str:
    """Return a deterministic root digest over entry digests and paths."""
    payload = [entry.model_dump(mode="json", exclude_none=True) for entry in entries]
    return digest_bytes(dumps_json(payload, pretty=False, sort_keys=True).encode("utf-8"))


def build_cas_manifest(paths: list[Path], *, base_dir: Path | None = None) -> CasManifest:
    """Build a CAS manifest for artifact paths."""
    entries = [build_file_entry(path, base_dir=base_dir) for path in sorted(paths, key=lambda value: str(value))]
    return CasManifest(
        generated_at=datetime.now(UTC),
        root_digest=root_digest_for_entries(entries),
        entry_count=len(entries),
        total_bytes=sum(entry.byte_size for entry in entries),
        entries=entries,
        limitations=[
            "Content addressing proves byte-level integrity only; it does not certify legal correctness.",
            "External storage publication, access controls, and retention policies are outside this manifest.",
        ],
    )


def write_cas_manifest(paths: list[Path], output: Path, *, base_dir: Path | None = None) -> dict[str, Any]:
    """Write a CAS manifest and return a compact summary."""
    manifest = build_cas_manifest(paths, base_dir=base_dir)
    write_json(output, manifest.model_dump(mode="json", exclude_none=True))
    return {
        "ok": True,
        "output": str(output),
        "entry_count": manifest.entry_count,
        "total_bytes": manifest.total_bytes,
        "root_digest": manifest.root_digest,
    }


def materialise_jsonl_cas(input_jsonl: Path, output_dir: Path, index_output: Path) -> dict[str, Any]:
    """Write each JSONL record as a content-addressed JSON file plus index JSONL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    index_records: list[dict[str, Any]] = []
    for sequence, record in enumerate(iter_jsonl(input_jsonl)):
        payload = canonical_record_bytes(record)
        digest = digest_bytes(payload)
        shard = output_dir / digest[:2]
        shard.mkdir(parents=True, exist_ok=True)
        path = shard / f"{digest}.json"
        path.write_bytes(payload + b"\n")
        record_id = (
            record.get("event_id")
            or record.get("chunk_id")
            or record.get("request_id")
            or record.get("assessment_id")
            or f"record-{sequence}"
        )
        index_records.append(
            CasEntry(
                uri=f"sha256:{digest}",
                sha256=digest,
                media_type="application/json",
                byte_size=len(payload) + 1,
                path=str(path),
                source_path=str(input_jsonl),
                record_count=1,
                record_type="json_record",
                metadata={"source_record_id": str(record_id), "sequence": sequence},
            ).model_dump(mode="json", exclude_none=True)
        )
    write_jsonl(index_output, index_records)
    root_digest = digest_bytes(dumps_json(index_records, pretty=False, sort_keys=True).encode("utf-8"))
    return {
        "ok": True,
        "input": str(input_jsonl),
        "output_dir": str(output_dir),
        "index_output": str(index_output),
        "record_count": len(index_records),
        "root_digest": root_digest,
    }


def read_cas_manifest(path: Path) -> CasManifest:
    """Read and validate a CAS manifest."""
    return CasManifest.model_validate(loads_json(path.read_text(encoding="utf-8")))
