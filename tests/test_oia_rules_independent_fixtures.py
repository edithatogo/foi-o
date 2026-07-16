import hashlib
import json
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator

from foi_o_nz.dates import load_holiday_dates
from foi_o_nz.oia_rules import RuleInvocation, ValueObject, evaluate_invocation

ROOT = Path(__file__).parent.parent
AUTHORING_FIXTURE = ROOT / "tests/fixtures/oia_rules/oia-clock-fixtures.json"
CANDIDATE_FIXTURE = ROOT / "tests/fixtures/oia_rules/oia-event-time-independent-candidates.json"
FIXTURE_SCHEMA = ROOT / "schemas/json/oia-event-time-fixture-set.schema.json"
HOLIDAY_CALENDAR = ROOT / "examples/nz-public-holidays-2026.govt-nz.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _input_dates(case: dict) -> set[str]:
    return {
        value["value"]
        for value in case["inputs"].values()
        if isinstance(value.get("value"), str)
        and len(value["value"]) == 10
        and value["value"][4] == "-"
    }


def test_candidate_fixture_is_schema_valid_and_independent() -> None:
    candidate = _load(CANDIDATE_FIXTURE)
    authoring = _load(AUTHORING_FIXTURE)
    schema = _load(FIXTURE_SCHEMA)

    Draft202012Validator(schema).validate(candidate)
    assert candidate["status"] == "candidate"
    assert candidate["humanReview"]["status"] == "pending"
    assert candidate["humanReview"]["promotionAllowed"] is False
    assert candidate["independence"]["authoringFixtureSha256"] == hashlib.sha256(
        AUTHORING_FIXTURE.read_bytes()
    ).hexdigest()

    authoring_ids = {case["caseId"] for case in authoring["cases"]}
    candidate_ids = {case["caseId"] for case in candidate["cases"]}
    assert candidate_ids.isdisjoint(authoring_ids)

    authoring_dates = set().union(*(_input_dates(case) for case in authoring["cases"]))
    candidate_dates = set().union(*(_input_dates(case) for case in candidate["cases"]))
    assert candidate_dates.isdisjoint(authoring_dates)


def test_candidate_fixture_matches_current_runtime_without_promoting_it() -> None:
    candidate = _load(CANDIDATE_FIXTURE)
    holidays = load_holiday_dates(HOLIDAY_CALENDAR)

    for case in candidate["cases"]:
        inputs = {
            variable_id: ValueObject(**value)
            for variable_id, value in case["inputs"].items()
        }
        invocation = RuleInvocation(
            decision_id=case["decisionId"],
            inputs=inputs,
            parameter_set=candidate["parameterSet"],
            invoked_by=case["caseId"],
        )
        result = evaluate_invocation(invocation, holidays=holidays)
        actual = result.outputs[case["decisionId"]]
        expected = case["expected"]
        assert actual.valueState == expected["valueState"], case["caseId"]
        assert actual.value == expected.get("value"), case["caseId"]
        for warning in expected.get("warnings", []):
            assert warning in (actual.warnings or []), case["caseId"]


def test_candidate_sources_are_authoritative_and_event_time_is_explicit() -> None:
    candidate = _load(CANDIDATE_FIXTURE)
    source_urls = {source["url"] for source in candidate["sources"]}
    assert source_urls == {
        "https://www.legislation.govt.nz/act/public/1982/0156/latest/whole.html",
        "https://www.ombudsman.parliament.nz/agency-assistance/official-information-calculators",
        "https://www.govt.nz/browse/work/public-holidays-and-work/public-holidays-and-anniversary-dates/",
    }
    for case in candidate["cases"]:
        assert date.fromisoformat(case["eventTime"]).year == 2026
        assert case["sourceRefs"]
