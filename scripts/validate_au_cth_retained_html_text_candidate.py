"""Validate the non-final retained-HTML AU-CTH text candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_retained_html_text import validate_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--text-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--classification-summary", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_candidate(
            args.summary,
            text_root=args.text_root,
            manifest_path=args.manifest,
            classification_summary=args.classification_summary,
            replay_root=args.replay_root,
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0
