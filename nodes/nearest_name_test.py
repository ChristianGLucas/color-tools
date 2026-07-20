from gen.messages_pb2 import Color
from nodes.nearest_name import nearest_name
from nodes.testkit import assert_error, assert_ok, ax, color, srgb


def _n(c):
    return nearest_name(ax(), c)


def test_exact_css_colour_returns_its_own_name_with_zero_difference():
    r = _n(srgb(255, 0, 0))
    assert_ok(r)
    assert r.name == "red"
    assert r.hex == "#ff0000"
    assert r.delta_e < 1e-6


def test_tomato_is_found_exactly():
    r = _n(srgb(255, 99, 71))
    assert_ok(r)
    assert r.name == "tomato"
    assert r.delta_e < 1e-6


def test_a_near_colour_snaps_to_the_closest_name():
    r = _n(srgb(253, 2, 1))     # a hair off pure red
    assert_ok(r)
    assert r.name == "red"
    assert 0.0 < r.delta_e < 2.0


def test_works_from_any_space():
    # Lab coordinates of pure white -> "white".
    r = _n(color("lab", 100.0, 0.0, 0.0))
    assert_ok(r)
    assert r.name == "white"


def test_malformed_colour_is_invalid_color():
    assert_error(_n(Color()), "INVALID_COLOR")
    assert_error(_n(color("srgb", 1, 2)), "INVALID_COLOR")
