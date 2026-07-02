"""Release checklist helpers for publication-ready repo-local evidence."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from foi_o_nz.constants import RELEASE_CHECKLIST_SCHEMA_VERSION
from foi_o_nz.io import write_json
from foi_o_nz.version import __version__

REQUIRED_RELEASE_VALIDATION_COMMANDS: tuple[str, ...] = (
    "uv run ruff check src tests scripts",
    "uv run ruff format --check src tests scripts",
    "uv run pytest -q",
    "uv run python scripts/validate_examples.py",
)


class ReleaseValidationCommand(BaseModel):
    """One command required before claiming repo-local release readiness."""

    model_config = ConfigDict(extra="forbid")

    command: str
    description: str
    required: bool = True


class ReleaseEvidenceItem(BaseModel):
    """Repo-local file evidence referenced by the release checklist."""

    model_config = ConfigDict(extra="forbid")

    path: str
    description: str
    required: bool = True


class ReleaseExternalGate(BaseModel):
    """Manual or external gate that cannot be proven by local validation."""

    model_config = ConfigDict(extra="forbid")

    name: str
    status: Literal["external_gate", "manual_approval_required"]
    reason: str


class ReleasePublicationArtifact(BaseModel):
    """Publication artefact readiness record."""

    model_config = ConfigDict(extra="forbid")

    name: str
    status: Literal["repo_local", "planned", "external_gate", "manual_approval_required"]
    path: str | None = None
    description: str


class ReleaseChecklist(BaseModel):
    """Machine-readable release checklist for repo-local publication readiness."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["foi-o-nz.release-checklist.v0.1.0"] = RELEASE_CHECKLIST_SCHEMA_VERSION
    release_version: str
    repository: str = "https://github.com/edithatogo/foi-o"
    package_scope: str
    rights_notice: str
    validation_commands: list[ReleaseValidationCommand]
    evidence: list[ReleaseEvidenceItem]
    publication_artifacts: list[ReleasePublicationArtifact] = Field(default_factory=list)
    external_gates: list[ReleaseExternalGate]


def build_release_checklist(*, release_version: str | None = None) -> ReleaseChecklist:
    """Build the default publication release checklist."""
    version = release_version or __version__
    return ReleaseChecklist(
        release_version=version,
        package_scope=(
            "Code, schemas, ontology, SHACL/SKOS vocabularies, documentation, "
            "small examples, and release evidence for FOI-O NZ."
        ),
        rights_notice=(
            "MIT applies to code, schemas, ontology, examples, and documentation in "
            "this repository. Source FYI/archive content retains its original rights "
            "and platform terms and is not republished by this release package."
        ),
        validation_commands=[
            ReleaseValidationCommand(
                command=command,
                description="Required repo-local release validation command.",
            )
            for command in REQUIRED_RELEASE_VALIDATION_COMMANDS
        ],
        evidence=[
            ReleaseEvidenceItem(
                path="README.md",
                description="Current product surface, boundaries, examples, and license notice.",
            ),
            ReleaseEvidenceItem(
                path="docs/11-implementation-status.md",
                description="Current implemented, optional, planned, and external-gated status.",
            ),
            ReleaseEvidenceItem(
                path="docs/19-release-readiness-evidence.md",
                description="Repeatable release-readiness validation sequence and external gates.",
            ),
            ReleaseEvidenceItem(
                path="examples/dataset-metadata.examples.json",
                description="Dataset metadata fixture for derived process artifacts.",
            ),
            ReleaseEvidenceItem(
                path="examples/reproducibility-manifest.examples.json",
                description="Reproducibility manifest fixture for local tool/file evidence.",
            ),
            ReleaseEvidenceItem(
                path="conductor/archive/ontology_shacl_maturation_20260702/final-verification.md",
                description="Most recent roadmap track final verification evidence.",
            ),
        ],
        publication_artifacts=[
            ReleasePublicationArtifact(
                name="release checklist",
                status="repo_local",
                path="examples/release-checklist.v0.9.0.json",
                description="Machine-readable release package checklist fixture.",
            ),
            ReleasePublicationArtifact(
                name="dataset metadata",
                status="repo_local",
                path="examples/dataset-metadata.examples.json",
                description="Machine-readable derived-artifact metadata fixture.",
            ),
            ReleasePublicationArtifact(
                name="methods paper",
                status="repo_local",
                path="docs/23-methods-paper.md",
                description="Short methods paper for the release package.",
            ),
        ],
        external_gates=[
            ReleaseExternalGate(
                name="GitHub release publication",
                status="manual_approval_required",
                reason="Requires maintainer tag/release approval and final changelog review.",
            ),
            ReleaseExternalGate(
                name="Hugging Face dataset publication",
                status="manual_approval_required",
                reason="Requires credentials, terms review, and human approval before upload.",
            ),
            ReleaseExternalGate(
                name="Zenodo or OSF deposit",
                status="manual_approval_required",
                reason="Requires registry credentials, metadata review, and manual publication.",
            ),
            ReleaseExternalGate(
                name="Live FYI/archive pulls",
                status="external_gate",
                reason="Network/source availability and source snapshot capture are outside repo-local proof.",
            ),
            ReleaseExternalGate(
                name="Native Mojo/MAX release certification",
                status="external_gate",
                reason="Requires available Modular toolchain and passing native format/test/build checks.",
            ),
        ],
    )


def _load_checklist_document(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_release_checklist_document(path: Path, *, base_dir: Path) -> dict[str, Any]:
    """Validate repo-local path and external-gate references in a checklist."""
    data = _load_checklist_document(path)
    errors: list[str] = []
    commands = {item.get("command") for item in data.get("validation_commands", [])}
    for command in REQUIRED_RELEASE_VALIDATION_COMMANDS:
        if command not in commands:
            errors.append(f"missing required validation command: {command}")
    for item in data.get("validation_commands", []):
        executable = str(item.get("command", "")).split(" ", 1)[0]
        if executable and shutil.which(executable) is None:
            errors.append(f"validation command executable unavailable: {executable}")
    for item in data.get("evidence", []):
        if item.get("required", True):
            item_path = base_dir / str(item.get("path", ""))
            if not item_path.exists():
                errors.append(f"missing required evidence path: {item.get('path')}")
    for item in data.get("publication_artifacts", []):
        if item.get("status") == "repo_local":
            artifact_path = base_dir / str(item.get("path", ""))
            if not artifact_path.exists():
                errors.append(f"missing repo-local publication artifact: {item.get('path')}")
    for gate in data.get("external_gates", []):
        if gate.get("status") not in {"external_gate", "manual_approval_required"}:
            errors.append(f"external gate is not explicitly labelled: {gate.get('name')}")
    rights_notice = str(data.get("rights_notice", ""))
    if "MIT" not in rights_notice or "original rights" not in rights_notice:
        errors.append("rights_notice must separate MIT code/docs from original source rights")
    return {"ok": not errors, "errors": errors}


def write_release_checklist(output: Path, *, release_version: str | None = None) -> dict[str, Any]:
    """Write a release checklist JSON fixture."""
    checklist = build_release_checklist(release_version=release_version)
    write_json(output, checklist.model_dump(mode="json", exclude_none=True))
    return {
        "ok": True,
        "output": str(output),
        "release_version": checklist.release_version,
        "evidence_count": len(checklist.evidence),
        "external_gate_count": len(checklist.external_gates),
    }
