"""Fail-closed, content-agnostic result contracts for the two-case pilot."""

from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from typing import Any, cast

REQUEST_IDS = ("11872", "35076")
ANALYST_IDS = ("agent:bounded-pilot-analyst-a", "agent:bounded-pilot-analyst-b")
RECONCILER_ID = "agent:bounded-pilot-reconciler"
LABELS = frozenset(
    (
        "observed",
        "submitted",
        "awaiting_response",
        "awaiting_clarification",
        "scope_amended",
        "transferred",
        "extension_notified",
        "decision_communicated",
        "released_in_full",
        "released_in_part",
        "refused",
        "information_not_held",
        "withdrawn",
        "overdue",
        "complaint_observed",
        "closed",
        "unknown",
    )
)
PROHIBITED_ACTIONS = [
    "empirical_result_approval",
    "population_inference",
    "archive_wide_claims",
    "human_reviewed_claims",
    "gold_promotion",
    "legal_certification",
    "redistribution",
    "publication",
    "training",
    "fine_tuning",
    "release",
    "dataset_publication",
    "paper_updates",
    "arxiv_submission",
]


def canonical_sha256(value: object) -> str:
    """Return SHA-256 over compact canonical JSON and reject non-finite numbers."""
    return sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def context_manifest_sha256(value: object) -> str:
    """Hash the exact compact newline-terminated context-manifest serialization."""
    encoded = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _instant(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError("timestamp must be an ISO 8601 date-time") from error
    if result.tzinfo is None:
        raise ValueError("timestamp must include an offset")
    return result


def _pin(value: object, *, name: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError(f"{name} must be an exact path/SHA-256 pin")
    mapping = cast("dict[str, Any]", value)
    path, digest = mapping["path"], mapping["sha256"]
    if not isinstance(path, str) or not path or not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"{name} is malformed")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{name} SHA-256 is malformed")
    return {"path": path, "sha256": digest}


def _runtime(value: object, *, actor_id: str, role: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"actor_id", "actor_class", "role", "runtime"}:
        raise ValueError(f"{role} identity envelope is malformed")
    mapping = cast("dict[str, Any]", value)
    if mapping != {
        "actor_id": actor_id,
        "actor_class": "automated_agent",
        "role": role,
        "runtime": mapping["runtime"],
    }:
        raise ValueError(f"{role} identity mismatch")
    runtime = mapping["runtime"]
    required = {"provider", "model", "prompt_sha256", "session_id"}
    if not isinstance(runtime, dict) or set(runtime) != required:
        raise ValueError(f"{role} runtime is malformed")
    runtime = cast("dict[str, Any]", runtime)
    if runtime["provider"] != "OpenAI" or not runtime["model"] or not runtime["session_id"]:
        raise ValueError(f"{role} runtime is incomplete")
    if not isinstance(runtime["prompt_sha256"], str) or len(runtime["prompt_sha256"]) != 64:
        raise ValueError(f"{role} prompt SHA-256 is malformed")
    return mapping


def validate_context_manifest(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate metadata-only source extents used for span-bound checking."""
    required = {
        "schema_version",
        "status",
        "authorization_sha256",
        "repository_commit",
        "request_ids",
        "contexts",
        "analyst_context_sha256",
        "byte_count",
        "codepoint_count",
        "segments",
        "analyst_contexts_identical",
        "local_only",
        "reconciliation_allowed",
        "empirical_result_approved",
        "publication_allowed",
    }
    if (
        set(value) != required
        or value["schema_version"] != "foi-o.bounded-pilot-context-manifest.v0.2.0"
    ):
        raise ValueError("context manifest shape or schema version mismatch")
    if (
        value["status"] != "locked_local_contexts"
        or value["request_ids"] != list(REQUEST_IDS)
        or value["local_only"] is not True
        or value["analyst_contexts_identical"] is not True
        or value["reconciliation_allowed"] is not False
        or value["empirical_result_approved"] is not False
        or value["publication_allowed"] is not False
    ):
        raise ValueError("context manifest is outside the exact local two-case scope")
    for key, length in (
        ("authorization_sha256", 64),
        ("repository_commit", 40),
        ("analyst_context_sha256", 64),
    ):
        observed = value[key]
        if (
            not isinstance(observed, str)
            or len(observed) != length
            or any(character not in "0123456789abcdef" for character in observed)
        ):
            raise ValueError(f"context manifest {key} is malformed")
    if value["byte_count"] < 1 or value["codepoint_count"] < 1:
        raise ValueError("context manifest extent is invalid")
    contexts = value["contexts"]
    if not isinstance(contexts, list) or [item.get("request_id") for item in contexts] != list(
        REQUEST_IDS
    ):
        raise ValueError("context manifest must contain the exact ordered census")
    contexts = cast("list[dict[str, Any]]", contexts)
    result: dict[str, dict[str, Any]] = {}
    for context_index, context in enumerate(contexts):
        if set(context) != {
            "request_id",
            "unit_sha256",
            "context_sha256",
            "global_start",
            "global_end",
            "sources",
        }:
            raise ValueError("context entry shape mismatch")
        if any(
            not isinstance(context[key], str)
            or len(context[key]) != 64
            or any(character not in "0123456789abcdef" for character in context[key])
            for key in ("unit_sha256", "context_sha256")
        ):
            raise ValueError("context entry digest is malformed")
        sources = context["sources"]
        expected_source_count = 7 if context["request_id"] == "11872" else 1
        if not isinstance(sources, list) or len(sources) != expected_source_count:
            raise ValueError("context source count does not match the governed census")
        sources = cast("list[dict[str, Any]]", sources)
        if context_index == 0 and context["global_start"] != 0:
            raise ValueError("first context must begin at global codepoint zero")
        if context["global_end"] <= context["global_start"]:
            raise ValueError("context global extent is invalid")
        source_ids: set[str] = set()
        previous_end = -1
        for source_index, source in enumerate(sources):
            if set(source) != {
                "source_kind",
                "source_id",
                "source_sha256",
                "start",
                "end",
                "character_count",
            }:
                raise ValueError("context source shape mismatch")
            if (
                source["source_id"] in source_ids
                or source["character_count"] < 1
                or source["end"] - source["start"] != source["character_count"]
                or (source_index == 0 and source["start"] != 0)
                or source["start"] <= previous_end
            ):
                raise ValueError("context source identity or extent is invalid")
            if source["source_kind"] not in {"correspondence", "attachment_derived_text"}:
                raise ValueError("context source kind is invalid")
            source_ids.add(source["source_id"])
            previous_end = source["end"]
        if sources[-1]["end"] != context["global_end"] - context["global_start"]:
            raise ValueError("unit-local source extents do not cover the context")
        result[context["request_id"]] = context
    if contexts[1]["global_start"] <= contexts[0]["global_end"]:
        raise ValueError("context global extents overlap or are reordered")
    if contexts[-1]["global_end"] != value["codepoint_count"]:
        raise ValueError("context extents do not cover the materialized context")
    segments = value["segments"]
    if not isinstance(segments, list) or len(segments) != 8:
        raise ValueError("global segment census must contain exactly eight sources")
    expected_segments = []
    for context in contexts:
        for source in context["sources"]:
            expected_segments.append(
                {
                    "request_id": context["request_id"],
                    "segment_id": source["source_id"],
                    "source_sha256": source["source_sha256"],
                    "source_kind": source["source_kind"],
                    "start": context["global_start"] + source["start"],
                    "end": context["global_start"] + source["end"],
                }
            )
    if segments != expected_segments:
        raise ValueError("global segments do not match ordered unit-local sources")
    return result


def _validate_span(span: dict[str, Any], sources: dict[str, dict[str, Any]]) -> None:
    required = {"source_kind", "source_id", "source_sha256", "start", "end", "coordinate_system"}
    if (
        set(span) != required
        or span["coordinate_system"]
        != "zero_based_utf8_codepoint_half_open_in_materialized_unit_context"
    ):
        raise ValueError("source span shape or coordinate system mismatch")
    source = sources.get(span["source_id"])
    if (
        source is None
        or span["source_kind"] != source["source_kind"]
        or span["source_sha256"] != source["source_sha256"]
    ):
        raise ValueError("source span does not bind an authorized source")
    if not source["start"] <= span["start"] < span["end"] <= source["end"]:
        raise ValueError("source span is outside the authorized source extent")


def validate_analyst_record(
    record: dict[str, Any], *, expected_actor_id: str, context: dict[str, Any]
) -> None:
    """Revalidate one complete first-pass record against exact context metadata."""
    if record["schema_version"] != "foi-o.bounded-pilot-analyst-record.v0.2.0":
        raise ValueError("analyst record schema version mismatch")
    if expected_actor_id not in ANALYST_IDS:
        raise ValueError("unknown analyst role")
    key = "a" if expected_actor_id == ANALYST_IDS[0] else "b"
    request_id = record["request_id"]
    if (
        request_id not in REQUEST_IDS
        or record["record_id"] != f"bounded-pilot:analyst-{key}:{request_id}"
    ):
        raise ValueError("analyst record identity mismatch")
    if record["status"] != "locked_agent_first_pass":
        raise ValueError("analyst record is not locked")
    _runtime(record["analyst"], actor_id=expected_actor_id, role="analyst")
    if (
        record["unit_sha256"] != context["unit_sha256"]
        or record["context_sha256"] != context["context_sha256"]
    ):
        raise ValueError("analyst record context binding mismatch")
    if record["label"] is not None and record["label"] not in LABELS:
        raise ValueError("label is outside the approved vocabulary")
    spans = record["source_spans"]
    source_index = {source["source_id"]: source for source in context["sources"]}
    if record["abstention"]:
        if record["label"] is not None or spans or record["abstention_reason"] is None:
            raise ValueError("abstention must omit label and spans and give a reason")
    elif record["label"] is None or not spans or record["abstention_reason"] is not None:
        raise ValueError("non-abstaining analysis requires label and span evidence")
    for span in spans:
        _validate_span(span, source_index)
    span_keys = [
        (span["source_kind"], span["source_id"], span["start"], span["end"], span["source_sha256"])
        for span in spans
    ]
    if span_keys != sorted(set(span_keys)):
        raise ValueError("source spans must be unique and deterministically sorted")
    if _instant(record["created_at"]) > _instant(record["locked_at"]):
        raise ValueError("analyst timestamps are out of order")
    if not 0 <= record["repair_attempt_count"] <= 2:
        raise ValueError("only two format-only repairs are permitted")
    if set(record["independence"]) != {
        "blinded_to_peer_outputs",
        "blinded_to_candidate_labels",
        "blinded_to_prior_reviews",
    } or not all(record["independence"].values()):
        raise ValueError("analyst independence assertions must all be true")
    if not 0 <= record["uncertainty"] <= 1 or not record["rationale"]:
        raise ValueError("uncertainty or rationale is invalid")
    if any(record[key] for key in ("empirical_result_approved", "human_reviewed", "gold_eligible")):
        raise ValueError("promotion flags must remain false")


def build_analysis_set(
    *,
    analyst_id: str,
    records: list[dict[str, Any]],
    authorization: dict[str, str],
    codebook: dict[str, str],
    context_manifest_pin: dict[str, str],
    context_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Build an exact two-record set after full semantic revalidation."""
    contexts = validate_context_manifest(context_manifest)
    for name, pin in (
        ("authorization", authorization),
        ("codebook", codebook),
        ("context_manifest", context_manifest_pin),
    ):
        _pin(pin, name=name)
    if context_manifest_pin["sha256"] != context_manifest_sha256(context_manifest):
        raise ValueError("context manifest pin does not match supplied manifest")
    if context_manifest["authorization_sha256"] != authorization["sha256"]:
        raise ValueError("context manifest does not bind the supplied authorization")
    if [record.get("request_id") for record in records] != list(REQUEST_IDS):
        raise ValueError("analysis must contain the exact ordered two-case census")
    for record in records:
        validate_analyst_record(
            record, expected_actor_id=analyst_id, context=contexts[record["request_id"]]
        )
        if record["codebook_sha256"] != codebook["sha256"]:
            raise ValueError("analyst record codebook binding mismatch")
    analyst = records[0]["analyst"]
    if any(record["analyst"] != analyst for record in records):
        raise ValueError("analyst runtime changed within a result set")
    key = "a" if analyst_id == ANALYST_IDS[0] else "b"
    return {
        "schema_version": "foi-o.bounded-pilot-analysis-set.v0.2.0",
        "set_id": f"bounded-pilot-{key}-first-pass",
        "status": "locked_complete_first_pass",
        "authorization": authorization,
        "codebook": codebook,
        "context_manifest": context_manifest_pin,
        "analyst": analyst,
        "request_ids": list(REQUEST_IDS),
        "record_count": 2,
        "record_hash_algorithm": "sha256_canonical_json_utf8_sort_keys_compact_v1",
        "entries": [
            {
                "request_id": record["request_id"],
                "record_sha256": canonical_sha256(record),
                "record": record,
            }
            for record in records
        ],
        "local_only": True,
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "prohibited_actions": list(PROHIBITED_ACTIONS),
    }


def validate_analysis_set(value: dict[str, Any], *, context_manifest: dict[str, Any]) -> None:
    """Reject tampering in an analysis-set envelope or embedded record."""
    contexts = validate_context_manifest(context_manifest)
    actor = value["analyst"]["actor_id"]
    key = "a" if actor == ANALYST_IDS[0] else "b" if actor == ANALYST_IDS[1] else None
    if key is None or value["set_id"] != f"bounded-pilot-{key}-first-pass":
        raise ValueError("analysis-set role identity mismatch")
    if (
        value["schema_version"] != "foi-o.bounded-pilot-analysis-set.v0.2.0"
        or value["status"] != "locked_complete_first_pass"
    ):
        raise ValueError("analysis-set schema or status mismatch")
    if value["request_ids"] != list(REQUEST_IDS) or value["record_count"] != 2:
        raise ValueError("analysis-set census is incomplete or reordered")
    for name in ("authorization", "codebook", "context_manifest"):
        _pin(value[name], name=name)
    if value["context_manifest"]["sha256"] != context_manifest_sha256(context_manifest):
        raise ValueError("analysis-set context-manifest pin mismatch")
    if context_manifest["authorization_sha256"] != value["authorization"]["sha256"]:
        raise ValueError("analysis-set authorization differs from context manifest")
    if (
        value["prohibited_actions"] != PROHIBITED_ACTIONS
        or value["record_hash_algorithm"] != "sha256_canonical_json_utf8_sort_keys_compact_v1"
    ):
        raise ValueError("analysis-set policy constants changed")
    if (
        any(value[key] for key in ("empirical_result_approved", "human_reviewed", "gold_eligible"))
        or value["local_only"] is not True
    ):
        raise ValueError("analysis-set scope or promotion flags changed")
    if [entry.get("request_id") for entry in value["entries"]] != list(REQUEST_IDS):
        raise ValueError("analysis-set entry order or membership mismatch")
    for entry in value["entries"]:
        record = entry["record"]
        if entry["record_sha256"] != canonical_sha256(record):
            raise ValueError("embedded analyst record hash mismatch")
        validate_analyst_record(
            record, expected_actor_id=actor, context=contexts[entry["request_id"]]
        )
        if (
            record["codebook_sha256"] != value["codebook"]["sha256"]
            or record["analyst"] != value["analyst"]
        ):
            raise ValueError("embedded analyst record provenance mismatch")


def build_dual_analysis_lock(
    *,
    analysis_a: dict[str, Any],
    analysis_b: dict[str, Any],
    paths: tuple[str, str],
    context_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Bind two verified sets; agreement/disagreement remains mechanically derivable."""
    for value in (analysis_a, analysis_b):
        validate_analysis_set(value, context_manifest=context_manifest)
    sets = (analysis_a, analysis_b)
    if tuple(value["analyst"]["actor_id"] for value in sets) != ANALYST_IDS:
        raise ValueError("dual lock requires exact ordered distinct analyst roles")
    for key in ("authorization", "codebook", "context_manifest", "request_ids"):
        if analysis_a[key] != analysis_b[key]:
            raise ValueError(f"analyst sets disagree on {key}")
    for left, right in zip(analysis_a["entries"], analysis_b["entries"], strict=True):
        if left["record"]["context_sha256"] != right["record"]["context_sha256"]:
            raise ValueError("analysts did not receive identical case contexts")
    return {
        "schema_version": "foi-o.bounded-pilot-dual-analysis-lock.v0.2.0",
        "lock_id": "bounded-pilot-11872-35076-dual-first-pass",
        "status": "locked_complete_dual_analysis",
        "authorization": analysis_a["authorization"],
        "codebook": analysis_a["codebook"],
        "context_manifest": analysis_a["context_manifest"],
        "analysis_sets": [
            {"path": path, "sha256": canonical_sha256(value), "analyst_id": actor}
            for path, value, actor in zip(paths, sets, ANALYST_IDS, strict=True)
        ],
        "request_ids": list(REQUEST_IDS),
        "first_pass_sets_complete": True,
        "analysts_distinct": True,
        "reconciliation_inputs_ready": True,
        "reconciliation_executed": False,
        "local_only": True,
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "prohibited_actions": list(PROHIBITED_ACTIONS),
    }


def _index(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["request_id"]: entry for entry in value["entries"]}


def disagreement_ids(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Return cases whose label, abstention, or exact span list differs."""
    ai, bi = _index(a), _index(b)
    fields = ("label", "abstention", "abstention_reason", "source_spans")
    return [
        request_id
        for request_id in REQUEST_IDS
        if tuple(ai[request_id]["record"][key] for key in fields)
        != tuple(bi[request_id]["record"][key] for key in fields)
    ]


def validate_dual_lock(
    lock: dict[str, Any],
    *,
    analysis_a: dict[str, Any],
    analysis_b: dict[str, Any],
    paths: tuple[str, str],
    context_manifest: dict[str, Any],
) -> None:
    """Recompute the exact expected lock and reject any linkage drift."""
    expected = build_dual_analysis_lock(
        analysis_a=analysis_a, analysis_b=analysis_b, paths=paths, context_manifest=context_manifest
    )
    if lock != expected:
        raise ValueError("dual-analysis lock or set linkage mismatch")


def build_reconciliation_set(
    *,
    records: list[dict[str, Any]],
    reconciler: dict[str, Any],
    analysis_a: dict[str, Any],
    analysis_b: dict[str, Any],
    analysis_lock: dict[str, Any],
    analysis_paths: tuple[str, str],
    analysis_lock_path: str,
    context_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Lock decisions for verified disagreements only; agreements stay mechanical."""
    validate_dual_lock(
        analysis_lock,
        analysis_a=analysis_a,
        analysis_b=analysis_b,
        paths=analysis_paths,
        context_manifest=context_manifest,
    )
    _runtime(reconciler, actor_id=RECONCILER_ID, role="reconciler")
    ids = disagreement_ids(analysis_a, analysis_b)
    if [record.get("request_id") for record in records] != ids:
        raise ValueError("reconciliation must cover verified disagreements only, in order")
    indexes = (_index(analysis_a), _index(analysis_b))
    contexts = validate_context_manifest(context_manifest)
    entries: list[dict[str, Any]] = []
    for record in records:
        request_id = record["request_id"]
        inputs = [index[request_id] for index in indexes]
        refs = [
            {"analyst_id": actor, "record_sha256": item["record_sha256"]}
            for actor, item in zip(ANALYST_IDS, inputs, strict=True)
        ]
        if (
            record["schema_version"] != "foi-o.bounded-pilot-reconciliation-record.v0.2.0"
            or record["record_id"] != f"bounded-pilot:reconciler:{request_id}"
            or record["status"] != "locked_agent_reconciliation"
        ):
            raise ValueError("reconciliation record schema, identity, or status mismatch")
        if record["analysis_refs"] != refs or record["reconciler"] != reconciler:
            raise ValueError("reconciliation provenance does not match locked inputs")
        if record["outcome"] == "unresolved":
            if record["label"] is not None or record["source_spans"]:
                raise ValueError("unresolved reconciliation cannot assert label or spans")
        elif (
            record["outcome"] != "resolved_disagreement"
            or record["label"] not in LABELS
            or not record["source_spans"]
        ):
            raise ValueError("resolved disagreement requires an approved label and span")
        sources = {source["source_id"]: source for source in contexts[request_id]["sources"]}
        for span in record["source_spans"]:
            _validate_span(span, sources)
        span_keys = [
            (
                span["source_kind"],
                span["source_id"],
                span["start"],
                span["end"],
                span["source_sha256"],
            )
            for span in record["source_spans"]
        ]
        if span_keys != sorted(set(span_keys)):
            raise ValueError("reconciliation spans must be unique and deterministically sorted")
        latest = max(_instant(item["record"]["locked_at"]) for item in inputs)
        if _instant(record["created_at"]) < latest or _instant(record["created_at"]) > _instant(
            record["locked_at"]
        ):
            raise ValueError("reconciliation timestamps are out of order")
        if not 0 <= record["repair_attempt_count"] <= 2 or not record["rationale"]:
            raise ValueError("reconciliation repair count or rationale is invalid")
        if any(
            record[key] for key in ("empirical_result_approved", "human_reviewed", "gold_eligible")
        ):
            raise ValueError("reconciliation promotion flags must remain false")
        entries.append(
            {"request_id": request_id, "record_sha256": canonical_sha256(record), "record": record}
        )
    agreements = [request_id for request_id in REQUEST_IDS if request_id not in ids]
    return {
        "schema_version": "foi-o.bounded-pilot-reconciliation-set.v0.2.0",
        "set_id": "bounded-pilot-11872-35076-reconciliation",
        "status": "locked_complete_agent_reconciliation",
        "analysis_lock": {"path": analysis_lock_path, "sha256": canonical_sha256(analysis_lock)},
        "analysis_sets": analysis_lock["analysis_sets"],
        "authorization": analysis_lock["authorization"],
        "codebook": analysis_lock["codebook"],
        "context_manifest": analysis_lock["context_manifest"],
        "reconciler": reconciler,
        "request_ids": list(REQUEST_IDS),
        "agreement_request_ids": agreements,
        "disagreement_request_ids": ids,
        "record_count": len(entries),
        "entries": entries,
        "local_only": True,
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "prohibited_actions": list(PROHIBITED_ACTIONS),
    }


def validate_reconciliation_set(
    value: dict[str, Any],
    *,
    analysis_a: dict[str, Any],
    analysis_b: dict[str, Any],
    analysis_lock: dict[str, Any],
    analysis_paths: tuple[str, str],
    analysis_lock_path: str,
    context_manifest: dict[str, Any],
) -> None:
    """Rebuild the reconciliation envelope from its records and reject tampering."""
    records = [entry["record"] for entry in value["entries"]]
    expected = build_reconciliation_set(
        records=records,
        reconciler=value["reconciler"],
        analysis_a=analysis_a,
        analysis_b=analysis_b,
        analysis_lock=analysis_lock,
        analysis_paths=analysis_paths,
        analysis_lock_path=analysis_lock_path,
        context_manifest=context_manifest,
    )
    if value != expected:
        raise ValueError("reconciliation set, embedded hash, or upstream linkage mismatch")


def compute_candidate_diagnostics(
    *,
    analysis_a: dict[str, Any],
    analysis_b: dict[str, Any],
    analysis_lock: dict[str, Any],
    analysis_paths: tuple[str, str],
    analysis_lock_path: str,
    reconciliation: dict[str, Any],
    context_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Compute bounded descriptive diagnostics after revalidating the whole chain."""
    for value in (analysis_a, analysis_b):
        validate_analysis_set(value, context_manifest=context_manifest)
    validate_dual_lock(
        analysis_lock,
        analysis_a=analysis_a,
        analysis_b=analysis_b,
        paths=analysis_paths,
        context_manifest=context_manifest,
    )
    validate_reconciliation_set(
        reconciliation,
        analysis_a=analysis_a,
        analysis_b=analysis_b,
        analysis_lock=analysis_lock,
        analysis_paths=analysis_paths,
        analysis_lock_path=analysis_lock_path,
        context_manifest=context_manifest,
    )
    a, b = _index(analysis_a), _index(analysis_b)
    reconciled = _index(reconciliation)
    cases: list[dict[str, Any]] = []
    label_agreements = span_agreements = abstention_agreements = 0
    abstentions_a = abstentions_b = unresolved = 0
    for request_id in REQUEST_IDS:
        left, right = a[request_id]["record"], b[request_id]["record"]
        label_agree = left["label"] == right["label"]
        span_agree = left["source_spans"] == right["source_spans"]
        abstention_agree = left["abstention"] == right["abstention"]
        label_agreements += int(label_agree)
        span_agreements += int(span_agree)
        abstention_agreements += int(abstention_agree)
        abstentions_a += int(left["abstention"])
        abstentions_b += int(right["abstention"])
        if request_id in reconciled:
            outcome = reconciled[request_id]["record"]["outcome"]
            unresolved += int(outcome == "unresolved")
        else:
            outcome = "mechanical_agreement"
        cases.append(
            {
                "request_id": request_id,
                "label_agreement": label_agree,
                "span_exact_agreement": span_agree,
                "abstention_agreement": abstention_agree,
                "reconciliation_outcome": outcome,
            }
        )
    return {
        "schema_version": "foi-o.bounded-pilot-candidate-diagnostics.v0.2.0",
        "diagnostics_id": "bounded-pilot-11872-35076-candidate-diagnostics",
        "status": "candidate_pending_exact_result_approval",
        "analysis_sets": [canonical_sha256(analysis_a), canonical_sha256(analysis_b)],
        "analysis_lock_sha256": canonical_sha256(analysis_lock),
        "reconciliation_sha256": canonical_sha256(reconciliation),
        "request_ids": list(REQUEST_IDS),
        "denominator": 2,
        "label_agreement": {"count": label_agreements, "denominator": 2},
        "span_exact_agreement": {"count": span_agreements, "denominator": 2},
        "abstention_agreement": {"count": abstention_agreements, "denominator": 2},
        "abstention_counts": {"analyst_a": abstentions_a, "analyst_b": abstentions_b},
        "unresolved_count": unresolved,
        "cohens_kappa": None,
        "cohens_kappa_omission_reason": "purposive_two_case_pilot_too_small_for_stable_inference",
        "cases": cases,
        "claim_scope": "descriptive_case_level_feasibility_only",
        "population_inference": False,
        "archive_wide_claim": False,
        "empirical_result_approved": False,
        "human_reviewed": False,
        "gold_eligible": False,
        "local_only": True,
        "prohibited_actions": list(PROHIBITED_ACTIONS),
    }
