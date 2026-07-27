"""Validate the AU-CTH subset sampling-membership candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.australian_subset_sampling import validate_membership

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("membership", type=Path)
parser.add_argument("--frame", type=Path, required=True)
parser.add_argument("--registry", type=Path, required=True)
args = parser.parse_args()
print(
    json.dumps(
        validate_membership(args.membership, frame_path=args.frame, registry_path=args.registry),
        sort_keys=True,
    )
)
