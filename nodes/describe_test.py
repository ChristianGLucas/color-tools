from gen.messages_pb2 import Color
from nodes.describe import describe
from nodes.testkit import assert_error, assert_ok, ax, color, srgb


def _d(c):
    return describe(ax(), c)


def test_describe_red():
    r = _d(srgb(255, 0, 0))
    assert_ok(r)
    assert r.hex == "#ff0000"
    for got, expected in zip(r.srgb, [255.0, 0.0, 0.0]):
        assert abs(got - expected) < 1e-6
    for got, expected in zip(r.hsl, [0.0, 100.0, 50.0]):
        assert abs(got - expected) < 1e-4
    # WCAG relative luminance of pure red is 0.2126 by definition.
    assert abs(r.relative_luminance - 0.2126) < 1e-4


def test_tomato_oklch_and_hex():
    r = _d(srgb(255, 99, 71))
    assert_ok(r)
    assert r.hex == "#ff6347"
    for got, expected in zip(r.oklch, [0.6962, 0.1955, 32.3044]):
        assert abs(got - expected) < 1e-3


def test_black_wants_white_text_white_wants_black_text():
    assert _d(srgb(0, 0, 0)).is_dark is True
    assert _d(srgb(255, 255, 255)).is_dark is False


def test_luminance_is_monotonic_in_lightness():
    dark = _d(srgb(30, 30, 30)).relative_luminance
    light = _d(srgb(220, 220, 220)).relative_luminance
    assert dark < light


def test_describe_accepts_any_space():
    from gen.messages_pb2 import ConvertRequest
    from nodes.convert import convert
    lab = convert(ax(), ConvertRequest(color=srgb(255, 0, 0), to_space="lab"))
    r = _d(lab)
    assert_ok(r)
    assert r.hex == "#ff0000"


def test_malformed_colour_is_invalid_color():
    assert_error(_d(Color()), "INVALID_COLOR")
