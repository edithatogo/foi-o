"""Build extractor-blinded AU annotation packets from a frozen authentic frame."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

SHA256_LENGTH = 64
SEED = 20260721


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), "input frame must be a JSON object")
    return value


def _unit_for_packet(unit: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "unit_id",
        "jurisdiction",
        "text",
        "unit_sha256",
        "duplicate_cluster_id",
        "stratum",
        "source_ref",
    }
    return {key: unit[key] for key in sorted(allowed) if key in unit}


def build_packets(
    frame_path: Path,
    codebook_path: Path,
    output_a: Path,
    output_b: Path,
    *,
    seed: int = SEED,
    approval_path: Path | None = None,
) -> dict[str, Any]:
    """Build two deterministic packets while omitting extractor candidate fields."""
    frame = _load(frame_path)
    codebook = _load(codebook_path)
    _require(frame.get("status") == "frozen_authentic", "frame is not frozen authentic data")
    _require(frame.get("rights_eligible") is True, "frame is not rights eligible")
    _require(frame.get("jurisdiction") in {"AU-CTH", "AU-NSW"}, "unsupported AU jurisdiction")
    _require(
        isinstance(frame.get("source_population_sha256"), str), "source population digest missing"
    )
    _require(
        len(frame["source_population_sha256"]) == SHA256_LENGTH, "invalid source population digest"
    )
    if codebook.get("status") != "approved":
        if approval_path is None:
            raise ValueError("pending codebook requires a separate approval wrapper")
        approval = _load(approval_path)
        _require(
            approval.get("status") == "approved_for_fresh_holdout_use",
            "codebook approval wrapper is not approved",
        )
        _require(
            approval.get("approved_artifact", {}).get("sha256") == _sha256(codebook_path),
            "codebook approval hash mismatch",
        )
        _require(
            approval.get("approved_artifact", {}).get("codebook_id") == codebook.get("codebook_id"),
            "codebook approval identity mismatch",
        )
    _require(isinstance(codebook.get("revision"), str), "codebook revision missing")
    _require(len(codebook["revision"]) == 40, "invalid codebook revision")
    _require(_sha256(codebook_path) == frame.get("codebook_sha256"), "codebook digest mismatch")
    _require(isinstance(frame.get("units"), list) and frame["units"], "authentic units are missing")

    units: list[dict[str, Any]] = []
    for index, raw in enumerate(frame["units"]):
        _require(isinstance(raw, dict), f"unit {index} is not an object")
        _require(
            set(raw).isdisjoint({"candidate_label", "candidate_confidence", "extractor_output"}),
            f"unit {index} leaks extractor candidate",
        )
        _require(raw.get("rights_eligible") is True, f"unit {index} is not rights eligible")
        _require(isinstance(raw.get("unit_id"), str), f"unit {index} id missing")
        _require(isinstance(raw.get("text"), str) and raw["text"], f"unit {index} text missing")
        _require(
            isinstance(raw.get("unit_sha256"), str) and len(raw["unit_sha256"]) == SHA256_LENGTH,
            f"unit {index} digest missing",
        )
        units.append(_unit_for_packet(raw))

    units.sort(key=lambda item: item["unit_id"])
    random.Random(seed).shuffle(units)  # noqa: S311 - reproducibility, not secrecy
    base = {
        "schema_version": "foi-o.australian-blinded-annotation-packet.v0.1.0",
        "jurisdiction": frame["jurisdiction"],
        "seed": seed,
        "source_population_sha256": frame["source_population_sha256"],
        "codebook_revision": codebook["revision"],
        "codebook_sha256": frame["codebook_sha256"],
        "blinded_to_extractor_candidate": True,
        "blinded_to_peer_annotations": True,
        "annotation_status": "unlabelled",
        "units": units,
    }
    output_a.parent.mkdir(parents=True, exist_ok=True)
    output_b.parent.mkdir(parents=True, exist_ok=True)
    for path, role in ((output_a, "annotator_a"), (output_b, "annotator_b")):
        payload = {
            "packet_id": f"{frame['jurisdiction']}:annotation:{role}:v0.1.0",
            "role": role,
            **base,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "jurisdiction": frame["jurisdiction"],
        "unit_count": len(units),
        "seed": seed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--codebook", type=Path, required=True)
    parser.add_argument("--output-a", type=Path, required=True)
    parser.add_argument("--output-b", type=Path, required=True)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build_packets(
                args.frame, args.codebook, args.output_a, args.output_b, approval_path=args.approval
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
