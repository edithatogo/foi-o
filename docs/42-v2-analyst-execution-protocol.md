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

For the initial local packet, the unit is a synthetic fixture event object used
for engineering classification, not authentic assertion-level source evidence.
The unit is addressed by an exact UTF-8 character half-open source span and its
literal-byte SHA-256. Analyst-visible context is produced by parsing that object,
removing `assertion_status` and `confidence`, and serialising JSON with UTF-8,
`ensure_ascii=false`, sorted keys, and compact `(",", ":")` separators. Both the
raw-unit and redacted-context hashes are locked. A source state is preserved
when present and is never synthesised when missing or null.

Duplicate clusters, split isolation, inclusion probabilities, weights,
exclusions, and bootstrap settings remain pre-registered. Inputs must be
committed, locally readable, rights-eligible for the declared use, and pinned
by SHA-256. Missing dates, evidence, or labels are recorded as missing or as a
controlled abstention; they are never invented.

The initial automated execution uses committed synthetic fixture/example
material only after exact bounded local authorization. The repository's licence
placeholder does not establish unrestricted or redistributable rights.
Restricted FYI snapshots, correspondence, attachments, raw exports, and
provider content are excluded unless a separate use authorization names their
exact bytes and purpose.

## Analysis and reconciliation

Each analyst records a candidate label, optional UTF-8 half-open span,
uncertainty, notes, and either a non-abstaining outcome or one controlled
abstention reason. Any label, span, or abstention disagreement requires
reconciliation. Agreement without disagreement does not permit the reconciler
to rewrite first-pass records.

The fixture packet uses the dedicated `fixture_engineering_classification`
codebook task. It does not reuse the authentic candidate-assertion task or
convert fixture events into authentic candidate assertions.

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

1. Construct and freeze the candidate population, codebook, sampling, unit,
   redaction, and duplicate-cluster packet with rights false and execution
   disabled.
2. Obtain exact bounded rights and execution-input approval for the committed
   readiness hash.
3. Record the approved rights, codebook, and sampling states, then regenerate
   and freeze the rights-eligible unit and dependent cluster bytes.
4. Assign two concrete isolated analyst runtimes and one distinct reconciler
   runtime.
5. Obtain exact approval of a committed v0.2 authorization that pins every
   final artifact, role, runtime, prompt, and session.
6. Run the pre-execution verifier against the exact repository commit and
   authorization hash.
7. Run both analysts independently, lock both complete sets, and then give only
   those locked sets and source context to the distinct reconciler.
8. Verify results and emit local inter-agent diagnostics with every downstream
   promotion gate disabled.
