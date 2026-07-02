from __future__ import annotations

from foi_o_nz.embeddings import embedding_record
from foi_o_nz.inference_providers import (
    InferenceProviderConfig,
    select_embedding_provider,
    validate_candidate_output,
)


def test_deterministic_provider_is_default_and_records_provenance() -> None:
    status = select_embedding_provider(InferenceProviderConfig())

    assert status.provider_id == "deterministic.feature_hash"
    assert status.available is True
    assert status.fallback is True
    assert status.legal_effect == "none"
    assert status.machine_certification_allowed is False

    record = embedding_record(
        {"request_id": "1", "title": "Health request", "authority": "Agency"},
        kind="request",
        dimensions=8,
        provider_status=status,
    )

    assert record["embedding_provider"] == "deterministic.feature_hash"
    assert record["provider_provenance"]["fallback"] is True
    assert record["provider_provenance"]["runtime"] == "python"
    assert record["provider_provenance"]["legal_effect"] == "none"
    assert record["provider_provenance"]["machine_certification_allowed"] is False


def test_configured_max_provider_reports_available_without_network(
    monkeypatch,
) -> None:
    monkeypatch.setattr("foi_o_nz.inference_providers._module_available", lambda name: True)

    status = select_embedding_provider(
        InferenceProviderConfig(
            provider="max",
            model="local-oia-embeddings",
            endpoint="http://localhost:8000/v1",
        )
    )

    assert status.provider_id == "max.openai_compatible"
    assert status.available is True
    assert status.fallback is False
    assert status.model == "local-oia-embeddings"
    assert status.endpoint == "http://localhost:8000/v1"
    assert "network not contacted" in status.message


def test_missing_max_dependency_degrades_to_deterministic_fallback(monkeypatch) -> None:
    monkeypatch.setattr("foi_o_nz.inference_providers._module_available", lambda name: False)

    status = select_embedding_provider(InferenceProviderConfig(provider="max"))

    assert status.provider_id == "max.openai_compatible"
    assert status.available is False
    assert status.fallback is True
    assert status.fallback_provider_id == "deterministic.feature_hash"
    assert "Install foi-o-nz[max]" in status.message
    assert status.legal_effect == "none"


def test_candidate_output_rejects_certified_legal_outcomes() -> None:
    report = validate_candidate_output(
        {
            "event_id": "foio-nz:event:model-release",
            "event_type": "ReleaseMade",
            "assertion_status": "certified",
            "machine_generated": True,
            "requires_human_certification": False,
        }
    )

    assert report["ok"] is False
    assert any(
        finding["code"] == "certified_model_output_rejected"
        for finding in report["findings"]
    )
