"""Typed DTOs for isolated OIA rule invocations and results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValueObject:
    """A value with explicit epistemic / value-state metadata (PIC-aligned)."""

    value: Any = None
    valueState: str = "known"  # noqa: N815 - PIC valueState field name
    epistemicStatus: str | None = None  # noqa: N815 - PIC epistemicStatus field name
    warnings: list[str] | None = None


@dataclass
class RuleInvocation:
    """A single deterministic rule call with typed inputs."""

    decision_id: str  # e.g., "nz-oia/decision.response_deadline"
    inputs: dict[str, ValueObject]
    parameter_set: str  # e.g., "0.1.0"
    invoked_by: str  # foi-o event id


@dataclass
class DiscretionPoint:
    """A non-computable issue requiring human certification."""

    discretion_id: str
    message: str
    metadata: dict[str, Any]


@dataclass
class RuleResult:
    """Outputs, optional PIC-style trace step, and optional discretion signal."""

    outputs: dict[str, ValueObject]
    trace_step: dict  # PIC trace step
    discretion_required: DiscretionPoint | None = None
