from foi_o_nz.clock import is_machine_working_day, is_oia_summer_excluded, is_weekend
from std.testing import assert_false, assert_true, TestSuite


def test_summer_exclusion() raises:
    assert_true(is_oia_summer_excluded(12, 25))
    assert_true(is_oia_summer_excluded(1, 15))
    assert_false(is_oia_summer_excluded(1, 16))


def test_machine_working_day() raises:
    assert_true(is_weekend(5))
    assert_true(is_weekend(6))
    assert_true(is_machine_working_day(0, 6, 1))
    assert_false(is_machine_working_day(5, 6, 1))
    assert_false(is_machine_working_day(0, 12, 25))


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
