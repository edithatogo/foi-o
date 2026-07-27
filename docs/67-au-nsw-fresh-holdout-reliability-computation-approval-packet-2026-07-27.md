# AU-NSW fresh holdout reliability-computation approval packet

## Proposed operation

Compute restricted-local descriptive agreement statistics from the locked
15-unit AU-NSW fresh-holdout annotation report. This operation will not score
an extractor or make a threshold, maturity, gold-promotion, publication, or
population-inference decision.

## Pinned inputs

| Item | SHA-256 |
| --- | --- |
| Locked annotation report | `83dfd246d5e51fcb6a05decfb5fd72ac66ca77ede2a16fb59146bcab5c660683` |
| Fresh holdout membership | `2acdb55b8679a060175eaca7c2183e90e59a557fb53fc992df45c965275f8d91` |
| Immutable AU-NSW frame | `d09deb2ce966fb1b13ef33244f542a4c897df534baaeab94e7bc064c10643176` |
| Revised codebook | `56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6` |
| Sampling/annotation protocol | `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf` |

The report contains 15 units, zero annotator disagreements, and zero
adjudications. The computation will record descriptive agreement and an
explicit small-sample/undefined disposition where a statistic is not
informative. It will not silently treat zero disagreements as maturity proof.

## Required decision

> I authorize restricted-local descriptive reliability computation from locked
> AU-NSW fresh-holdout annotation report SHA-256
> `83dfd246d5e51fcb6a05decfb5fd72ac66ca77ede2a16fb59146bcab5c660683`, using
> the pinned membership, immutable frame, revised codebook, and protocol
> recorded in this packet. This authorizes creation and validation of a
> descriptive reliability report only. It does not authorize extractor
> metrics, threshold satisfaction or maturity decisions, gold promotion,
> publication, redistribution, training, legal certification, profile
> promotion, push, pull request, or merge.
