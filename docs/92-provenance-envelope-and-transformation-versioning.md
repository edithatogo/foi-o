# Provenance envelope and transformation versioning

## Purpose

`foio.provenance-envelope.v1.0.0` records how a future FOI-O artifact was
produced without changing any approved historical artifact. Existing AU-CTH,
AU-NSW, manifest, reliability, and approval records remain byte-for-byte legacy
evidence. A provenance envelope may be added as a sidecar; it must not be used
to rewrite or retroactively upgrade those records.

The design separates reproducible meaning from execution occurrence:

- A `foio.transformation-contract.v1.0.0` record is stable. It defines accepted
  schemas, algorithms, ordering, duplicate, missingness and exclusion rules,
  required capabilities, prohibited successor effects, and compatibility. It
  contains no timestamps, host paths, commands, or environment details.
- `run_occurrence` belongs to one envelope. It records the exact repository
  commit, dirty-worktree disposition, argument-array command, implementation
  and dependency-lock hashes, parameters, environment, and timestamps.
- A `foio.authorization-record.v1.0.0` record names the exact object and
  population scope, pins every approved input plus the transformation contract
  and sealed run occurrence, and carries explicit allowed and denied capability
  sets.
- A `foio.validation-attestation.v1.0.0` record reports integrity checks and
  states that those checks are not legal or rights certification.

## Content identity

Version 1 uses `foio.sorted-compact-json.v1`. It is Python standard-library
JSON with:

- UTF-8 encoding;
- lexicographically sorted object keys;
- compact separators with no insignificant whitespace;
- Unicode emitted directly (`ensure_ascii=false`);
- array order preserved; and
- non-finite floating-point values rejected.

This is an explicit FOI-O canonicalization contract and is not represented as
RFC 8785. A record self-pin is SHA-256 over these canonical bytes after removing
only its self-pin field. The fields are `contract_sha256`,
`authorization_sha256`, `attestation_sha256`, and `envelope_sha256`.

Paths are hints, not identities. Every input and output has an artifact ID,
byte size, schema version, and SHA-256 digest.

## Authorization boundary

The packet renderer accepts only `pending_human_decision` records. Generated
text is always a proposal and cannot create its own approval. Approved and
rejected records require a distinct human-decision record.

The denial set must be present and non-empty. “All prior restrictions remain”
is not sufficient. Allowed and denied capabilities cannot overlap. A successor
effect is invalid unless:

1. the authorization status is `approved`;
2. the effect is explicitly allowed; and
3. the transformation contract does not prohibit it.

Approval of one transformation therefore never activates sampling, annotation,
publication, redistribution, training, certification, promotion, push, pull
request, merge, or another successor stage unless that exact capability is
separately permitted.

## Population conservation

Every envelope records predecessor, included, excluded, and unresolved counts.
Validation fails unless:

```text
predecessor = included + excluded + unresolved
```

Excluded and unresolved positions remain visible rather than disappearing from
the denominator.

## Independent verification

`scripts/verify_provenance_envelope.py` is a standalone standard-library
oracle. It deliberately does not import producer canonicalization, builders, or
validators. It independently recomputes self-pins and checks:

- all Draft 2020-12 structural schemas, references, and date-time formats;
- transformation and authorization linkage;
- exact approved-input, population, transformation, and run-occurrence pins;
- exact approval-statement hash;
- explicit denial set and allowed/denied disjointness;
- population conservation; and
- successor authorization and contract prohibitions.

Only this independent path may originate a validation attestation marked
`independent_oracle=true`; producer modules do not expose such a builder.
The producer also validates the same published schemas through a separately
wired registry, but producer success is not independent evidence. A digest
proves byte identity only; it does not prove authorship, source rights, factual
correctness, methodological maturity, or legal status.

## Commands

Build from a JSON specification:

```bash
uv run python scripts/build_provenance_envelope.py spec.json envelope.json
```

Render a pending proposal:

```bash
uv run python scripts/render_provenance_approval_packet.py \
  authorization.json approval-packet.md
```

Run the independent oracle:

```bash
uv run python scripts/verify_provenance_envelope.py envelope.json
```

The verifier exits non-zero and emits JSON when any invariant fails.
