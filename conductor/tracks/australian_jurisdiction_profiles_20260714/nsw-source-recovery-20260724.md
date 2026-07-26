# AU-NSW historical source recovery plan

Status: repository recovery support implemented; no CDX export, replay,
manifest, empirical frame, publication, redistribution, training, legal
conclusion, or profile-promotion action is authorized by this plan.

## Purpose and correction

The prior Internet Archive route used CDX `collapse=urlkey`. That is a
`url_index`: it discovers one archived record per URL and is not an export of
all historical capture versions. `fyi-archive` commit `4d410d6` now distinguishes
that lightweight scheduled mode from a manually confirmed `all_captures` mode,
which preserves timestamped CDX records without URL collapse.

The Internet Archive CDX index is a locator and provenance input. It is not
replayed page content, a rights disposition, an immutable manifest, or an
empirical source population.

## Workflow

```mermaid
flowchart TD
  A[Approved exact CDX request] --> B[Export complete all-captures CDX metadata]
  B --> C{Complete pagination and non-empty?}
  C -- no --> D[Retain failure or negative evidence only]
  C -- yes --> E[Retain raw export privately and verify SHA-256]
  E --> F[Recover only CDX-listed archived snapshots]
  F --> G{Provenance, coverage and rights sufficient?}
  G -- no --> H[Record exclusions and keep source blocked]
  G -- yes --> I[Classify NSW with authority evidence]
  I --> J[Validate normalized JSONL]
  J --> K[Human approves exact hashes and bounded use]
  K --> L[Create immutable manifest and empirical frame]
```

The equivalent BPMN 2.0 review model is
[`nsw-source-recovery-20260724.bpmn`](./nsw-source-recovery-20260724.bpmn).

## Execution plan

- [x] Implement explicit `url_index` and `all_captures` CDX modes, fail-safe
      retrieval evidence, a registry-selected manual all-captures workflow, and
      tests. (`fyi-archive` `4d410d6`)
- [x] Commit the request packet for the exact RightToKnow scope, selected
      instance, page/runtime caps, source endpoint, private output location,
      and `EXPORT_ALL_CAPTURE_METADATA` confirmation. (`599fe4e`; request
      SHA-256 `3c9bb6bda4b51ffc60001ee4f230fb6050269adb78a64122b40867ea1c9e06f1`)
- [x] Execute the first authorized manual CDX export: GitHub Actions run
      `30068038481` on `2026-07-24`, `au-rtk`,
      `www.righttoknow.org.au/request/*`, page size `1000`, maximum pages
      `1000`, and runtime `600` seconds. It failed after bounded retries with
      Internet Archive CDX connection refusal; the retained 90-day failure
      artifact has ZIP SHA-256
      `5efe286d76f2ce7bcd71c866e4f6504dcecdd517fed9d951277792777f233237`.
      It contains no source export and is negative evidence only.
- [x] Record two subsequent separately authorized full-capture attempts for the
      same bounded scope. Run `30075664496` failed after bounded retries with
      connection refusal; its 530-byte, 90-day failure ZIP is artifact
      `8589791549`, SHA-256
      `5726f087090ee2c8abef46ab7c425c4c491bd5e0673b0cd8e640f97778728c72`.
      Run `30176570901` on `fyi-archive` commit
      `ab1080c20cdfa9c342d96b18ba2e93f3d28c7945` failed after bounded retries
      with an Internet Archive CDX TLS-handshake timeout; its 535-byte, 90-day
      failure ZIP is artifact `8624447034`, SHA-256
      `954af9aa0b844484cc9d88cf3a6b5bb9812644176b237c238f0419ec82fe1449`.
      Its sole `retrieval.json` member has SHA-256
      `e9a6735eb3fbf803e07c04fcbb1ff2446cd819cd1f65effb0900e98c7a77554d` and
      records `retrieval_status=failed`, `pagination_complete=false`, no
      response hash, and no record count. Both are negative evidence only;
      neither is a CDX export or source artifact.
- [ ] Run a separately authorized CDX export. Accept it only when the evidence
      record reports `retrieval_status=complete`, `pagination_complete=true`, a
      non-null response SHA-256, and a non-zero record count.
- [ ] If the result is empty, capped, or failed, record the evidence and stop.
      Do not retry automatically and do not create a partial export or source
      population.
- [ ] For a successful export, retain raw bytes privately; verify the evidence
      hash and reconcile header/row count before any snapshot recovery.
- [ ] Recover only timestamped snapshots named by the export, recording replay
      URL, timestamp, HTTP status, response hash, and exclusion reason. Preserve
      all CDX records even when derived analysis units later cluster duplicates.
- [ ] Classify AU-NSW records using recorded authority/process evidence. Route
      ambiguity to review; do not infer jurisdiction from a request's wording.
- [ ] Validate the normalized JSONL with
      `scripts/validate_australian_source_artifact.py`, including source,
      retrieval time, coverage, rights, and byte hashes.
- [ ] Seek a separate human approval that names the raw and normalized hashes,
      coverage, exclusions, duplicate rule, and bounded use. Only then create
      an immutable manifest and freeze the empirical frame.

## Gate register

| Gate | Status | Required evidence |
| --- | --- | --- |
| Exact all-captures request | Three authorized attempts executed; failed safely | Request SHA, run ID, scope, caps, confirmation token, failure artifact SHA |
| CDX completeness | Pending external source | Complete pagination, non-empty rows, raw bytes and SHA-256 |
| Archived-content recovery | Pending external source | Capture timestamp, replay status, response hash, exclusions |
| Rights and source validation | Pending review | Source, time, scope, coverage, rights, normalized JSONL validation |
| Empirical freeze | Pending hash-bound human approval | Exact artifact hashes, units, exclusions, duplicate rules, permitted use |

## Explicit exclusions

No route may substitute an official NSW source for RightToKnow without a new,
separately labelled scope decision. A third-party catalogue is not a verification
source unless it supplies the exact independently identifiable object and its
provenance/rights can be validated. In particular, unavailable Anna's Archive
material cannot fill a missing Internet Archive capture.

## Operator-supplied candidate intake boundary

An operator-supplied non-empty CDX export may be prepared for review only as a
candidate. Its intake record must identify the provider and source URL, exact
RightToKnow URL scope, retrieval time, raw-file SHA-256, record count, and
pagination/completeness status; the raw bytes remain private. Supply does not
make the object authoritative, complete, rights-cleared, or eligible for
import. It must first pass the same provenance, coverage, rights, and source-
artifact validation gates described above.

This intake route is not a standing authorization. Before any importer,
enricher, replay, manifest, freeze, annotation, or empirical analysis, a new
human approval must name the actual candidate's hashes, scope, coverage,
exclusions, and bounded use. It cannot revive or extend the consumed
authorizations for runs `30068038481`, `30075664496`, or `30176570901`.
