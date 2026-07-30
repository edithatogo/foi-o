# AU RightToKnow nine-URL CDX lookup outcome

The authorized metadata-only Internet Archive CDX lookup was performed for
exactly the nine canonical URLs in
`docs/89-au-rtk-nine-failure-disposition-approval-packet-2026-07-30.md`.
The operation was bound to failure-ledger SHA-256
`0df9720ea56fe1882091093adbfbaf2d201ab7ab8f2b76ca9956ab2733ce4c50`.

Retrieval completed at `2026-07-30T22:54:52.109548+00:00`. All nine exact-match
CDX metadata queries returned successfully. Each response contained only the
already-selected timestamp/digest, so there are zero replacement candidates.
No archived snapshot was replayed and the RightToKnow origin was not accessed.

| Slug | CDX rows | Alternatives | Response SHA-256 |
| --- | ---: | ---: | --- |
| `acting_treasurer_scott_morrisons` | 1 | 0 | `6ffd1fd111ca1c5ce9184ae443c60bb8e9dd0b1cf1e41861333a75cad05a8e84` |
| `inquiry_about_contact_tracing_ap` | 1 | 0 | `20e67ede540bb9345c74ca678f5089e8c257208ea8cf4187e70bf00efac99adb` |
| `inquiry_about_contact_tracing_ap_2` | 1 | 0 | `e57b5403acdd24786f00c7e687e8e9886aa6c6a9737f9d7b3ddd6fc23193ad66` |
| `inquiry_about_contact_tracing_ap_5` | 1 | 0 | `255e27bc90c3bea3e6288c547da717f4c57e88d52f21dee893adbbdcf7b0a216` |
| `inquiry_about_contact_tracing_ap_7` | 1 | 0 | `1b0c5a6b0eaa365d301d764f9aa2ddd4c2a646fff9116bfb121210e31bd206ed` |
| `masschallenge_contracts` | 1 | 0 | `5d6b12df2b04aca07e826ffad8f450b5550245d376babafe2e81c185351a787e` |
| `nuclear_fuel_cycle_activities_in` | 1 | 0 | `a0013b96b7a5f26bf91cf0c1ac6f715e08072717d1d6d882ef64d535eceed2f4` |
| `number_of_approved_citizens_wait` | 1 | 0 | `ea5ea7e7d3edc832c6b634d800da7c0f04f66ebf552769a708d7ef5e3ba41a8a` |
| `which_agencies_are_rbas_transact` | 1 | 0 | `1d42ad07676a4457613f6a6c37a6475b727432fdd5d0d5503518e7a1dbdbbf4f` |

The restricted-local summary artifact has SHA-256
`e6ea1326395dbe48c130a707113c0a623738bd30dd342adb903434bbbfde31f5`.
Its status is `candidate_metadata_only_no_replay`.

## Remaining decision

Because no replacement candidate exists, manifest finalization requires an
explicit disposition of the nine 404 positions:

> I authorize finalization of one restricted-local immutable AU RightToKnow
> manifest for selection SHA-256
> `a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`,
> retaining failure-ledger SHA-256
> `0df9720ea56fe1882091093adbfbaf2d201ab7ab8f2b76ca9956ab2733ce4c50`
> as nine explicit HTTP 404 exclusions and using authorization confirmation
> `FINALIZE_WITH_NINE_EXPLICIT_404_EXCLUSIONS`. The nine positions must be
> excluded from empirical full-text units and population inference. This does
> not authorize additional replay, origin access, publication, redistribution,
> training, legal certification, profile promotion, push, pull request, merge,
> or downstream empirical reruns.
