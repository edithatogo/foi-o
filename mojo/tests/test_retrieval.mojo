from foi_o_nz.retrieval import blend_scores, clamp_top_k, normalise_cosine, should_include_hit
from std.testing import assert_equal, assert_false, assert_true, TestSuite


def test_blend_scores() raises:
    assert_equal(blend_scores(2.0, 1.0, 1.0), 2.0)
    assert_equal(blend_scores(2.0, 1.0, 0.0), 1.0)
    assert_equal(blend_scores(2.0, 1.0, 0.5), 1.5)


def test_normalise_cosine() raises:
    assert_equal(normalise_cosine(-2.0), 0.0)
    assert_equal(normalise_cosine(0.0), 0.5)
    assert_equal(normalise_cosine(2.0), 1.0)


def test_threshold_and_top_k() raises:
    assert_true(should_include_hit(0.8, 0.5))
    assert_false(should_include_hit(0.2, 0.5))
    assert_equal(clamp_top_k(0, 100), 1)
    assert_equal(clamp_top_k(500, 100), 100)
    assert_equal(clamp_top_k(5, 100), 5)


def main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()
