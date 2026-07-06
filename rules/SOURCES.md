# OIA Rules Source Notes

Verified by Codex on 2026-07-05 from New Zealand Legislation, Official Information Act 1982, latest version as at 5 April 2025.

Primary source URL: https://www.legislation.govt.nz/act/public/1982/0156/latest/DLM64785.html

## Consolidation Status

The source page identifies the Act as in force, latest version, as at 05 April 2025. The notes state that the consolidation incorporates amendments so that it shows the law at its stated date and that the electronic consolidation is an official version.

## Section 2: Working Day Definition

Relevant rule: `nz-oia/parameter.holiday_exclusions`.

The current definition excludes:

- Saturdays and Sundays.
- Waitangi Day.
- Good Friday and Easter Monday.
- Anzac Day.
- the Sovereign's birthday.
- Te Ra Aro ki a Matariki/Matariki Observance Day.
- Labour Day.
- the following Monday when Waitangi Day or Anzac Day falls on a Saturday or Sunday.
- the period from 25 December through 15 January.

Ambiguity note: regional anniversary days are not listed in the current s 2 working-day definition. The rules module therefore does not exclude regional anniversary days unless a later human-reviewed parameter extends the calendar.

## Section 12(3): Urgency

Relevant rule: `nz-oia/decision.urgency_flag`.

The Act allows the requester to ask for urgency and requires reasons for seeking urgency. This track treats urgency as a discretion point and routing signal, not as a computable entitlement or certified outcome.

## Section 14: Transfer Deadline

Relevant rule: `nz-oia/decision.transfer_deadline`.

Current text requires transfer promptly and in any case no later than 10 working days after receipt when the transfer conditions are met.

## Section 15: Decision Deadline

Relevant rule: `nz-oia/decision.response_deadline`.

Section 15(1) requires a decision as soon as reasonably practicable and no later than 20 working days after receipt, subject to the Act and any extension.

Clarification note: this module calculates the outer statutory deadline; it does not certify whether the agency acted as soon as reasonably practicable.

## Section 15A: Extension Validity

Relevant rule: `nz-oia/decision.extension_validity`.

Permitted grounds verified:

- large quantity of official information, or search through a large quantity, where meeting the original limit would unreasonably interfere with operations.
- consultations needed to make a decision mean a proper response cannot reasonably be made within the original limit.

The extension must be for a reasonable period. Notice must be given within 20 working days after receipt and must specify the extension period, reasons, Ombudsman complaint right, and other necessary information.

Implementation boundary: the module can deterministically check known ground labels and whether notice was within the original deadline. It cannot certify reasonableness of the extended period; that remains a discretion/human-review field.

## Section 28: Review and Deemed Refusal

Relevant rule: `nz-oia/decision.deemed_refusal`.

Section 28 makes refusal decisions reviewable by Ombudsmen. For this module, the relevant deterministic elements are:

- failure to comply with section 15(1) is included as refusal for review purposes.
- failure within an extended time limit notified under section 15A(3) is also included.
- undue delay is deemed to be a refusal.

Implementation boundary: the module can flag deadline expiry from known dates. It cannot decide the Ombudsman's review outcome.

## Source Reference IDs Used in Artifacts

- `OIA 1982 s 2, latest as at 2025-04-05`
- `OIA 1982 s 12(3), latest as at 2025-04-05`
- `OIA 1982 s 14, latest as at 2025-04-05`
- `OIA 1982 s 15, latest as at 2025-04-05`
- `OIA 1982 s 15A, latest as at 2025-04-05`
- `OIA 1982 s 28, latest as at 2025-04-05`

