from foi_o_nz.contract_capabilities import (
    CapabilityDeclaration,
    ContractCapability,
    negotiate_contract,
)


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
