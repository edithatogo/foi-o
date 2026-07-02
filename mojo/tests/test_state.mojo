from foi_o_nz.state import (
    can_agent_certify_event,
    confidence_for_alaveteli_state,
    is_terminal_state,
    normalise_alaveteli_state,
    requires_human_certification,
)
from std.testing import assert_equal, assert_false, assert_true, TestSuite


def test_normalise_successful() raises:
    assert_equal(normalise_alaveteli_state("successful"), "ReleasedInFull")


def test_normalise_unknown() raises:
    assert_equal(normalise_alaveteli_state("future_state"), "Unknown")


def test_human_certification_guard() raises:
    assert_true(requires_human_certification("ReleaseMade"))
    assert_false(can_agent_certify_event("ReleaseMade"))
    assert_false(requires_human_certification("SearchPlanDrafted"))
    assert_true(can_agent_certify_event("SearchPlanDrafted"))


def test_confidence_and_terminal() raises:
    assert_equal(confidence_for_alaveteli_state("successful"), 0.55)
    assert_true(is_terminal_state("ReleasedInFull"))
    assert_false(is_terminal_state("Searching"))


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
