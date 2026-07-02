"""Bounded inference provider selection and output guardrails."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any, Literal

from foi_o_nz.constants import HUMAN_CERTIFICATION_EVENT_TYPES

ProviderName = Literal["deterministic", "max"]


@dataclass(frozen=True, slots=True)
class InferenceProviderConfig:
    """Configuration for bounded local inference/embedding experiments."""

    provider: ProviderName = "deterministic"
    model: str | None = None
    endpoint: str | None = None


@dataclass(frozen=True, slots=True)
class InferenceProviderStatus:
    """Selected provider status and provenance."""

    provider_id: str
    available: bool
    fallback: bool
    fallback_provider_id: str | None
    model: str
    endpoint: str | None
    runtime: str
    legal_effect: Literal["none"] = "none"
    machine_certification_allowed: bool = False
    message: str = ""

    def as_provenance(self) -> dict[str, Any]:
        """Return JSON-serialisable provider provenance."""
        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "runtime": self.runtime,
            "available": self.available,
            "fallback": self.fallback,
            "fallback_provider_id": self.fallback_provider_id,
            "endpoint": self.endpoint,
            "legal_effect": self.legal_effect,
            "machine_certification_allowed": self.machine_certification_allowed,
            "message": self.message,
        }


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def select_embedding_provider(
    config: InferenceProviderConfig | None = None,
) -> InferenceProviderStatus:
    """Select a bounded embedding provider without contacting live endpoints."""
    config = config or InferenceProviderConfig()
    if config.provider == "deterministic":
        return InferenceProviderStatus(
            provider_id="deterministic.feature_hash",
            available=True,
            fallback=True,
            fallback_provider_id=None,
            model=config.model or "foi-o-nz-feature-hash",
            endpoint=None,
            runtime="python",
            message="Deterministic feature-hash provider selected as local fallback.",
        )
    if config.provider == "max":
        model = config.model or "local-model"
        endpoint = config.endpoint or "http://localhost:8000/v1"
        if not _module_available("openai"):
            return InferenceProviderStatus(
                provider_id="max.openai_compatible",
                available=False,
                fallback=True,
                fallback_provider_id="deterministic.feature_hash",
                model=model,
                endpoint=endpoint,
                runtime="max/openai-compatible",
                message=(
                    "Install foi-o-nz[max] to use MAX/OpenAI-compatible providers; "
                    "deterministic feature-hash fallback remains available."
                ),
            )
        return InferenceProviderStatus(
            provider_id="max.openai_compatible",
            available=True,
            fallback=False,
            fallback_provider_id="deterministic.feature_hash",
            model=model,
            endpoint=endpoint,
            runtime="max/openai-compatible",
            message="MAX/OpenAI-compatible provider configured; network not contacted during selection.",
        )
    raise ValueError(f"unsupported provider: {config.provider}")


def validate_candidate_output(record: dict[str, Any]) -> dict[str, Any]:
    """Validate that a model output remains candidate/preparatory only."""
    findings: list[dict[str, str]] = []
    event_type = str(record.get("event_type") or "")
    assertion_status = str(record.get("assertion_status") or "")
    machine_generated = record.get("machine_generated") is True
    if machine_generated and record.get("human_review_required") is not True:
        findings.append(
            {
                "severity": "error",
                "code": "model_output_review_required",
                "message": "Machine-generated provider outputs must be routed for human review.",
            }
        )
    if assertion_status == "certified" and machine_generated:
        findings.append(
            {
                "severity": "error",
                "code": "certified_model_output_rejected",
                "message": "Machine-generated provider outputs must not assert certified status.",
            }
        )
    if (
        event_type in HUMAN_CERTIFICATION_EVENT_TYPES
        and record.get("requires_human_certification") is not True
    ):
        findings.append(
            {
                "severity": "error",
                "code": "human_certification_boundary_required",
                "message": f"{event_type} provider outputs must require human certification.",
            }
        )
    certification = record.get("human_certification")
    if isinstance(certification, dict) and certification.get("certified") is True:
        findings.append(
            {
                "severity": "error",
                "code": "provider_human_certification_rejected",
                "message": "Provider outputs cannot carry positive human certification metadata.",
            }
        )
    return {
        "ok": not any(finding["severity"] == "error" for finding in findings),
        "finding_count": len(findings),
        "findings": findings,
        "legal_effect": "none",
        "machine_certification_allowed": False,
    }
