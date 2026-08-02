"""Render a pending-only provenance approval packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from foi_o_nz.provenance import render_pending_approval_packet


def main() -> int:
    """Render an authorization proposal without changing its decision state."""
    parser = argparse.ArgumentParser()
    parser.add_argument("authorization", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
    args.output.write_text(
        render_pending_approval_packet(authorization),
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
