"""Run the authorized bounded AU-CTH automated annotation roles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_subset_annotation import run_annotation

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--membership", type=Path, required=True)
parser.add_argument("--frame", type=Path, required=True)
parser.add_argument("--text-root", type=Path, required=True)
parser.add_argument("--codebook", type=Path, required=True)
parser.add_argument("--output-root", type=Path, required=True)
args = parser.parse_args()
print(
    json.dumps(
        run_annotation(
            membership_path=args.membership,
            frame_path=args.frame,
            text_root=args.text_root,
            codebook_path=args.codebook,
            output_root=args.output_root,
        ),
        sort_keys=True,
    )
)
