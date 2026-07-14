from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from foi_o_nz.empirical_contracts import (
    AuthorityIdentityRecord,
    CodebookEntry,
    EvidenceAssertion,
    LabelAssertion,
    NormativeSource,
    ProcessAnalysisRun,
    SamplingDesign,
)

EXAMPLES = Path(__file__).parents[1] / "examples" / "v2"


def load(kind: str, name: str) -> dict:
    return json.loads((EXAMPLES / kind / name).read_text(encoding="utf-8"))


def test_codebook_maturity_guard() -> None:
    CodebookEntry.model_validate(load("schema-valid", "codebook-entry-2.json"))
    with pytest.raises(ValidationError):
        CodebookEntry.model_validate(load("schema-invalid", "codebook-entry-2.json"))


def test_model_cannot_certify() -> None:
    LabelAssertion.model_validate(load("schema-valid", "label-assertion-2.json"))
    with pytest.raises(ValidationError):
        LabelAssertion.model_validate(load("schema-invalid", "label-assertion-2.json"))


def test_evidence_dimensions_match_source_kind() -> None:
    EvidenceAssertion.model_validate(load("schema-valid", "evidence-assertion-2.json"))
    with pytest.raises(ValidationError):
        EvidenceAssertion.model_validate(load("schema-invalid", "evidence-assertion-2.json"))


def test_normative_source_rights_guard() -> None:
    NormativeSource.model_validate(load("schema-valid", "normative-source-1.json"))
    with pytest.raises(ValidationError):
        NormativeSource.model_validate(load("schema-invalid", "normative-source-2.json"))


def test_sampling_design_guard() -> None:
    SamplingDesign.model_validate(
        {
            "design_type": "probability_stratified",
            "strata_variables": ["year"],
            "population_estimation_allowed": True,
            "weights_available": True,
            "inclusion_probability_field": "pi",
            "weight_field": "w",
        }
    )
    with pytest.raises(ValidationError):
        SamplingDesign.model_validate(
            {
                "design_type": "rare_event_enrichment",
                "population_estimation_allowed": True,
                "weights_available": False,
            }
        )


def test_authority_identity_conflict_and_approval_guards() -> None:
    AuthorityIdentityRecord.model_validate(load("schema-valid", "authority-identity-record-1.json"))
    AuthorityIdentityRecord.model_validate(load("schema-valid", "authority-identity-record-2.json"))
    with pytest.raises(ValidationError):
        AuthorityIdentityRecord.model_validate(
            load("schema-invalid", "authority-identity-record-1.json")
        )
    with pytest.raises(ValidationError):
        AuthorityIdentityRecord.model_validate(
            load("schema-invalid", "authority-identity-record-2.json")
        )


def test_process_analysis_boundary_and_comparability_guards() -> None:
    ProcessAnalysisRun.model_validate(load("schema-valid", "process-analysis-run-1.json"))
    ProcessAnalysisRun.model_validate(load("schema-valid", "process-analysis-run-2.json"))
    with pytest.raises(ValidationError):
        ProcessAnalysisRun.model_validate(load("schema-invalid", "process-analysis-run-1.json"))
    with pytest.raises(ValidationError):
        ProcessAnalysisRun.model_validate(load("schema-invalid", "process-analysis-run-2.json"))
    with pytest.raises(ValidationError):
        ProcessAnalysisRun.model_validate(load("schema-invalid", "process-analysis-run-3.json"))
