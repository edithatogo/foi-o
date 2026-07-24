# Bounded AU public-record capture authorization

## Status

This record captures the user-provided authorization for the separately scoped
bounded capture run described below.

- Recorded in repository: 2026-07-21 (Australia/Sydney)
- Approval date: 2026-07-21 (Australia/Sydney)
- Approval recorded at: 2026-07-21T12:57:52Z
- Authorization subject: public AU-CTH and AU-NSW FOI records
- Permitted purpose: local empirical validation and immutable local archival
- Operating mode: bounded, read-only, rate-limited live capture
- Source authorization: the user's message in the Codex task on 2026-07-21

The source authorization is preserved verbatim:

> I authorize bounded, read-only, rate-limited live capture of public AU-CTH and AU-NSW FOI records solely for local empirical validation and immutable archival. This does not authorize submissions, access-control bypass, publication, dataset release, training, profile promotion, or tranche 5.

## Authorized scope

The authorization is limited to live capture of public records for:

- `AU-CTH` (Commonwealth); and
- `AU-NSW` (New South Wales).

Any future run must have an exact committed request, scope, source-pack or
manifest boundary, rate-limit configuration, and content/provenance hash
recorded before execution. Captured material must remain local and immutable
for the stated validation/archive purpose.

## Explicit prohibitions

This authorization does not permit:

- submissions or other outbound requests made on behalf of a requester;
- access-control bypass, circumvention, or authenticated/private access;
- publication, dataset release, redistribution, or external sharing;
- model training, fine-tuning, or other training use;
- profile promotion, legal certification, or legal-outcome claims; or
- tranche 5 / remaining-jurisdiction expansion.

This record authorizes the bounded capture operation only. It is not a pilot
go/no-go decision, profile validation, legal certification, or release
authorization.

## Provenance and gate handling

Repository recording time is provenance for this record, not the approval time.
The original authorization text must be retained with any execution packet and
anchored to the exact committed packet used for a run. A later execution
request must be reviewed for scope, rights, source availability, rate limits,
and immutable archival integrity before any capture begins.
