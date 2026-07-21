from pathlib import Path

import pytest

from scripts.validate_requirements import validate


def test_requirements_registry_has_complete_traceability_fields():
    result = validate()
    assert result["ok"], result["errors"]
    assert result["requirement_count"] >= 11


def test_requirements_registry_rejects_paths_outside_repository() -> None:
    with pytest.raises(ValueError, match="inside repository"):
        validate(Path("../requirements.yaml"))
