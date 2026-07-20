from gen.messages_pb2 import ConvertRequest
from nodes.convert import convert
from nodes.testkit import assert_error, assert_ok, ax, color, srgb


def _conv(c, to_space):
    return convert(ax(), ConvertRequest(color=c, to_space=to_space))


def test_srgb_red_to_lab_matches_the_known_value():
    r = _conv(srgb(255, 0, 0), "lab")
    assert_ok(r)
    assert r.space == "lab"
    assert abs(r.components[0] - 53.2329) < 1e-2
    assert abs(r.components[1] - 80.1112) < 1e-2
    assert abs(r.components[2] - 67.2237) < 1e-2


def test_srgb_red_to_hsl_is_pure_red():
    r = _conv(srgb(255, 0, 0), "hsl")
    assert_ok(r)
    assert r.space == "hsl"
    assert abs(r.components[0] - 0.0) < 1e-6      # hue 0
    assert abs(r.components[1] - 100.0) < 1e-6    # saturation 100
    assert abs(r.components[2] - 50.0) < 1e-6     # lightness 50


def test_blue_to_hsl_hue_is_240_degrees():
    r = _conv(srgb(0, 0, 255), "hsl")
    assert_ok(r)
    assert abs(r.components[0] - 240.0) < 1e-4


def test_white_stays_white_across_spaces():
    r = _conv(srgb(255, 255, 255), "lab")
    assert_ok(r)
    assert abs(r.components[0] - 100.0) < 1e-3    # L* = 100
    assert abs(r.components[1]) < 0.02            # a*, b* ~ 0
    assert abs(r.components[2]) < 0.02


def test_srgb_round_trips_through_lab():
    for rgb in ([255, 0, 0], [12, 200, 130], [0, 0, 128], [240, 240, 10]):
        lab = _conv(srgb(*rgb), "lab")
        assert_ok(lab)
        back = _conv(lab, "srgb")
        assert_ok(back)
        # Round-trip through Lab accumulates only sub-quantisation float error
        # (< 0.1 of one 8-bit step), far below a visible difference.
        for got, expected in zip(back.components, rgb):
            assert abs(got - expected) < 0.1, f"{rgb} round-tripped to {list(back.components)}"


def test_srgb_round_trips_through_oklch():
    lab = _conv(srgb(34, 139, 34), "oklch")
    assert_ok(lab)
    back = _conv(lab, "srgb")
    assert_ok(back)
    for got, expected in zip(back.components, [34, 139, 34]):
        assert abs(got - expected) < 1e-2


def test_unknown_target_space_is_invalid_argument():
    assert_error(_conv(srgb(1, 2, 3), "cmyk"), "INVALID_ARGUMENT")


def test_empty_target_space_is_invalid_argument():
    assert_error(_conv(srgb(1, 2, 3), ""), "INVALID_ARGUMENT")


def test_unknown_source_space_is_invalid_color():
    assert_error(_conv(color("cmyk", 1, 2, 3), "srgb"), "INVALID_COLOR")


def test_wrong_component_count_is_invalid_color():
    assert_error(_conv(color("srgb", 1, 2), "lab"), "INVALID_COLOR")
    assert_error(_conv(color("srgb", 1, 2, 3, 4), "lab"), "INVALID_COLOR")


def test_defaulted_empty_color_is_invalid_color():
    assert_error(_conv(color(""), "lab"), "INVALID_COLOR")


def test_upstream_error_is_propagated_unchanged():
    from gen.messages_pb2 import Color, Error
    poisoned = Color(error=Error(code="INVALID_HEX", message="bad hex upstream"))
    r = _conv(poisoned, "lab")
    assert r.error.code == "INVALID_HEX"
    assert "upstream" in r.error.message
