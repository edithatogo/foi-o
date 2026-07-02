from __future__ import annotations

import builtins
from pathlib import Path
from typing import Any

from foi_o_nz.shacl_validation import validate_with_shacl

SHAPES = Path("shacl/foi-o-nz.shapes.ttl")


def _write_graph(tmp_path: Path, turtle: str) -> Path:
    path = tmp_path / "data.ttl"
    path.write_text(turtle, encoding="utf-8")
    return path


def test_candidate_decision_like_event_can_pass_with_review_required(tmp_path: Path) -> None:
    data = _write_graph(
        tmp_path,
        """
@prefix foio: <https://w3id.org/foio-nz/ontology#> .

foio:evidence-1 a foio:Evidence .
foio:event-1
  a foio:ProcessEvent, foio:DecisionLikeEvent ;
  foio:hasEvidence foio:evidence-1 ;
  foio:requiresHumanCertification true ;
  foio:humanReviewRequired true ;
  foio:machineCertificationAllowed false .
""",
    )

    result = validate_with_shacl(data, SHAPES)

    assert result["mode"] == "pyshacl"
    assert result["ok"] is True, result["report_text"]


def test_process_event_without_evidence_fails_shacl(tmp_path: Path) -> None:
    data = _write_graph(
        tmp_path,
        """
@prefix foio: <https://w3id.org/foio-nz/ontology#> .

foio:event-1
  a foio:ProcessEvent ;
  foio:requiresHumanCertification false .
""",
    )

    result = validate_with_shacl(data, SHAPES)

    assert result["mode"] == "pyshacl"
    assert result["ok"] is False
    assert "Every FOI-O NZ process event should have at least one evidence reference" in result[
        "report_text"
    ]


def test_agent_action_machine_certification_is_rejected(tmp_path: Path) -> None:
    data = _write_graph(
        tmp_path,
        """
@prefix foio: <https://w3id.org/foio-nz/ontology#> .

foio:action-1
  a foio:AgentAction ;
  foio:machineCertificationAllowed true ;
  foio:legalEffect "prohibited" .
""",
    )

    result = validate_with_shacl(data, SHAPES)

    assert result["mode"] == "pyshacl"
    assert result["ok"] is False
    assert "Agent actions must not allow machine certification" in result["report_text"]


def test_dataset_publication_requires_caveat(tmp_path: Path) -> None:
    data = _write_graph(
        tmp_path,
        """
@prefix foio: <https://w3id.org/foio-nz/ontology#> .

foio:dataset-1 a foio:DatasetPublication .
""",
    )

    result = validate_with_shacl(data, SHAPES)

    assert result["mode"] == "pyshacl"
    assert result["ok"] is False
    assert "Dataset publications should carry caveats" in result["report_text"]


def test_shacl_validation_degrades_to_parse_only_without_pyshacl(
    tmp_path: Path, monkeypatch
) -> None:
    data = _write_graph(
        tmp_path,
        """
@prefix foio: <https://w3id.org/foio-nz/ontology#> .

foio:event-1
  a foio:ProcessEvent ;
  foio:requiresHumanCertification false .
""",
    )
    real_import = builtins.__import__

    def missing_pyshacl(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "pyshacl":
            raise ModuleNotFoundError("pyshacl")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", missing_pyshacl)

    result = validate_with_shacl(data, SHAPES)

    assert result["ok"] is True
    assert result["mode"] == "parse_only_pyshacl_not_installed"
    assert result["warning"] == "install pyshacl for full SHACL constraint validation"
