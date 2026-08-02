# Remaining-jurisdiction authoritative-source and rights plan

Status: candidate evidence captured, rights review pending (2026-08-02). This document
does not authorise network retrieval, source capture, replay, redistribution,
runtime activation, legal conclusions, empirical freezing, or profile
promotion.

## Objective

Produce one hash-pinned, jurisdiction-specific source-evidence packet for each
remaining Australian jurisdiction: ACT, QLD, VIC, WA, SA, TAS, and NT. Each
packet must distinguish authoritative status, machine-readable availability,
effective-date/version semantics, access terms, copyright/licence scope,
retrieval evidence, and the exact adapter capability that those facts support.

## Evidence packet contract

For every candidate source, record:

1. jurisdiction and authority identity;
2. exact source URL and source type (register, API, Gazette, feed, HTML, XML,
   PDF, or Word);
3. retrieval timestamp, HTTP status, MIME type, byte count, and SHA-256;
4. version/effective-date and point-in-time semantics;
5. authoritative-versus-convenience status;
6. terms, licence, attribution, exclusions, rate limits, registration, and
   redistribution constraints;
7. parser fixture and negative fixture, with the source bytes kept restricted
   local unless redistribution is explicitly approved;
8. transformation lineage from source bytes to normalized candidate; and
9. the precise next gate: adapter-only, restricted-local candidate, or blocked.

No source is treated as authoritative merely because it is public, searchable,
mirrored, or machine-readable.

The first bounded candidate evidence record is
`source-evidence-candidate-2026-08-02.json`, SHA-256
`d177f2133790d4f23610edb99a845ec7b58d5669d72e24f7ed8db34b2909cfcb`.
It contains official HTML retrieval receipts for WA, VIC, TAS, ACT, NT, and
QLD, plus explicit SA HTTP 403 failures. The source bytes remain restricted
local in the capture workspace; the JSON record is a candidate provenance
index, not an immutable source manifest.

## Public metadata findings and source routes

| Jurisdiction | Primary authority route | Current evidence | Next bounded action | Gate |
| --- | --- | --- | --- | --- |
| QLD | [Queensland Legislation](https://www.legislation.qld.gov.au/) and [API](https://www.legislation.qld.gov.au/api) | Official site states authorised legislation is available and XML can be made available. API documents JSON/XML/HTML/PDF renditions and requires registration; the access agreement specifies CC BY 4.0 subject to its terms and copyright statement. | Prepare registration/terms packet, then obtain a custodian-approved credential in the approved environment; capture one non-sensitive API fixture only after registration. | Human registration and terms acceptance; credential custody; fixture-rights approval. |
| TAS | [Tasmanian Legislation Online](https://www.legislation.tas.gov.au/) | Official site provides consolidated and point-in-time legislation. Help documentation defines stable `/view/{format}/{status}/{date}/{id}` routes and lists HTML, PDF, and XML. Copyright/CC terms must be captured from the live notice with each candidate. | Capture one Act and one statutory-rule metadata/format fixture; compare XML/HTML identity and authorised-version PDF where present. | Rights notice and byte-level fixture evidence. |
| ACT | [ACT Legislation Register](https://www.legislation.act.gov.au/) | Register describes itself as the authorised electronic statute book. It states authorised versions are PDF; Word is unauthorised and provided for accessibility; HTML is a convenience/search format. | Build PDF-authority plus Word/HTML-accessibility adapter boundary; retain PDF as authority and test identity crosswalks. | Restricted-local source/rights packet; no authority promotion from Word/HTML. |
| SA | [South Australian Legislation](https://legislation.sa.gov.au/) | Official authorised-version page identifies authorised electronic versions. Copyright notice states most SA content is CC BY 4.0 but excludes specified material and requires attribution/disclaimer language. | Capture terms page and one representative authorised-version metadata fixture; preserve excluded-content classification. | Rights review before any retained text or redistribution. |
| WA | [WALW](https://www.legislation.wa.gov.au/) | Official register provides in-force, ceased, as-passed, reprint, subsidiary-legislation, Gazette, search, and notification-feed routes. WA Legislation Act materials describe official electronic versions and publication responsibilities. | Determine stable document/notification URLs and obtain current copyright/terms and format evidence; use XML/HTML only if exact official identity is demonstrated. | Format and rights evidence; WA/ACT identity conflict review. |
| VIC | [Victorian legislation](https://www.legislation.vic.gov.au/) | Official site identifies itself as the primary source and distinguishes in-force, as-made, historical, repealed, and Gazette material. | Capture source navigation, one in-force/as-made pair, MIME/identity metadata, and current terms; add parser only after stable URL/version rules are proven. | Stable machine-access and rights evidence. |
| NT | [Northern Territory Legislation](https://legislation.nt.gov.au/en) | Official site provides current and historical legislation, Bills, subordinate legislation, Gazettes, and superseded reprints. Individual records expose PDF/Word downloads and a site API route, but authoritative status of each rendition must be established. | Capture one record's register metadata and rendition identities; test HTML/PDF/Word/API equivalence without assuming Word is authoritative. | Rendition authority and rights evidence. |

## Dependency sequence

### Lane A — immediately safe, no credential

- Record exact authority URLs, terms pages, format routes, and effective-date
  semantics for all seven jurisdictions.
- Build metadata-only positive/negative fixtures for identity, version, MIME,
  and unsupported-format handling.
- Resolve WA/ACT authority-label conflicts through an explicit crosswalk; do
  not classify empirical records from tags alone.

### Lane B — bounded official-source candidates

- TAS, ACT, SA, WA, VIC, and NT: capture only the approved representative
  official metadata/format fixtures after a source-rights packet is approved.
- Keep PDF and HTML/XML/Word as separate evidence classes; do not silently
  substitute one for another.
- Hash every byte and attach retrieval/provenance evidence before adapter
  implementation is called source-ready.

### Lane C — Queensland registration

- Prepare a registration packet containing the API URL, requested scope,
  terms/agreement, privacy notice, rate limits, and credential handling.
- After the user completes registration in the approved environment, retrieve
  one bounded fixture and verify JSON/XML/HTML/PDF identity and licence scope.
- If registration is unavailable, fall back to the official public website's
  non-API HTML/PDF routes for adapter-shape work only; do not claim API access.

### Lane D — adapter and rollout gates

- Implement parsers only against hash-pinned fixtures and explicit schemas.
- Run positive and negative contract tests plus independent identity checks.
- Keep runtime capability disabled until the relevant source pack, rights
  packet, and repository checks are complete.
- Keep empirical capture, archive replay, manifests, annotation, and profile
  maturity as later independent gates.

## Options and recommendation

### Option 1 — official-first, metadata then bounded fixtures (recommended)

Proceed with Lane A now, then process jurisdictions in readiness order:
TAS/ACT/SA first, WA/VIC/NT next, and QLD after registration. This preserves
authority and rights provenance and minimizes rework.

### Option 2 — implement against public HTML immediately

Faster initial adapters, but higher risk of unstable selectors, incorrect
authority/version claims, and rights ambiguity. Suitable only for disabled
scaffolds and negative tests.

### Option 3 — use mirrors or AustLII as primary sources

Useful for cross-checking and gap detection, but not acceptable as the
authoritative source pack unless the jurisdiction explicitly designates that
mirror. Keep mirrors as independent-oracle evidence only.

Recommendation: Option 1, with Option 2 permitted only for fail-closed parser
scaffolds and Option 3 limited to non-authoritative triangulation.

## Decisions requiring the user

1. **QLD registration:** authorize one interactive registration/session and one
   bounded official API fixture retrieval, or keep QLD API work blocked and use
   public HTML/PDF only for disabled scaffolding. Recommended: authorize the
   registration session, with credentials entered only by the user and never
   stored in the repository.
2. **Retained official fixtures:** approve restricted-local retention of the
   representative official bytes and terms pages for TAS, ACT, SA, WA, VIC, and
   NT after their URLs, retrieval metadata, hashes, and rights dispositions are
   presented. Recommended: approve restricted-local retention only; no
   publication or redistribution.
3. **Cross-checking:** approve mirrors such as AustLII only as independent
   comparison evidence, never as authority or a source of empirical population
   membership. Recommended: approve this limited use.

## Contingencies

- 403/Cloudflare or unstable public routes: record the failure, use official
  index/terms metadata, and keep the runtime adapter disabled; do not bypass
  controls.
- API registration unavailable: use public official HTML/PDF only for disabled
  scaffolding and return to API registration when a custodian-approved account
  exists.
- No stable XML: use official HTML/PDF with a format-specific parser and retain
  the authoritative PDF boundary; do not label convenience text authoritative.
- Rights unclear or contradictory: stop at candidate status and request a
  custodian/rights decision; do not infer permission from accessibility.
- Source changes after fixture capture: invalidate the candidate by hash,
  retain the old evidence, and create a new versioned candidate rather than
  rewriting history.
