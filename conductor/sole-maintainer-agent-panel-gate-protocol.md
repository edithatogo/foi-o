# Sole-maintainer agent-panel gate protocol

## Status and purpose

This is the repository-wide control for every human, external, or irreversible
gate. FOI-O has one accountable maintainer: the repository owner. Agents may
prepare evidence and independent advisory reviews; they cannot approve rights,
credentials, retention, empirical execution, release, publication, legal
certification, or profile promotion.

The protocol reduces approval churn by presenting one complete, hash-pinned
decision bundle only when a decision is needed. It does not collapse actions
whose rights basis, evidence set, destination, visibility, or irreversibility
materially differs.

## Required sequence

1. **Prepare.** The orchestrator completes the repository-owned work and
   validates the exact candidate, inputs, prerequisites, and exclusions.
2. **Panel.** At least three isolated advisory roles review the same pinned
   bundle: provenance-and-rights, technical-reproducibility, and
   operational-risk. Their prompts, role identifiers, input hashes, findings,
   limitations, and any material dissent are retained in a restricted-local
   decision record.
3. **Synthesize.** The orchestrator prepares one concise decision brief for
   the sole maintainer. It must state options, recommendation, rationale,
   trade-offs, contingencies, stop conditions, exact authorization wording,
   and the actions that remain unauthorized.
4. **Decide.** The sole maintainer explicitly approves, rejects, or requests
   revision. An agent cannot infer consent from silence, a passing check, or
   panel consensus.
5. **Act and verify.** Only the approved exact action occurs. The
   orchestrator records a redacted receipt and independently verifies its
   target, visibility, and hashes.

If a panel cannot be formed, a candidate remains pending. A single agent, a
shared-context echo, or a rerun of the same prompt does not constitute the
panel.

## Decision-bundle minimum fields

- Stable gate and decision-bundle identifiers; repository revision; candidate
  and input SHA-256 values.
- Provenance, rights or terms version, retrieval time, scope, exclusions,
  retention, visibility, destination, and exact proposed action.
- The three advisory reviews, evidence examined, limitations, dissent, and a
  synthesis that distinguishes observations from recommendations.
- Options, recommendation, rationale, material trade-offs, contingencies,
  stop conditions, non-authorized actions, and invalidation conditions.
- The maintainer's exact decision, time, scope, exclusions, and the verified
  post-action receipt.

## Bundling and invalidation

Compatible decisions may appear in one decision brief as separately scoped
decision lines when they use the same evidence set, rights basis, destination,
visibility, and operational class. Keep separate decisions for a new
authentic-content class, credential/terms acceptance, empirical execution,
new destination or visibility, release, publication, legal conclusion, or
profile-maturity decision.

A decision is invalidated by a changed revision, candidate hash, source or
rights basis, terms version, destination, visibility, scope, retention rule,
or irreversible action. New agent commentary or a repeated validation alone
does not invalidate an otherwise exact decision.

## Evidence language

Use **agent advisory panel**, **sole maintainer approval**, and **verified
receipt**. Do not describe agents as human reviewers, approvers, rights
holders, legal reviewers, or independent authorities. Panel consensus is not
legal clearance or accountable approval.
