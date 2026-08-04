from __future__ import annotations

import json
import subprocess
import tarfile
from pathlib import Path

from jsonschema import Draft202012Validator

from foi_o_nz.release_manifest import (
    build_release_bundle,
    build_release_manifest,
    validate_release_bundle,
    validate_release_manifest,
)
from scripts.build_release_manifest import INCLUDE_FILES, INCLUDE_ROOTS, LICENSE_POLICY

ROOT = Path(__file__).parent.parent


def test_repository_release_policy_is_semantic_core_only() -> None:
    assert INCLUDE_FILES == (
        "CITATION.cff",
        "LICENSE-CODE.md",
        "LICENSE-CONTENT.md",
        "LICENSE.md",
        "contexts/foi-o-nz.context.jsonld",
        "ontology/foi-o-nz.ttl",
        "shacl/foi-o-nz.shapes.ttl",
        "vocab/agent-boundaries.skos.ttl",
        "vocab/assertion-status.skos.ttl",
        "vocab/event-types.skos.ttl",
        "vocab/request-states.skos.ttl",
    )
    assert INCLUDE_ROOTS == ()
    assert LICENSE_POLICY == {
        "CITATION.cff": "CC-BY-4.0",
        "LICENSE-CODE.md": "MIT",
        "LICENSE-CONTENT.md": "CC-BY-4.0",
        "LICENSE.md": "CC-BY-4.0",
        "contexts": "MIT",
        "ontology": "CC-BY-4.0",
        "shacl": "MIT",
        "vocab": "CC-BY-4.0",
    }

    prohibited_roots = {"conductor", "docs", "examples", "mappings", "schemas", "src", "tests"}
    assert prohibited_roots.isdisjoint(INCLUDE_ROOTS)


def test_repository_split_licence_contract() -> None:
    licence_map = (ROOT / "LICENSE.md").read_text(encoding="utf-8")
    code_licence = (ROOT / "LICENSE-CODE.md").read_text(encoding="utf-8")
    content_licence = (ROOT / "LICENSE-CONTENT.md").read_text(encoding="utf-8")

    assert "MIT" in licence_map
    assert "CC BY 4.0" in licence_map
    assert "third-party" in licence_map.lower()
    assert "source content" in licence_map.lower()
    assert "MIT License" in code_licence
    assert "Creative Commons Attribution 4.0 International" in content_licence
    assert "https://creativecommons.org/licenses/by/4.0/" in content_licence


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def repository(tmp_path: Path) -> tuple[Path, str]:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "release@example.invalid")
    git(tmp_path, "config", "user.name", "Release Test")
    (tmp_path / "src").mkdir()
    (tmp_path / "examples").mkdir()
    (tmp_path / "README.md").write_text("public\n", encoding="utf-8")
    (tmp_path / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "examples/private.json").write_text('{"secret": true}\n', encoding="utf-8")
    git(tmp_path, "add", "README.md", "src/app.py", "examples/private.json")
    git(tmp_path, "commit", "-qm", "fixture")
    return tmp_path, git(tmp_path, "rev-parse", "HEAD")


def test_manifest_is_commit_bound_allowlisted_and_self_pinned(tmp_path: Path) -> None:
    repo, revision = repository(tmp_path)

    manifest = build_release_manifest(
        repo=repo,
        revision=revision,
        include_files=("README.md",),
        include_roots=("src",),
        excluded_classes=("authentic_source_content",),
        license_policy={"README.md": "CC-BY-4.0", "src": "MIT"},
    )

    assert manifest["target_commit"] == revision
    assert [item["path"] for item in manifest["files"]] == ["README.md", "src/app.py"]
    assert manifest["file_count"] == 2
    assert manifest["total_bytes"] == sum(item["size"] for item in manifest["files"])
    assert manifest["manifest_sha256"]
    assert [item["license"] for item in manifest["files"]] == ["CC-BY-4.0", "MIT"]
    assert validate_release_manifest(manifest, repo=repo) == []
    schema = json.loads(
        (ROOT / "schemas/json/release-manifest.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(manifest)


def test_manifest_validation_rejects_hash_and_self_pin_mutation(tmp_path: Path) -> None:
    repo, revision = repository(tmp_path)
    manifest = build_release_manifest(
        repo=repo,
        revision=revision,
        include_files=("README.md",),
        include_roots=("src",),
        excluded_classes=("authentic_source_content",),
        license_policy={"README.md": "CC-BY-4.0", "src": "MIT"},
    )
    manifest["files"][0]["sha256"] = "0" * 64

    errors = validate_release_manifest(manifest, repo=repo)

    assert "file hash mismatch: README.md" in errors
    assert "manifest self-pin mismatch" in errors

    schema = json.loads(
        (ROOT / "schemas/json/release-manifest.schema.json").read_text(encoding="utf-8")
    )
    invalid = dict(manifest)
    invalid["publication_authorized"] = True
    assert list(Draft202012Validator(schema).iter_errors(invalid))


def test_manifest_validation_rejects_licence_mismatch(tmp_path: Path) -> None:
    repo, revision = repository(tmp_path)
    manifest = build_release_manifest(
        repo=repo,
        revision=revision,
        include_files=("README.md",),
        include_roots=("src",),
        excluded_classes=("authentic_source_content",),
        license_policy={"README.md": "CC-BY-4.0", "src": "MIT"},
    )
    manifest["files"][0]["license"] = "MIT"

    errors = validate_release_manifest(manifest, repo=repo)

    assert "file licence mismatch: README.md" in errors
    assert "manifest self-pin mismatch" in errors


def test_manifest_validation_rejects_incomplete_selection(tmp_path: Path) -> None:
    repo, revision = repository(tmp_path)
    manifest = build_release_manifest(
        repo=repo,
        revision=revision,
        include_files=("README.md",),
        include_roots=("src",),
        excluded_classes=("authentic_source_content",),
        license_policy={"README.md": "CC-BY-4.0", "src": "MIT"},
    )
    manifest["files"].pop()

    errors = validate_release_manifest(manifest, repo=repo)

    assert "manifest file set does not match selection" in errors


def test_manifest_rejects_empty_or_unsafe_selection(tmp_path: Path) -> None:
    repo, revision = repository(tmp_path)

    for include_files, include_roots in [(("missing.md",), ()), (("../README.md",), ())]:
        try:
            build_release_manifest(
                repo=repo,
                revision=revision,
                include_files=include_files,
                include_roots=include_roots,
                excluded_classes=("authentic_source_content",),
                license_policy={"README.md": "CC-BY-4.0"},
            )
        except ValueError as exc:
            assert str(exc) in {
                "missing release file: missing.md",
                "release selection is empty",
                "unsafe release path",
            }
        else:
            raise AssertionError("unsafe or empty release selection was accepted")


def test_release_bundle_is_deterministic_and_exact(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    repo, revision = repository(repo_dir)
    manifest = build_release_manifest(
        repo=repo,
        revision=revision,
        include_files=("README.md",),
        include_roots=("src",),
        excluded_classes=("authentic_source_content",),
        license_policy={"README.md": "CC-BY-4.0", "src": "MIT"},
    )
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    first_receipt = build_release_bundle(
        manifest=manifest,
        repo=repo,
        output=first,
        bundle_name="example-semantic-core-0.1.0",
    )
    second_receipt = build_release_bundle(
        manifest=manifest,
        repo=repo,
        output=second,
        bundle_name="example-semantic-core-0.1.0",
    )

    assert first.read_bytes() == second.read_bytes()
    assert first_receipt == second_receipt
    assert validate_release_bundle(first_receipt, bundle=first, manifest=manifest) == []
    receipt_schema = json.loads(
        (ROOT / "schemas/json/release-bundle-receipt.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(receipt_schema).validate(first_receipt)
    with tarfile.open(first, "r:gz") as archive:
        assert archive.getnames() == [
            "example-semantic-core-0.1.0/RELEASE-MANIFEST.json",
            "example-semantic-core-0.1.0/README.md",
            "example-semantic-core-0.1.0/src/app.py",
        ]


def test_release_bundle_validation_rejects_changed_bytes(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    repo, revision = repository(repo_dir)
    manifest = build_release_manifest(
        repo=repo,
        revision=revision,
        include_files=("README.md",),
        include_roots=(),
        excluded_classes=("authentic_source_content",),
        license_policy={"README.md": "CC-BY-4.0"},
    )
    bundle = tmp_path / "bundle.tar.gz"
    receipt = build_release_bundle(
        manifest=manifest,
        repo=repo,
        output=bundle,
        bundle_name="example-semantic-core-0.1.0",
    )
    bundle.write_bytes(bundle.read_bytes() + b"changed")

    assert "bundle SHA-256 mismatch" in validate_release_bundle(
        receipt, bundle=bundle, manifest=manifest
    )
