"""Optional MAX/OpenAI-compatible client helpers.

MAX is intentionally an optional runtime dependency. The first FOI-O NZ milestone
uses MAX only for future local extraction/embedding experiments; deterministic
process validation must not depend on an LLM endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MaxEndpointConfig:
    """Configuration for a local MAX OpenAI-compatible endpoint."""

    base_url: str = "http://localhost:8000/v1"
    api_key: str = "EMPTY"
    model: str = "local-model"


def build_client(config: MaxEndpointConfig) -> Any:
    """Build an OpenAI-compatible client for MAX endpoints.

    Import is lazy so the core package remains usable without the ``max`` extra.
    """
    try:
        from openai import OpenAI  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("Install foi-o-nz[max] to use MAX/OpenAI-compatible helpers") from exc
    return OpenAI(base_url=config.base_url, api_key=config.api_key)


def draft_extraction_prompt(text: str) -> list[dict[str, str]]:
    """Create a bounded extraction prompt for local experimentation.

    The prompt asks for candidate events only and prohibits final legal decisions.
    """
    return [
        {
            "role": "system",
            "content": (
                "Extract candidate FOI-O NZ process events from public OIA text. "
                "Do not certify access, refusal, redaction, charging, transfer, extension, "
                "or complaint decisions. Return JSON only."
            ),
        },
        {"role": "user", "content": text},
    ]
