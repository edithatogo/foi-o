from foi_o_nz.epistemic import assertion_status_rank, can_agent_assert_status, confidence_band
from std.testing import assert_equal, assert_false, assert_true, TestSuite


def test_assertion_rank() raises:
    assert_equal(assertion_status_rank("unknown"), 0)
    assert_equal(assertion_status_rank("certified"), 4)
    assert_equal(assertion_status_rank("future"), -1)


def test_confidence_band() raises:
    assert_equal(confidence_band(0.0), "none")
    assert_equal(confidence_band(0.4), "low")
    assert_equal(confidence_band(0.74), "medium")
    assert_equal(confidence_band(0.95), "high")


def test_agent_assert_status() raises:
    assert_true(can_agent_assert_status("observed"))
    assert_true(can_agent_assert_status("inferred"))
    assert_false(can_agent_assert_status("certified"))


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
