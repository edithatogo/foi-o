# Event Extraction and Timeline Audit

## Current Repo-Local Proof

- `src/foi_o_nz/extractors.py` reads correspondence-like fields: `correspondence`, `messages`, `communications`, `updates`, `mail`, and single text blocks under `body`, `text`, `response`, or `description`.
- The extractor emits `MessageObserved` events plus candidate process events for extension, transfer, clarification, charge, refusal, release, complaint/review, and decision language.
- Candidate dispositive events use `assertion_status="inferred"` and carry `requires_human_certification=true` plus negative `human_certification.certified=false` metadata when the event type is inside the human-certification boundary.
- `src/foi_o_nz/quality.py` flags missing evidence, missing generator metadata, and dispositive event certification-boundary violations.
- `src/foi_o_nz/evaluation.py` provides deterministic set-based precision/recall/F1 matching by event type, state, and optional strict confidence/assertion status.

## Gaps To Close

- Fixture tests currently exercise only one correspondence candidate path (`ExtensionNotified`) through `tests/test_normalise.py`.
- Message-shape coverage is missing for alternate public manifest fields and string/dict message variants.
- Candidate fixture coverage is missing for `TransferNotified`, `ClarificationRequested`, `ComplaintObserved`, `DecisionCommunicated`, `ReleaseMade`, `RefusalCommunicated`, and `ChargeNoticeSent`.
- There is no dedicated timeline reconstruction helper that sorts events by observed time, source order, and fallback provenance while warning about missing or ambiguous dates.
- Event evaluation has in-memory tests but no committed safe fixture records or schema-valid example output for the event-track workflow.

## Certification Boundary Assumptions

- `ExtensionNotified`, `TransferNotified`, `DecisionCommunicated`, `ReleaseMade`, `RefusalCommunicated`, and `ChargeNoticeSent` are candidate/inferred process events unless a human certifies them.
- `ClarificationRequested` and `ComplaintObserved` are still reviewable process observations but do not by themselves certify a legal outcome.
- Extractors may surface candidate events and evidence excerpts; they must not mark release/refusal/redaction/charge/extension/transfer/complaint outcomes as certified.

## Next Tests

- Add fixture tests for all supported message fields and single text fields.
- Add candidate event tests for each current regex rule and assert certification metadata for dispositive candidates.
- Add timeline ordering tests with missing-date warnings.
- Add committed event evaluation fixture tests with deterministic precision/recall/F1 output.
