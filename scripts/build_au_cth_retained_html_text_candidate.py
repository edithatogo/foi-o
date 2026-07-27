"""Build the approved non-final retained-HTML AU-CTH text candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_retained_html_text import build_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--classification-summary", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_candidate(
            manifest_path=args.manifest,
            classification_summary=args.classification_summary,
            replay_root=args.replay_root,
            output_root=args.output_root,
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
