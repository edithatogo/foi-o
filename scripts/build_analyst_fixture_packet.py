"""Build the deterministic local analyst-fixture packet candidate."""

from __future__ import annotations

import json
from hashlib import sha1, sha256
from pathlib import Path

from foi_o_nz.analyst_packet_verification import derive_fixture_units, ordered_unit_commitment

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "examples/v2/analyst-fixture-packet"
CREATED_AT = "2026-07-17T12:00:00Z"
PROHIBITED = [
    "redistribution",
    "publication",
    "training",
    "fine_tuning",
    "release",
    "dataset_publication",
    "gold_promotion",
    "legal_certification",
    "paper_update",
]


def _write(output: Path, name: str, value: object) -> Path:
    path = output / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main(output: Path = OUTPUT) -> None:
    def write(name: str, value: object) -> Path:
        return _write(output, name, value)

    units = derive_fixture_units(ROOT)
    protocol = ROOT / "docs/42-v2-analyst-execution-protocol.md"
    source_paths = sorted({unit.source_path for unit in units})
    source_counts = {path: sum(unit.source_path == path for unit in units) for path in source_paths}
    source_hashes = {path: _digest(ROOT / path) for path in source_paths}

    population_path = write(
        "source-population.json",
        {
            "schema_version": "foi-o.analyst-fixture-source-population.v0.1.0",
            "population_id": "foi-o-local-fixture-census-11",
            "status": "locked_synthetic_fixture_population",
            "task": "fixture_engineering_classification",
            "sources": [
                {"path": path, "sha256": source_hashes[path], "expected_units": source_counts[path]}
                for path in source_paths
            ],
            "expected_unit_count": 11,
            "coverage_start": "2026-06-01",
            "coverage_end": "2026-07-09",
            "source_state_policy": "preserve_present_null_or_absent_never_synthesize",
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "created_at": CREATED_AT,
            "locked_at": CREATED_AT,
        },
    )

    codebook_id = "foi-o-agent-fixture-engineering-v0.1.0"
    codebook_path = write(
        "codebook.json",
        {
            "schema_version": "foi-o.analyst-fixture-codebook.v0.1.0",
            "codebook_id": codebook_id,
            "revision": sha1(codebook_id.encode(), usedforsecurity=False).hexdigest(),
            "revision_algorithm": "sha1_utf8_codebook_id_v1",
            "status": "candidate_contract_fixture",
            "protocol_sha256": _digest(protocol),
            "task_type": "fixture_engineering_classification",
            "labels": [
                {
                    "label": label,
                    "definition": definition,
                    "positive_criteria": [positive],
                    "negative_criteria": [negative],
                }
                for label, definition, positive, negative in [
                    (
                        "observed",
                        "Visible fixture fields support a direct process observation.",
                        "Use only for direct visible observation evidence.",
                        "Do not use for derived, candidate, certified, or insufficient evidence.",
                    ),
                    (
                        "inferred",
                        "Visible fixture fields support a machine or deterministic derivation.",
                        "Use only when visible derivation evidence is present.",
                        "Do not use for direct observations, drafts, certification, or insufficient evidence.",
                    ),
                    (
                        "candidate",
                        "Visible fixture fields support an engineering proposal or draft.",
                        "Use only for visibly proposed or drafted events.",
                        "Do not use for observed, derived, certified, or insufficient evidence.",
                    ),
                    (
                        "certified",
                        "Visible fixture fields support a recorded human certification boundary.",
                        "Use only when visible certification fields consistently support it.",
                        "Do not infer certification from an event name alone.",
                    ),
                    (
                        "unknown",
                        "Visible fixture fields explicitly encode an unknown epistemic category.",
                        "Use only for an explicit readable unknown category.",
                        "Use abstention for missing or insufficient evidence.",
                    ),
                ]
            ],
            "span_required": False,
            "span_coordinate_system": "utf8_character_half_open",
            "overlap_threshold": 1.0,
            "abstention_reasons": [
                "missing_evidence",
                "insufficient_evidence",
                "out_of_scope",
                "other",
            ],
            "reconciliation_trigger": "any_label_span_or_abstention_disagreement",
            "created_at": CREATED_AT,
            "approved_by": None,
            "approved_at": None,
        },
    )

    sampling_path = write(
        "sampling-configuration.json",
        {
            "schema_version": "foi-o.sampling-configuration.v0.1.0",
            "configuration_id": "local-fixture-census-11",
            "status": "candidate_contract_fixture",
            "protocol_sha256": _digest(protocol),
            "source_population_sha256": _digest(population_path),
            "codebook_revision": json.loads(codebook_path.read_text())["revision"],
            "random_seed": 20260717,
            "probability_sample_size": 11,
            "enrichment_sample_size": 0,
            "sample_size_justification": "Deterministic census of all eleven dated committed synthetic fixture events.",
            "strata": ["synthetic_fixture"],
            "inclusion_probability_field": "inclusion_probability",
            "weight_field": "sampling_weight",
            "duplicate_cluster_rule": "Exact redacted-context SHA-256 singleton clusters.",
            "exclusion_rule": "Exclude every path outside the two pinned committed fixture artifacts.",
            "split_policy": {"grouped_by": "duplicate_cluster", "splits": ["annotation_only"]},
            "bootstrap": {
                "confidence_level": 0.95,
                "sides": "two_sided",
                "resampling_unit": "duplicate_cluster",
                "replicates": 2000,
                "interval_method": "percentile",
            },
            "created_at": CREATED_AT,
            "approved_by": None,
            "approved_at": None,
        },
    )

    unit_path = write(
        "unit-manifest.json",
        {
            "schema_version": "foi-o.analyst-fixture-unit-manifest.v0.1.0",
            "manifest_id": "local-fixture-census-11",
            "status": "locked_local_fixture_census",
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "ordered_unit_commitment_sha256": ordered_unit_commitment(
                [unit.unit_sha256 for unit in units]
            ),
            "ordered_unit_commitment_algorithm": "sha256_lowercase_hex_lines_final_newline_v1",
            "created_at": CREATED_AT,
            "locked_at": CREATED_AT,
            "units": [
                {
                    "unit_id": unit.unit_id,
                    "source_path": unit.source_path,
                    "source_artifact_sha256": unit.source_artifact_sha256,
                    "unit_sha256": unit.unit_sha256,
                    "context_sha256": unit.context_sha256,
                    "source_span": {
                        "start": unit.source_span[0],
                        "end": unit.source_span[1],
                        "coordinate_system": "utf8_character_half_open",
                    },
                    "observed_date": unit.observed_date,
                    "request_linkage_group": unit.request_linkage_group,
                    "duplicate_cluster_id": f"exact:{unit.context_sha256}",
                    "split": "annotation_only",
                    "inclusion_probability": 1.0,
                    "sampling_weight": 1.0,
                    "rights_eligible_for_local_use": False,
                }
                for unit in units
            ],
        },
    )

    cluster_path = write(
        "cluster-registry.json",
        {
            "schema_version": "foi-o.analyst-fixture-cluster-registry.v0.1.0",
            "registry_id": "local-fixture-exact-context",
            "status": "locked_local_fixture_clusters",
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "unit_manifest_sha256": _digest(unit_path),
            "algorithm": {
                "name": "exact_redacted_context_sha256",
                "version": "1",
                "threshold": 1.0,
            },
            "created_at": CREATED_AT,
            "locked_at": CREATED_AT,
            "clusters": [
                {
                    "cluster_id": f"exact:{unit.context_sha256}",
                    "member_unit_sha256": [unit.unit_sha256],
                    "split": "annotation_only",
                }
                for unit in units
            ],
        },
    )

    redaction_path = write(
        "redaction-manifest.json",
        {
            "schema_version": "foi-o.analyst-redaction-manifest.v0.1.0",
            "manifest_id": "local-fixture-redaction-v1",
            "status": "locked",
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "forbidden_keys": ["assertion_status", "confidence"],
            "canonicalization": {
                "parse": "json_object",
                "ensure_ascii": False,
                "sort_keys": True,
                "separators": [",", ":"],
                "encoding": "utf-8",
            },
            "created_at": CREATED_AT,
            "locked_at": CREATED_AT,
            "entries": [
                {
                    "unit_id": unit.unit_id,
                    "unit_sha256": unit.unit_sha256,
                    "context_sha256": unit.context_sha256,
                    "removed_keys": list(unit.removed_keys),
                    "forbidden_keys_absent": True,
                }
                for unit in units
            ],
        },
    )

    rights_path = write(
        "local-rights-review.pending.json",
        {
            "schema_version": "foi-o.analyst-local-rights-review.v0.1.0",
            "review_id": "local-fixture-census-11",
            "status": "pending_exact_human_approval",
            "purpose": "bounded_local_agent_analysis",
            "sources": [{"path": path, "sha256": source_hashes[path]} for path in source_paths],
            "license_placeholder": {
                "path": "LICENSE.md",
                "sha256": _digest(ROOT / "LICENSE.md"),
                "grants_redistribution": False,
            },
            "local_analysis_allowed": False,
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "redistribution_granted": False,
            "prohibited_actions": PROHIBITED,
            "created_at": CREATED_AT,
            "approved_by": None,
            "approved_at": None,
        },
    )

    artifacts = [
        population_path,
        codebook_path,
        sampling_path,
        unit_path,
        cluster_path,
        redaction_path,
        rights_path,
    ]
    write(
        "readiness.json",
        {
            "status": "pending_exact_human_rights_and_execution_input_approval",
            "protocol": {"path": str(protocol.relative_to(ROOT)), "sha256": _digest(protocol)},
            "artifacts": [
                {
                    "path": f"examples/v2/analyst-fixture-packet/{path.name}",
                    "sha256": _digest(path),
                }
                for path in artifacts
            ],
            "execution_allowed": False,
            "local_only": True,
            "empirical_evidence": False,
            "human_reviewed": False,
            "gold_eligible": False,
            "release_qualifying": False,
            "publication_eligible": False,
            "prohibited_actions": PROHIBITED,
        },
    )


if __name__ == "__main__":
    main()
