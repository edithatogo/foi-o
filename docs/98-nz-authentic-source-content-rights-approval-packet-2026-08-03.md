# NZ authentic source-content rights approval packet

Status: candidate approval packet; no source-content rights are inferred.

## Requested bounded scope

This packet concerns only the two-case local NZ pilot for requests `11872`
and `35076`. The requested use is restricted-local feasibility analysis and
request-linked extraction validation. It is not a request for publication,
redistribution, model training, legal certification, population-wide
inference, or release.

The source roots are currently absent, so this packet does not authorize
materialization or recovery of content. Any future payload must reproduce the
approved provenance pins before use.

## Provenance inputs

| Item | Pin or reference | Current status |
| --- | --- | --- |
| NZ metadata-only source pack | `examples/v2/nz-source-pack.governed-metadata.json` | Approved metadata-only; no content rights expansion |
| Source-rights registry | `mappings/nz-source-rights-registry.yaml`, SHA-256 `6a2b0d958d19415e36fd59cbd5cf0632f9837c44819f8aafef02a0d635c9cc77` | Registry reference |
| 11872 snapshot manifest | SHA-256 `0c7cee553ca3b01a6416784a1b691df5a6d90159a8f4d55e51a799934f655629` | Expected pin; payload absent |
| 11872 attachment inventory | SHA-256 `a0dfea7c979de9760bcf12fee0a321e8e323b4176decd086f2530408da4c171f` | Expected pin; payload absent |
| 35076 governed bundle | SHA-256 `c929b312f4b627049b7867e46fa74b08ed8e9a43c35ba866871bead6f8a19b7d` | Expected pin; payload absent |
| 35076 candidate | SHA-256 `90550ce084be684ee493e2ce7470cbe0b01dee13b6253c50f91c7de9974d6007` | Expected pin; payload absent |
| 35076 independent verification | SHA-256 `23270c27202286e3476f39ccf5df2267cb41641f9cfdf3f1664b8f23e441a9a1` | Expected pin; payload absent |

## Rights matrix

| Artifact class | Requested disposition | Required evidence | Current disposition |
| --- | --- | --- | --- |
| Request-page HTML | Restricted-local analysis only | Exact source hash, URL, retrieval time, provider terms | Pending item-level review |
| Correspondence text | Restricted-local request-linked analysis only | Exact record hashes and permitted-use terms | Pending item-level review |
| Attachments | Restricted-local processing only for explicitly listed files | Attachment inventory, per-file hashes, rights/exclusions | Pending; no files materialized |
| OCR/text derivatives | Restricted-local transient or owner-only retention | Source-to-derivative hash map and approved method | Not authorized by this packet |
| Metadata and hashes | Local provenance and validation | Manifest and transformation hashes | Metadata-only approval exists |
| Annotations/extractor outputs | Local candidate artifacts only | Approved source frame and execution authorization | Not authorized by this packet |

## Required reviewer decisions

Two separate reviews are required:

1. Provenance review: confirm that each future payload is the exact artifact
   described by its manifest, hash, source URL, retrieval time, and
   transformation record.
2. Rights review: confirm permitted local operations, exclusions, retention,
   access controls, and whether attachments or derived text are included.

Neither review may authorize publication, redistribution, training, legal
certification, or population-wide inference.

## Proposed approval statement

> I approve restricted-local use of the exact NZ source artifacts for requests
> `11872` and `35076` only, after each artifact reproduces its recorded
> manifest, source, retrieval, rights, and SHA-256 evidence. The permitted use
> is request-linked local feasibility analysis and extraction validation. HTML,
> correspondence, attachments, and derived text must each remain within their
> separately approved disposition; metadata-only approval does not extend to
> source content or attachments. This does not authorize new capture, live-origin
> access, publication, redistribution, training, legal certification,
> population-wide inference, profile promotion, or release. A separate exact
> source-frame and execution authorization remains required.

This statement is a template only. It does not approve the currently absent
payloads or change the blocked `G-EMP-LOCAL-INPUT-RECOVERY` gate.
