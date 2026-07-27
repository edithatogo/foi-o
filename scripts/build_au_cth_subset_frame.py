"""Build the authorized restricted-local AU-CTH retained-HTML subset frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_subset_frame import build_subset_frame

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--candidate-summary", type=Path, required=True)
parser.add_argument("--candidate-jsonl", type=Path, required=True)
parser.add_argument("--text-root", type=Path, required=True)
parser.add_argument("--classification-summary", type=Path, required=True)
parser.add_argument("--output-root", type=Path, required=True)
args = parser.parse_args()
print(json.dumps(build_subset_frame(**vars(args)), sort_keys=True))
