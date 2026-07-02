# Implementation delta v0.8 — static Mojo audit and kernel manifest

This delta responds to the project direction: **use Mojo where possible, with Python as fallback**.

The implementation now treats the Python fallback as the executable compatibility
contract and the Mojo source tree as the preferred native implementation surface.
Because the local sandbox does not include the Modular Mojo/MAX toolchain, v0.8
adds the strongest checks that can run without native compilation:

- static discovery of Mojo function declarations;
- comparison with Python fallback conformance operations;
- JSON kernel manifests for native/fallback parity planning;
- JSONL conformance fixtures for future native Mojo test harnesses;
- readiness reports that separate Python-fallback readiness, static Mojo-source
  readiness, and native release readiness.

## New commands

```text
foi-o-nz mojo-audit
foi-o-nz export-kernel-manifest
foi-o-nz export-kernel-fixtures
foi-o-nz kernel-readiness
```

## New schemas

```text
schemas/json/mojo-audit.schema.json
schemas/json/kernel-manifest.schema.json
schemas/json/kernel-readiness.schema.json
```

## New examples

```text
examples/mojo-audit.static.json
examples/kernel-manifest.static.json
examples/kernel-readiness.fallback.json
mojo/tests/fixtures/kernel-conformance.jsonl
```

## New Mojo source

```text
mojo/foi_o_nz/epistemic.mojo
mojo/tests/test_epistemic.mojo
```

The static audit now reports that all Python fallback operations represented in
the conformance corpus have matching Mojo declarations. Native parity still
requires the external Modular toolchain checks:

```bash
pixi run mojo-format-check
pixi run mojo-test
pixi run mojo-build
```

## Local verification

```text
88 passed
repository validation ok
examples ok
```
