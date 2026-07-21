from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tarfile
from pathlib import Path

import pytest

from foi_o_nz.validation import validate_json_schema

SCRIPT = Path("scripts/build_submission_latex.py")
LATEXMKRC = Path("submission/latex/latexmkrc")
README = Path("submission/latex/README.md")
PIPELINE_EXAMPLE = Path("examples/submission-latex-pipeline.planned.json")
PIPELINE_SCHEMA = Path("schemas/json/submission-latex-pipeline.schema.json")
ARXIV_READINESS = Path("examples/arxiv-readiness.manuscript-planned.json")
ARXIV_DOC = Path("docs/30-arxiv-readiness.md")


def _load_pipeline_module():
    spec = importlib.util.spec_from_file_location("build_submission_latex", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_submission_latex"] = module
    spec.loader.exec_module(module)
    return module


def test_submission_latex_pipeline_example_validates() -> None:
    result = validate_json_schema(PIPELINE_EXAMPLE, PIPELINE_SCHEMA)
    assert not result.errors, result.errors

    manifest = json.loads(PIPELINE_EXAMPLE.read_text(encoding="utf-8"))
    targets = {target["target"]: target for target in manifest["targets"]}
    assert targets["arxiv"]["engine"] == "pdflatex"
    assert targets["arxiv"]["arxiv_upload_candidate"] is True
    assert targets["enhanced"]["engine"] == "lualatex"
    assert targets["enhanced"]["accessibility_experiment"] is True


def test_latexmkrc_keeps_arxiv_and_enhanced_targets_separate() -> None:
    text = LATEXMKRC.read_text(encoding="utf-8")
    assert "FOIO_LATEX_TARGET" in text
    assert "pdflatex" in text
    assert "lualatex" in text
    assert "shell-escape" not in text

    readme = README.read_text(encoding="utf-8")
    assert "`arxiv`" in readme
    assert "`enhanced`" in readme
    assert "Vancouver-style numbered references" in readme


def test_arxiv_readiness_references_modern_latex_pipeline() -> None:
    doc = ARXIV_DOC.read_text(encoding="utf-8")
    report = json.loads(ARXIV_READINESS.read_text(encoding="utf-8"))

    assert "scripts/build_submission_latex.py" in doc
    assert "submission/latex/latexmkrc" in doc
    assert "Tectonic is optional local smoke tooling only" in doc

    tool_checks = {check["tool"]: check for check in report["tool_checks"]}
    assert tool_checks["scripts/build_submission_latex.py"]["requirement_level"] == "required"
    assert tool_checks["latexmk with LuaLaTeX"]["requirement_level"] == "conditional"


def test_builder_generates_two_targets_and_flags_current_manuscript_gates(tmp_path: Path) -> None:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc is required for the submission LaTeX builder")

    module = _load_pipeline_module()
    manifest = module.build_manifest(
        ["arxiv", "enhanced"],
        output_root=tmp_path,
        skip_compile=True,
        skip_cleaner=True,
    )

    targets = {target["target"]: target for target in manifest["targets"]}
    assert manifest["references"] == "submission/references/references.csl.json"
    assert set(targets) == {"arxiv", "enhanced"}
    assert (tmp_path / "arxiv" / "source" / "main.tex").exists()
    assert (tmp_path / "arxiv" / "source" / "references.csl.json").exists()
    assert (tmp_path / "arxiv" / "source" / "references.vancouver.md").exists()
    assert (tmp_path / "arxiv" / "source" / "main.bbl").exists()
    assert (tmp_path / "arxiv" / "source" / "sourceright-reference-report.json").exists()
    enhanced_tex = tmp_path / "enhanced" / "source" / "main.tex"
    enhanced_tex_text = enhanced_tex.read_text(encoding="utf-8")
    assert enhanced_tex_text.startswith("\\DocumentMetadata")
    assert "\\usepackage{flowchart}" in enhanced_tex_text
    assert "\\begin{tikzpicture}" in enhanced_tex_text
    assert "{[}\\hyperlink{ref-1}{1}-\\hyperlink{ref-3}{3}{]}" in enhanced_tex_text
    assert "\\hypertarget{ref-1}{}" in enhanced_tex_text
    assert "\\hypertarget{ref-26}{}" in enhanced_tex_text
    assert "docs/assets/foi-o-process-architecture.png" not in enhanced_tex_text

    arxiv_checks = {check["check_id"]: check for check in targets["arxiv"]["checks"]}
    assert arxiv_checks["raw-mermaid"]["status"] == "passed"
    assert arxiv_checks["vancouver-reference-shape"]["status"] == "passed"
    assert arxiv_checks["sourceright-csl-validation"]["status"] in {"passed", "warning"}
    assert arxiv_checks["vancouver-bibliography-generated"]["status"] == "passed"
    assert arxiv_checks["pdf-hyperlink-contract"]["status"] == "passed"
    assert arxiv_checks["sourceright-provider-verification"]["status"] == "external_gate"
    assert targets["arxiv"]["status"] == "passed"

    enhanced_checks = {check["check_id"]: check for check in targets["enhanced"]["checks"]}
    assert enhanced_checks["enhanced-figure-alt-text"]["status"] == "passed"
    assert enhanced_checks["enhanced-table-header-structure"]["status"] == "passed"
    assert enhanced_checks["enhanced-pdf-metadata-source"]["status"] == "passed"


def test_arxiv_source_package_uses_cleaned_source_tree(tmp_path: Path) -> None:
    module = _load_pipeline_module()
    source_root = tmp_path / "arxiv" / "source"
    cleaned_root = tmp_path / "arxiv" / "source_arXiv"
    cleaned_root.mkdir(parents=True)
    source_root.mkdir(parents=True)
    (cleaned_root / "main.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
    (cleaned_root / "main.bbl").write_text("\\begin{thebibliography}{1}\n", encoding="utf-8")
    (cleaned_root / "anc").mkdir()
    (cleaned_root / "anc" / "foi-o-nz-submission-supplement.pdf").write_bytes(b"%PDF-1.7\n")
    (cleaned_root / "main.aux").write_text("auxiliary build file\n", encoding="utf-8")
    (cleaned_root / "main.log").write_text("build log\n", encoding="utf-8")
    (cleaned_root / "main.pdf").write_bytes(b"%PDF-1.7\n")
    (cleaned_root / "latexmkrc").write_text("$pdf_mode = 1;\n", encoding="utf-8")

    result = module._create_arxiv_source_archive(source_root)
    archive_path = tmp_path / "arxiv" / "foi-o-arxiv-source.tar.gz"
    first_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    result_again = module._create_arxiv_source_archive(source_root)
    second_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()

    assert result.status == "passed"
    assert result_again.status == "passed"
    assert first_hash == second_hash
    with tarfile.open(archive_path, "r:gz") as archive:
        assert archive.getnames() == [
            "anc/foi-o-nz-submission-supplement.pdf",
            "latexmkrc",
            "main.bbl",
            "main.tex",
        ]
