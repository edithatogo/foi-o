# AU RightToKnow nine-record replay-failure disposition

This packet records the only unresolved positions in the approved
2,082-record AU RightToKnow replay. The approved selection SHA-256 is
`a1c2308ecc81de3754f37b3c26f7ba7fc232ff5bac930b86b36fb10463178c51`, derived
from CDX SHA-256
`954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`.

The current restricted-local failure ledger has SHA-256
`0df9720ea56fe1882091093adbfbaf2d201ab7ab8f2b76ca9956ab2733ce4c50`.
It records nine exact CDX-selected timestamps that returned HTTP 404 after
serial replay and retry:

| Slug | Media | CDX timestamp |
| --- | --- | --- |
| `acting_treasurer_scott_morrisons` | JSON | `20230109003309` |
| `inquiry_about_contact_tracing_ap` | JSON | `20210408051634` |
| `inquiry_about_contact_tracing_ap_2` | JSON | `20210408044258` |
| `inquiry_about_contact_tracing_ap_5` | JSON | `20210408051611` |
| `inquiry_about_contact_tracing_ap_7` | JSON | `20210408044308` |
| `masschallenge_contracts` | JSON | `20210408054624` |
| `nuclear_fuel_cycle_activities_in` | HTML | `20240116015703` |
| `number_of_approved_citizens_wait` | JSON | `20221105053902` |
| `which_agencies_are_rbas_transact` | JSON | `20240806012406` |

No live-origin access, attachment retrieval, link traversal, or unapproved
replacement capture has been used.

## Decision A: targeted metadata lookup

> I authorize targeted Internet Archive CDX metadata lookups for exactly the
> nine canonical URLs listed in this packet, solely to identify exact
> CDX-listed replacement captures. This does not authorize replay of any newly
> discovered capture; each replacement’s URL, timestamp, digest, retrieval
> evidence, and hash must be presented for approval before replay.

## Decision B: retain explicit failures

> I authorize finalization of one restricted-local immutable manifest for the
> approved 2,082-position population with the nine exact 404s retained as
> explicit failed-capture evidence. The nine positions must be excluded from
> full-text empirical units and population inference. This does not authorize
> publication, redistribution, training, legal certification, profile
> promotion, or downstream empirical reruns.

Until Decision A or B is approved, the current packet remains a non-final
candidate. The 2,073 successful records may be validated and classified, but
the nine failures must not be silently dropped or replaced.
