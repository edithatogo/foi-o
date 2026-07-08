from dataclasses import dataclass
from typing import Any

@dataclass
class ValueObject:
    value: Any = None
    valueState: str = "known"
    epistemicStatus: str | None = None
    warnings: list[str] | None = None

@dataclass
class RuleInvocation:
    decision_id: str          # e.g., "nz-oia/decision.response_deadline"
    inputs: dict[str, ValueObject]
    parameter_set: str        # e.g., "0.1.0"
    invoked_by: str           # foi-o event id

@dataclass
class DiscretionPoint:
    discretion_id: str
    message: str
    metadata: dict[str, Any]

@dataclass
class RuleResult:
    outputs: dict[str, ValueObject]
    trace_step: dict          # PIC trace step
    discretion_required: DiscretionPoint | None = None
