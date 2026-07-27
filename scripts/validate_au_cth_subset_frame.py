"""Validate the restricted-local AU-CTH retained-HTML subset frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_subset_frame import validate_subset_frame

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("frame", type=Path)
parser.add_argument("--registry", type=Path, required=True)
args = parser.parse_args()
print(json.dumps(validate_subset_frame(args.frame, registry_path=args.registry), sort_keys=True))
