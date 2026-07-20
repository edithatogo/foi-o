"""Pin downloaded official OIA version PDFs into the candidate version index."""

from __future__ import annotations

import argparse
import re
from hashlib import sha256
from pathlib import Path

ROW = re.compile(
    r'(?P<prefix>.*as_at: "(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})".*'
    r'content_sha256: )(?P<digest>null|"[a-f0-9]{64}")(?P<suffix>}.*)'
)


def pin_hashes(index_path: Path, pdf_dir: Path) -> int:
    """Replace null/previous digests with SHA-256 values from a complete PDF directory."""
    lines = index_path.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    pinned = 0
    for line in lines:
        match = ROW.fullmatch(line)
        if match is None:
            output.append(line)
            continue
        pdf_path = pdf_dir / f"{match.group('date')}.pdf"
        if not pdf_path.is_file():
            raise FileNotFoundError(f"missing official version PDF: {pdf_path}")
        if not pdf_path.read_bytes().startswith(b"%PDF-"):
            raise ValueError(f"download is not a PDF: {pdf_path}")
        digest = sha256(pdf_path.read_bytes()).hexdigest()
        output.append(f'{match.group("prefix")}"{digest}"{match.group("suffix")}')
        pinned += 1
    if pinned == 0:
        raise ValueError("no version rows found in index")
    index_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    return pinned


def main() -> None:
    """Run the deterministic local pinning command."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    args = parser.parse_args()
    print(f"pinned {pin_hashes(args.index, args.pdf_dir)} official OIA versions")


if __name__ == "__main__":
    main()
