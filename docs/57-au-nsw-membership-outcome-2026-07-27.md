# AU-NSW paired-annotation membership outcome

The approved deterministic membership draw completed locally on 2026-07-27.
It used the immutable AU-NSW frame and the approved protocol seed; no packet
was generated and no unit was annotated.

| Item | Value |
| --- | --- |
| Immutable frame stored SHA-256 | `d09deb2ce966fb1b13ef33244f542a4c897df534baaeab94e7bc064c10643176` |
| Immutable frame self-pin | `37af88495c8896e83028b4692a10f18f2dd5a5e4dcad6b6140f40312f64d4000` |
| Population | 115 |
| Selected paired workload | 100 |
| Retained outside workload | 15 |
| Seed | `20260721` |
| Design | Sorted text SHA-256, Python MT19937, no replacement |
| Membership SHA-256 | `4f9ec5e094ff9e9fa4e2dbb6f1c83c3fe33d28eb68c89397997c4e9bb9988840` |

The membership remains `candidate_membership_not_annotation`. Annotation,
adjudication, extractor metrics, publication, redistribution, training, and
profile promotion remain unauthorized.

The next gate is approval of this exact membership hash. After that approval,
the already approved role arrangement can be used to generate blinded packets
and perform bounded annotation/adjudication under the protocol.
