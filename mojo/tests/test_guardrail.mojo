from foi_o_nz.guardrail import (
    action_requires_review,
    can_replay_pass,
    is_dispositive_event,
    severity_rank,
)
from std.testing import assert_equal, assert_false, assert_true, TestSuite


def test_dispositive_event() raises:
    assert_true(is_dispositive_event("ReleaseMade"))
    assert_false(is_dispositive_event("SearchPlanDrafted"))


def test_severity_rank() raises:
    assert_equal(severity_rank("error"), 3)
    assert_equal(severity_rank("warning"), 2)
    assert_equal(severity_rank("info"), 1)
    assert_equal(severity_rank("unknown"), 0)


def test_action_requires_review_and_replay_pass() raises:
    assert_true(action_requires_review("high", False))
    assert_true(action_requires_review("low", True))
    assert_false(action_requires_review("low", False))
    assert_true(can_replay_pass(0))
    assert_false(can_replay_pass(1))


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
