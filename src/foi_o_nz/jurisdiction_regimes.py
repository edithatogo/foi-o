"""Canonical declarative registry of statutory FOI regime profiles.

The registry is the single source of truth for jurisdiction statutory
parameters (statute, response timeframe, agency scope, exemption clauses)
consumed by the agent-triangulated Medallion pipeline. Data lives in
``registries/jurisdiction-regimes.yaml`` and is validated against
``schemas/json/jurisdiction-regimes.schema.json`` on load; the Python module
is a thin, read-only loader boundary.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict

DEFAULT_REGISTRY = Path("registries/jurisdiction-regimes.yaml")
DEFAULT_SCHEMA = Path("schemas/json/jurisdiction-regimes.schema.json")


def _repo_root() -> Path:
    """Repository root as seen from this installed/source module location."""
    return Path(__file__).resolve().parents[2]


def _resolve(existing: Path, fallback: Path) -> Path:
    return existing if existing.exists() else fallback


class StatutoryProfile(BaseModel):
    """Statutory regime parameters for a jurisdiction."""

    model_config = ConfigDict(extra="forbid")

    jurisdiction: str
    regime: str
    statute_name: str
    statutory_timeframe_days: int
    timeframe_type: Literal["working_days", "calendar_days"]
    default_agency_scope: str
    exemption_clauses: list[str]


@lru_cache(maxsize=1)
def load_jurisdiction_regimes(
    registry_path: Path | None = None,
    schema_path: Path | None = None,
) -> dict[str, StatutoryProfile]:
    """Load, schema-validate, and freeze the canonical jurisdiction registry."""
    registry_file = _resolve(registry_path or DEFAULT_REGISTRY, _repo_root() / DEFAULT_REGISTRY)
    schema_file = _resolve(schema_path or DEFAULT_SCHEMA, _repo_root() / DEFAULT_SCHEMA)
    document = yaml.safe_load(registry_file.read_text(encoding="utf-8"))
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda err: list(err.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors[:5]
        )
        raise ValueError(f"jurisdiction regime registry failed schema validation: {details}")
    profiles: dict[str, StatutoryProfile] = {}
    for item in document["profiles"]:
        profile_id = item["id"]
        if profile_id in profiles:
            raise ValueError(f"duplicate jurisdiction profile id: {profile_id}")
        if item["jurisdiction"] != profile_id:
            raise ValueError(
                f"profile id must match jurisdiction field: {profile_id} != {item['jurisdiction']}"
            )
        profiles[profile_id] = StatutoryProfile(
            jurisdiction=item["jurisdiction"],
            regime=item["regime"],
            statute_name=item["statute_name"],
            statutory_timeframe_days=item["statutory_timeframe_days"],
            timeframe_type=item["timeframe_type"],
            default_agency_scope=item["default_agency_scope"],
            exemption_clauses=list(item["exemption_clauses"]),
        )
    return dict(profiles)


JURISDICTION_REGIMES: dict[str, StatutoryProfile] = load_jurisdiction_regimes()
