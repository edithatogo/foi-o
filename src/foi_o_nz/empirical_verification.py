"""Fail-closed verification for authentic empirical artifact bundles."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from math import isclose
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_DIR = Path(__file__).parents[2] / "schemas" / "json"


@dataclass(frozen=True, slots=True)
class EmpiricalVerificationResult:
    """Verified bundle identities and counts, never a promotion decision."""

    unit_count: int
    annotator_ids: tuple[str, str]
    adjudicator_id: str
    adjudication_count: int
    reliability_report_sha256: str
    promotion_allowed: bool = False


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"{path.name}: expected JSON object")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        _require(isinstance(value, dict), f"{path.name}:{line_number}: expected object")
        records.append(value)
    _require(bool(records), f"{path.name}: empty artifact set")
    return records


def _schema(name: str) -> dict[str, Any]:
    return _load_object(SCHEMA_DIR / name)


def _validate(instance: dict[str, Any], schema_name: str, label: str) -> None:
    validator = Draft202012Validator(_schema(schema_name), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    if errors:
        path = ".".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise ValueError(f"{label}.{path}: {errors[0].message}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _instant(value: str, label: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    _require(parsed.tzinfo is not None, f"{label}: timezone required")
    return parsed


def _record_digest(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _rate_matches(rate: dict[str, Any], label: str) -> None:
    numerator = rate["numerator"]
    denominator = rate["denominator"]
    estimate = rate["estimate"]
    _require(numerator <= denominator, f"{label}: numerator exceeds denominator")
    if denominator == 0:
        _require(estimate is None, f"{label}: zero denominator requires null estimate")
    else:
        _require(
            estimate is not None and isclose(estimate, numerator / denominator, abs_tol=1e-12),
            f"{label}: estimate does not match numerator/denominator",
        )


def _ci_contains(metric: dict[str, Any], label: str) -> None:
    estimate = metric["estimate"]
    interval = metric["ci"]
    if estimate is None:
        _require(interval is None, f"{label}: null estimate requires null confidence interval")
        return
    _require(interval is not None, f"{label}: estimate requires confidence interval")
    _require(
        interval["lower"] <= estimate <= interval["upper"],
        f"{label}: confidence interval does not contain estimate",
    )


def _span_f1(first: dict[str, Any], second: dict[str, Any]) -> float:
    overlap = max(0, min(first["end"], second["end"]) - max(first["start"], second["start"]))
    return 2 * overlap / ((first["end"] - first["start"]) + (second["end"] - second["start"]))


def verify_authentic_empirical_bundle(
    *,
    authorization_path: Path,
    protocol_path: Path,
    source_population_path: Path,
    codebook_path: Path,
    sampling_configuration_path: Path,
    sample_manifest_path: Path,
    unit_manifest_path: Path,
    duplicate_cluster_registry_path: Path,
    annotation_set_paths: tuple[Path, Path],
    adjudication_set_path: Path,
    reliability_report_path: Path,
    expected_reliability_report_sha256: str,
) -> EmpiricalVerificationResult:
    """Verify authentic empirical artifacts and their relational invariants."""
    authorization = _load_object(authorization_path)
    sample = _load_object(sample_manifest_path)
    units = _load_object(unit_manifest_path)
    clusters = _load_object(duplicate_cluster_registry_path)
    report = _load_object(reliability_report_path)
    annotation_sets = tuple(_load_jsonl(path) for path in annotation_set_paths)
    adjudications = _load_jsonl(adjudication_set_path)

    _validate(
        authorization,
        "empirical-execution-authorization.schema.json",
        "authorization",
    )
    _validate(sample, "empirical-sample-manifest.schema.json", "sample")
    _validate(units, "empirical-unit-manifest.schema.json", "units")
    _validate(clusters, "duplicate-cluster-registry.schema.json", "clusters")
    _validate(report, "reliability-report.schema.json", "reliability")
    for set_index, records in enumerate(annotation_sets):
        for record_index, record in enumerate(records):
            _validate(
                record,
                "locked-annotation-record.schema.json",
                f"annotations[{set_index}][{record_index}]",
            )
    for record_index, record in enumerate(adjudications):
        _validate(record, "adjudication-record.schema.json", f"adjudications[{record_index}]")

    report_digest = _digest(reliability_report_path)
    _require(
        report_digest == expected_reliability_report_sha256, "reliability report SHA-256 mismatch"
    )
    pins = report["artifact_pins"]
    _require(
        pins["authorization_sha256"] == _digest(authorization_path),
        "authorization SHA-256 mismatch",
    )
    _require(pins["protocol_sha256"] == _digest(protocol_path), "protocol SHA-256 mismatch")
    _require(
        pins["sample_manifest_sha256"] == _digest(sample_manifest_path),
        "sample manifest SHA-256 mismatch",
    )
    _require(
        pins["duplicate_cluster_registry_sha256"] == _digest(duplicate_cluster_registry_path),
        "duplicate registry SHA-256 mismatch",
    )
    _require(
        pins["annotation_set_sha256"] == [_digest(path) for path in annotation_set_paths],
        "annotation set SHA-256 mismatch",
    )
    _require(
        pins["adjudication_set_sha256"] == _digest(adjudication_set_path),
        "adjudication set SHA-256 mismatch",
    )
    _require(
        sample["unit_manifest_sha256"] == _digest(unit_manifest_path),
        "sample unit-manifest pin mismatch",
    )
    _require(
        sample["duplicate_cluster_registry_sha256"] == _digest(duplicate_cluster_registry_path),
        "sample duplicate-registry pin mismatch",
    )

    _require(
        authorization["status"]
        in {"approved_human_authorization", "approved_analyst_authorization"}
        and authorization["execution_allowed"] is True,
        "empirical execution is not authorized",
    )
    analyst_execution = authorization["status"] == "approved_analyst_authorization"
    _require(
        not analyst_execution or len(authorization.get("actor_provenance", [])) == 3,
        "analyst execution requires three actor-provenance records",
    )
    if analyst_execution:
        provenance = authorization["actor_provenance"]
        expected_roles = {
            (authorization["annotator_ids"][0], "analyst"),
            (authorization["annotator_ids"][1], "analyst"),
            (authorization["adjudicator_id"], "reconciler"),
        }
        _require(
            {(actor["actor_id"], actor["role"]) for actor in provenance} == expected_roles,
            "actor provenance does not match authorized roles",
        )
        for actor in provenance:
            expected_class = (
                "automated_agent" if actor["actor_id"].startswith("agent:") else "human"
            )
            _require(
                actor["actor_class"] == expected_class,
                "actor class does not match actor identity",
            )
    authorization_artifacts = {
        "protocol": protocol_path,
        "source_population": source_population_path,
        "codebook": codebook_path,
        "sampling_configuration": sampling_configuration_path,
    }
    for name, path in authorization_artifacts.items():
        artifact = authorization[name]
        _require(
            artifact["approved"] is True and artifact["sha256"] == _digest(path),
            f"authorized {name} artifact mismatch",
        )

    _require(
        units["status"] == "frozen" and units["empirical_evidence"] is True,
        "unit manifest is not authentic and frozen",
    )
    _require(
        clusters["status"] == "frozen" and clusters["empirical_evidence"] is True,
        "duplicate registry is not authentic and frozen",
    )
    _require(
        report["status"] in {"computed_human_reliability", "computed_analyst_reliability"}
        and report["empirical_evidence"] is True,
        "reliability report is not authentic and computed",
    )
    _require(report["promotion_allowed"] is False, "reliability report cannot authorize promotion")
    _require(
        units["sampling_protocol_sha256"] == _digest(protocol_path), "unit protocol pin mismatch"
    )
    _require(
        units["source_population_manifest_sha256"] == _digest(source_population_path),
        "unit source-population pin mismatch",
    )
    _require(
        units["sampling_configuration_sha256"] == _digest(sampling_configuration_path),
        "unit sampling-configuration pin mismatch",
    )
    _require(
        clusters["population_manifest_sha256"] == units["source_population_manifest_sha256"],
        "source population pin mismatch",
    )

    unit_records = units["units"]
    unit_ids = [unit["unit_sha256"] for unit in unit_records]
    _require(len(unit_ids) == len(set(unit_ids)), "duplicate unit in frozen manifest")
    for unit in unit_records:
        _require(
            unit["source_span"]["end"] > unit["source_span"]["start"],
            "unit source span is empty or reversed",
        )
    cluster_members: dict[str, tuple[str, str]] = {}
    for cluster in clusters["clusters"]:
        for member in cluster["member_unit_sha256"]:
            _require(member not in cluster_members, "unit appears in multiple duplicate clusters")
            cluster_members[member] = (cluster["cluster_id"], cluster["split"])
    _require(
        set(cluster_members) == set(unit_ids),
        "cluster membership does not equal frozen unit membership",
    )
    for unit in unit_records:
        _require(
            cluster_members[unit["unit_sha256"]] == (unit["duplicate_cluster_id"], unit["split"]),
            "unit duplicate-cluster ID or split mismatch",
        )
    _require(
        {unit["split"] for unit in unit_records}.issubset(set(sample["split_policy"]["splits"])),
        "unit split is absent from sample split policy",
    )

    annotation_maps: list[dict[str, dict[str, Any]]] = []
    annotator_ids: list[str] = []
    codebooks: set[str] = set()
    latest_annotation_lock: datetime | None = None
    for records in annotation_sets:
        record_map: dict[str, dict[str, Any]] = {}
        identities = {record["annotator_id"] for record in records}
        _require(len(identities) == 1, "annotation set contains mixed annotator identities")
        annotator_id = identities.pop()
        _require(
            annotator_id.startswith(("human:", "agent:")),
            "analysis identity has unsupported actor class",
        )
        annotator_ids.append(annotator_id)
        for record in records:
            _require(
                record["status"] in {"locked_human_annotation", "locked_analyst_analysis"}
                and record["empirical_evidence"] is True,
                "annotation record is not authentic and locked",
            )
            _require(
                record["blinded_to_candidate"] is True, "annotation record is not candidate-blinded"
            )
            _require(record["unit_sha256"] not in record_map, "duplicate annotation unit")
            if record["span"] is not None:
                _require(
                    record["span"]["end"] > record["span"]["start"],
                    "annotation span is empty or reversed",
                )
            created = _instant(record["created_at"], "annotation created_at")
            locked = _instant(record["locked_at"], "annotation locked_at")
            _require(created <= locked, "annotation lock precedes creation")
            latest_annotation_lock = (
                max(latest_annotation_lock, locked) if latest_annotation_lock else locked
            )
            record_map[record["unit_sha256"]] = record
            codebooks.add(record["codebook_revision"])
        annotation_maps.append(record_map)
    _require(len(set(annotator_ids)) == 2, "annotator identities are not distinct")
    _require(
        set(annotation_maps[0]) == set(unit_ids) == set(annotation_maps[1]),
        "annotation coverage does not equal frozen unit membership",
    )
    _require(
        len(codebooks) == 1 and pins["codebook_revision"] in codebooks,
        "annotation codebook pin mismatch",
    )
    _require(
        authorization["codebook_revision"] == pins["codebook_revision"],
        "authorization codebook revision mismatch",
    )
    _require(
        authorization["annotator_ids"] == annotator_ids,
        "authorized annotator identities mismatch",
    )
    earliest_annotation_creation = min(
        _instant(record["created_at"], "annotation created_at")
        for records in annotation_sets
        for record in records
    )
    _require(
        _instant(units["frozen_at"], "units frozen_at") <= earliest_annotation_creation,
        "annotation precedes unit freeze",
    )
    _require(
        _instant(clusters["frozen_at"], "clusters frozen_at") <= earliest_annotation_creation,
        "annotation precedes cluster freeze",
    )

    disagreements = {
        unit_id
        for unit_id in unit_ids
        if annotation_maps[0][unit_id]["abstention"]
        or annotation_maps[1][unit_id]["abstention"]
        or annotation_maps[0][unit_id]["label"] != annotation_maps[1][unit_id]["label"]
        or annotation_maps[0][unit_id]["span"] != annotation_maps[1][unit_id]["span"]
    }
    adjudication_map: dict[str, dict[str, Any]] = {}
    adjudicator_ids: set[str] = set()
    for record in adjudications:
        unit_id = record["unit_sha256"]
        _require(unit_id in disagreements, "adjudication does not correspond to a disagreement")
        _require(unit_id not in adjudication_map, "duplicate adjudication unit")
        _require(
            record["status"] in {"locked_human_adjudication", "locked_analyst_reconciliation"}
            and record["empirical_evidence"] is True,
            "adjudication is not authentic and locked",
        )
        adjudicator_ids.add(record["adjudicator_id"])
        expected_refs = {
            (
                annotation_maps[index][unit_id]["annotator_id"],
                _record_digest(annotation_maps[index][unit_id]),
            )
            for index in range(2)
        }
        actual_refs = {(ref["annotator_id"], ref["sha256"]) for ref in record["annotation_refs"]}
        _require(actual_refs == expected_refs, "adjudication annotation reference mismatch")
        created = _instant(record["created_at"], "adjudication created_at")
        locked = _instant(record["locked_at"], "adjudication locked_at")
        _require(
            latest_annotation_lock is not None and latest_annotation_lock <= created <= locked,
            "adjudication timestamp ordering invalid",
        )
        adjudication_map[unit_id] = record
    _require(
        set(adjudication_map) == disagreements, "adjudication coverage does not equal disagreements"
    )
    _require(len(adjudicator_ids) == 1, "adjudication set contains mixed adjudicators")
    adjudicator_id = next(iter(adjudicator_ids))
    _require(
        adjudicator_id.startswith(("human:", "agent:")) and adjudicator_id not in annotator_ids,
        "reconciler is not a distinct supported actor",
    )
    _require(
        authorization["adjudicator_id"] == adjudicator_id,
        "authorized adjudicator identity mismatch",
    )

    report_time = _instant(report["computed_at"], "reliability computed_at")
    _require(
        _instant(authorization["approved_at"], "authorization approved_at")
        <= _instant(units["created_at"], "units created_at"),
        "unit manifest creation precedes execution authorization",
    )
    _require(
        _instant(units["frozen_at"], "units frozen_at") <= report_time,
        "unit freeze follows reliability computation",
    )
    _require(
        _instant(clusters["frozen_at"], "clusters frozen_at") <= report_time,
        "cluster freeze follows reliability computation",
    )
    for record in adjudications:
        _require(
            _instant(record["locked_at"], "adjudication locked_at") <= report_time,
            "adjudication lock follows reliability computation",
        )

    paired = [
        unit_id
        for unit_id in unit_ids
        if not annotation_maps[0][unit_id]["abstention"]
        and not annotation_maps[1][unit_id]["abstention"]
    ]
    raw_matches = sum(
        annotation_maps[0][unit_id]["label"] == annotation_maps[1][unit_id]["label"]
        for unit_id in paired
    )
    nominal = report["nominal_agreement"]
    _require(nominal["eligible_pairs"] == len(paired), "nominal eligible-pair count mismatch")
    _require(
        nominal["raw_agreement"]["numerator"] == raw_matches
        and nominal["raw_agreement"]["denominator"] == len(paired),
        "raw-agreement counts mismatch",
    )
    _rate_matches(nominal["raw_agreement"], "raw agreement")
    _ci_contains(nominal["raw_agreement"], "raw agreement")
    if not paired:
        _require(
            nominal["cohen_kappa"]["estimate"] is None
            and nominal["kappa_undefined_reason"] == "no_eligible_pairs",
            "kappa no-pair handling mismatch",
        )
    else:
        first_counts = Counter(annotation_maps[0][unit_id]["label"] for unit_id in paired)
        second_counts = Counter(annotation_maps[1][unit_id]["label"] for unit_id in paired)
        labels = set(first_counts) | set(second_counts)
        expected_agreement = (
            sum(first_counts[label] * second_counts[label] for label in labels) / len(paired) ** 2
        )
        if isclose(expected_agreement, 1.0, abs_tol=1e-12):
            _require(
                nominal["cohen_kappa"]["estimate"] is None
                and nominal["kappa_undefined_reason"] == "expected_agreement_equals_one",
                "kappa constant-marginal handling mismatch",
            )
        else:
            observed_agreement = raw_matches / len(paired)
            expected_kappa = (observed_agreement - expected_agreement) / (1 - expected_agreement)
            _require(
                nominal["kappa_undefined_reason"] is None
                and isclose(nominal["cohen_kappa"]["estimate"], expected_kappa, abs_tol=1e-12),
                "Cohen kappa estimate mismatch",
            )
    _ci_contains(nominal["cohen_kappa"], "Cohen kappa")

    span_pairs = [
        unit_id
        for unit_id in paired
        if annotation_maps[0][unit_id]["span"] is not None
        and annotation_maps[1][unit_id]["span"] is not None
    ]
    exact_matches = sum(
        annotation_maps[0][unit_id]["span"] == annotation_maps[1][unit_id]["span"]
        for unit_id in span_pairs
    )
    span = report["span_agreement"]
    _require(span["eligible_pairs"] == len(span_pairs), "span eligible-pair count mismatch")
    _require(
        span["exact_agreement"]["numerator"] == exact_matches
        and span["exact_agreement"]["denominator"] == len(span_pairs),
        "exact-span counts mismatch",
    )
    _rate_matches(span["exact_agreement"], "exact span agreement")
    _ci_contains(span["exact_agreement"], "exact span agreement")
    _require(
        span["overlap_f1"]["denominator"] == len(span_pairs), "overlap-F1 denominator mismatch"
    )
    if span_pairs:
        expected_f1 = sum(
            _span_f1(annotation_maps[0][unit_id]["span"], annotation_maps[1][unit_id]["span"])
            for unit_id in span_pairs
        ) / len(span_pairs)
        _require(
            isclose(span["overlap_f1"]["estimate"], expected_f1, abs_tol=1e-12),
            "overlap-F1 estimate mismatch",
        )
    _ci_contains(span["overlap_f1"], "overlap F1")

    counts = report["counts"]
    resolved = sum(record["outcome"] == "resolved" for record in adjudications)
    unresolved = len(adjudications) - resolved
    _require(counts["units"] == len(unit_ids), "unit count mismatch")
    missing_evidence_units = {
        record["unit_sha256"]
        for records in annotation_sets
        for record in records
        if record["abstention_reason"] == "missing_evidence"
    }
    _require(
        counts["missing_evidence"] == len(missing_evidence_units),
        "missing-evidence count mismatch",
    )
    _require(
        counts["annotator_abstentions"]
        == [sum(record["abstention"] for record in records) for records in annotation_sets],
        "annotator abstention counts mismatch",
    )
    _require(
        counts["resolved_adjudications"] == resolved
        and counts["unresolved_adjudications"] == unresolved,
        "adjudication outcome counts mismatch",
    )
    _require(
        counts["label_counts"]
        == dict(
            Counter(
                record["label"]
                for records in annotation_sets
                for record in records
                if record["label"] is not None
            )
        ),
        "label counts mismatch",
    )
    rates = report["rates"]
    _require(
        rates["adjudication"]["numerator"] == len(adjudications)
        and rates["adjudication"]["denominator"] == len(disagreements),
        "adjudication-rate counts mismatch",
    )
    _require(
        rates["unresolved"]["numerator"] == unresolved
        and rates["unresolved"]["denominator"] == len(adjudications),
        "unresolved-rate counts mismatch",
    )
    _rate_matches(rates["adjudication"], "adjudication rate")
    _rate_matches(rates["unresolved"], "unresolved rate")
    calculation = report["calculation"]
    _require(
        calculation["bootstrap_replicates_valid"] + calculation["bootstrap_replicates_invalid"]
        == calculation["bootstrap_replicates_requested"],
        "bootstrap replicate accounting mismatch",
    )

    return EmpiricalVerificationResult(
        unit_count=len(unit_ids),
        annotator_ids=(annotator_ids[0], annotator_ids[1]),
        adjudicator_id=adjudicator_id,
        adjudication_count=len(adjudications),
        reliability_report_sha256=report_digest,
    )
