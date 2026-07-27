# AU RightToKnow immutable-manifest approval packet

## Proposed operation

Create and validate one restricted-local immutable manifest for the complete,
bounded AU RightToKnow replay population. This packet is a proposal only: it
does not create a manifest, freeze an empirical frame, or authorize any later
stage.

## Pinned inputs

| Input | SHA-256 | Scope |
| --- | --- | --- |
| Complete Internet Archive CDX export | `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd` | 26,000 metadata records for `https://www.righttoknow.org.au/request/*` |
| Authorized replay selection | `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51` | 2,082 canonical request pages |
| Parser-v3 normalized replay candidate | `3801b4b99de6152bfcaf5f093e00e137acb4ee5d636611ada75820aed55fd807` | Exact retained replay bytes and parsed records |
| Four-way jurisdiction candidate summary | `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab` | 1,578 AU-CTH; 179 AU-NSW; 115 out of scope; 210 unresolved |
| Canonical completion candidate | `0dafc44c1b871357802282f138bf0e6e9d68f249a171c1d9627809bd928531c8` | 1,716 exact canonical metadata lookups |
| Completion replay selection | `370a6d84e20a4bd260619209d84098458c9e72acf7e4e6f5cb3465cbaba88bb6` | Zero additional selections; 858 no-capture slugs |

The CDX completion packet was independently validated against its retained
response bodies. It found no qualifying canonical JSON or primary HTML capture
for any of the 858 attachment-only slugs. The proposed immutable manifest must
therefore cover exactly the existing 2,082-record population and must not add
records.

## Required decision

> I approve finalization of one immutable, restricted-local AU RightToKnow
> manifest for the bounded 2,082-record replay population. The manifest must
> be derived only from the six pinned inputs in
> `docs/44-au-rtk-immutable-manifest-approval-packet-2026-07-27.md`. This
> authorizes local immutable-manifest finalization and validation only. It does
> not authorize empirical freezing, annotation, archived-page replay beyond the
> existing 2,082 records, publication, redistribution, training, legal
> certification, profile promotion, push, pull request, or merge.

## Effect of approval

An approval permits creation of the one local, hash-pinned manifest and an
independent validation result. It does not determine sample membership or
authorize use of records for empirical analysis. A separate approval will be
required for any empirical-frame freeze, annotation, adjudication, or maturity
decision.
