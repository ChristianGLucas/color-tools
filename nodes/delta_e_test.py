from gen.messages_pb2 import PairRequest
from nodes.delta_e import delta_e
from nodes.testkit import assert_error, assert_ok, ax, color, srgb


def _de(a, b, method=""):
    return delta_e(ax(), PairRequest(a=a, b=b, method=method))


def test_a_colour_has_zero_difference_from_itself():
    r = _de(srgb(120, 60, 200), srgb(120, 60, 200))
    assert_ok(r)
    assert r.delta_e < 1e-6
    assert r.method == "CIE 2000"


def test_difference_can_be_measured_across_different_spaces():
    # Same colour expressed two ways must be ~0 apart.
    r = _de(srgb(255, 0, 0), color("lab", 53.2329, 80.1112, 67.2237))
    assert_ok(r)
    assert r.delta_e < 0.05


def test_black_vs_white_is_a_large_difference():
    r = _de(srgb(0, 0, 0), srgb(255, 255, 255))
    assert_ok(r)
    assert r.delta_e > 90     # maximal lightness difference


def test_default_method_is_ciede2000():
    r = _de(srgb(10, 20, 30), srgb(40, 50, 60))
    assert_ok(r)
    assert r.method == "CIE 2000"


def test_method_aliases_are_accepted():
    for alias, canon in [("cie2000", "CIE 2000"), ("CIE 1976", "CIE 1976"), ("cmc", "CMC")]:
        r = _de(srgb(10, 20, 30), srgb(40, 50, 60), method=alias)
        assert_ok(r)
        assert r.method == canon


def test_cie1976_is_plain_euclidean_distance_in_lab():
    # dE76 between two Lab points is exactly the Euclidean distance.
    a = color("lab", 50.0, 10.0, 20.0)
    b = color("lab", 55.0, 14.0, 20.0)
    r = _de(a, b, method="CIE 1976")
    assert_ok(r)
    assert abs(r.delta_e - (25.0 + 16.0) ** 0.5) < 1e-6   # sqrt(5^2 + 4^2)


def test_unknown_method_is_invalid_argument():
    assert_error(_de(srgb(1, 2, 3), srgb(4, 5, 6), method="cie9999"), "INVALID_ARGUMENT")


def test_malformed_colour_is_invalid_color():
    assert_error(_de(color("srgb", 1, 2), srgb(4, 5, 6)), "INVALID_COLOR")
