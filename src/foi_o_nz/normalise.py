"""Normalisation pipeline for FYI archive-style request manifests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from pydantic import AnyUrl

from foi_o_nz.constants import DEFAULT_REGIME, SOURCE_SYSTEM_FYI_ARCHIVE
from foi_o_nz.io import read_json_records, write_jsonl
from foi_o_nz.models import Actor, CoreEvent, EvidenceRef, RequestProfile, RequestRef, StateMapping
from foi_o_nz.state_machine import map_alaveteli_state


def _safe_url(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return None


def _source_url(record: dict[str, Any]) -> str | None:
    explicit = _safe_url(record.get("source_url") or record.get("url"))
    if explicit:
        return explicit
    url_title = record.get("url_title")
    if isinstance(url_title, str) and url_title:
        return f"https://fyi.org.nz/request/{url_title}"
    return None


def _parse_attachments(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _parse_warc_ids(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _event_id(kind: str, request_id: str | int, source_state: str | None = None) -> str:
    base = f"https://w3id.org/foio-nz/event/{kind}/{request_id}/{source_state or ''}"
    return f"urn:uuid:{uuid5(NAMESPACE_URL, base)}"


def build_request_profile(record: dict[str, Any], *, source: str = SOURCE_SYSTEM_FYI_ARCHIVE) -> RequestProfile:
    """Build a normalised request profile from an FYI archive-style record."""
    request_id = record.get("request_id") or record.get("id") or record.get("url_title")
    if request_id is None:
        raise ValueError("record is missing request_id/id/url_title")
    source_state = str(record.get("state") or record.get("source_state") or "unknown")
    mapping = map_alaveteli_state(source_state)
    evidence_id = f"evidence:{source}:{request_id}:manifest"
    return RequestProfile(
        source=source,
        request_id=request_id,
        url_title=record.get("url_title"),
        source_url=_source_url(record),
        title=str(record.get("title") or "Untitled request"),
        authority=str(record.get("authority") or record.get("public_body") or "Unknown authority"),
        source_state=source_state,
        normalised_state=mapping.normalised_state.value,
        state_mapping=StateMapping(
            method="rule",
            confidence=mapping.confidence,
            evidence_ids=[evidence_id],
            notes=mapping.notes,
        ),
        first_sent=record.get("first_sent"),
        last_updated=record.get("last_updated"),
        content_sha256=record.get("content_sha256"),
        html_captured=record.get("html_captured"),
        attachments=_parse_attachments(record.get("attachments")),
        warc_record_ids=_parse_warc_ids(record.get("warc_record_ids")),
    )


def build_observed_events(
    profile: RequestProfile,
    *,
    observed_at: datetime | None = None,
) -> list[CoreEvent]:
    """Create conservative observed/inferred events from a request profile."""
    event_time = observed_at or profile.last_updated or profile.first_sent or datetime.now(UTC)
    evidence = EvidenceRef(
        evidence_id=f"evidence:{profile.source}:{profile.request_id}:manifest",
        evidence_type="archive_manifest",
        source_url=profile.source_url,
        archive_ref=profile.url_title,
        content_sha256=profile.content_sha256,
        observed_at=event_time,
    )
    request_ref = RequestRef(
        source_system=profile.source,
        source_request_id=profile.request_id,
        source_url=profile.source_url,
        url_title=profile.url_title,
        content_sha256=profile.content_sha256,
    )
    common = {
        "event_time": event_time,
        "request_ref": request_ref,
        "regime": DEFAULT_REGIME,
        "source_system": profile.source,
        "actor": Actor(role="system", name="fyi-archive-nz"),
        "machine_generated": True,
        "generator": {
            "system": "foi-o-nz",
            "model": None,
            "prompt_id": None,
            "software_version": "0.1.0",
        },
        "requires_human_certification": False,
        "evidence": [evidence],
    }
    request_event = CoreEvent(
        **common,
        event_id=_event_id("request-observed", profile.request_id),
        event_type="RequestObserved",
        lifecycle_state_after=profile.normalised_state,
        assertion_status="observed",
        confidence=1.0,
        payload={
            "title": profile.title,
            "authority": profile.authority,
            "first_sent": profile.first_sent.isoformat() if profile.first_sent else None,
        },
    )
    state_event = CoreEvent(
        **common,
        event_id=_event_id("state-observed", profile.request_id, profile.source_state),
        event_type="StateObserved",
        lifecycle_state_after=profile.normalised_state,
        assertion_status=(profile.state_mapping.method if False else "inferred"),
        confidence=profile.state_mapping.confidence if profile.state_mapping else None,
        payload={
            "source_state": profile.source_state,
            "normalised_state": profile.normalised_state,
            "mapping": profile.state_mapping.model_dump(mode="json") if profile.state_mapping else None,
        },
    )
    return [request_event, state_event]


def normalise_records(records: list[dict[str, Any]]) -> tuple[list[RequestProfile], list[CoreEvent]]:
    """Normalise raw manifest records into request profiles and core events."""
    profiles: list[RequestProfile] = []
    events: list[CoreEvent] = []
    for record in records:
        profile = build_request_profile(record)
        profiles.append(profile)
        events.extend(build_observed_events(profile))
    return profiles, events


def normalise_manifest_file(
    input_path: Path,
    *,
    requests_output: Path,
    events_output: Path,
    parquet_dir: Path | None = None,
) -> dict[str, Any]:
    """Normalise a manifest file and write JSONL plus optional Parquet outputs."""
    records = read_json_records(input_path)
    profiles, events = normalise_records(records)
    request_dicts = [profile.model_dump(mode="json", exclude_none=True) for profile in profiles]
    event_dicts = [event.model_dump(mode="json", exclude_none=True) for event in events]
    request_count = write_jsonl(requests_output, request_dicts)
    event_count = write_jsonl(events_output, event_dicts)
    parquet_written: list[str] = []
    if parquet_dir is not None:
        parquet_written = write_optional_parquet(
            parquet_dir,
            request_dicts=request_dicts,
            event_dicts=event_dicts,
        )
    return {
        "input": str(input_path),
        "requests_output": str(requests_output),
        "events_output": str(events_output),
        "request_count": request_count,
        "event_count": event_count,
        "parquet_written": parquet_written,
    }


def write_optional_parquet(
    parquet_dir: Path,
    *,
    request_dicts: list[dict[str, Any]],
    event_dicts: list[dict[str, Any]],
) -> list[str]:
    """Write Parquet outputs when Polars/PyArrow are installed."""
    try:
        import polars as pl  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return []
    parquet_dir.mkdir(parents=True, exist_ok=True)
    request_path = parquet_dir / "requests.parquet"
    event_path = parquet_dir / "events.parquet"
    pl.DataFrame(request_dicts).write_parquet(request_path)
    pl.DataFrame(event_dicts).write_parquet(event_path)
    return [str(request_path), str(event_path)]
