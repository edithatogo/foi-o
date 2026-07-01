# Review of pasted Mojo/MAX discussion

The pasted GoogleAI discussion is treated as a planning note, not as an authoritative source. Its practical conclusion is useful: use Mojo where it provides clear leverage, but do not replace production data engineering with immature Mojo dataframe tooling yet.

## Accepted into this scaffold

- Mojo/MAX is included as a first-class experimental core.
- The repository uses `pixi.toml` with Modular channels.
- Mojo code is limited to deterministic kernels at v0.1.
- Polars/DuckDB/LanceDB remain the pragmatic data layer.
- CI includes Mojo format/build/test and Python validation.

## Cautious corrections

- The current Mojo testing documentation says the old `mojo test` command has been removed; this repo therefore uses `mojo run` with `TestSuite` rather than `mojo test`.
- The MAX quickstart currently documents installing the `modular` package for the `max` CLI; this repo includes `modular` in the Pixi environment rather than assuming an unspecified `max` package.
- MojoFrame/Mojo-native dataframe tooling is tracked as experimental, not as a v0.1 dependency.

## Design consequence

The first implementation slice is intentionally boring in the best way: deterministic, auditable, testable process/state/evidence models. Acceleration is added after the process semantics are stable.
