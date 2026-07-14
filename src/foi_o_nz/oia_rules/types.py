"""Value and result types used by the New Zealand OIA rule evaluators."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ValueObject:
    """Represent a value together with its epistemic state and warnings."""

    value: Any = None
    valueState: str = "known"  # noqa: N815 - external contract uses camelCase
    epistemicStatus: str | None = None  # noqa: N815 - external contract uses camelCase
    warnings: list[str] | None = None


@dataclass
class RuleInvocation:
    """Describe a deterministic rule invocation and its input values."""

    decision_id: str  # e.g., "nz-oia/decision.response_deadline"
    inputs: dict[str, ValueObject]
    parameter_set: str  # e.g., "0.1.0"
    invoked_by: str  # foi-o event id


@dataclass
class DiscretionPoint:
    """Identify a decision that must remain subject to human judgment."""

    discretion_id: str
    message: str
    metadata: dict[str, Any]


@dataclass
class RuleResult:
    """Return rule outputs, an audit trace, and any discretion points."""

    outputs: dict[str, ValueObject]
    trace_step: dict  # PIC trace step
    discretion_required: DiscretionPoint | None = None
