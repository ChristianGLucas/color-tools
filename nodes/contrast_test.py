from gen.messages_pb2 import ContrastRequest
from nodes.contrast import contrast
from nodes.testkit import assert_error, assert_ok, ax, color, srgb


def _c(fg, bg):
    return contrast(ax(), ContrastRequest(foreground=fg, background=bg))


def test_identical_colours_have_ratio_one_and_fail_everything():
    r = _c(srgb(80, 80, 80), srgb(80, 80, 80))
    assert_ok(r)
    assert abs(r.ratio - 1.0) < 1e-9
    assert not r.aa_normal and not r.aa_large and not r.aaa_normal and not r.aaa_large


def test_contrast_is_order_independent():
    a = _c(srgb(0, 0, 0), srgb(255, 255, 255))
    b = _c(srgb(255, 255, 255), srgb(0, 0, 0))
    assert_ok(a)
    assert_ok(b)
    assert abs(a.ratio - b.ratio) < 1e-12


def test_low_contrast_fails_aa():
    # Light grey on white is a classic failure.
    r = _c(srgb(200, 200, 200), srgb(255, 255, 255))
    assert_ok(r)
    assert r.ratio < 3.0
    assert not r.aa_normal and not r.aa_large


def test_contrast_accepts_colours_in_any_space():
    # A lab-specified near-black on an hsl white should be high contrast.
    r = _c(color("lab", 0, 0, 0), color("hsl", 0, 0, 100))
    assert_ok(r)
    assert abs(r.ratio - 21.0) < 1e-6


def test_malformed_colour_is_invalid_color():
    assert_error(_c(color("srgb", 1), srgb(255, 255, 255)), "INVALID_COLOR")
