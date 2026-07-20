from gen.messages_pb2 import MixRequest
from nodes.mix import mix
from nodes.testkit import assert_error, assert_ok, ax, color, srgb


def _m(a, b, weight, space=""):
    return mix(ax(), MixRequest(a=a, b=b, weight=weight, space=space))


def test_weight_zero_returns_the_first_colour():
    r = _m(srgb(255, 0, 0), srgb(0, 0, 255), 0.0, space="srgb")
    assert_ok(r)
    assert r.space == "srgb"
    for got, expected in zip(r.components, [255.0, 0.0, 0.0]):
        assert abs(got - expected) < 1e-6


def test_weight_one_returns_the_second_colour():
    r = _m(srgb(255, 0, 0), srgb(0, 0, 255), 1.0, space="srgb")
    assert_ok(r)
    for got, expected in zip(r.components, [0.0, 0.0, 255.0]):
        assert abs(got - expected) < 1e-6


def test_srgb_midpoint_is_the_component_average():
    r = _m(srgb(0, 0, 0), srgb(100, 200, 40), 0.5, space="srgb")
    assert_ok(r)
    for got, expected in zip(r.components, [50.0, 100.0, 20.0]):
        assert abs(got - expected) < 1e-6


def test_default_space_is_oklab():
    r = _m(srgb(255, 0, 0), srgb(0, 0, 255), 0.5)
    assert_ok(r)
    assert r.space == "oklab"


def test_oklab_midpoint_is_between_the_endpoints():
    a = srgb(255, 0, 0)
    b = srgb(0, 0, 255)
    mid = _m(a, b, 0.5)
    assert_ok(mid)
    # The mixed L is the mean of the endpoints' Oklab L.
    from gen.messages_pb2 import ConvertRequest
    from nodes.convert import convert
    la = convert(ax(), ConvertRequest(color=a, to_space="oklab")).components[0]
    lb = convert(ax(), ConvertRequest(color=b, to_space="oklab")).components[0]
    assert abs(mid.components[0] - (la + lb) / 2.0) < 1e-9


def test_cylindrical_space_is_rejected():
    for space in ["hsl", "hsv", "lch", "oklch"]:
        assert_error(_m(srgb(1, 2, 3), srgb(4, 5, 6), 0.5, space=space), "INVALID_ARGUMENT")


def test_weight_out_of_range_is_rejected():
    assert_error(_m(srgb(1, 2, 3), srgb(4, 5, 6), 1.5), "INVALID_ARGUMENT")
    assert_error(_m(srgb(1, 2, 3), srgb(4, 5, 6), -0.1), "INVALID_ARGUMENT")


def test_malformed_colour_is_invalid_color():
    assert_error(_m(color("srgb", 1, 2), srgb(4, 5, 6), 0.5), "INVALID_COLOR")
