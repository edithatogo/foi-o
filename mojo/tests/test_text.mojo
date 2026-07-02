from foi_o_nz.text import (
    can_machine_certify_safety_class,
    review_required_for_score,
    risk_level_from_score,
    token_estimate_from_chars,
)
from std.testing import assert_equal, assert_false, assert_true, TestSuite


def test_token_estimate_from_chars() raises:
    assert_equal(token_estimate_from_chars(0), 1)
    assert_equal(token_estimate_from_chars(1), 1)
    assert_equal(token_estimate_from_chars(4), 1)
    assert_equal(token_estimate_from_chars(5), 2)


def test_risk_level_from_score() raises:
    assert_equal(risk_level_from_score(0, False), "low")
    assert_equal(risk_level_from_score(1, False), "medium")
    assert_equal(risk_level_from_score(5, False), "high")
    assert_equal(risk_level_from_score(0, True), "high")


def test_review_and_certification_boundary() raises:
    assert_false(review_required_for_score(0, False))
    assert_true(review_required_for_score(0, True))
    assert_false(can_machine_certify_safety_class("low"))
    assert_false(can_machine_certify_safety_class("high"))


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
