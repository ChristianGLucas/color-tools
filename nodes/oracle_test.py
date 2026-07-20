"""Independent-oracle tests.

These check the package against values computed INDEPENDENTLY of colour-science,
so they show correctness, not merely self-consistency:

  * The CIEDE2000 differences are the published reference values from Sharma,
    Wu & Dalal (2005), "The CIEDE2000 Color-Difference Formula: Implementation
    Notes, Supplementary Test Data, and Mathematical Observations" — the
    canonical conformance table every CIEDE2000 implementation is checked
    against. The expected numbers come from that paper, not from this library.

  * The WCAG contrast anchors are definitional (black-on-white is exactly 21:1)
    and a from-scratch scalar reimplementation of the WCAG 2.x formula, so the
    node's numpy/scaling integration is checked against an independent
    computation of the same specification.
"""

import math

from gen.messages_pb2 import ContrastRequest, PairRequest
from nodes.contrast import contrast
from nodes.delta_e import delta_e
from nodes.testkit import assert_ok, ax, close, color, srgb

# ── Sharma et al. (2005) CIEDE2000 supplementary test data ─────────────────
# (Lab1, Lab2, published Delta E 2000). A representative spread including the
# near-neutral and blue-region cases the formula is famously subtle on.
SHARMA_CIEDE2000 = [
    ((50.0000, 2.6772, -79.7751), (50.0000, 0.0000, -82.7485), 2.0425),
    ((50.0000, -1.3802, -84.2814), (50.0000, 0.0000, -82.7485), 1.0000),
    ((50.0000, 0.0000, 0.0000), (50.0000, -1.0000, 2.0000), 2.3669),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0009), 7.1792),
    ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
    ((2.0776, 0.0795, -1.1350), (0.9033, -0.0636, -0.5514), 0.9082),
]


def test_ciede2000_matches_the_sharma_reference_table():
    for lab1, lab2, expected in SHARMA_CIEDE2000:
        result = delta_e(
            ax(),
            PairRequest(a=color("lab", *lab1), b=color("lab", *lab2), method="CIE 2000"),
        )
        assert_ok(result)
        assert result.method == "CIE 2000"
        # Published to 4 decimals; the node's lab->XYZ->lab round-trip adds only
        # floating-point noise far below that.
        close(result.delta_e, expected, rel=0.0, abs_=1e-3)


def test_ciede2000_is_symmetric_like_the_reference_defines_it():
    lab1, lab2, expected = SHARMA_CIEDE2000[0]
    forward = delta_e(ax(), PairRequest(a=color("lab", *lab1), b=color("lab", *lab2)))
    reverse = delta_e(ax(), PairRequest(a=color("lab", *lab2), b=color("lab", *lab1)))
    assert_ok(forward)
    assert_ok(reverse)
    close(forward.delta_e, expected, rel=0.0, abs_=1e-3)
    close(reverse.delta_e, forward.delta_e, rel=0.0, abs_=1e-9)


# ── WCAG 2.x contrast, checked against an independent computation ───────────
def _wcag_luminance(rgb255):
    """A from-scratch scalar implementation of the WCAG relative-luminance
    formula — deliberately NOT the node's numpy version — used as the oracle."""
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(x) for x in rgb255)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _wcag_ratio(fg, bg):
    lf, lb = _wcag_luminance(fg), _wcag_luminance(bg)
    hi, lo = max(lf, lb), min(lf, lb)
    return (hi + 0.05) / (lo + 0.05)


def test_black_on_white_is_exactly_the_maximum_ratio():
    result = contrast(ax(), ContrastRequest(foreground=srgb(0, 0, 0), background=srgb(255, 255, 255)))
    assert_ok(result)
    close(result.ratio, 21.0, rel=0.0, abs_=1e-9)
    assert result.aa_normal and result.aa_large and result.aaa_normal and result.aaa_large


def test_contrast_matches_the_independent_wcag_computation():
    cases = [
        ((0, 0, 0), (255, 255, 255)),
        ((118, 118, 118), (255, 255, 255)),   # #767676 on white — a known AA boundary
        ((255, 255, 255), (0, 0, 255)),
        ((255, 99, 71), (0, 0, 0)),            # tomato on black
    ]
    for fg, bg in cases:
        result = contrast(ax(), ContrastRequest(foreground=srgb(*fg), background=srgb(*bg)))
        assert_ok(result)
        close(result.ratio, _wcag_ratio(fg, bg), rel=1e-9, abs_=1e-9)


def test_the_known_aa_boundary_colour_is_classified_correctly():
    # #767676 on white is the canonical "just passes AA normal" grey (~4.54:1).
    result = contrast(ax(), ContrastRequest(foreground=srgb(118, 118, 118), background=srgb(255, 255, 255)))
    assert_ok(result)
    assert result.ratio > 4.5 and result.ratio < 4.6
    assert result.aa_normal          # >= 4.5
    assert result.aa_large           # >= 3.0
    assert not result.aaa_normal     # < 7.0
