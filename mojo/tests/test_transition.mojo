from foi_o_nz.transition import is_forward_transition, transition_rank
from std.testing import assert_equal, assert_false, assert_true, TestSuite


def test_transition_rank() raises:
    assert_equal(transition_rank("Received"), 2)
    assert_equal(transition_rank("DecisionApproved"), 12)
    assert_equal(transition_rank("Future"), -1)


def test_forward_transition() raises:
    assert_true(is_forward_transition("Received", "Searching"))
    assert_false(is_forward_transition("Searching", "Received"))
    assert_false(is_forward_transition("Future", "Received"))


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
