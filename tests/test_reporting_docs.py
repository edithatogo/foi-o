from __future__ import annotations

from pathlib import Path


README = Path("README.md")
STATUS_DOC = Path("docs/11-implementation-status.md")


def test_readme_documents_reporting_commands_and_publication_boundary() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "uv run foi-o-nz reporting-metrics" in readme
    assert "uv run foi-o-nz psc-report" in readme
    assert "examples/psc-report.small.json" in readme
    assert "not official PSC reporting" in readme


def test_status_doc_marks_reporting_profile_and_sample_reports_implemented() -> None:
    status = STATUS_DOC.read_text(encoding="utf-8")

    assert "PSC reporting metric profile" in status
    assert "PSC sample aggregate reports" in status
    assert "PSC sample aggregate reports and publication-safe reporting documentation" not in status
