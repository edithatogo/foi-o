from scripts.validate_requirements import validate


def test_requirements_registry_has_complete_traceability_fields():
    result = validate()
    assert result["ok"], result["errors"]
    assert result["requirement_count"] >= 11
