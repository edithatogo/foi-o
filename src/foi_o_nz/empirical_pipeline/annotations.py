"""Role-isolated annotation locking and mechanical disagreement queues."""

from __future__ import annotations

import re
from itertools import pairwise
from typing import Any

from .contracts import content_sha256, seal_record
from .execution import VerifiedExecutionContext
from .packets import (
    PacketContractError,
    _canonical_units,
    _require_capability,
    _validate_execution_evidence,
    canonical_source_bundle_sha256,
)

SHA256 = re.compile(r"^[0-9a-f]{64}$")
ANNOTATION_FIELDS = frozenset({
    "unit_id",
    "unit_sha256",
    "role_id",
    "label",
    "abstention_reason",
    "spans",
})
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


class AnnotationContractError(ValueError):
    """Raised when annotation or disagreement evidence fails closed."""


def _translate_packet_error(action) -> None:
    try:
        action()
    except PacketContractError as error:
        raise AnnotationContractError(str(error)) from error


def _validate_span(span: object, text: str) -> dict[str, int]:
    if not isinstance(span, dict) or set(span) != {"start", "end"}:
        raise AnnotationContractError("span must contain exactly start and end")
    start, end = span.get("start"), span.get("end")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or start < 0
        or end <= start
        or end > len(text)
    ):
        raise AnnotationContractError("span is outside the packet text")
    return {"start": start, "end": end}


def _validate_record(
    record: dict[str, Any],
    *,
    packet_unit: dict[str, Any],
    role_id: str,
    labels: set[str],
    abstention_reasons: set[str],
) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != ANNOTATION_FIELDS:
        raise AnnotationContractError("annotation fields violate the strict field allowlist")
    if (
        record["unit_id"] != packet_unit["unit_id"]
        or record["unit_sha256"] != packet_unit["unit_sha256"]
    ):
        raise AnnotationContractError("annotation identity differs from its packet unit")
    if record["role_id"] != role_id:
        raise AnnotationContractError("annotation role differs from the isolated packet role")
    label = record["label"]
    reason = record["abstention_reason"]
    if label is None:
        if reason not in abstention_reasons:
            raise AnnotationContractError("null label requires a registered abstention reason")
    elif label not in labels:
        raise AnnotationContractError("annotation label is not registered")
    elif reason is not None:
        raise AnnotationContractError("labeled annotation cannot include an abstention reason")
    spans = record["spans"]
    if not isinstance(spans, list):
        raise AnnotationContractError("annotation spans must be an array")
    if label is None and spans:
        raise AnnotationContractError("abstention cannot include evidence spans")
    parsed_spans = [_validate_span(span, packet_unit["text"]) for span in spans]
    if parsed_spans != sorted(parsed_spans, key=lambda item: (item["start"], item["end"])):
        raise AnnotationContractError("spans must be sorted")
    if any(left["end"] > right["start"] for left, right in pairwise(parsed_spans)):
        raise AnnotationContractError("spans must not overlap")
    return seal_record({**record, "spans": parsed_spans}, "annotation_sha256")


def _require_packet_lineage(
    packet: dict[str, Any],
    *,
    calibration: dict[str, Any],
    authorization: dict[str, Any],
) -> list[dict[str, Any]]:
    from .packets import PACKET_FIELDS

    if set(packet) != PACKET_FIELDS:
        raise AnnotationContractError("packet fields violate the strict field allowlist")
    if packet.get("packet_sha256") != content_sha256(packet, "packet_sha256"):
        raise AnnotationContractError("invalid packet self-pin")
    if packet.get("packet_can_authorize_execution") is not False:
        raise AnnotationContractError("packet cannot self-authorize annotation")
    raw_units = packet.get("units")
    if not isinstance(raw_units, list):
        raise AnnotationContractError("packet units must be an array")
    try:
        units = _canonical_units(raw_units)
    except PacketContractError as error:
        raise AnnotationContractError(str(error)) from error
    if packet.get("source_bundle_sha256") != canonical_source_bundle_sha256(units):
        raise AnnotationContractError("packet source bundle binding mismatch")
    for field, expected in (
        ("calibration_sha256", calibration.get("calibration_sha256")),
        ("authorization_sha256", authorization.get("authorization_sha256")),
    ):
        if packet.get(field) != expected:
            raise AnnotationContractError(f"packet {field} mismatch")
    return units


def _require_packet_matches_context(
    packet: dict[str, Any],
    units: list[dict[str, Any]],
    context: VerifiedExecutionContext,
) -> None:
    expected = {
        "run_id": context.run_id,
        "run_spec_sha256": context.run_spec_sha256,
        "membership_sha256": context.membership_sha256,
        "codebook_sha256": context.codebook_sha256,
        "calibration_sha256": context.calibration_sha256,
        "authorization_sha256": context.authorization_sha256,
        "source_bundle_sha256": context.source_bundle_sha256,
    }
    if any(packet.get(field) != value for field, value in expected.items()):
        raise AnnotationContractError("packet lineage differs from verified context")
    if units != list(context.units):
        raise AnnotationContractError("packet units differ from verified source bundle")


def lock_annotation_output(
    *,
    context: VerifiedExecutionContext,
    packet: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate and lock one annotator role without exposing peer state."""
    run_spec = context.run_spec
    labels = set(context.codebook.labels)
    abstention_reasons = set(context.codebook.abstention_reasons)
    calibration = context.calibration
    authorization = context.authorization
    _translate_packet_error(
        lambda: _require_capability(context, "annotation", "annotation.execute")
    )
    packet_units = _require_packet_lineage(
        packet,
        calibration=calibration,
        authorization=authorization,
    )
    _require_packet_matches_context(packet, packet_units, context)
    membership_sha256 = packet.get("membership_sha256")
    codebook_sha256 = packet.get("codebook_sha256")
    if not isinstance(membership_sha256, str) or not isinstance(codebook_sha256, str):
        raise AnnotationContractError("packet evidence pins are invalid")
    role_id = packet.get("role_id")
    if not isinstance(role_id, str) or not role_id:
        raise AnnotationContractError("packet role is invalid")
    roles = set(authorization.get("approved_roles", []))
    _translate_packet_error(
        lambda: _validate_execution_evidence(
            run_spec=run_spec,
            membership_sha256=membership_sha256,
            codebook_sha256=codebook_sha256,
            roles=roles,
            required_capability="annotation.execute",
            source_bundle_sha256=packet["source_bundle_sha256"],
            calibration=calibration,
            authorization=authorization,
        )
    )
    for field, expected in (
        ("run_spec_sha256", run_spec.run_spec_sha256),
        ("calibration_sha256", calibration.get("calibration_sha256")),
        ("authorization_sha256", authorization.get("authorization_sha256")),
    ):
        if packet.get(field) != expected:
            raise AnnotationContractError(f"packet {field} mismatch")
    if role_id not in roles:
        raise AnnotationContractError("packet role is not approved")
    if not isinstance(records, list):
        raise AnnotationContractError("packet units and annotation records must be arrays")
    by_id = {unit.get("unit_id"): unit for unit in packet_units if isinstance(unit, dict)}
    if len(by_id) != len(packet_units):
        raise AnnotationContractError("packet contains duplicate unit identities")
    record_ids = [record.get("unit_id") for record in records if isinstance(record, dict)]
    if len(record_ids) != len(records) or len(set(record_ids)) != len(record_ids):
        raise AnnotationContractError("annotation records contain duplicate identities")
    if set(record_ids) != set(by_id):
        raise AnnotationContractError("annotation output is not complete for the packet")
    locked = [
        _validate_record(
            record,
            packet_unit=by_id[record["unit_id"]],
            role_id=role_id,
            labels=labels,
            abstention_reasons=abstention_reasons,
        )
        for record in sorted(records, key=lambda item: item["unit_id"])
    ]
    return seal_record(
        {
            "schema_version": "foio.empirical-locked-annotation-set.v1.0.0",
            "status": "locked",
            "run_id": run_spec.run_id,
            "run_spec_sha256": run_spec.run_spec_sha256,
            "membership_sha256": packet["membership_sha256"],
            "codebook_sha256": packet["codebook_sha256"],
            "calibration_sha256": calibration["calibration_sha256"],
            "authorization_sha256": authorization["authorization_sha256"],
            "packet_sha256": packet["packet_sha256"],
            "source_bundle_sha256": packet["source_bundle_sha256"],
            "role_id": role_id,
            "annotations": locked,
        },
        "annotation_set_sha256",
    )


def validate_locked_annotation_output(
    output: dict[str, Any],
    *,
    context: VerifiedExecutionContext,
    packet: dict[str, Any],
) -> None:
    """Revalidate a locked role output against its packet and external evidence."""
    _translate_packet_error(
        lambda: _require_capability(context, "annotation", "annotation.execute")
    )
    labels = set(context.codebook.labels)
    abstention_reasons = set(context.codebook.abstention_reasons)
    calibration = context.calibration
    authorization = context.authorization
    packet_units = _require_packet_lineage(
        packet,
        calibration=calibration,
        authorization=authorization,
    )
    _require_packet_matches_context(packet, packet_units, context)
    roles = set(authorization.get("approved_roles", []))
    _translate_packet_error(
        lambda: _validate_execution_evidence(
            run_spec=context.run_spec,
            membership_sha256=context.membership_sha256,
            codebook_sha256=context.codebook_sha256,
            roles=roles,
            required_capability="annotation.execute",
            source_bundle_sha256=context.source_bundle_sha256,
            calibration=calibration,
            authorization=authorization,
        )
    )
    if set(output) != LOCKED_OUTPUT_FIELDS:
        raise AnnotationContractError("locked annotation fields violate the strict allowlist")
    if output.get("annotation_set_sha256") != content_sha256(output, "annotation_set_sha256"):
        raise AnnotationContractError("invalid locked annotation self-pin")
    expected_lineage = {
        "status": "locked",
        "run_id": packet.get("run_id"),
        "run_spec_sha256": packet.get("run_spec_sha256"),
        "membership_sha256": packet.get("membership_sha256"),
        "codebook_sha256": packet.get("codebook_sha256"),
        "calibration_sha256": calibration.get("calibration_sha256"),
        "authorization_sha256": authorization.get("authorization_sha256"),
        "packet_sha256": packet.get("packet_sha256"),
        "source_bundle_sha256": packet.get("source_bundle_sha256"),
        "role_id": packet.get("role_id"),
    }
    for field, expected in expected_lineage.items():
        if output.get(field) != expected:
            raise AnnotationContractError(f"locked annotation {field} binding mismatch")
    records = []
    raw_records = output.get("annotations")
    if not isinstance(raw_records, list):
        raise AnnotationContractError("locked annotations must be an array")
    for record in raw_records:
        if not isinstance(record, dict) or set(record) != ANNOTATION_FIELDS | {"annotation_sha256"}:
            raise AnnotationContractError("locked annotation record structure is invalid")
        if record.get("annotation_sha256") != content_sha256(record, "annotation_sha256"):
            raise AnnotationContractError("invalid annotation record self-pin")
        records.append({key: record[key] for key in ANNOTATION_FIELDS})
    by_id = {unit["unit_id"]: unit for unit in packet_units}
    if len(by_id) != len(packet_units):
        raise AnnotationContractError("packet contains duplicate unit identities")
    record_ids = [record["unit_id"] for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise AnnotationContractError("locked annotation unit identities must be unique")
    if len(records) != len(packet_units) or set(record_ids) != set(by_id):
        raise AnnotationContractError("locked annotation output differs from its packet")
    expected = {
        record["annotation_sha256"]
        for record in (
            _validate_record(
                item,
                packet_unit=by_id[item["unit_id"]],
                role_id=packet["role_id"],
                labels=labels,
                abstention_reasons=abstention_reasons,
            )
            for item in records
        )
    }
    actual = {record["annotation_sha256"] for record in output["annotations"]}
    if expected != actual or len(actual) != len(packet["units"]):
        raise AnnotationContractError("locked annotation output differs from its packet")


def _dimensions(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    dimensions = []
    if left["label"] != right["label"]:
        dimensions.append("label")
    if left["abstention_reason"] != right["abstention_reason"]:
        dimensions.append("abstention")
    if left["spans"] != right["spans"]:
        dimensions.append("span")
    return dimensions


def _require_locked_structure(output: dict[str, Any]) -> None:
    if set(output) != LOCKED_OUTPUT_FIELDS:
        raise AnnotationContractError("locked annotation fields violate the strict allowlist")
    if output.get("annotation_set_sha256") != content_sha256(output, "annotation_set_sha256"):
        raise AnnotationContractError("invalid locked annotation self-pin")
    if output.get("status") != "locked":
        raise AnnotationContractError("annotation output is not locked")
    annotations = output.get("annotations")
    if not isinstance(annotations, list) or not annotations:
        raise AnnotationContractError("locked annotations must be a nonempty array")
    identities: set[str] = set()
    for record in annotations:
        if not isinstance(record, dict) or set(record) != ANNOTATION_FIELDS | {"annotation_sha256"}:
            raise AnnotationContractError("locked annotation record structure is invalid")
        if record.get("annotation_sha256") != content_sha256(record, "annotation_sha256"):
            raise AnnotationContractError("invalid annotation record self-pin")
        if record.get("role_id") != output.get("role_id"):
            raise AnnotationContractError("locked annotation role lineage mismatch")
        unit_id = record.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id or unit_id in identities:
            raise AnnotationContractError("locked annotation unit identities are invalid")
        identities.add(unit_id)


def derive_disagreements(
    left_output: dict[str, Any], right_output: dict[str, Any]
) -> list[dict[str, Any]]:
    """Derive disagreements mechanically from two distinct locked role outputs."""
    _require_locked_structure(left_output)
    _require_locked_structure(right_output)
    if left_output.get("role_id") == right_output.get("role_id"):
        raise AnnotationContractError("independent annotator roles must be distinct")
    for field in (
        "run_id",
        "run_spec_sha256",
        "membership_sha256",
        "codebook_sha256",
        "calibration_sha256",
        "authorization_sha256",
        "source_bundle_sha256",
    ):
        if left_output.get(field) != right_output.get(field):
            raise AnnotationContractError(f"annotation outputs have different {field}")
    left = {record["unit_id"]: record for record in left_output["annotations"]}
    right = {record["unit_id"]: record for record in right_output["annotations"]}
    if set(left) != set(right):
        raise AnnotationContractError("annotation outputs have different unit sets")
    disagreements = []
    for unit_id in sorted(left):
        if left[unit_id]["unit_sha256"] != right[unit_id]["unit_sha256"]:
            raise AnnotationContractError("cross-role unit identity digest mismatch")
        dimensions = _dimensions(left[unit_id], right[unit_id])
        if dimensions:
            disagreements.append(
                seal_record(
                    {
                        "unit_id": unit_id,
                        "unit_sha256": left[unit_id]["unit_sha256"],
                        "annotator_roles": [left_output["role_id"], right_output["role_id"]],
                        "run_id": left_output["run_id"],
                        "run_spec_sha256": left_output["run_spec_sha256"],
                        "membership_sha256": left_output["membership_sha256"],
                        "codebook_sha256": left_output["codebook_sha256"],
                        "calibration_sha256": left_output["calibration_sha256"],
                        "authorization_sha256": left_output["authorization_sha256"],
                        "source_bundle_sha256": left_output["source_bundle_sha256"],
                        "annotator_packet_sha256s": sorted([
                            left_output["packet_sha256"],
                            right_output["packet_sha256"],
                        ]),
                        "dimensions": dimensions,
                        "left_annotation": left[unit_id],
                        "right_annotation": right[unit_id],
                    },
                    "disagreement_sha256",
                )
            )
    return disagreements


def _queue_source_bundle_sha256(disagreements: list[dict[str, Any]]) -> str:
    pins = {
        disagreement.get("source_bundle_sha256")
        for disagreement in disagreements
        if isinstance(disagreement, dict)
    }
    if len(pins) != 1:
        raise AnnotationContractError(
            "adjudication disagreement queue requires one exact source bundle binding"
        )
    pin = next(iter(pins))
    if not isinstance(pin, str) or SHA256.fullmatch(pin) is None:
        raise AnnotationContractError("adjudication queue source bundle binding is invalid")
    return pin


def build_adjudication_queue(
    *,
    context: VerifiedExecutionContext,
    left_output: dict[str, Any],
    right_output: dict[str, Any],
    left_packet: dict[str, Any],
    right_packet: dict[str, Any],
    adjudicator_role: str,
) -> dict[str, Any]:
    """Build a locked queue containing recomputable disagreements only."""
    run_spec = context.run_spec
    membership_sha256 = context.membership_sha256
    codebook_sha256 = context.codebook_sha256
    calibration = context.calibration
    authorization = context.authorization
    _translate_packet_error(
        lambda: _require_capability(context, "annotation", "adjudication.queue.prepare")
    )
    validate_locked_annotation_output(left_output, context=context, packet=left_packet)
    validate_locked_annotation_output(right_output, context=context, packet=right_packet)
    disagreements = derive_disagreements(left_output, right_output)
    expected_packet_pins = sorted([left_output["packet_sha256"], right_output["packet_sha256"]])
    roles = set(authorization.get("approved_roles", []))
    annotator_roles = roles - {adjudicator_role}
    if adjudicator_role not in roles or len(annotator_roles) != 2:
        raise AnnotationContractError("adjudicator must be distinct from both annotators")
    observed_annotators = {
        role for disagreement in disagreements for role in disagreement.get("annotator_roles", [])
    }
    if adjudicator_role in observed_annotators:
        raise AnnotationContractError("adjudicator must be distinct from both annotators")
    _translate_packet_error(
        lambda: _validate_execution_evidence(
            run_spec=run_spec,
            membership_sha256=membership_sha256,
            codebook_sha256=codebook_sha256,
            roles=roles,
            required_capability="adjudication.queue.prepare",
            source_bundle_sha256=(
                _queue_source_bundle_sha256(disagreements)
                if disagreements
                else context.source_bundle_sha256
            ),
            calibration=calibration,
            authorization=authorization,
        )
    )
    items = []
    identities: set[str] = set()
    expected_lineage = {
        "run_id": run_spec.run_id,
        "run_spec_sha256": run_spec.run_spec_sha256,
        "membership_sha256": membership_sha256,
        "codebook_sha256": codebook_sha256,
        "calibration_sha256": calibration["calibration_sha256"],
        "authorization_sha256": authorization["authorization_sha256"],
    }
    common_source_bundle: str | None = context.source_bundle_sha256
    common_packet_pins: list[str] | None = expected_packet_pins
    for disagreement in disagreements:
        if disagreement.get("disagreement_sha256") != content_sha256(
            disagreement, "disagreement_sha256"
        ):
            raise AnnotationContractError("invalid disagreement self-pin")
        if set(disagreement.get("annotator_roles", [])) != annotator_roles:
            raise AnnotationContractError("disagreement annotator roles mismatch")
        for field, expected in expected_lineage.items():
            if disagreement.get(field) != expected:
                raise AnnotationContractError(f"disagreement {field} lineage mismatch")
        packet_pins = disagreement.get("annotator_packet_sha256s")
        if (
            not isinstance(packet_pins, list)
            or len(packet_pins) != 2
            or packet_pins != sorted(set(packet_pins))
            or any(SHA256.fullmatch(pin) is None for pin in packet_pins)
        ):
            raise AnnotationContractError("disagreement packet lineage is invalid")
        if SHA256.fullmatch(str(disagreement.get("source_bundle_sha256"))) is None:
            raise AnnotationContractError("disagreement source bundle lineage is invalid")
        if common_source_bundle is not None and disagreement["source_bundle_sha256"] != (
            common_source_bundle
        ):
            raise AnnotationContractError("disagreement source bundle lineage mismatch")
        if common_packet_pins is not None and packet_pins != common_packet_pins:
            raise AnnotationContractError("disagreement packet lineage mismatch")
        common_source_bundle = disagreement["source_bundle_sha256"]
        common_packet_pins = packet_pins
        for side in ("left_annotation", "right_annotation"):
            annotation = disagreement.get(side)
            if not isinstance(annotation, dict) or annotation.get(
                "annotation_sha256"
            ) != content_sha256(annotation, "annotation_sha256"):
                raise AnnotationContractError("invalid nested annotation self-pin")
        if not disagreement.get("dimensions") or disagreement["dimensions"] != _dimensions(
            disagreement["left_annotation"], disagreement["right_annotation"]
        ):
            raise AnnotationContractError("queue item is not a mechanical disagreement")
        unit_id = disagreement.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id:
            raise AnnotationContractError("disagreement unit identity is invalid")
        if unit_id in identities:
            raise AnnotationContractError("duplicate disagreement unit identity")
        identities.add(unit_id)
        items.append(disagreement)
    return seal_record(
        {
            "schema_version": "foio.empirical-adjudication-queue.v1.0.0",
            "status": "locked_disagreement_only_queue",
            "run_id": run_spec.run_id,
            "run_spec_sha256": run_spec.run_spec_sha256,
            "membership_sha256": membership_sha256,
            "codebook_sha256": codebook_sha256,
            "calibration_sha256": calibration["calibration_sha256"],
            "authorization_sha256": authorization["authorization_sha256"],
            "source_bundle_sha256": common_source_bundle,
            "annotator_packet_sha256s": common_packet_pins or [],
            "adjudicator_role": adjudicator_role,
            "queue_can_authorize_execution": False,
            "items": sorted(items, key=lambda item: item["unit_id"]),
        },
        "queue_sha256",
    )


def lock_adjudication_output(
    *,
    context: VerifiedExecutionContext,
    queue: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Lock adjudicator decisions for exactly the verified disagreement queue."""
    _translate_packet_error(
        lambda: _require_capability(context, "annotation", "annotation.execute")
    )
    if queue.get("queue_sha256") != content_sha256(queue, "queue_sha256"):
        raise AnnotationContractError("invalid adjudication queue self-pin")
    expected_queue = {
        "status": "locked_disagreement_only_queue",
        "run_id": context.run_id,
        "run_spec_sha256": context.run_spec_sha256,
        "membership_sha256": context.membership_sha256,
        "codebook_sha256": context.codebook_sha256,
        "calibration_sha256": context.calibration_sha256,
        "authorization_sha256": context.authorization_sha256,
        "source_bundle_sha256": context.source_bundle_sha256,
    }
    if any(queue.get(field) != value for field, value in expected_queue.items()):
        raise AnnotationContractError("adjudication queue differs from verified context")
    role = queue.get("adjudicator_role")
    if not isinstance(role, str) or role not in context.authorization.get("approved_roles", []):
        raise AnnotationContractError("adjudicator role is not approved")
    raw_item_ids = [item.get("unit_id") for item in queue.get("items", [])]
    if any(not isinstance(item_id, str) or not item_id for item_id in raw_item_ids):
        raise AnnotationContractError("adjudication queue identities are invalid")
    item_ids = [item_id for item_id in raw_item_ids if isinstance(item_id, str)]
    if len(item_ids) != len(set(item_ids)):
        raise AnnotationContractError("adjudication queue identities are invalid")
    by_unit = {unit["unit_id"]: unit for unit in context.units}
    raw_record_ids = [record.get("unit_id") for record in records]
    if any(not isinstance(record_id, str) or not record_id for record_id in raw_record_ids):
        raise AnnotationContractError("adjudication output identities are invalid")
    record_ids = [record_id for record_id in raw_record_ids if isinstance(record_id, str)]
    if sorted(record_ids) != sorted(item_ids):
        raise AnnotationContractError("adjudication output differs from disagreement queue")
    locked = [
        _validate_record(
            record,
            packet_unit=by_unit[record["unit_id"]],
            role_id=role,
            labels=set(context.codebook.labels),
            abstention_reasons=set(context.codebook.abstention_reasons),
        )
        for record in sorted(records, key=lambda item: item["unit_id"])
    ]
    return seal_record(
        {
            "schema_version": "foio.empirical-locked-annotation-set.v1.0.0",
            "status": "locked",
            "run_id": context.run_id,
            "run_spec_sha256": context.run_spec_sha256,
            "membership_sha256": context.membership_sha256,
            "codebook_sha256": context.codebook_sha256,
            "calibration_sha256": context.calibration_sha256,
            "authorization_sha256": context.authorization_sha256,
            "packet_sha256": queue["queue_sha256"],
            "source_bundle_sha256": context.source_bundle_sha256,
            "role_id": role,
            "annotations": locked,
        },
        "annotation_set_sha256",
    )


def validate_locked_adjudication_output(
    output: dict[str, Any], *, context: VerifiedExecutionContext, queue: dict[str, Any]
) -> None:
    """Revalidate adjudication against the exact approved queue and context."""
    if output.get("annotation_set_sha256") != content_sha256(output, "annotation_set_sha256"):
        raise AnnotationContractError("invalid adjudication output self-pin")
    records = output.get("annotations")
    if not isinstance(records, list):
        raise AnnotationContractError("adjudication records must be an array")
    raw_records = []
    for record in records:
        if not isinstance(record, dict) or set(record) != ANNOTATION_FIELDS | {"annotation_sha256"}:
            raise AnnotationContractError("adjudication record structure is invalid")
        if record.get("annotation_sha256") != content_sha256(record, "annotation_sha256"):
            raise AnnotationContractError("invalid adjudication record self-pin")
        raw_records.append({field: record[field] for field in ANNOTATION_FIELDS})
    expected = lock_adjudication_output(context=context, queue=queue, records=raw_records)
    if output != expected:
        raise AnnotationContractError("adjudication output differs from approved queue")
