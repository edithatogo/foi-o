"""Deterministic, commit-bound public-safe release manifests."""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tarfile
from gzip import GzipFile
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "foi-o.release-manifest.v2"
ALLOWED_LICENSES = frozenset({"MIT", "CC-BY-4.0"})
BUNDLE_SCHEMA_VERSION = "foi-o.release-bundle-receipt.v1"


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return result.stdout


def _safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def _canonical_hash(value: dict[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "manifest_sha256"}
    payload = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def build_release_manifest(
    *,
    repo: Path,
    revision: str,
    include_files: tuple[str, ...],
    include_roots: tuple[str, ...],
    excluded_classes: tuple[str, ...],
    license_policy: dict[str, str],
) -> dict[str, Any]:
    """Build a deterministic allow-list from files committed at ``revision``."""
    repo = repo.resolve()
    target_commit = _git(repo, "rev-parse", f"{revision}^{{commit}}").decode().strip()
    declared = (*include_files, *include_roots)
    if any(not _safe_path(path) for path in declared):
        raise ValueError("unsafe release path")
    if not license_policy or any(
        not _safe_path(path) or license_id not in ALLOWED_LICENSES
        for path, license_id in license_policy.items()
    ):
        raise ValueError("invalid release licence policy")

    tree_paths = sorted(
        item.decode()
        for item in _git(repo, "ls-tree", "-r", "-z", "--name-only", target_commit).split(b"\0")
        if item
    )
    missing_include_files = sorted(set(include_files) - set(tree_paths))
    if missing_include_files:
        raise ValueError(f"missing release file: {missing_include_files[0]}")
    selected = [
        path
        for path in tree_paths
        if path in include_files
        or any(path == root or path.startswith(f"{root}/") for root in include_roots)
    ]
    if not selected:
        raise ValueError("release selection is empty")

    def license_for(path: str) -> str:
        matches = [
            (key, value)
            for key, value in license_policy.items()
            if path == key or path.startswith(f"{key}/")
        ]
        if not matches:
            raise ValueError(f"missing release licence: {path}")
        return max(matches, key=lambda item: len(item[0]))[1]

    files: list[dict[str, Any]] = []
    for path in selected:
        content = _git(repo, "show", f"{target_commit}:{path}")
        blob_oid = _git(repo, "rev-parse", f"{target_commit}:{path}").decode().strip()
        files.append(
            {
                "path": path,
                "blob_oid": blob_oid,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
                "license": license_for(path),
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_not_authorized",
        "repository": "https://github.com/edithatogo/foi-o",
        "target_commit": target_commit,
        "selection": {
            "include_files": list(include_files),
            "include_roots": list(include_roots),
            "excluded_classes": list(excluded_classes),
            "license_policy": dict(sorted(license_policy.items())),
        },
        "files": files,
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files),
        "publication_authorized": False,
        "release_authorized": False,
    }
    manifest["manifest_sha256"] = _canonical_hash(manifest)
    return manifest


def validate_release_manifest(manifest: dict[str, Any], *, repo: Path) -> list[str]:
    """Validate hashes, counts, ordering, boundaries, and the manifest self-pin."""
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported schema version")
    if manifest.get("status") != "candidate_not_authorized":
        errors.append("manifest is not candidate-only")
    if manifest.get("publication_authorized") is not False:
        errors.append("publication must remain unauthorized")
    if manifest.get("release_authorized") is not False:
        errors.append("release must remain unauthorized")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        errors.append("manifest files must be non-empty")
        files = []
    paths = [
        path
        for item in files
        if isinstance(item, dict)
        for path in [item.get("path")]
        if isinstance(path, str)
    ]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        errors.append("manifest paths must be sorted and unique")
    if manifest.get("file_count") != len(files):
        errors.append("file count mismatch")
    if manifest.get("total_bytes") != sum(
        item.get("size", 0) for item in files if isinstance(item, dict)
    ):
        errors.append("total byte count mismatch")

    selection = manifest.get("selection")
    policy = selection.get("license_policy") if isinstance(selection, dict) else None
    include_files = selection.get("include_files") if isinstance(selection, dict) else None
    include_roots = selection.get("include_roots") if isinstance(selection, dict) else None
    declared_paths = (
        [*include_files, *include_roots]
        if isinstance(include_files, list) and isinstance(include_roots, list)
        else []
    )
    if (
        not isinstance(include_files, list)
        or not isinstance(include_roots, list)
        or any(not isinstance(path, str) or not _safe_path(path) for path in declared_paths)
    ):
        errors.append("invalid release selection")
        include_files = []
        include_roots = []
    if (
        not isinstance(policy, dict)
        or not policy
        or any(
            not isinstance(path, str) or not _safe_path(path) or license_id not in ALLOWED_LICENSES
            for path, license_id in policy.items()
        )
    ):
        errors.append("invalid release licence policy")
        policy = {}

    repo = repo.resolve()
    target = str(manifest.get("target_commit", ""))
    try:
        tree_paths = sorted(
            item.decode()
            for item in _git(repo, "ls-tree", "-r", "-z", "--name-only", target).split(b"\0")
            if item
        )
    except subprocess.CalledProcessError:
        errors.append("invalid target commit")
        tree_paths = []
    if sorted(set(include_files) - set(tree_paths)):
        errors.append("declared release file is missing")
    expected_paths = [
        path
        for path in tree_paths
        if path in include_files
        or any(path == root or path.startswith(f"{root}/") for root in include_roots)
    ]
    if paths != expected_paths:
        errors.append("manifest file set does not match selection")
    for item in files:
        if not isinstance(item, dict) or not _safe_path(str(item.get("path", ""))):
            errors.append("unsafe release path")
            continue
        path = str(item["path"])
        matches = [
            (key, value)
            for key, value in policy.items()
            if path == key or path.startswith(f"{key}/")
        ]
        expected_license = max(matches, key=lambda value: len(value[0]))[1] if matches else None
        if expected_license is None:
            errors.append(f"missing release licence: {path}")
        elif item.get("license") != expected_license:
            errors.append(f"file licence mismatch: {path}")
        try:
            content = _git(repo, "show", f"{target}:{path}")
            blob_oid = _git(repo, "rev-parse", f"{target}:{path}").decode().strip()
        except subprocess.CalledProcessError:
            errors.append(f"missing target file: {path}")
            continue
        if item.get("sha256") != hashlib.sha256(content).hexdigest():
            errors.append(f"file hash mismatch: {path}")
        if item.get("size") != len(content):
            errors.append(f"file size mismatch: {path}")
        if item.get("blob_oid") != blob_oid:
            errors.append(f"blob oid mismatch: {path}")
    if manifest.get("manifest_sha256") != _canonical_hash(manifest):
        errors.append("manifest self-pin mismatch")
    return errors


def _manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, indent=2) + "\n").encode("utf-8")


def _tar_member(name: str, content: bytes) -> tuple[tarfile.TarInfo, io.BytesIO]:
    info = tarfile.TarInfo(name=name)
    info.size = len(content)
    info.mode = 0o644
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info, io.BytesIO(content)


def _bundle_bytes(bundle_name: str, members: list[tuple[str, bytes, str]]) -> bytes:
    raw = io.BytesIO()
    with (
        GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive,
    ):
        for relative, content, _license in members:
            info, stream = _tar_member(f"{bundle_name}/{relative}", content)
            archive.addfile(info, stream)
    return raw.getvalue()


def build_release_bundle(
    *,
    manifest: dict[str, Any],
    repo: Path,
    output: Path,
    bundle_name: str,
) -> dict[str, Any]:
    """Materialize a deterministic candidate archive from a validated manifest."""
    if not bundle_name or "/" in bundle_name or "\\" in bundle_name or bundle_name in {".", ".."}:
        raise ValueError("unsafe bundle name")
    errors = validate_release_manifest(manifest, repo=repo)
    if errors:
        raise ValueError("invalid release manifest: " + "; ".join(errors))

    manifest_content = _manifest_bytes(manifest)
    members: list[tuple[str, bytes, str]] = [
        ("RELEASE-MANIFEST.json", manifest_content, "CC-BY-4.0")
    ]
    target = str(manifest["target_commit"])
    for item in manifest["files"]:
        path = str(item["path"])
        members.append(
            (path, _git(repo.resolve(), "show", f"{target}:{path}"), str(item["license"]))
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    bundle_bytes = _bundle_bytes(bundle_name, members)
    output.write_bytes(bundle_bytes)
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "status": "candidate_not_authorized",
        "bundle_name": bundle_name,
        "target_commit": target,
        "manifest_sha256": manifest["manifest_sha256"],
        "manifest_file_sha256": hashlib.sha256(manifest_content).hexdigest(),
        "bundle_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        "bundle_size": len(bundle_bytes),
        "member_count": len(members),
        "members": [
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
                "license": license_id,
            }
            for relative, content, license_id in members
        ],
        "release_authorized": False,
        "publication_authorized": False,
    }


def validate_release_bundle(
    receipt: dict[str, Any], *, bundle: Path, manifest: dict[str, Any], repo: Path
) -> list[str]:
    """Validate a deterministic archive receipt against its release manifest."""
    errors = [
        f"invalid release manifest: {error}"
        for error in validate_release_manifest(manifest, repo=repo)
    ]
    if receipt.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        errors.append("unsupported bundle receipt schema")
    if receipt.get("status") != "candidate_not_authorized":
        errors.append("bundle is not candidate-only")
    if receipt.get("release_authorized") is not False:
        errors.append("bundle release must remain unauthorized")
    if receipt.get("publication_authorized") is not False:
        errors.append("bundle publication must remain unauthorized")

    content = bundle.read_bytes()
    if receipt.get("bundle_sha256") != hashlib.sha256(content).hexdigest():
        errors.append("bundle SHA-256 mismatch")
    if receipt.get("bundle_size") != len(content):
        errors.append("bundle size mismatch")
    if receipt.get("manifest_sha256") != manifest.get("manifest_sha256"):
        errors.append("bundle manifest self-pin mismatch")
    if receipt.get("target_commit") != manifest.get("target_commit"):
        errors.append("bundle target commit mismatch")
    manifest_content = _manifest_bytes(manifest)
    if receipt.get("manifest_file_sha256") != hashlib.sha256(manifest_content).hexdigest():
        errors.append("bundle manifest file SHA-256 mismatch")

    bundle_name = receipt.get("bundle_name")
    if (
        not isinstance(bundle_name, str)
        or not bundle_name
        or "/" in bundle_name
        or "\\" in bundle_name
    ):
        errors.append("unsafe bundle name")
        return errors
    expected: list[tuple[str, bytes | None, str]] = [
        ("RELEASE-MANIFEST.json", manifest_content, "CC-BY-4.0")
    ]
    expected.extend(
        (str(item["path"]), None, str(item["license"])) for item in manifest.get("files", [])
    )
    try:
        with tarfile.open(bundle, "r:gz") as archive:
            members = archive.getmembers()
            expected_names = [f"{bundle_name}/{path}" for path, _content, _license in expected]
            if [member.name for member in members] != expected_names:
                errors.append("bundle member set mismatch")
            actual_receipt_members: list[dict[str, Any]] = []
            canonical_members: list[tuple[str, bytes, str]] = []
            manifest_by_path = {str(item["path"]): item for item in manifest.get("files", [])}
            for member in members:
                if not member.isfile() or member.issym() or member.islnk():
                    errors.append(f"unsafe bundle member: {member.name}")
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    errors.append(f"missing bundle member bytes: {member.name}")
                    continue
                member_content = extracted.read()
                relative = member.name.removeprefix(f"{bundle_name}/")
                if relative == "RELEASE-MANIFEST.json":
                    expected_content = manifest_content
                    license_id = "CC-BY-4.0"
                else:
                    item = manifest_by_path.get(relative)
                    expected_content = None
                    license_id = str(item["license"]) if item else ""
                if expected_content is not None and member_content != expected_content:
                    errors.append(f"bundle member content mismatch: {relative}")
                if relative in manifest_by_path:
                    item = manifest_by_path[relative]
                    if hashlib.sha256(member_content).hexdigest() != item["sha256"]:
                        errors.append(f"bundle member hash mismatch: {relative}")
                actual_receipt_members.append(
                    {
                        "path": relative,
                        "sha256": hashlib.sha256(member_content).hexdigest(),
                        "size": len(member_content),
                        "license": license_id,
                    }
                )
                canonical_members.append((relative, member_content, license_id))
            if receipt.get("members") != actual_receipt_members:
                errors.append("bundle member receipt mismatch")
            if receipt.get("member_count") != len(members):
                errors.append("bundle member count mismatch")
            if content != _bundle_bytes(bundle_name, canonical_members):
                errors.append("bundle is not canonical")
    except (tarfile.TarError, OSError):
        errors.append("invalid release bundle archive")
    return errors
