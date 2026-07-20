from gen.messages_pb2 import Color
from nodes.to_hex import to_hex
from nodes.testkit import assert_error, assert_ok, ax, color, srgb


def _h(c):
    return to_hex(ax(), c)


def test_srgb_renders_to_hex():
    r = _h(srgb(255, 99, 71))
    assert_ok(r)
    assert r.hex == "#ff6347"


def test_black_and_white():
    assert _h(srgb(0, 0, 0)).hex == "#000000"
    assert _h(srgb(255, 255, 255)).hex == "#ffffff"


def test_lab_red_round_trips_back_to_hex():
    # Derive red's Lab at full precision (not rounded literals) so the round
    # trip lands back exactly on #ff0000.
    from gen.messages_pb2 import ConvertRequest
    from nodes.convert import convert
    lab = convert(ax(), ConvertRequest(color=srgb(255, 0, 0), to_space="lab"))
    r = _h(lab)
    assert_ok(r)
    assert r.hex == "#ff0000"


def test_out_of_gamut_colour_is_clamped_to_valid_hex():
    # A very saturated Oklch magenta lies outside sRGB; it must still yield a
    # syntactically valid 6-digit hex, not an error or a malformed string.
    r = _h(color("oklch", 0.7, 0.37, 328.0))
    assert_ok(r)
    assert len(r.hex) == 7 and r.hex.startswith("#")
    int(r.hex[1:], 16)  # parses as hex


def test_malformed_colour_is_invalid_color():
    assert_error(_h(color("srgb", 1, 2)), "INVALID_COLOR")
    assert_error(_h(Color()), "INVALID_COLOR")
