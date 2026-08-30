"""Bounded automated AU-CTH annotation roles and disagreement-only adjudication."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

MEMBERSHIP_SHA256 = "f86ed488429009bf3d6a78a7853cca8bb67b8783c728d5ffd255575a9665bda7"
CODEBOOK_SHA256 = "ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9"
PROTOCOL_SHA256 = "9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf"
_A_OBSERVED = re.compile(r"\bfreedom\s+of\s+information\b|\bfoi\b", re.IGNORECASE)
_B_OBSERVED = re.compile(r"\bfreedom\s+of\s+information\b|\bfoi\s+(?:request|act)\b", re.IGNORECASE)
_CANDIDATE = re.compile(r"\binformation\s+request\b|\brequest\s+for\s+information\b", re.IGNORECASE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _annotate(unit: dict[str, Any], text: str, *, role: str) -> dict[str, Any]:
    observed = _A_OBSERVED if role == "agent:au-cth-annotator-a" else _B_OBSERVED
    match = observed.search(text)
    label = (
        "observed" if match else "candidate" if (match := _CANDIDATE.search(text)) else "unknown"
    )
    return {
        "unit_id": unit["unit_id"],
        "unit_sha256": unit["unit_sha256"],
        "role": role,
        "label": label,
        "abstention": label == "unknown",
        "abstention_reason": "insufficient_evidence" if label == "unknown" else None,
        "span": None
        if match is None
        else {
            "start": match.start(),
            "end": match.end(),
            "coordinate_system": "utf8_character_half_open",
        },
    }


def validate_annotation_record(record: dict[str, Any], *, expected_role: str) -> None:
    """Validate one locked automated role record without consulting peer output."""
    if record.get("role") != expected_role:
        raise ValueError("annotation role identity mismatch")
    if not isinstance(record.get("unit_id"), str) or not record["unit_id"]:
        raise ValueError("annotation unit identity is missing")
    unit_sha256 = record.get("unit_sha256")
    if not isinstance(unit_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", unit_sha256):
        raise ValueError("annotation unit SHA-256 is invalid")
    if record.get("label") not in {"observed", "inferred", "candidate", "unknown"}:
        raise ValueError("annotation label is not in the approved codebook")
    abstention = record.get("abstention")
    if not isinstance(abstention, bool):
        raise ValueError("annotation abstention must be boolean")
    span = record.get("span")
    reason = record.get("abstention_reason")
    allowed_reasons = {"missing_evidence", "insufficient_evidence", "out_of_scope", "other"}
    if reason is not None and reason not in allowed_reasons:
        raise ValueError("annotation abstention reason is not in the approved codebook")
    if abstention:
        if record.get("label") != "unknown" or not reason:
            raise ValueError("abstention requires unknown label and reason")
        if span is not None:
            raise ValueError("abstention span must be null")
    elif record.get("label") == "unknown" or record.get("abstention_reason") is not None:
        raise ValueError("non-abstaining annotation has invalid null encoding")
    elif not isinstance(span, dict):
        raise ValueError("non-abstaining annotation requires a span")
    if span is not None:
        if span.get("coordinate_system") != "utf8_character_half_open":
            raise ValueError("annotation span coordinate system is invalid")
        if (
            not isinstance(span.get("start"), int)
            or not isinstance(span.get("end"), int)
            or span["start"] < 0
            or span["end"] <= span["start"]
            or span["end"] - span["start"] > 1000
        ):
            raise ValueError("annotation span bounds are invalid")


def validate_annotation_packet(packet: dict[str, Any], *, expected_role: str | None = None) -> None:
    """Validate one blinded annotation packet before or during role execution."""
    if not isinstance(packet, dict):
        raise ValueError("packet must be an object")
    role = packet.get("role")
    if not isinstance(role, str) or not role.startswith("agent:"):
        raise ValueError("packet role identity is missing or invalid")
    if expected_role is not None and role != expected_role:
        raise ValueError("packet role identity mismatch")
    if packet.get("blinded_to_peer") is not True:
        raise ValueError("packet must be blinded to peer annotator")
    if packet.get("blinded_to_extractor") is not True:
        raise ValueError("packet must be blinded to extractor")
    units = packet.get("units")
    if not isinstance(units, list) or not units:
        raise ValueError("packet units must be a non-empty list")
    seen_units: set[str] = set()
    for item in units:
        if not isinstance(item, dict):
            raise ValueError("packet unit item is not an object")
        unit_id = item.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id:
            raise ValueError("packet unit_id is missing")
        if unit_id in seen_units:
            raise ValueError(f"duplicate unit_id in packet: {unit_id}")
        seen_units.add(unit_id)
        unit_sha256 = item.get("unit_sha256")
        if not isinstance(unit_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", unit_sha256):
            raise ValueError("packet unit SHA-256 is invalid")
        text_filename = item.get("text_filename")
        if not isinstance(text_filename, str) or not text_filename:
            raise ValueError("packet text_filename is missing")
        if any(
            leak_key in item
            for leak_key in (
                "label",
                "span",
                "peer_label",
                "extractor_label",
                "confidence",
            )
        ):
            raise ValueError("packet contains unblinded label or extractor prediction metadata")


def validate_adjudication_record(
    record: dict[str, Any], *, expected_role: str = "agent:au-cth-adjudicator"
) -> None:
    """Validate one adjudication record."""
    if not isinstance(record, dict):
        raise ValueError("adjudication record must be an object")
    if record.get("role") != expected_role:
        raise ValueError("adjudication role identity mismatch")
    if not isinstance(record.get("unit_id"), str) or not record["unit_id"]:
        raise ValueError("adjudication unit identity is missing")
    outcome = record.get("outcome")
    if outcome not in {"resolved", "unresolved"}:
        raise ValueError("adjudication outcome is invalid")
    label = record.get("label")
    if outcome == "resolved":
        if label not in {"observed", "inferred", "candidate", "unknown"}:
            raise ValueError("resolved adjudication label is not in approved codebook")
    elif label is not None:
        raise ValueError("unresolved adjudication label must be null")
    rationale = record.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("adjudication rationale is required")


def validate_disagreement_queue(disagreements: list[dict[str, Any]]) -> None:
    """Validate disagreement queue accounting and structure."""
    if not isinstance(disagreements, list):
        raise ValueError("disagreement queue must be a list")
    seen_units: set[str] = set()
    for row in disagreements:
        if not isinstance(row, dict):
            raise ValueError("disagreement item must be an object")
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id:
            raise ValueError("disagreement unit_id is missing")
        if unit_id in seen_units:
            raise ValueError(f"duplicate unit_id in disagreement queue: {unit_id}")
        seen_units.add(unit_id)
        if row.get("a_label") not in {"observed", "inferred", "candidate", "unknown"}:
            raise ValueError("disagreement a_label is invalid")
        if row.get("b_label") not in {"observed", "inferred", "candidate", "unknown"}:
            raise ValueError("disagreement b_label is invalid")
        if not isinstance(row.get("dimension"), str) or not row["dimension"]:
            raise ValueError("disagreement dimension is required")


def validate_metric_inputs(report: dict[str, Any]) -> None:
    """Validate report inputs and calculation integrity before metric derivation."""
    if not isinstance(report, dict):
        raise ValueError("metric input report must be an object")
    unit_count = report.get("unit_count")
    if not isinstance(unit_count, int) or unit_count <= 0:
        raise ValueError("metric input unit_count must be a positive integer")
    raw_agreement = report.get("raw_label_agreement")
    if not isinstance(raw_agreement, dict):
        raise ValueError("raw_label_agreement must be an object")
    num = raw_agreement.get("numerator")
    den = raw_agreement.get("denominator")
    est = raw_agreement.get("estimate")
    if (
        not isinstance(num, int)
        or not isinstance(den, int)
        or den != unit_count
        or num < 0
        or num > den
    ):
        raise ValueError("raw_label_agreement numerator/denominator mismatch")
    if not isinstance(est, (int, float)) or abs(est - (num / den)) > 1e-9:
        raise ValueError("raw_label_agreement estimate mismatch")
    disagreements = report.get("disagreement_count")
    adjudications = report.get("adjudication_count")
    if (
        not isinstance(disagreements, int)
        or not isinstance(adjudications, int)
        or disagreements != adjudications
    ):
        raise ValueError("disagreement_count and adjudication_count mismatch")
    if any(item is not False for key, item in report.items() if key.endswith("_authorized")):
        raise ValueError("metric inputs contain unauthorized promotion/release flags")


def run_annotation(
    *,
    membership_path: Path,
    frame_path: Path,
    text_root: Path,
    codebook_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Execute two blinded automated roles, then adjudicate exact disagreements only."""
    if _sha256(membership_path) != MEMBERSHIP_SHA256 or _sha256(codebook_path) != CODEBOOK_SHA256:
        raise ValueError("membership or approved codebook SHA-256 mismatch")
    membership = json.loads(membership_path.read_text(encoding="utf-8"))
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    units = {unit["unit_id"]: unit for unit in frame["units"]}
    selected_value = membership.get("membership")
    if not isinstance(selected_value, list) or len(selected_value) != 385:
        raise ValueError("candidate membership is not the approved 385-unit set")
    selected = cast("list[dict[str, Any]]", selected_value)
    chosen = [units[row["unit_id"]] for row in selected]
    if any(
        unit["unit_sha256"] != row["unit_sha256"]
        for unit, row in zip(chosen, selected, strict=True)
    ):
        raise ValueError("candidate membership escaped the frozen frame")
    output_root.mkdir(parents=True, exist_ok=True)
    packets = {}
    annotations: dict[str, list[dict[str, Any]]] = {}
    for role in ("agent:au-cth-annotator-a", "agent:au-cth-annotator-b"):
        packet = [
            {key: unit[key] for key in ("unit_id", "unit_sha256", "text_filename", "source_spans")}
            for unit in chosen
        ]
        packet_path = output_root / f"{role.rsplit(':', 1)[1]}.packet.json"
        packet_path.write_text(
            json.dumps(
                {
                    "role": role,
                    "blinded_to_peer": True,
                    "blinded_to_extractor": True,
                    "units": packet,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        packets[role] = _sha256(packet_path)
        annotations[role] = [
            _annotate(
                unit,
                (text_root / unit["text_filename"]).read_text(encoding="utf-8").rstrip("\n"),
                role=role,
            )
            for unit in chosen
        ]
        (output_root / f"{role.rsplit(':', 1)[1]}.annotations.json").write_text(
            json.dumps(annotations[role], indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    a, b = annotations.values()
    disagreements = [
        {
            "unit_id": left["unit_id"],
            "a_label": left["label"],
            "b_label": right["label"],
            "dimension": "label_or_span_or_abstention",
        }
        for left, right in zip(a, b, strict=True)
        if (left["label"], left["span"], left["abstention"])
        != (right["label"], right["span"], right["abstention"])
    ]
    adjudications = [
        {
            "unit_id": row["unit_id"],
            "role": "agent:au-cth-adjudicator",
            "outcome": "resolved",
            "label": "observed" if "observed" in {row["a_label"], row["b_label"]} else "candidate",
            "rationale": "Distinct disagreement-only automated adjudication under the approved codebook.",
        }
        for row in disagreements
    ]
    (output_root / "adjudications.json").write_text(
        json.dumps(adjudications, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    matches = sum(left["label"] == right["label"] for left, right in zip(a, b, strict=True))
    report = {
        "schema": "foi-o.au-cth-subset-automated-annotation-report.v1",
        "status": "bounded_automated_annotation_not_gold",
        "membership_sha256": MEMBERSHIP_SHA256,
        "codebook_sha256": CODEBOOK_SHA256,
        "protocol_sha256": PROTOCOL_SHA256,
        "roles": [
            "agent:au-cth-annotator-a",
            "agent:au-cth-annotator-b",
            "agent:au-cth-adjudicator",
        ],
        "packet_sha256": packets,
        "annotation_sha256": {
            role: _sha256(output_root / f"{role.rsplit(':', 1)[1]}.annotations.json")
            for role in annotations
        },
        "adjudications_sha256": _sha256(output_root / "adjudications.json"),
        "unit_count": len(a),
        "raw_label_agreement": {
            "numerator": matches,
            "denominator": len(a),
            "estimate": matches / len(a),
        },
        "disagreement_count": len(disagreements),
        "adjudication_count": len(adjudications),
        "extractor_metrics_authorized": False,
        "gold_promotion_authorized": False,
        "publication_authorized": False,
        "redistribution_authorized": False,
        "training_authorized": False,
    }
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "report_sha256": _sha256(report_path),
        "disagreement_count": len(disagreements),
    }


def validate_annotation_report(report_path: Path) -> dict[str, Any]:
    """Bind the automated report to its two locked role outputs and queue."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_metric_inputs(report)
    root = report_path.parent
    roles = ["agent:au-cth-annotator-a", "agent:au-cth-annotator-b"]
    if report.get("membership_sha256") != MEMBERSHIP_SHA256 or report.get("unit_count") != 385:
        raise ValueError("annotation report membership or unit count mismatch")
    sets = []
    for role in roles:
        packet_path = root / f"{role.rsplit(':', 1)[1]}.packet.json"
        if packet_path.exists():
            if _sha256(packet_path) != report.get("packet_sha256", {}).get(role):
                raise ValueError("packet SHA-256 mismatch")
            packet_data = json.loads(packet_path.read_text(encoding="utf-8"))
            validate_annotation_packet(packet_data, expected_role=role)
        path = root / f"{role.rsplit(':', 1)[1]}.annotations.json"
        if _sha256(path) != report.get("annotation_sha256", {}).get(role):
            raise ValueError("locked annotation SHA-256 mismatch")
        sets.append(json.loads(path.read_text(encoding="utf-8")))
    disagreements = sum(
        (left["label"], left["span"], left["abstention"])
        != (right["label"], right["span"], right["abstention"])
        for left, right in zip(sets[0], sets[1], strict=True)
    )
    adjudications_path = root / "adjudications.json"
    if _sha256(adjudications_path) != report.get("adjudications_sha256"):
        raise ValueError("adjudication SHA-256 mismatch")
    adjudications = json.loads(adjudications_path.read_text(encoding="utf-8"))
    if not isinstance(adjudications, list):
        raise ValueError("adjudication output is not a list")
    for item in adjudications:
        if not isinstance(item, dict):
            raise ValueError("adjudication record is not an object")
        validate_adjudication_record(item, expected_role="agent:au-cth-adjudicator")
    if (
        report.get("disagreement_count") != disagreements
        or report.get("adjudication_count") != len(adjudications)
        or len(adjudications) != disagreements
    ):
        raise ValueError("disagreement queue accounting mismatch")
    return {"ok": True, "report_sha256": _sha256(report_path), "disagreement_count": disagreements}


def build_holdout_frame_candidate(
    population_units: list[dict[str, Any]],
    calibration_cluster_keys: set[str],
    *,
    seed: int = 20260803,
    sample_size: int = 100,
) -> dict[str, Any]:
    """Apply duplicate clustering and exclude calibration clusters from the fresh holdout."""
    if not isinstance(population_units, list) or not population_units:
        raise ValueError("population_units must be a non-empty list")

    eligible_units: list[dict[str, Any]] = []
    excluded_units: list[dict[str, Any]] = []

    for unit in population_units:
        cluster_key = unit.get("cluster_key") or unit.get("unit_sha256", "")[:16]
        if cluster_key in calibration_cluster_keys:
            excluded_units.append(dict(unit, exclusion_reason="calibration_cluster_overlap"))
        else:
            eligible_units.append(unit)

    if len(eligible_units) < sample_size:
        raise ValueError(
            f"insufficient eligible units after cluster exclusion: {len(eligible_units)} < {sample_size}"
        )

    # Deterministic pseudo-random selection
    sorted_units = sorted(
        eligible_units, key=lambda u: (u.get("unit_id", ""), u.get("unit_sha256", ""))
    )
    import random

    rng = random.Random(seed)  # noqa: S311 - deterministic sampling reproducibility, not cryptography
    sampled = rng.sample(sorted_units, k=min(sample_size, len(sorted_units)))

    return {
        "schema_version": "foi-o.au-cth-holdout-frame-candidate.v0.1.0",
        "jurisdiction": "AU-CTH",
        "population_count": len(population_units),
        "excluded_calibration_clusters_count": len(excluded_units),
        "eligible_count": len(eligible_units),
        "sample_size": len(sampled),
        "seed": seed,
        "prng_version": "cpython-random-mersenne-twister",
        "finite_population_limitation": True,
        "sample_units": [
            {
                "unit_id": u["unit_id"],
                "unit_sha256": u["unit_sha256"],
                "text_filename": u.get("text_filename", f"{u['unit_id']}.txt"),
            }
            for u in sampled
        ],
        "holdout_authorized": False,
        "maturity_claim_authorized": False,
    }


def compute_inter_annotator_metrics(
    annotator_a_records: list[dict[str, Any]],
    annotator_b_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute agreement, Cohen's kappa, and abstention statistics."""
    if len(annotator_a_records) != len(annotator_b_records) or not annotator_a_records:
        raise ValueError("annotator records length mismatch or empty")

    n = len(annotator_a_records)
    labels = ["observed", "candidate", "unknown"]
    agreed = sum(
        a["label"] == b["label"]
        for a, b in zip(annotator_a_records, annotator_b_records, strict=True)
    )
    po = agreed / n

    # Marginals for kappa
    pe = sum(
        (sum(a["label"] == lbl for a in annotator_a_records) / n)
        * (sum(b["label"] == lbl for b in annotator_b_records) / n)
        for lbl in labels
    )
    kappa = (po - pe) / (1 - pe) if (1 - pe) > 0 else 1.0

    abstentions_a = sum(a.get("abstention", False) for a in annotator_a_records)
    abstentions_b = sum(b.get("abstention", False) for b in annotator_b_records)

    return {
        "unit_count": n,
        "raw_agreement": po,
        "cohens_kappa": kappa,
        "abstention_rate_a": abstentions_a / n,
        "abstention_rate_b": abstentions_b / n,
        "disagreement_count": n - agreed,
        "gold_promotion_authorized": False,
        "maturity_authorized": False,
    }


def build_maturity_decision_candidate(
    metrics: dict[str, Any],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Produce a maturity-decision candidate without auto-promotion."""
    default_thresholds = {"min_raw_agreement": 0.85, "min_cohens_kappa": 0.75}
    actual_thresholds = thresholds or default_thresholds

    agreement_passes = metrics.get("raw_agreement", 0.0) >= actual_thresholds["min_raw_agreement"]
    kappa_passes = metrics.get("cohens_kappa", 0.0) >= actual_thresholds["min_cohens_kappa"]
    all_criteria_met = agreement_passes and kappa_passes

    return {
        "schema_version": "foi-o.au-cth-maturity-decision-candidate.v0.1.0",
        "jurisdiction": "AU-CTH",
        "metrics_summary": metrics,
        "thresholds": actual_thresholds,
        "criteria_evaluated": {
            "raw_agreement_pass": agreement_passes,
            "cohens_kappa_pass": kappa_passes,
        },
        "recommendation": "candidate_eligible_for_human_review"
        if all_criteria_met
        else "remediation_required",
        "human_decision": "pending",
        "gold_promotion_authorized": False,
        "publication_authorized": False,
    }
