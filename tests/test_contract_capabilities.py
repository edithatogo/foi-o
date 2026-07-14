from pathlib import Path

from foi_o_nz.contract_capabilities import (
    CapabilityDeclaration,
    ContractCapability,
    build_capability_declaration,
    negotiate_contract,
    write_capability_declaration,
)
from foi_o_nz.validation import validate_json_schema


def test_capability_declaration_matches_public_json_schema(tmp_path) -> None:
    declaration = CapabilityDeclaration(
        consumer_id="fyi-archive-nz",
        capabilities=[
            ContractCapability(
                contract_id="foi-o-nz.core-event",
                supported_versions=["v0.1.0"],
            )
        ],
    )
    instance = tmp_path / "capability.json"
    instance.write_text(declaration.model_dump_json(), encoding="utf-8")
    result = validate_json_schema(
        instance,
        Path("schemas/json/capability-declaration.schema.json"),
    )
    assert not result.errors, result.errors


def test_capability_negotiation_accepts_declared_version() -> None:
    declaration = CapabilityDeclaration(
        consumer_id="fyi-archive-nz",
        capabilities=[
            ContractCapability(
                contract_id="foi-o-nz.core-event",
                supported_versions=["v0.1.0"],
            )
        ],
    )
    result = negotiate_contract(
        declaration, contract_id="foi-o-nz.core-event", requested_version="v0.1.0"
    )
    assert result.accepted is True
    assert result.reason == "supported"


def test_default_capability_declaration_can_be_exported(tmp_path: Path) -> None:
    output = tmp_path / "capabilities.json"
    result = write_capability_declaration(output)
    assert result["consumer_id"] == "foi-o-nz"
    assert output.exists()
    declaration = build_capability_declaration()
    assert declaration.capabilities[0].contract_id == "foi-o-nz.core-event"


def test_unknown_version_rejects_by_default_and_can_be_explicitly_retained() -> None:
    rejected = CapabilityDeclaration(
        consumer_id="nlp-policy-nz",
        capabilities=[
            ContractCapability(
                contract_id="foi-o-nz.core-event",
                supported_versions=["v0.1.0"],
            )
        ],
    )
    result = negotiate_contract(
        rejected, contract_id="foi-o-nz.core-event", requested_version="v0.2.0"
    )
    assert result.accepted is False
    assert result.reason == "unknown_version_rejected"

    retained = rejected.model_copy(
        update={
            "capabilities": [
                ContractCapability(
                    contract_id="foi-o-nz.core-event",
                    supported_versions=["v0.1.0"],
                    unknown_version_behavior="retain_with_warning",
                )
            ]
        }
    )
    result = negotiate_contract(
        retained, contract_id="foi-o-nz.core-event", requested_version="v0.2.0"
    )
    assert result.accepted is True
    assert result.reason == "unknown_version_retained"
