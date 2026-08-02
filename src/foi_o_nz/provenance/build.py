"""Builders for content-addressed provenance records."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .canonical import CANONICALIZATION_ID, content_sha256
from .validate import validate_envelope


def seal_record(record: Mapping[str, Any], self_pin_field: str) -> dict[str, Any]:
    """Return a copy carrying a verified content self-pin."""
    sealed = copy.deepcopy(dict(record))
    expected = content_sha256(sealed, self_pin_field)
    supplied = sealed.get(self_pin_field)
    if supplied is not None and supplied != expected:
        raise ValueError(f"{self_pin_field} does not match canonical record content")
    sealed[self_pin_field] = expected
    return sealed


def build_envelope(
    *,
    envelope_id: str,
    transformation_contract: Mapping[str, Any],
    run_occurrence: Mapping[str, Any],
    authorization: Mapping[str, Any],
    inputs: Sequence[Mapping[str, Any]],
    outputs: Sequence[Mapping[str, Any]],
    population: Mapping[str, str | int],
    successor_effects: Sequence[str] = (),
    lineage: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    """Build and semantically validate one occurrence-specific envelope."""
    contract = seal_record(transformation_contract, "contract_sha256")
    occurrence = seal_record(run_occurrence, "run_occurrence_sha256")
    auth = seal_record(authorization, "authorization_sha256")
    if auth.get("transformation_contract_sha256") != contract["contract_sha256"]:
        raise ValueError("authorization does not pin the transformation contract")

    envelope = {
        "schema_version": "foio.provenance-envelope.v1.0.0",
        "envelope_id": envelope_id,
        "canonicalization": CANONICALIZATION_ID,
        "transformation_contract": contract,
        "run_occurrence": occurrence,
        "authorization": auth,
        "inputs": [copy.deepcopy(dict(item)) for item in inputs],
        "outputs": [copy.deepcopy(dict(item)) for item in outputs],
        "population": copy.deepcopy(dict(population)),
        "successor_effects": list(successor_effects),
        "lineage": [copy.deepcopy(dict(item)) for item in lineage],
    }
    sealed = seal_record(envelope, "envelope_sha256")
    validate_envelope(sealed)
    return sealed
