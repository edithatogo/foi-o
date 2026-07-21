# FOI-O versioning

FOI-O uses independent version axes. `FOI-O V2` is a methodological/paper
generation and does not imply a Python major release.

The canonical machine-readable registry is `versions/registry.yaml`; exact
combinations used by a run are locked in `versions/current-lock.yaml` and
checked against `versions/compatibility.yaml`. Legal source packs carry both
effective time and an immutable digest. Profile and capability versions are
independent of the `foi-o-nz` package version.

The CLI exposes `version explain`, `version check`, `version lock`, and
`version diff` as the target interface. Until all commands are wired into the
installed entry point, `python scripts/version_tool.py` is the portable
implementation and CI authority.
