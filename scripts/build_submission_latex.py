"""Build and preflight FOI-O NZ LaTeX submission targets."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_MD = ROOT / "docs" / "27-submission-manuscript.md"
SUPPLEMENT_MD = ROOT / "docs" / "28-submission-supplement.md"
LATEX_CONFIG_DIR = ROOT / "submission" / "latex"
LATEXMKRC = LATEX_CONFIG_DIR / "latexmkrc"
REFERENCES_CSL = ROOT / "submission" / "references" / "references.csl.json"
LOCAL_SOURCERIGHT_CANDIDATES = (
    ROOT / ".repo-tools" / "sourceright" / "target" / "release" / "sourceright",
    ROOT / ".repo-tools" / "sourceright" / "target" / "debug" / "sourceright",
)
LOCAL_AUTHENTEXT = ROOT / ".repo-tools" / "authentext"
DEFAULT_OUTPUT_ROOT = ROOT / "build" / "submission" / "latex"

Target = Literal["arxiv", "enhanced"]


@dataclass(frozen=True, slots=True)
class TargetConfig:
    name: Target
    engine: str
    compile_runs: int
    accessibility_experiment: bool
    arxiv_upload_candidate: bool


@dataclass(slots=True)
class CheckResult:
    check_id: str
    status: Literal["passed", "failed", "warning", "skipped", "external_gate"]
    message: str
    evidence_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    cwd: str
    status: Literal["passed", "failed", "skipped"]
    returncode: int | None
    log_path: str | None


TARGETS: dict[Target, TargetConfig] = {
    "arxiv": TargetConfig(
        name="arxiv",
        engine="pdflatex",
        compile_runs=2,
        accessibility_experiment=False,
        arxiv_upload_candidate=True,
    ),
    "enhanced": TargetConfig(
        name="enhanced",
        engine="lualatex",
        compile_runs=1,
        accessibility_experiment=True,
        arxiv_upload_candidate=False,
    ),
}

LOCAL_PATH_PATTERN = re.compile(r"(/Users/|/Volumes/|file://)")
RAW_MERMAID_PATTERN = re.compile(r"^```mermaid\b", re.MULTILINE)
MARKDOWN_BULLET_REFERENCES_PATTERN = re.compile(r"^# References\s*\n\s*-\s+", re.MULTILINE)
NUMERIC_REFERENCE_PATTERN = re.compile(r"^\s*(?:\[[0-9]+\]\s+|[0-9]+\.\s+)", re.MULTILINE)
LATEX_NUMERIC_CITATION_PATTERN = re.compile(r"\{\[\}([0-9][0-9,\- ]*)\{\]\}")
UNSUPPORTED_ARXIV_PATTERNS = {
    "shell-escape": re.compile(r"(?:shell-escape|\\write18|\\input\|)", re.IGNORECASE),
    "minted": re.compile(r"\\usepackage(?:\[[^\]]*\])?\{minted\}", re.IGNORECASE),
    "pythontex": re.compile(r"\\usepackage(?:\[[^\]]*\])?\{pythontex\}", re.IGNORECASE),
    "local-font-path": re.compile(r"\\set(?:main|sans|mono)font\{(?:/|\.{2}/)"),
}
LATEX_LOG_FAILURE_PATTERNS = {
    "overfull-box": re.compile(r"Overfull \\[hv]box"),
    "undefined-citation": re.compile(r"(Citation .* undefined|There were undefined references)"),
    "missing-file": re.compile(r"(File .* not found|LaTeX Error: File `[^']+' not found)"),
    "fatal-error": re.compile(r"(Fatal error occurred|Emergency stop|! LaTeX Error)"),
}
ARXIV_PACKAGE_EXCLUDED_SUFFIXES = {
    ".aux",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".pdf",
    ".run.xml",
    ".synctex.gz",
    ".toc",
    ".xdv",
}


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> CommandResult:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    log_path.write_text(
        "$ " + " ".join(command) + "\n\n"
        "## stdout\n" + completed.stdout + "\n\n## stderr\n" + completed.stderr,
        encoding="utf-8",
    )
    return CommandResult(
        command=command,
        cwd=_relative(cwd),
        status="passed" if completed.returncode == 0 else "failed",
        returncode=completed.returncode,
        log_path=_relative(log_path),
    )


def _tool_version(tool: str, args: list[str] | None = None) -> dict[str, Any]:
    executable = shutil.which(tool)
    if executable is None:
        return {"tool": tool, "available": False}
    command = [executable, *(args or ["--version"])]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    first_line = (completed.stdout or completed.stderr).strip().splitlines()
    return {
        "tool": tool,
        "available": True,
        "path": executable,
        "version": first_line[0] if first_line else "",
        "returncode": completed.returncode,
    }


def _sourceright_tool_version() -> dict[str, Any]:
    executable = _sourceright_binary()
    if executable is None:
        return {"tool": "sourceright", "available": False}
    completed = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    first_line = (completed.stdout or completed.stderr).strip().splitlines()
    return {
        "tool": "sourceright",
        "available": True,
        "path": executable,
        "version": first_line[0] if first_line else "",
        "returncode": completed.returncode,
    }


def _texlive_check() -> CheckResult:
    version = _tool_version("pdflatex")
    if not version.get("available"):
        return CheckResult(
            "texlive-2025-parity",
            "failed",
            "pdflatex is not available, so arXiv TeX Live parity cannot be checked.",
        )
    text = str(version.get("version", ""))
    if "TeX Live 2025" in text:
        return CheckResult(
            "texlive-2025-parity",
            "passed",
            "Local TeX reports TeX Live 2025.",
        )
    return CheckResult(
        "texlive-2025-parity",
        "external_gate",
        f"Local TeX is not TeX Live 2025 ({text}); arXiv parity remains a submission gate.",
    )


def _scan_markdown(path: Path) -> list[CheckResult]:
    text = path.read_text(encoding="utf-8")
    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            "raw-mermaid",
            "failed" if RAW_MERMAID_PATTERN.search(text) else "passed",
            "Raw Mermaid fences must be rendered before manuscript packaging."
            if RAW_MERMAID_PATTERN.search(text)
            else "No raw Mermaid fences detected.",
            [_relative(path)],
        )
    )
    checks.append(
        CheckResult(
            "absolute-local-paths",
            "failed" if LOCAL_PATH_PATTERN.search(text) else "passed",
            "Absolute local paths are not allowed in manuscript source."
            if LOCAL_PATH_PATTERN.search(text)
            else "No absolute local paths detected in manuscript source.",
            [_relative(path)],
        )
    )
    checks.append(
        CheckResult(
            "vancouver-reference-shape",
            "failed" if MARKDOWN_BULLET_REFERENCES_PATTERN.search(text) else "passed",
            "References must be numbered Vancouver-style, not a bullet list."
            if MARKDOWN_BULLET_REFERENCES_PATTERN.search(text)
            else "No bullet-style references detected.",
            [_relative(path)],
        )
    )
    if "# References" in text and not NUMERIC_REFERENCE_PATTERN.search(
        text.split("# References", 1)[1]
    ):
        checks.append(
            CheckResult(
                "numbered-reference-list",
                "failed",
                "References section does not contain numbered reference entries.",
                [_relative(path)],
            )
        )
    else:
        checks.append(
            CheckResult(
                "numbered-reference-list",
                "passed",
                "References section contains numbered entries or is absent from this source.",
                [_relative(path)],
            )
        )
    return checks


def _scan_tex(path: Path) -> list[CheckResult]:
    text = path.read_text(encoding="utf-8")
    checks: list[CheckResult] = []
    for check_id, pattern in UNSUPPORTED_ARXIV_PATTERNS.items():
        checks.append(
            CheckResult(
                f"unsupported-arxiv-pattern:{check_id}",
                "failed" if pattern.search(text) else "passed",
                f"Unsupported arXiv pattern detected: {check_id}."
                if pattern.search(text)
                else f"Unsupported arXiv pattern absent: {check_id}.",
                [_relative(path)],
            )
        )
    checks.append(
        CheckResult(
            "generated-source-local-paths",
            "failed" if LOCAL_PATH_PATTERN.search(text) else "passed",
            "Generated TeX contains absolute local paths."
            if LOCAL_PATH_PATTERN.search(text)
            else "Generated TeX contains no absolute local paths.",
            [_relative(path)],
        )
    )
    return checks


def _scan_latex_log(path: Path, *, prefix: str = "latex-log") -> list[CheckResult]:
    if not path.exists():
        return [
            CheckResult(
                f"{prefix}:present",
                "skipped",
                "No LaTeX log exists because compile did not run.",
                [_relative(path)],
            )
        ]
    text = path.read_text(encoding="utf-8", errors="replace")
    checks: list[CheckResult] = []
    for check_id, pattern in LATEX_LOG_FAILURE_PATTERNS.items():
        checks.append(
            CheckResult(
                f"{prefix}:{check_id}",
                "failed" if pattern.search(text) else "passed",
                f"LaTeX log contains {check_id}."
                if pattern.search(text)
                else f"LaTeX log does not contain {check_id}.",
                [_relative(path)],
            )
        )
    return checks


def _scan_figures(tex_path: Path) -> list[CheckResult]:
    text = tex_path.read_text(encoding="utf-8")
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text)
    missing = [
        figure
        for figure in figures
        if not (tex_path.parent / figure).exists() and not (ROOT / figure).exists()
    ]
    if missing:
        return [
            CheckResult(
                "figure-assets-present",
                "failed",
                "Missing included figure assets: " + ", ".join(sorted(missing)),
                [_relative(tex_path)],
            )
        ]
    return [
        CheckResult(
            "figure-assets-present",
            "passed",
            f"All included figure assets exist ({len(figures)} checked).",
            [_relative(tex_path)],
        )
    ]


def _scan_pdf_hyperlink_contract(tex_path: Path) -> CheckResult:
    """Require navigable links for the manuscript's named elements.

    This is deliberately source-level: it catches a broken Pandoc/LaTeX
    transformation before a PDF is handed to a reviewer or packaged.
    """
    text = tex_path.read_text(encoding="utf-8")
    anchors = set(re.findall(r"\\hypertarget\{([^}]+)\}", text))
    links = set(re.findall(r"\\hyperlink\{([^}]+)\}", text))
    required_targets = {
        "abbreviations": {"tab-abbreviations"},
        "glossary": {"tab-glossary"},
        "tables": {
            target
            for target in anchors
            if target.startswith("tab-") and target not in {"tab-abbreviations", "tab-glossary"}
        },
        "figures": {target for target in anchors if target.startswith("fig-")},
    }
    missing: list[str] = []
    for category, targets in required_targets.items():
        for target in sorted(targets):
            if target not in anchors:
                missing.append(f"{category} target {target}")
            if target not in links:
                missing.append(f"{category} link {target}")
    for target in sorted(target for target in links if target.startswith("ref-")):
        if target not in anchors:
            missing.append(f"citation target {target}")
    return CheckResult(
        "pdf-hyperlink-contract",
        "failed" if missing else "passed",
        "Missing required PDF hyperlinks or anchors: " + ", ".join(missing)
        if missing
        else "Citations, abbreviations, glossary terms, tables, and figures have matching PDF links and anchors.",
        [_relative(tex_path)],
    )


def _copy_figure_assets(tex_path: Path, source_root: Path) -> list[CheckResult]:
    text = tex_path.read_text(encoding="utf-8")
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text)
    copied: list[str] = []
    missing: list[str] = []
    for figure in figures:
        source_path = ROOT / figure
        target_path = source_root / figure
        if not source_path.exists():
            missing.append(figure)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied.append(_relative(target_path))
    if missing:
        return [
            CheckResult(
                "figure-assets-copied",
                "failed",
                "Referenced figure assets could not be copied: " + ", ".join(missing),
                [_relative(tex_path)],
            )
        ]
    return [
        CheckResult(
            "figure-assets-copied",
            "passed",
            f"Copied referenced figure assets into the generated source tree ({len(copied)} copied).",
            copied or [_relative(tex_path)],
        )
    ]


def _scan_enhanced_accessibility(tex_path: Path) -> list[CheckResult]:
    text = tex_path.read_text(encoding="utf-8")
    figure_matches = re.findall(
        r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}",
        text,
    )
    figures_missing_alt = [figure for options, figure in figure_matches if "alt=" not in options]
    table_blocks = re.findall(
        r"\\begin\{longtable\}.*?\\end\{longtable\}",
        text,
        flags=re.DOTALL,
    )
    tables_missing_headers = [
        str(index)
        for index, block in enumerate(table_blocks, start=1)
        if "\\endhead" not in block or "\\toprule" not in block
    ]
    metadata_present = "pdftitle=" in text and "pdfauthor=" in text
    return [
        CheckResult(
            "enhanced-figure-alt-text",
            "failed" if figures_missing_alt else "passed",
            "Figures missing alt text: " + ", ".join(figures_missing_alt)
            if figures_missing_alt
            else f"All included figures have alt text metadata ({len(figure_matches)} checked).",
            [_relative(tex_path)],
        ),
        CheckResult(
            "enhanced-table-header-structure",
            "failed" if tables_missing_headers else "passed",
            "Generated longtables missing reusable header structure: "
            + ", ".join(tables_missing_headers)
            if tables_missing_headers
            else f"Generated longtables retain header structure ({len(table_blocks)} checked).",
            [_relative(tex_path)],
        ),
        CheckResult(
            "enhanced-pdf-metadata-source",
            "passed" if metadata_present else "failed",
            "Generated source contains PDF title and author metadata."
            if metadata_present
            else "Generated source is missing PDF title or author metadata.",
            [_relative(tex_path)],
        ),
    ]


def _sourceright_binary() -> str | None:
    for candidate in LOCAL_SOURCERIGHT_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return shutil.which("sourceright")


def _authentext_repo() -> Path | None:
    if (LOCAL_AUTHENTEXT / "package.json").exists():
        return LOCAL_AUTHENTEXT
    return None


def _authentext_tool_version() -> dict[str, Any]:
    repo = _authentext_repo()
    if repo is None:
        return {"tool": "authentext", "available": False}
    package = json.loads((repo / "package.json").read_text(encoding="utf-8"))
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=False
    )
    return {
        "tool": "authentext",
        "available": True,
        "path": str(repo),
        "version": package.get("version", ""),
        "commit": commit.stdout.strip(),
    }


def _csl_items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("CSL reference source must be a JSON array")
    return [item for item in data if isinstance(item, dict)]


def _csl_year(item: dict[str, Any]) -> str:
    date_parts = item.get("issued", {}).get("date-parts", [])
    if date_parts and date_parts[0]:
        return str(date_parts[0][0])
    return "n.d."


def _csl_author_text(item: dict[str, Any]) -> str | None:
    authors = item.get("author") or []
    rendered: list[str] = []
    for author in authors:
        if not isinstance(author, dict):
            continue
        if author.get("literal"):
            rendered.append(str(author["literal"]))
            continue
        family = str(author.get("family", "")).strip()
        given = str(author.get("given", "")).strip()
        initials = "".join(part[:1] for part in given.replace(".", "").split() if part)
        rendered.append(" ".join(part for part in [family, initials] if part))
    return ", ".join(rendered) if rendered else None


def _vancouver_reference(item: dict[str, Any]) -> str:
    title = str(item.get("title") or item.get("id") or "Untitled reference")
    year = _csl_year(item)
    url = item.get("URL")
    author = _csl_author_text(item)
    if item.get("type") == "legislation":
        base = f"{title}. {year}"
    else:
        base = f"{author + '. ' if author else ''}{title}. {year}"
    if item.get("type") == "software":
        base = base.replace(f"{title}.", f"{title} [software].")
    if url:
        base += f" [cited 2026 Jul 3]. Available from: {url}"
    return base + "."


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in text)


def _write_reference_outputs(
    items: list[dict[str, Any]],
    *,
    source_root: Path,
    sourceright_ok: bool,
) -> None:
    vancouver_lines = [
        f"{index}. {_vancouver_reference(item)}" for index, item in enumerate(items, start=1)
    ]
    (source_root / "references.vancouver.md").write_text(
        "\n".join(vancouver_lines) + "\n",
        encoding="utf-8",
    )
    bbl_lines = ["\\begin{thebibliography}{" + str(len(items)) + "}"]
    for item in items:
        reference_id = str(item.get("id") or f"reference-{len(bbl_lines)}")
        bbl_lines.append(f"\\bibitem{{{reference_id}}} {_latex_escape(_vancouver_reference(item))}")
    bbl_lines.append("\\end{thebibliography}")
    (source_root / "main.bbl").write_text("\n".join(bbl_lines) + "\n", encoding="utf-8")

    review_count = 0 if sourceright_ok else len(items)
    issues = [
        {
            "severity": "info",
            "category": "manual_review",
            "reference_id": str(item.get("id") or ""),
            "code": "provider-verification-pending",
            "message": "CSL shape is valid, but live provider verification remains a human/external gate.",
            "ai_risk_signal": False,
        }
        for item in items
    ]
    report = {
        "schema_version": "sourceright.reference_report.v1",
        "report_type": "foi-o-submission-reference-integrity",
        "summary": {
            "total_references": len(items),
            "verified_references": 0,
            "review_queue_count": review_count,
            "unresolved_count": len(items),
            "conflict_count": 0,
            "ai_risk_issue_count": 0,
            "error_count": 0,
            "warning_count": 0,
            "info_count": len(issues),
        },
        "issues": issues,
    }
    (source_root / "sourceright-reference-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _citation_target(reference_number: int) -> str:
    return f"ref-{reference_number}"


def _link_citation_numbers(citation_body: str) -> str:
    parts: list[str] = []
    for token in re.split(r"([,\- ])", citation_body):
        if token.isdigit():
            number = int(token)
            parts.append(f"\\hyperlink{{{_citation_target(number)}}}{{{number}}}")
        else:
            parts.append(token)
    return "{[}" + "".join(parts) + "{]}"


def _link_numeric_citations(tex: str) -> str:
    references_marker = "\\section{References}"
    if references_marker not in tex:
        return LATEX_NUMERIC_CITATION_PATTERN.sub(
            lambda match: _link_citation_numbers(match.group(1)), tex
        )
    body, references = tex.split(references_marker, 1)
    linked_body = LATEX_NUMERIC_CITATION_PATTERN.sub(
        lambda match: _link_citation_numbers(match.group(1)), body
    )
    return linked_body + references_marker + references


def _anchor_reference_items(tex: str) -> str:
    references_marker = "\\section{References}"
    if references_marker not in tex:
        return tex
    body, references = tex.split(references_marker, 1)
    reference_index = 0

    def replace_item(match: re.Match[str]) -> str:
        nonlocal reference_index
        reference_index += 1
        return f"\\hypertarget{{{_citation_target(reference_index)}}}{{}}\n{match.group(0)}"

    anchored_references = re.sub(r"(?m)^\\item$", replace_item, references)
    return body + references_marker + anchored_references


def _prepare_references(source_root: Path) -> tuple[list[CommandResult], list[CheckResult]]:
    if not REFERENCES_CSL.exists():
        return (
            [],
            [
                CheckResult(
                    "reference-csl-source-present",
                    "failed",
                    "CSL reference source is missing.",
                    [_relative(REFERENCES_CSL)],
                )
            ],
        )

    target_csl = source_root / "references.csl.json"
    shutil.copy2(REFERENCES_CSL, target_csl)
    items = _csl_items(target_csl)
    commands: list[CommandResult] = []
    checks = [
        CheckResult(
            "reference-csl-source-present",
            "passed",
            f"CSL reference source copied ({len(items)} records).",
            [_relative(target_csl)],
        )
    ]

    sourceright = _sourceright_binary()
    sourceright_ok = False
    if sourceright:
        command = _run_command(
            [sourceright, "validate-csl", "--json", str(target_csl)],
            cwd=ROOT,
            log_path=source_root.parent / "logs" / "sourceright-validate-csl.log",
        )
        commands.append(command)
        sourceright_ok = command.status == "passed"
        checks.append(
            CheckResult(
                "sourceright-csl-validation",
                "passed" if sourceright_ok else "failed",
                "SourceRight validated the CSL reference source."
                if sourceright_ok
                else "SourceRight reported CSL validation diagnostics.",
                [_relative(target_csl), command.log_path or ""],
            )
        )
    else:
        checks.append(
            CheckResult(
                "sourceright-csl-validation",
                "warning",
                "SourceRight CLI is unavailable; reference outputs use local CSL validation only.",
                [_relative(target_csl)],
            )
        )

    _write_reference_outputs(items, source_root=source_root, sourceright_ok=sourceright_ok)
    authentext = _authentext_repo()
    if authentext is not None:
        command = _run_command(
            ["npm", "test"],
            cwd=authentext,
            log_path=source_root.parent / "logs" / "authentext-test.log",
            env={**os.environ, "CI": "1"},
        )
        commands.append(command)
        checks.append(
            CheckResult(
                "authentext-manuscript-review",
                "passed" if command.status == "passed" else "failed",
                "AuthenText academic-pattern and documentation checks passed."
                if command.status == "passed"
                else "AuthenText validation reported diagnostics.",
                [command.log_path or ""],
            )
        )
    else:
        checks.append(
            CheckResult(
                "authentext-manuscript-review",
                "warning",
                "AuthenText checkout is unavailable; manuscript prose review remains local-only.",
            )
        )
    checks.extend(
        [
            CheckResult(
                "vancouver-bibliography-generated",
                "passed",
                "Generated numbered Vancouver-style reference review output and arXiv-compatible main.bbl.",
                [
                    _relative(source_root / "references.vancouver.md"),
                    _relative(source_root / "main.bbl"),
                ],
            ),
            CheckResult(
                "sourceright-provider-verification",
                "external_gate",
                "Live provider enrichment and final citation verification remain outside the offline build.",
                [_relative(source_root / "sourceright-reference-report.json")],
            ),
        ]
    )
    return commands, checks


def _patch_tex_for_target(tex: str, config: TargetConfig) -> str:
    tex = _anchor_reference_items(_link_numeric_citations(tex))
    if not config.accessibility_experiment:
        return tex
    metadata = (
        "\\DocumentMetadata{\n"
        "  lang=en,\n"
        "  pdfstandard=ua-2,\n"
        "  pdfstandard=a-4f,\n"
        "  tagging=on\n"
        "}\n"
    )
    if tex.startswith("\\DocumentMetadata"):
        return tex
    return metadata + tex


def _prepare_source(config: TargetConfig, output_root: Path) -> tuple[Path, list[CommandResult]]:
    target_root = output_root / config.name
    source_root = target_root / "source"
    logs_root = target_root / "logs"
    if source_root.exists():
        shutil.rmtree(source_root)
    source_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LATEXMKRC, source_root / "latexmkrc")

    pandoc_log = logs_root / "pandoc.log"
    main_tex = source_root / "main.tex"
    command = [
        "pandoc",
        str(MANUSCRIPT_MD),
        "--standalone",
        "--from",
        "markdown+yaml_metadata_block",
        "--to",
        "latex",
        "--number-sections",
        "--output",
        str(main_tex),
    ]
    result = _run_command(command, cwd=ROOT, log_path=pandoc_log)
    if main_tex.exists():
        main_tex.write_text(
            _patch_tex_for_target(main_tex.read_text(encoding="utf-8"), config),
            encoding="utf-8",
        )
    return source_root, [result]


def _compile_source(
    config: TargetConfig,
    source_root: Path,
    *,
    skip_compile: bool,
) -> list[CommandResult]:
    if skip_compile:
        return [
            CommandResult(
                command=["latexmk", "main.tex"],
                cwd=_relative(source_root),
                status="skipped",
                returncode=None,
                log_path=None,
            )
        ]
    commands: list[CommandResult] = []
    env = dict(**os_environ(), FOIO_LATEX_TARGET=config.name)
    for run_index in range(1, config.compile_runs + 1):
        commands.append(
            _run_command(
                ["latexmk", "-r", "latexmkrc", "main.tex"],
                cwd=source_root,
                log_path=source_root.parent / "logs" / f"latexmk-run-{run_index}.log",
                env=env,
            )
        )
    return commands


def os_environ() -> dict[str, str]:
    import os

    return os.environ.copy()


def _run_pdf_checks(source_root: Path, *, skip_compile: bool) -> list[CommandResult]:
    pdf = source_root / "main.pdf"
    if skip_compile or not pdf.exists():
        return [
            CommandResult(
                command=["pdfinfo", "main.pdf"],
                cwd=_relative(source_root),
                status="skipped",
                returncode=None,
                log_path=None,
            )
        ]
    results: list[CommandResult] = []
    if shutil.which("pdfinfo"):
        results.append(
            _run_command(
                ["pdfinfo", str(pdf)],
                cwd=ROOT,
                log_path=source_root.parent / "logs" / "pdfinfo.log",
            )
        )
    if shutil.which("qpdf"):
        results.append(
            _run_command(
                ["qpdf", "--check", str(pdf)],
                cwd=ROOT,
                log_path=source_root.parent / "logs" / "qpdf-check.log",
            )
        )
    return results


def _run_arxiv_cleaner(source_root: Path, *, skip_cleaner: bool) -> list[CommandResult]:
    if skip_cleaner:
        return [
            CommandResult(
                command=["arxiv_latex_cleaner", _relative(source_root)],
                cwd=_relative(ROOT),
                status="skipped",
                returncode=None,
                log_path=None,
            )
        ]
    cleaner = shutil.which("arxiv_latex_cleaner")
    command = (
        [cleaner, str(source_root)]
        if cleaner
        else [
            "uvx",
            "--from",
            "arxiv-latex-cleaner",
            "arxiv_latex_cleaner",
            str(source_root),
        ]
    )
    return [
        _run_command(
            command,
            cwd=ROOT,
            log_path=source_root.parent / "logs" / "arxiv-latex-cleaner.log",
        )
    ]


def _run_cleaned_rebuild(source_root: Path) -> list[CommandResult]:
    cleaned_root = source_root.parent / f"{source_root.name}_arXiv"
    if not cleaned_root.exists():
        return [
            CommandResult(
                command=["latexmk", "-r", "latexmkrc", "main.tex"],
                cwd=_relative(cleaned_root),
                status="skipped",
                returncode=None,
                log_path=None,
            )
        ]
    return [
        _run_command(
            ["latexmk", "-r", "latexmkrc", "main.tex"],
            cwd=cleaned_root,
            log_path=source_root.parent / "logs" / "cleaned-latexmk.log",
            env=dict(**os_environ(), FOIO_LATEX_TARGET="arxiv"),
        )
    ]


def _prepare_supplement_ancillary(
    source_root: Path,
    *,
    skip_compile: bool,
) -> tuple[list[CommandResult], list[CheckResult]]:
    cleaned_root = source_root.parent / f"{source_root.name}_arXiv"
    supplement_pdf = cleaned_root / "anc" / "foi-o-nz-submission-supplement.pdf"
    if not cleaned_root.exists():
        return (
            [],
            [
                CheckResult(
                    "ancillary-supplement-pdf",
                    "skipped",
                    "Cleaned arXiv source tree does not exist, so no ancillary supplement was prepared.",
                    [_relative(cleaned_root)],
                )
            ],
        )
    if skip_compile:
        return (
            [],
            [
                CheckResult(
                    "ancillary-supplement-pdf",
                    "skipped",
                    "Compilation was skipped, so the ancillary supplement PDF was not generated.",
                    [_relative(supplement_pdf)],
                )
            ],
        )

    supplement_pdf.parent.mkdir(parents=True, exist_ok=True)
    command = _run_command(
        [
            "pandoc",
            str(SUPPLEMENT_MD),
            "--standalone",
            "--from",
            "markdown+raw_tex+yaml_metadata_block",
            "--to",
            "pdf",
            "--pdf-engine=pdflatex",
            "--output",
            str(supplement_pdf),
        ],
        cwd=ROOT,
        log_path=source_root.parent / "logs" / "supplement-ancillary-pandoc.log",
    )
    if command.status != "passed" or not supplement_pdf.exists():
        return (
            [command],
            [
                CheckResult(
                    "ancillary-supplement-pdf",
                    "failed",
                    "Ancillary supplement PDF could not be generated for the arXiv package.",
                    [_relative(supplement_pdf), command.log_path or ""],
                )
            ],
        )
    return (
        [command],
        [
            CheckResult(
                "ancillary-supplement-pdf",
                "passed",
                "Generated the supplement as an arXiv ancillary PDF under anc/.",
                [_relative(supplement_pdf), command.log_path or ""],
            )
        ],
    )


def _create_arxiv_source_archive(source_root: Path) -> CheckResult:
    cleaned_root = source_root.parent / f"{source_root.name}_arXiv"
    archive_path = source_root.parent / "foi-o-arxiv-source.tar.gz"
    if not cleaned_root.exists():
        return CheckResult(
            "arxiv-source-package",
            "skipped",
            "Cleaned arXiv source tree does not exist, so no source package was created.",
            [_relative(cleaned_root)],
        )
    if archive_path.exists():
        archive_path.unlink()

    def include_in_archive(path: Path) -> bool:
        if not path.is_file():
            return False
        relative = path.relative_to(cleaned_root)
        if relative.parts and relative.parts[0] == "anc":
            return True
        return not any(str(path).endswith(suffix) for suffix in ARXIV_PACKAGE_EXCLUDED_SUFFIXES)

    files = sorted(path for path in cleaned_root.rglob("*") if include_in_archive(path))
    with (
        archive_path.open("wb") as raw_handle,
        gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_handle,
            mtime=0,
        ) as gzip_handle,
        tarfile.open(fileobj=gzip_handle, mode="w") as archive,
    ):
        for path in files:
            arcname = str(path.relative_to(cleaned_root))
            info = archive.gettarinfo(path, arcname=arcname)
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            with path.open("rb") as file_handle:
                archive.addfile(info, file_handle)
    return CheckResult(
        "arxiv-source-package",
        "passed",
        f"Created deterministic arXiv source package from the cleaned source tree ({len(files)} files).",
        [_relative(archive_path)],
    )


def _artifact_inventory(source_root: Path) -> list[dict[str, str]]:
    inventory = []
    for path in sorted(source_root.rglob("*")):
        if path.is_file():
            inventory.append(
                {
                    "path": _relative(path),
                    "sha256": _sha256(path),
                }
            )
    return inventory


def _target_manifest(
    config: TargetConfig,
    output_root: Path,
    *,
    skip_compile: bool,
    skip_cleaner: bool,
) -> dict[str, Any]:
    source_root, command_results = _prepare_source(config, output_root)
    checks = _scan_markdown(MANUSCRIPT_MD)
    reference_commands, reference_checks = _prepare_references(source_root)
    command_results.extend(reference_commands)
    checks.extend(reference_checks)
    main_tex = source_root / "main.tex"
    if main_tex.exists():
        checks.extend(_copy_figure_assets(main_tex, source_root))
        checks.extend(_scan_tex(main_tex))
        checks.extend(_scan_figures(main_tex))
        checks.append(_scan_pdf_hyperlink_contract(main_tex))
    compile_results = _compile_source(config, source_root, skip_compile=skip_compile)
    command_results.extend(compile_results)
    log_path = source_root / "main.log"
    checks.extend(_scan_latex_log(log_path))
    command_results.extend(_run_pdf_checks(source_root, skip_compile=skip_compile))
    if config.name == "arxiv":
        cleaner_results = _run_arxiv_cleaner(source_root, skip_cleaner=skip_cleaner)
        command_results.extend(cleaner_results)
        if not skip_compile and any(result.status == "passed" for result in cleaner_results):
            command_results.extend(_run_cleaned_rebuild(source_root))
            checks.extend(
                _scan_latex_log(
                    source_root.parent / f"{source_root.name}_arXiv" / "main.log",
                    prefix="cleaned-latex-log",
                )
            )
            supplement_commands, supplement_checks = _prepare_supplement_ancillary(
                source_root,
                skip_compile=skip_compile,
            )
            command_results.extend(supplement_commands)
            checks.extend(supplement_checks)
            checks.append(_create_arxiv_source_archive(source_root))
    if config.name == "enhanced":
        if main_tex.exists():
            checks.extend(_scan_enhanced_accessibility(main_tex))
        checks.append(
            CheckResult(
                "documentmetadata-enabled",
                "passed"
                if main_tex.exists()
                and main_tex.read_text(encoding="utf-8").startswith("\\DocumentMetadata")
                else "failed",
                "Enhanced source begins with \\DocumentMetadata."
                if main_tex.exists()
                and main_tex.read_text(encoding="utf-8").startswith("\\DocumentMetadata")
                else "Enhanced source does not begin with \\DocumentMetadata.",
                [_relative(main_tex)],
            )
        )
    if config.name == "arxiv":
        checks.append(_texlive_check())

    failed_commands = [result for result in command_results if result.status == "failed"]
    failed_checks = [check for check in checks if check.status == "failed"]
    status = "failed" if failed_commands or failed_checks else "passed"
    return {
        "target": config.name,
        "engine": config.engine,
        "arxiv_upload_candidate": config.arxiv_upload_candidate,
        "accessibility_experiment": config.accessibility_experiment,
        "status": status,
        "source_root": _relative(source_root),
        "commands": [asdict(result) for result in command_results],
        "checks": [asdict(check) for check in checks],
        "artifacts": _artifact_inventory(source_root.parent),
    }


def build_manifest(
    targets: list[Target],
    *,
    output_root: Path,
    skip_compile: bool,
    skip_cleaner: bool,
) -> dict[str, Any]:
    target_reports = [
        _target_manifest(
            TARGETS[target],
            output_root,
            skip_compile=skip_compile,
            skip_cleaner=skip_cleaner,
        )
        for target in targets
    ]
    return {
        "schema_version": "foi-o-nz.submission-latex-pipeline.v0.1.0",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "manuscript": _relative(MANUSCRIPT_MD),
        "supplement": _relative(SUPPLEMENT_MD),
        "references": _relative(REFERENCES_CSL),
        "config": _relative(LATEXMKRC),
        "tools": [
            _tool_version("pandoc"),
            _tool_version("latexmk", ["-version"]),
            _tool_version("pdflatex"),
            _tool_version("xelatex"),
            _tool_version("lualatex"),
            _tool_version("pdfinfo"),
            _tool_version("qpdf", ["--version"]),
            _tool_version("arxiv_latex_cleaner"),
            _sourceright_tool_version(),
            _authentext_tool_version(),
        ],
        "targets": target_reports,
        "overall_status": "failed"
        if any(target["status"] == "failed" for target in target_reports)
        else "passed",
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        choices=["arxiv", "enhanced", "all"],
        help="Build target to prepare.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory for generated sources, logs, PDFs, and manifests.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest output path. Defaults to <output-root>/submission-latex-manifest.json.",
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Generate sources and run static checks without LaTeX compilation.",
    )
    parser.add_argument(
        "--skip-cleaner",
        action="store_true",
        help="Skip arxiv-latex-cleaner even for the arXiv target.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any target check or command fails.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    targets: list[Target] = ["arxiv", "enhanced"] if args.target == "all" else [args.target]
    manifest = build_manifest(
        targets,
        output_root=args.output_root,
        skip_compile=args.skip_compile,
        skip_cleaner=args.skip_cleaner,
    )
    manifest_path = args.manifest or args.output_root / "submission-latex-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": _relative(manifest_path), "status": manifest["overall_status"]}))
    return 1 if args.strict and manifest["overall_status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
