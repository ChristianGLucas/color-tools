"""Hostile / malformed-input tests.

Every node must answer bad input with a structured error, never a raised
exception, and never a non-finite number presented as an answer.
"""

import math

from gen.messages_pb2 import (
    Color,
    ContrastRequest,
    ConvertRequest,
    HexInput,
    MixRequest,
    PairRequest,
)
from nodes.contrast import contrast
from nodes.convert import convert
from nodes.delta_e import delta_e
from nodes.describe import describe
from nodes.from_hex import from_hex
from nodes.mix import mix
from nodes.nearest_name import nearest_name
from nodes.to_hex import to_hex
from nodes.testkit import assert_error, ax, color, srgb

INF = float("inf")
NAN = float("nan")


def test_non_finite_components_are_rejected_everywhere():
    bad = color("srgb", NAN, 0.0, 0.0)
    inf = color("srgb", INF, 0.0, 0.0)
    assert_error(convert(ax(), ConvertRequest(color=bad, to_space="lab")), "INVALID_COLOR")
    assert_error(convert(ax(), ConvertRequest(color=inf, to_space="lab")), "INVALID_COLOR")
    assert_error(to_hex(ax(), bad), "INVALID_COLOR")
    assert_error(describe(ax(), bad), "INVALID_COLOR")
    assert_error(nearest_name(ax(), bad), "INVALID_COLOR")
    assert_error(delta_e(ax(), PairRequest(a=bad, b=srgb(1, 2, 3))), "INVALID_COLOR")
    assert_error(
        contrast(ax(), ContrastRequest(foreground=bad, background=srgb(1, 2, 3))),
        "INVALID_COLOR",
    )
    assert_error(mix(ax(), MixRequest(a=bad, b=srgb(1, 2, 3), weight=0.5)), "INVALID_COLOR")


def test_no_node_raises_on_a_pile_of_garbage_inputs():
    garbage_colors = [
        Color(),
        color(""),
        color("srgb"),
        color("srgb", 1.0),
        color("srgb", 1, 2, 3, 4),
        color("nope", 1, 2, 3),
        color("srgb", NAN, NAN, NAN),
        color("lab", INF, -INF, 0.0),
        color("oklch", 1e300, 1e300, 1e300),
    ]
    for c in garbage_colors:
        # Each single-Color node must return a message with an error set, no raise.
        assert convert(ax(), ConvertRequest(color=c, to_space="lab")).error.code
        assert to_hex(ax(), c).error.code
        assert describe(ax(), c).error.code
        assert nearest_name(ax(), c).error.code


def test_extreme_values_never_yield_a_non_finite_answer():
    # A wildly out-of-range colour must be either rejected or clamped — never
    # returned with a NaN/inf component.
    r = convert(ax(), ConvertRequest(color=color("xyz", 1e200, 1e200, 1e200), to_space="srgb"))
    if not r.error.code:
        for c in r.components:
            assert math.isfinite(c)


def test_hex_garbage_is_rejected_without_raising():
    for bad in ["", "zzz", "#", "#12", "############", "0xffffff", "#ff 00 00"]:
        assert_error(from_hex(ax(), HexInput(hex=bad)), "INVALID_HEX")


def test_hue_wraparound_values_are_accepted():
    # H just above 360 is still a valid angle; the node must not reject or crash.
    r = convert(ax(), ConvertRequest(color=color("hsl", 720.0, 100.0, 50.0), to_space="srgb"))
    assert not r.error.code
    for c in r.components:
        assert math.isfinite(c)
