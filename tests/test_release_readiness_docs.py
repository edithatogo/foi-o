from __future__ import annotations

from pathlib import Path


def test_release_readiness_document_has_required_validation_sequence() -> None:
    text = Path("docs/19-release-readiness-evidence.md").read_text(encoding="utf-8")
    required_commands = [
        "uv run ruff check src tests scripts",
        "uv run ruff format --check src tests scripts",
        "uv run pytest -q",
        "uv run python scripts/validate_examples.py",
    ]
    for command in required_commands:
        assert command in text


def test_release_readiness_document_references_existing_local_paths() -> None:
    text = Path("docs/19-release-readiness-evidence.md").read_text(encoding="utf-8")
    required_paths = [
        Path("src/foi_o_nz/kernel_fallback.py"),
        Path("src/foi_o_nz/kernel_manifest.py"),
        Path("examples/kernel-readiness.fallback.json"),
        Path("examples/mojo-audit.static.json"),
        Path("scripts/validate_examples.py"),
    ]
    for path in required_paths:
        assert path.exists(), path
        assert str(path) in text
