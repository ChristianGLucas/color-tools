from gen.messages_pb2 import HexInput
from nodes.from_hex import from_hex
from nodes.testkit import assert_error, assert_ok, ax


def _h(s):
    return from_hex(ax(), HexInput(hex=s))


def test_six_digit_hex_parses_to_srgb():
    r = _h("#ff6347")
    assert_ok(r)
    assert r.space == "srgb"
    assert list(r.components) == [255.0, 99.0, 71.0]


def test_three_digit_hex_expands():
    r = _h("#f00")
    assert_ok(r)
    assert list(r.components) == [255.0, 0.0, 0.0]


def test_leading_hash_is_optional_and_case_insensitive():
    r = _h("00FF00")
    assert_ok(r)
    assert list(r.components) == [0.0, 255.0, 0.0]


def test_whitespace_is_tolerated():
    r = _h("  #808080  ")
    assert_ok(r)
    assert list(r.components) == [128.0, 128.0, 128.0]


def test_non_hex_is_rejected():
    for bad in ["", "#12", "#12345", "#gggggg", "rgb(1,2,3)", "#1234567"]:
        assert_error(_h(bad), "INVALID_HEX")
