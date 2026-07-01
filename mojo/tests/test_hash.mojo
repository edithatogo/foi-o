from foi_o_nz.hash import bounded_bucket, fnv1a64_seed, fnv1a64_update
from std.testing import assert_equal, assert_true, TestSuite


def test_fnv_seed_and_update() raises:
    var seed = fnv1a64_seed()
    assert_equal(seed, UInt64(14695981039346656037))
    var updated = fnv1a64_update(seed, UInt8(102))
    assert_true(updated != seed)


def test_bounded_bucket() raises:
    assert_equal(bounded_bucket(UInt64(10), 0), 0)
    assert_equal(bounded_bucket(UInt64(10), 3), 1)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
