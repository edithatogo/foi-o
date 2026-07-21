# Australian pilot objective completion audit

Audit date: 2026-07-21. This is an evidence index, not a maturity or legal
certification decision.

| Objective item | Current evidence | Status | Missing gate |
| --- | --- | --- | --- |
| Commonwealth and NSW legislation adapters | `examples/v2/australian-legislation-adapter-integration.pending.json`, pinned legislation commit `feb55b2` | Candidate implementation verified | Coordinated legislation-repository integration and source-pack manifest pin |
| Hash-pinned source-pack candidates | `examples/v2/australian-source-pack-au-cth.candidate.json`, `australian-source-pack-au-nsw.candidate.json` | Complete as candidates | Content/rights promotion remains separate |
| fyi-cli capture support | fyi-cli commit `3454a24`; targeted capture tests passed | Complete for bounded worker | Live source access |
| Bounded read-only capture plan | `conductor/tracks/australian_jurisdiction_profiles_20260714/capture-execution-plan-20260721.md` | Complete | None for planning |
| Authorized immutable manifests | `examples/v2/australian-capture-attempt-2026-07-21.json` | Not achieved; run failed closed | Official source route returning records rather than HTTP 403 |
| Ontology-pinned authentic extraction bundles | No authentic source population exists | Not achieved | Authentic, rights-cleared frozen samples |
| Codebook and sampling frame | `docs/42-australian-pilot-preregistration.md` | Complete as preregistration | Human approval/hash reconciliation for changed actor model |
| Blinded annotation packets | `scripts/build_australian_blinded_packets.py` and tests | Generator complete | Authentic frozen frame and approved codebook |
| Human annotation/adjudication metrics | No human annotation set exists | Not achieved | Human annotations and adjudication |
| Maturity-decision packets | No empirical metrics exist | Not achieved | Metrics, disagreement resolution, and human decision |
| PR #88 merge gate | GitHub merge commit `1796e88909d029f716774ef201e2f12d0ee68c3a` | Complete | None |

## Fail-closed source evidence

The bounded run used the pinned fyi-cli and fyi-archive revisions and stopped
on HTTP 403 during request discovery. The documented HTML list, Atom feed,
list JSON, and per-request JSON routes were also probed and returned HTTP 403.
No access-control bypass, authenticated access, or publication was attempted.

The empirical stages must not be marked complete, and placeholder fixtures
must not be promoted, until an official accessible route or an equivalent
rights-cleared source artifact is attached with byte and SHA-256 evidence.
