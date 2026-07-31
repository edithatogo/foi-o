"""Shared, versioned contracts for Australian empirical analysis."""

from .contracts import (
    ArtifactPin,
    EmpiricalContractError,
    PopulationSpecification,
    RunSpecification,
    StageSpecification,
    canonical_bytes,
    load_run_spec,
    parse_run_spec,
    seal_record,
    validate_run_spec,
    validate_stage_result,
)
from .execution import (
    ExecutionContextError,
    VerifiedCodebook,
    VerifiedExecutionContext,
    load_verified_execution_context,
)
from .legacy import (
    LegacyInterpretationError,
    LegacyInterpretationResult,
    LegacyUnknownMapping,
    interpret_legacy_annotation,
)

__all__ = [
    "ArtifactPin",
    "EmpiricalContractError",
    "ExecutionContextError",
    "LegacyInterpretationError",
    "LegacyInterpretationResult",
    "LegacyUnknownMapping",
    "PopulationSpecification",
    "RunSpecification",
    "StageSpecification",
    "VerifiedCodebook",
    "VerifiedExecutionContext",
    "canonical_bytes",
    "interpret_legacy_annotation",
    "load_run_spec",
    "load_verified_execution_context",
    "parse_run_spec",
    "seal_record",
    "validate_run_spec",
    "validate_stage_result",
]
