from foi_o_nz.redaction import candidate_requires_review, is_ascii_alpha, is_ascii_digit, is_email_domain_char, is_email_local_char, redaction_preview_width
from std.testing import assert_equal, assert_false, assert_true, TestSuite


def test_ascii_predicates() raises:
    assert_true(is_ascii_alpha(65))
    assert_true(is_ascii_alpha(122))
    assert_false(is_ascii_alpha(48))
    assert_true(is_ascii_digit(57))
    assert_false(is_ascii_digit(65))


def test_email_chars() raises:
    assert_true(is_email_local_char(43))
    assert_true(is_email_domain_char(46))
    assert_false(is_email_domain_char(95))


def test_preview_and_review() raises:
    assert_equal(redaction_preview_width(0), 0)
    assert_equal(redaction_preview_width(2), 2)
    assert_equal(redaction_preview_width(8), 1)
    assert_equal(redaction_preview_width(12), 2)
    assert_false(candidate_requires_review(0.0))
    assert_true(candidate_requires_review(0.1))


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
