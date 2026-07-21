"""Validate that the incremental jurisdiction programme covers the live roadmap."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "profiles" / "roadmap.yaml"
COMPLETION_MAP = ROOT / "conductor" / "jurisdiction-completion-map.yaml"

REQUIRED_PHASES = {
    "legislation_access": "edithatogo/legislation",
    "gazette_equivalent": "edithatogo/legislation",
    "bounded_capture": "edithatogo/fyi-cli",
    "immutable_archive": "edithatogo/fyi-archive",
    "governed_extraction": "edithatogo/nlp-policy-nz",
    "case_process_modelling": "edithatogo/foi-process",
}
REQUIRED_TRACK_REPOS = {
    "edithatogo/foi-o",
    "edithatogo/legislation",
    "edithatogo/fyi-cli",
    "edithatogo/fyi-archive",
    "edithatogo/nlp-policy-nz",
    "edithatogo/foi-process",
}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a mapping")
    return data


def _roadmap_targets(roadmap: dict) -> list[str]:
    targets: list[str] = []
    for tranche in roadmap.get("tranches", []):
        for key in ("profiles", "deployments", "profiles_or_platforms"):
            targets.extend(str(value) for value in tranche.get(key, []))
    return targets


def _mapped_targets(completion_map: dict) -> list[str]:
    return [
        str(target)
        for tranche in completion_map.get("tranches", [])
        for target in tranche.get("targets", [])
    ]


def main() -> None:
    roadmap = _load(ROADMAP)
    completion_map = _load(COMPLETION_MAP)
    errors: list[str] = []

    roadmap_targets = _roadmap_targets(roadmap)
    mapped_targets = _mapped_targets(completion_map)
    duplicates = sorted(target for target, count in Counter(mapped_targets).items() if count > 1)
    if duplicates:
        errors.append(f"targets occur more than once: {duplicates}")
    if set(mapped_targets) != set(roadmap_targets):
        errors.append(
            "coverage differs from profiles/roadmap.yaml: "
            f"missing={sorted(set(roadmap_targets) - set(mapped_targets))}, "
            f"extra={sorted(set(mapped_targets) - set(roadmap_targets))}"
        )

    phases = {
        str(phase.get("id")): str(phase.get("owner_repo"))
        for phase in completion_map.get("phase_contract", [])
    }
    if phases != REQUIRED_PHASES:
        errors.append(f"phase ownership differs from required contract: {phases}")
    for phase in completion_map.get("phase_contract", []):
        if not str(phase.get("requirement", "")).strip():
            errors.append(f"phase {phase.get('id')} has no requirement")

    tracks = completion_map.get("repository_tracks", [])
    track_repos = {str(track.get("repo")) for track in tracks}
    if track_repos != REQUIRED_TRACK_REPOS:
        errors.append(
            "repository track ownership differs: "
            f"missing={sorted(REQUIRED_TRACK_REPOS - track_repos)}, "
            f"extra={sorted(track_repos - REQUIRED_TRACK_REPOS)}"
        )
    for track in tracks:
        if not isinstance(track.get("issue"), int) or not str(track.get("track", "")).strip():
            errors.append(f"repository track lacks an issue or track id: {track}")

    if (
        completion_map.get("policy", {}).get("completion_rule")
        != "every_target_must_complete_every_phase"
    ):
        errors.append("completion rule must require every phase for every target")

    if errors:
        raise SystemExit("Jurisdiction completion validation failed:\n- " + "\n- ".join(errors))
    print(
        "Jurisdiction completion map valid: "
        f"{len(mapped_targets)} targets, {len(phases)} phases, {len(track_repos)} owner repositories"
    )


if __name__ == "__main__":
    main()
