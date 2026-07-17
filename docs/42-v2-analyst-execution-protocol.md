# FOI-O V2 analyst execution protocol

Status: active candidate protocol v0.2 for bounded local execution. It
supersedes the role requirements in
`docs/41-v2-sampling-and-annotation-protocol.md`, which remains the immutable,
hash-approved v0.1 historical protocol. This reframing was directed by
`human:edithatogo` on 2026-07-17. It does not retroactively alter the earlier
approval or any artifact pinned to the v0.1 bytes.

## Roles and provenance

Execution appoints two independent analysts and one distinct reconciler. Under
this protocol, automated agents may serve as analysts and as the reconciler. Each role record
must identify the actor class and stable actor ID and, for an automated agent,
the provider, model or runtime identifier, prompt hash, and isolated session
identifier. An agent is never represented as a human.

The two analysts work in separate contexts. Neither receives the other
analyst's output, the extractor candidate label, or extractor confidence before
both analysis sets are content-hash locked. Each record pins its source unit,
codebook revision, presented context, creation time, and lock time.

After both first-pass sets are locked, the distinct reconciler may inspect the
source and both analyses. Reconciliation records a reasoned candidate outcome
or an unresolved status and never overwrites either original analysis.

## Units, sampling, and rights

The unit remains the assertion-level source span defined in the v0.1 protocol.
Duplicate clusters, split isolation, inclusion probabilities, weights,
exclusions, and bootstrap settings remain pre-registered. Inputs must be
committed, locally readable, rights-eligible for the declared use, and pinned
by SHA-256. Missing dates, evidence, or labels are recorded as missing or as a
controlled abstention; they are never invented.

The initial automated execution uses only committed fixture/example material.
Restricted FYI snapshots, correspondence, attachments, raw exports, and
provider content are excluded unless a separate use authorization names their
exact bytes and purpose.

## Analysis and reconciliation

Each analyst records a candidate label, optional UTF-8 half-open span,
uncertainty, notes, and either a non-abstaining outcome or one controlled
abstention reason. Any label, span, or abstention disagreement requires
reconciliation. Agreement without disagreement does not permit the reconciler
to rewrite first-pass records.

The reconciler must differ from both analysts. Reconciliation is an engineering
consensus step, not human adjudication, gold promotion, legal certification, or
empirical ground truth.

## Claim boundary

An all-agent execution is explicitly not human-reviewed. Its outputs may be
used to exercise the sampling, locking, reconciliation, verification, and
agreement-calculation machinery. They must carry:

- `empirical_evidence: false`;
- `human_reviewed: false`;
- `gold_eligible: false`;
- `release_qualifying: false`; and
- `publication_eligible: false`.

Redistribution, publication, training, fine-tuning, release, dataset
publication, gold promotion, legal certification, and paper updates remain
prohibited unless separately authorized and supported by the required
evidence. Inter-agent agreement is reported as a diagnostic and must not be
described as inter-human reliability.

## Execution order

1. Pin the active protocol, source population, codebook, sampling
   configuration, actor records, and bounded human authorization.
2. Freeze the rights-eligible unit and duplicate-cluster manifests.
3. Run both analysts independently and lock both complete analysis sets.
4. Give only the locked sets and source context to the distinct reconciler.
5. Verify hashes, membership, isolation attestations, chronology, role
   separation, arithmetic, and claim-class flags.
6. Emit local inter-agent diagnostics with all downstream promotion gates
   disabled.
