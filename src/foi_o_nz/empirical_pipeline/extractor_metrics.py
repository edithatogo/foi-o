"""Pure adjudicated-reference construction and extractor evaluation."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from itertools import pairwise
from typing import Any, cast

from .annotations import (
    AnnotationContractError,
    build_adjudication_queue,
    validate_locked_adjudication_output,
    validate_locked_annotation_output,
)
from .contracts import content_sha256, seal_record
from .execution import ExecutionContextError, VerifiedExecutionContext
from .packets import canonical_unit_sha256

Prediction = dict[str, Any]
Extractor = Callable[[dict[str, Any]], Prediction]
SHA256 = re.compile(r"^[0-9a-f]{64}$")
LOCKED_OUTPUT_FIELDS = frozenset({
    "schema_version",
    "status",
    "run_id",
    "run_spec_sha256",
    "membership_sha256",
    "codebook_sha256",
    "calibration_sha256",
    "authorization_sha256",
    "packet_sha256",
    "source_bundle_sha256",
    "role_id",
    "annotations",
    "annotation_set_sha256",
})
COMMON_LINEAGE_FIELDS = (
    "run_id",
    "run_spec_sha256",
    "membership_sha256",
    "codebook_sha256",
    "calibration_sha256",
    "authorization_sha256",
    "source_bundle_sha256",
)


class ExtractorMetricsContractError(ValueError):
    """Raised when reference or extractor evidence fails closed."""


def _require_capability(context: VerifiedExecutionContext) -> None:
    if not isinstance(context, VerifiedExecutionContext):
        raise ExtractorMetricsContractError("verified execution context is required")
    try:
        context.require_capability("extractor_metrics", "extractor_metrics.compute")
    except ExecutionContextError as error:
        raise ExtractorMetricsContractError(str(error)) from error


def _locked(output: dict[str, Any], *, allow_subset: bool = False) -> dict[str, dict[str, Any]]:
    if set(output) != LOCKED_OUTPUT_FIELDS:
        raise ExtractorMetricsContractError(
            "locked annotation lineage is incomplete or has extra fields"
        )
    if output.get("annotation_set_sha256") != content_sha256(output, "annotation_set_sha256"):
        raise ExtractorMetricsContractError("invalid locked annotation set self-pin")
    if output.get("status") != "locked":
        raise ExtractorMetricsContractError("annotation set is not locked")
    for field in (
        "run_spec_sha256",
        "membership_sha256",
        "codebook_sha256",
        "calibration_sha256",
        "authorization_sha256",
        "packet_sha256",
        "source_bundle_sha256",
    ):
        if SHA256.fullmatch(str(output.get(field))) is None:
            raise ExtractorMetricsContractError(f"locked annotation {field} lineage is invalid")
    if not isinstance(output.get("run_id"), str) or not output["run_id"]:
        raise ExtractorMetricsContractError("locked annotation run lineage is invalid")
    if not isinstance(output.get("role_id"), str) or not output["role_id"]:
        raise ExtractorMetricsContractError("locked annotation role lineage is invalid")
    rows = output.get("annotations")
    if not isinstance(rows, list) or (not rows and not allow_subset):
        raise ExtractorMetricsContractError("annotation set is empty")
    parsed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("annotation_sha256") != content_sha256(
            row, "annotation_sha256"
        ):
            raise ExtractorMetricsContractError("invalid annotation record self-pin")
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id or unit_id in parsed:
            raise ExtractorMetricsContractError("annotation identities must be unique")
        if row.get("role_id") != output.get("role_id"):
            raise ExtractorMetricsContractError("annotation role differs from its locked set")
        parsed[unit_id] = row
    return parsed


def _membership_rows(membership: dict[str, Any]) -> dict[str, str]:
    if membership.get("membership_sha256") != content_sha256(membership, "membership_sha256"):
        raise ExtractorMetricsContractError("invalid membership self-pin")
    if membership.get("status") != "candidate_membership":
        raise ExtractorMetricsContractError("membership is not a candidate membership")
    rows = membership.get("membership")
    if not isinstance(rows, list) or not rows:
        raise ExtractorMetricsContractError("membership must contain units")
    parsed: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ExtractorMetricsContractError("membership row must be an object")
        unit_id, digest = row.get("unit_id"), row.get("unit_sha256")
        if not isinstance(unit_id, str) or not unit_id or unit_id in parsed:
            raise ExtractorMetricsContractError("membership unit identities must be unique")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ExtractorMetricsContractError("membership unit digest must be lowercase SHA-256")
        parsed[unit_id] = digest
    return parsed


def _same_annotation(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return all(
        left.get(field) == right.get(field)
        for field in ("unit_id", "unit_sha256", "label", "abstention_reason", "spans")
    )


def build_adjudicated_reference(
    *,
    context: VerifiedExecutionContext,
    left: dict[str, Any],
    right: dict[str, Any],
    adjudication: dict[str, Any],
    left_packet: dict[str, Any],
    right_packet: dict[str, Any],
    adjudication_queue: dict[str, Any],
) -> dict[str, Any]:
    """Resolve exactly the annotator disagreement set into a non-gold reference."""
    _require_capability(context)
    run_spec = context.run_spec
    membership = context.membership
    try:
        validate_locked_annotation_output(left, context=context, packet=left_packet)
        validate_locked_annotation_output(right, context=context, packet=right_packet)
        expected_queue = build_adjudication_queue(
            context=context,
            left_output=left,
            right_output=right,
            left_packet=left_packet,
            right_packet=right_packet,
            adjudicator_role=str(adjudication.get("role_id")),
        )
        if adjudication_queue != expected_queue:
            raise AnnotationContractError(
                "adjudication queue differs from exact annotator disagreements"
            )
        validate_locked_adjudication_output(adjudication, context=context, queue=adjudication_queue)
    except AnnotationContractError as error:
        raise ExtractorMetricsContractError(str(error)) from error
    membership_rows = _membership_rows(membership)
    left_rows, right_rows = _locked(left), _locked(right)
    adjudicated_rows = _locked(adjudication, allow_subset=True)
    roles = {left.get("role_id"), right.get("role_id"), adjudication.get("role_id")}
    if len(roles) != 3:
        raise ExtractorMetricsContractError("annotator and adjudicator roles must be distinct")
    for field in COMMON_LINEAGE_FIELDS:
        if left.get(field) != right.get(field) or left.get(field) != adjudication.get(field):
            raise ExtractorMetricsContractError(f"annotation {field} lineage mismatch")
    packet_hashes = {
        left.get("packet_sha256"),
        right.get("packet_sha256"),
        adjudication.get("packet_sha256"),
    }
    if len(packet_hashes) != 3:
        raise ExtractorMetricsContractError("distinct roles must have distinct packet lineage")
    if left.get("run_id") != run_spec.run_id:
        raise ExtractorMetricsContractError("annotation run identity mismatch")
    if left.get("run_spec_sha256") != run_spec.run_spec_sha256:
        raise ExtractorMetricsContractError("annotation run specification mismatch")
    if left.get("membership_sha256") != membership.get("membership_sha256"):
        raise ExtractorMetricsContractError("annotation membership lineage mismatch")
    if set(left_rows) != set(right_rows):
        raise ExtractorMetricsContractError("annotator unit sets differ")
    if set(left_rows) != set(membership_rows):
        raise ExtractorMetricsContractError("annotator units differ from exact membership")
    for unit_id in left_rows:
        left_digest = left_rows[unit_id].get("unit_sha256")
        if left_digest != right_rows[unit_id].get("unit_sha256"):
            raise ExtractorMetricsContractError("cross-role unit identity digest mismatch")
        if left_digest != membership_rows[unit_id]:
            raise ExtractorMetricsContractError("annotation unit digest differs from membership")
    disagreements = {
        unit_id
        for unit_id in left_rows
        if not _same_annotation(left_rows[unit_id], right_rows[unit_id])
    }
    if set(adjudicated_rows) != disagreements:
        raise ExtractorMetricsContractError(
            "adjudication must contain exactly the annotator disagreement set"
        )
    for unit_id, row in adjudicated_rows.items():
        if row.get("unit_sha256") != membership_rows[unit_id]:
            raise ExtractorMetricsContractError("adjudication unit digest differs from membership")
    records = []
    for unit_id in sorted(left_rows):
        source = adjudicated_rows.get(unit_id, left_rows[unit_id])
        if source.get("unit_sha256") != left_rows[unit_id].get("unit_sha256"):
            raise ExtractorMetricsContractError("adjudication unit digest mismatch")
        records.append(
            seal_record(
                {
                    "unit_id": unit_id,
                    "unit_sha256": source["unit_sha256"],
                    "label": source.get("label"),
                    "abstention_reason": source.get("abstention_reason"),
                    "spans": source.get("spans"),
                    "resolution": (
                        "adjudicated" if unit_id in adjudicated_rows else "annotator_agreement"
                    ),
                    "source_annotation_sha256": source["annotation_sha256"],
                },
                "reference_record_sha256",
            )
        )
    return seal_record(
        {
            "schema_version": "foio.empirical-adjudicated-reference.v1.0.0",
            "status": "locked_non_gold_reference",
            "run_id": run_spec.run_id,
            "run_spec_sha256": run_spec.run_spec_sha256,
            "membership_sha256": membership["membership_sha256"],
            "codebook_sha256": left["codebook_sha256"],
            "calibration_sha256": left["calibration_sha256"],
            "authorization_sha256": left["authorization_sha256"],
            "source_bundle_sha256": left["source_bundle_sha256"],
            "annotation_lineage": [
                {
                    "role_id": output["role_id"],
                    "packet_sha256": output["packet_sha256"],
                    "annotation_set_sha256": output["annotation_set_sha256"],
                }
                for output in sorted((left, right, adjudication), key=lambda item: item["role_id"])
            ],
            "annotation_set_sha256": [
                left["annotation_set_sha256"],
                right["annotation_set_sha256"],
                adjudication["annotation_set_sha256"],
            ],
            "records": records,
            "gold_promotion_authorized": False,
            "profile_promotion_authorized": False,
        },
        "reference_sha256",
    )


def _spans(value: object, text: str, *, allow_empty: bool = True) -> list[dict[str, int]]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ExtractorMetricsContractError("prediction spans are invalid")
    parsed = []
    for span in value:
        if not isinstance(span, dict) or set(span) != {"start", "end"}:
            raise ExtractorMetricsContractError("prediction span fields are invalid")
        span_dict = cast("dict[str, Any]", span)
        start, end = span_dict["start"], span_dict["end"]
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 0
            or end <= start
            or end > len(text)
        ):
            raise ExtractorMetricsContractError("prediction span is outside unit text")
        parsed.append({"start": start, "end": end})
    if parsed != sorted(parsed, key=lambda item: (item["start"], item["end"])):
        raise ExtractorMetricsContractError("prediction spans must be sorted")
    if any(a["end"] > b["start"] for a, b in pairwise(parsed)):
        raise ExtractorMetricsContractError("prediction spans must not overlap")
    return parsed


def _prf(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _span_iou(reference: list[dict[str, int]], predicted: list[dict[str, int]]) -> float:
    ref_points = {point for span in reference for point in range(span["start"], span["end"])}
    pred_points = {point for span in predicted for point in range(span["start"], span["end"])}
    union = ref_points | pred_points
    return len(ref_points & pred_points) / len(union) if union else 1.0


def evaluate_extractor(
    *,
    context: VerifiedExecutionContext,
    reference: dict[str, Any],
    left_annotation: dict[str, Any],
    right_annotation: dict[str, Any],
    adjudication: dict[str, Any],
    left_packet: dict[str, Any],
    right_packet: dict[str, Any],
    adjudication_queue: dict[str, Any],
    extractor: Extractor,
    provenance_required_fields: set[str] | None = None,
    span_iou_threshold: float | None = None,
) -> dict[str, Any]:
    """Evaluate a callable extractor against an exact locked reference population."""
    _require_capability(context)
    run_spec = context.run_spec
    membership = context.membership
    units = list(context.units)
    labels = set(context.codebook.labels)
    membership_rows = _membership_rows(membership)
    expected_reference = build_adjudicated_reference(
        context=context,
        left=left_annotation,
        right=right_annotation,
        adjudication=adjudication,
        left_packet=left_packet,
        right_packet=right_packet,
        adjudication_queue=adjudication_queue,
    )
    if reference != expected_reference:
        raise ExtractorMetricsContractError(
            "reference differs from exact approved annotation and adjudication artifacts"
        )
    if reference.get("reference_sha256") != content_sha256(reference, "reference_sha256"):
        raise ExtractorMetricsContractError("invalid adjudicated reference self-pin")
    if (
        reference.get("status") != "locked_non_gold_reference"
        or reference.get("run_spec_sha256") != run_spec.run_spec_sha256
        or reference.get("run_id") != run_spec.run_id
    ):
        raise ExtractorMetricsContractError("reference is not bound to this run")
    if reference.get("membership_sha256") != membership.get("membership_sha256"):
        raise ExtractorMetricsContractError("reference membership lineage mismatch")
    expected_lineage = {
        "codebook_sha256": context.codebook_sha256,
        "calibration_sha256": context.calibration_sha256,
        "authorization_sha256": context.authorization_sha256,
        "source_bundle_sha256": context.source_bundle_sha256,
    }
    if any(reference.get(field) != value for field, value in expected_lineage.items()):
        raise ExtractorMetricsContractError("reference lineage differs from verified context")
    annotation_lineage = reference.get("annotation_lineage")
    if not isinstance(annotation_lineage, list) or len(annotation_lineage) != 3:
        raise ExtractorMetricsContractError("reference annotation lineage is incomplete")
    roles: set[str] = set()
    packets: set[str] = set()
    annotation_sets: set[str] = set()
    for item in annotation_lineage:
        if not isinstance(item, dict) or set(item) != {
            "role_id",
            "packet_sha256",
            "annotation_set_sha256",
        }:
            raise ExtractorMetricsContractError("reference annotation lineage is malformed")
        role = item.get("role_id")
        packet_sha = item.get("packet_sha256")
        annotation_sha = item.get("annotation_set_sha256")
        if (
            not isinstance(role, str)
            or not role
            or not isinstance(packet_sha, str)
            or SHA256.fullmatch(packet_sha) is None
            or not isinstance(annotation_sha, str)
            or SHA256.fullmatch(annotation_sha) is None
        ):
            raise ExtractorMetricsContractError("reference annotation lineage is invalid")
        roles.add(role)
        packets.add(packet_sha)
        annotation_sets.add(annotation_sha)
    if len(roles) != 3 or len(packets) != 3 or len(annotation_sets) != 3:
        raise ExtractorMetricsContractError("reference annotation role lineage is not distinct")
    if sorted(annotation_sets) != sorted(reference.get("annotation_set_sha256", [])):
        raise ExtractorMetricsContractError("reference annotation set lineage mismatch")
    if not callable(extractor):
        raise ExtractorMetricsContractError("extractor must be callable")
    if not labels or any(not isinstance(label, str) or not label for label in labels):
        raise ExtractorMetricsContractError("labels must be registered nonempty strings")
    if span_iou_threshold is not None and (
        not isinstance(span_iou_threshold, float) or not 0 <= span_iou_threshold <= 1
    ):
        raise ExtractorMetricsContractError("span IoU threshold must be between zero and one")
    required = provenance_required_fields or set()
    references: dict[str, dict[str, Any]] = {}
    for row in reference.get("records", []):
        if not isinstance(row, dict) or row.get("reference_record_sha256") != content_sha256(
            row, "reference_record_sha256"
        ):
            raise ExtractorMetricsContractError("invalid reference record self-pin")
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id or unit_id in references:
            raise ExtractorMetricsContractError("reference identities must be unique")
        references[unit_id] = row
    if set(references) != set(membership_rows):
        raise ExtractorMetricsContractError("reference differs from exact membership")
    for unit_id, digest in membership_rows.items():
        if references[unit_id].get("unit_sha256") != digest:
            raise ExtractorMetricsContractError("reference unit digest differs from membership")
    unit_map: dict[str, dict[str, Any]] = {}
    for unit in units:
        if (
            not isinstance(unit, dict)
            or set(unit)
            not in (
                {"unit_id", "unit_sha256", "text"},
                {"unit_id", "unit_sha256", "text", "source_spans"},
            )
            or not isinstance(unit.get("unit_id"), str)
            or not unit.get("unit_id")
            or not isinstance(unit.get("text"), str)
            or unit.get("unit_id") in unit_map
        ):
            raise ExtractorMetricsContractError("evaluation unit violates strict input contract")
        if canonical_unit_sha256(unit) != unit.get("unit_sha256"):
            raise ExtractorMetricsContractError("evaluation unit content hash mismatch")
        unit_map[unit["unit_id"]] = unit
    if set(unit_map) != set(references):
        raise ExtractorMetricsContractError("units differ from exact reference population")
    for unit_id, unit in unit_map.items():
        if unit["unit_sha256"] != references[unit_id].get("unit_sha256"):
            raise ExtractorMetricsContractError("unit digest differs from reference")

    confusion_rows = []
    tp = fp = fn = covered = exact_span = iou_matched = provenance_complete = 0
    all_unit_exact_span = 0
    span_eligible_pairs = 0
    for unit_id in sorted(unit_map):
        unit, ref = unit_map[unit_id], references[unit_id]
        prediction = extractor(dict(unit))
        if not isinstance(prediction, dict) or set(prediction) != {"label", "spans", "provenance"}:
            raise ExtractorMetricsContractError("prediction violates strict output contract")
        label = prediction["label"]
        if label is not None and label not in labels:
            raise ExtractorMetricsContractError("prediction label is not registered")
        spans = _spans(prediction["spans"], unit["text"])
        if label is None and spans:
            raise ExtractorMetricsContractError("null prediction cannot contain spans")
        provenance = prediction["provenance"]
        if not isinstance(provenance, dict):
            raise ExtractorMetricsContractError("prediction provenance must be an object")
        ref_label = ref["label"]
        if ref_label is not None and ref_label not in labels:
            raise ExtractorMetricsContractError("reference label is not registered")
        if label is not None:
            covered += 1
            if all(
                field in provenance and provenance[field] not in (None, "") for field in required
            ):
                provenance_complete += 1
        correct = label is not None and label == ref_label
        tp += int(correct)
        fp += int(label is not None and not correct)
        fn += int(ref_label is not None and not correct)
        all_unit_exact_span += int(spans == ref["spans"])
        span_eligible = label is not None and label == ref_label
        if span_eligible:
            span_eligible_pairs += 1
            exact_span += int(spans == ref["spans"])
            if span_iou_threshold is not None:
                iou_matched += int(_span_iou(ref["spans"], spans) >= span_iou_threshold)
        confusion_rows.append({
            "unit_id": unit_id,
            "unit_sha256": unit["unit_sha256"],
            "reference_label": ref_label,
            "predicted_label": label,
            "label_match": label == ref_label,
            "exact_span_match": spans == ref["spans"],
            "span_threshold_eligible": span_eligible,
        })
    count = len(unit_map)
    record = {
        "schema_version": "foio.empirical-extractor-metrics.v1.0.0",
        "status": "computed_descriptive",
        "run_id": run_spec.run_id,
        "run_spec_sha256": run_spec.run_spec_sha256,
        "membership_sha256": membership["membership_sha256"],
        "codebook_sha256": reference["codebook_sha256"],
        "population_sha256": context.population_sha256("extractor_metrics"),
        "calibration_artifact_sha256": context.calibration_artifact_sha256,
        "authorization_artifact_sha256": context.authorization_artifact_sha256,
        "calibration_sha256": reference["calibration_sha256"],
        "authorization_sha256": reference["authorization_sha256"],
        "source_bundle_sha256": reference["source_bundle_sha256"],
        "annotation_lineage": annotation_lineage,
        "reference_sha256": reference["reference_sha256"],
        "unit_count": count,
        "label_metrics": _prf(tp, fp, fn),
        "coverage": {
            "numerator": covered,
            "denominator": count,
            "estimate": covered / count,
        },
        "all_unit_exact_span": {
            "numerator": all_unit_exact_span,
            "denominator": count,
            "estimate": all_unit_exact_span / count,
            "eligibility": "all_units_including_null_labels",
            "threshold_eligible": False,
        },
        "exact_span": {
            "numerator": exact_span,
            "denominator": span_eligible_pairs,
            "estimate": exact_span / span_eligible_pairs if span_eligible_pairs else None,
            "eligibility": "matching_non_null_label",
            "threshold_eligible": True,
        },
        "span_iou": (
            {
                "threshold": span_iou_threshold,
                "matched": iou_matched,
                "denominator": span_eligible_pairs,
                "estimate": iou_matched / span_eligible_pairs if span_eligible_pairs else None,
                "eligibility": "matching_non_null_label",
                "threshold_eligible": False,
            }
            if span_iou_threshold is not None
            else None
        ),
        "provenance_completeness": {
            "required_fields": sorted(required),
            "numerator": provenance_complete,
            "denominator": covered,
            "estimate": provenance_complete / covered if covered else None,
            "threshold_eligible": False,
        },
        "confusion_rows": confusion_rows,
        "gold_promotion_authorized": False,
        "profile_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    if any(
        isinstance(value, float) and (math.isnan(value) or math.isinf(value))
        for metric in (record["label_metrics"], record["coverage"])
        for value in metric.values()
    ):
        raise ExtractorMetricsContractError("non-finite metric")
    return seal_record(record, "extractor_metrics_sha256")
