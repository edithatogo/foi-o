# AU-NSW restricted-local candidate rights and frame approval packet

## Proposed operation

Create and validate one restricted-local AU-NSW empirical source frame from
the 179-record AU-NSW jurisdiction candidate already derived from the approved
RightToKnow Internet Archive replay. This packet proposes neither a new replay
nor a new source acquisition. It does not finalise a separate manifest, freeze
a sample, or authorise annotation.

## Pinned evidence

| Item | Value |
| --- | --- |
| Parent immutable manifest self-pin | `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c` |
| Parent stored-manifest SHA-256 | `c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393` |
| Internet Archive CDX export | `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd` |
| Authorized replay selection | `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51` |
| Four-way classification summary | `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab` |
| AU-NSW candidate JSONL | `c8486d035279e400b4100cbd7f9443a23dc648d6b1494527657cd294102238b6` |
| Exact membership | 179 records classified `AU-NSW` / `GIPA` |
| Record bytes | 252,583 |
| Source method | One authorized Internet Archive snapshot per canonical RightToKnow request slug; no live-origin access, link traversal, or attachment retrieval |

The candidate is stored only at
`/Volumes/PortableSSD/foio-restricted/au-rtk-30236042144/classification-candidate/au-nsw.candidate.jsonl`.
It is not a claim that every individual record is suitable for empirical use.
Before frame creation, the operation must confirm hash integrity, request-link
integrity, GIPA classification, text/accessibility disposition, and the
restricted-local rights boundary for every retained record. Records that do not
meet those checks must be excluded and listed by stable record identifier and
reason.

## Required decision

> I approve the restricted-local AU-NSW candidate JSONL SHA-256
> `c8486d035279e400b4100cbd7f9443a23dc648d6b1494527657cd294102238b6`,
> containing exactly 179 AU-NSW/GIPA-classified records and derived from parent
> immutable-manifest self-pin
> `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c`, for
> local rights/accessibility validation and creation of one non-final candidate
> AU-NSW empirical source frame only. The operation may verify local hashes,
> authority identity, request linkage, and text/accessibility disposition; it
> may apply documented exclusions and create a hash-pinned candidate frame with
> duplicate-clustering metadata.
>
> This does not authorise Internet Archive replay, live-origin access, link
> traversal, attachment retrieval, immutable-manifest finalisation, sampling,
> annotation, adjudication, extractor metrics, population-wide inference,
> publication, redistribution, training, legal certification, profile
> promotion, push, pull request, or merge.

## Next boundary

If the candidate frame is valid, a separate approval must identify its exact
frame and cluster-registry hashes, exclusions, sampling design, seed, and
sample membership before annotation or adjudication may begin.
