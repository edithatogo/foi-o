"""Validate the bounded AU-CTH automated annotation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_subset_annotation import validate_annotation_report

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("report", type=Path)
args = parser.parse_args()
print(json.dumps(validate_annotation_report(args.report), sort_keys=True))
