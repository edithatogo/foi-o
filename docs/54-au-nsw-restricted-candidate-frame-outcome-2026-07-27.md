# AU-NSW restricted candidate-frame outcome

The authorized restricted-local validation and non-final AU-NSW candidate-frame
operation completed on 2026-07-27. It used no network access, replay, live
origin, link traversal, or attachment retrieval.

| Item | Value |
| --- | --- |
| Source candidate | 179 records, SHA-256 `c8486d035279e400b4100cbd7f9443a23dc648d6b1494527657cd294102238b6` |
| Parent immutable manifest self-pin | `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c` |
| Stored candidate frame SHA-256 | `b0da88618793118f498b5467cd8ee097ad767f97057d47632f8844d3efa6512f` |
| Frame self-pin | `342009b2bc331f22fa3b19d4f19f7687ee98be3d1e9251dd142b75378884886e` |
| Retained request-text accessible | 115 HTML snapshots |
| Metadata-only, no retained request text | 64 JSON snapshots |

Every retained raw snapshot was verified against its replay-index and
classification-candidate SHA-256 before the frame was written. The 115 HTML
records contain text extracted only from the retained correspondence-text
container. The 64 JSON records are represented as metadata-only and are not
silently converted into text-bearing units.

The result remains `candidate_frame_restricted_local_not_empirical`:
`rights_eligible`, sampling, annotation, publication, and redistribution are
all false. It is therefore not a frozen empirical frame and cannot support a
sample, annotation packet, metric, legal conclusion, or profile decision.

The next gate is a separate approval that names this exact frame, decides any
rights-eligible subset and exclusions, and authorizes an immutable empirical
frame with duplicate-clustering metadata. That approval must not be inferred
from the present candidate-frame operation.
