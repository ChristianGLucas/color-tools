"""Shared colour-handling helpers for christiangeorgelucas/color-tools.

Everything that touches colour-science goes through here, so the input guards,
the human-unit scaling, the error vocabulary and the space-conversion routing
are defined exactly once.

WHAT THE LIBRARY OWNS vs. WHAT THIS FILE ADDS.
colour-science owns every algorithmically hard part: the sRGB opto-electronic
transfer function, the sRGB<->XYZ matrices, the CIE L*a*b* and Oklab transforms,
the LCh polar forms, and the CIEDE2000 / CIE94 / CMC colour-difference formulas.
This file adds only (a) input validation, (b) the scaling between the library's
internal 0..1 conventions and the human-facing units documented in the proto,
(c) routing conversions through the right hub (sRGB within the sRGB/HSL/HSV
family, CIE XYZ otherwise, bridging only on a cross-family conversion), and
(d) the WCAG 2.x contrast formula, which colour-science does not implement.

WHY THE GUARDS EXIST — each is a real property of the input surface:

  * An unset or edge-dropped ``Color`` arrives as ``{space: "", components: []}``.
    An empty space is refused, so a defaulted message can never be read as a
    valid black at the origin.
  * ``components`` must be exactly three finite numbers. A wrong count or a
    NaN/infinite value is refused BEFORE it reaches the library, which would
    otherwise broadcast or propagate it silently.
  * Conversions can, for extreme inputs, produce a non-finite component; that is
    refused on the way out as OVERFLOW rather than emitted as an answer.

There is essentially no cost surface here: every operation is fixed-size 3-vector
arithmetic, and the one iteration (nearest named colour) is over a fixed table.
"""

import math
import re
import warnings

# colour-science emits ColourUsageWarning when its OPTIONAL extras (scipy,
# matplotlib, networkx) are absent. This package uses none of them, so silence
# the warnings at import and on every call — they are not defects and must never
# reach a caller's logs.
warnings.filterwarnings("ignore", module="colour")

import numpy as np

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import colour
    from colour.notation import HEX_to_RGB


class ColorError(Exception):
    """A structured, caller-facing failure carrying an Error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# The eight supported spaces and the four that are rectangular (safe to
# interpolate in — no hue angle to wrap around).
SPACES = ("srgb", "hsl", "hsv", "xyz", "lab", "lch", "oklab", "oklch")
RECTANGULAR_SPACES = ("srgb", "xyz", "lab", "oklab")

# The colour-difference formulas exposed, mapped to colour-science's method
# names. Kept to a small, documented set rather than colour's full menu.
DELTA_E_METHODS = ("CIE 2000", "CIE 1976", "CIE 1994", "CMC")

# Per-space factor mapping the library's native component ranges to the
# human-facing units documented in the proto (native * factor = human):
#   srgb native 0..1  -> 0..255
#   hsl/hsv hue native 0..1 -> 0..360 ; sat/light/val 0..1 -> 0..100
#   lch/oklch hue is ALREADY in degrees from colour, so its factor is 1
#   xyz/lab/oklab are presented in the library's own units, factor 1
_SCALE = {
    "srgb": (255.0, 255.0, 255.0),
    "hsl": (360.0, 100.0, 100.0),
    "hsv": (360.0, 100.0, 100.0),
    "xyz": (1.0, 1.0, 1.0),
    "lab": (1.0, 1.0, 1.0),
    "lch": (1.0, 1.0, 1.0),
    "oklab": (1.0, 1.0, 1.0),
    "oklch": (1.0, 1.0, 1.0),
}

# WCAG 2.x contrast thresholds.
_WCAG = {"aa_normal": 4.5, "aa_large": 3.0, "aaa_normal": 7.0, "aaa_large": 4.5}

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def normalise_space(space: str, label: str, code: str) -> str:
    """Lower-case and validate a space name, or raise."""
    if not isinstance(space, str):
        raise ColorError(code, f"{label} must be a string")
    s = space.strip().lower()
    if not s:
        raise ColorError(
            code,
            f"{label} is empty; it must name a colour space "
            f"({', '.join(SPACES)}). An empty value is also what an unset field "
            f"looks like, so it is not treated as a colour",
        )
    if s not in SPACES:
        raise ColorError(
            code,
            f"{label} {space!r} is not a known colour space; use one of "
            f"{', '.join(SPACES)}",
        )
    return s


def _to_native(space: str, human) -> np.ndarray:
    """Human-unit components -> the library's native 0..1-ish array."""
    factors = _SCALE[space]
    return np.array([human[i] / factors[i] for i in range(3)], dtype=float)


def _from_native(space: str, native) -> list:
    """Library-native array -> human-unit components (plain floats)."""
    factors = _SCALE[space]
    return [float(native[i]) * factors[i] for i in range(3)]


def read_color(msg, label: str = "color"):
    """Validate a `Color` message and return (space, native_array).

    A Color that ALREADY CARRIES AN ERROR is refused and the upstream error is
    propagated unchanged — Color is both an input and an output type, so a
    failed upstream node's message must not be read as a valid colour here.
    """
    if msg.error.code:
        message = msg.error.message
        marker = "carries an error from an upstream node"
        if marker not in message:
            message = f"{label} {marker} and cannot be used as input: {message}"
        raise ColorError(msg.error.code, message)
    space = normalise_space(msg.space, f"{label}.space", "INVALID_COLOR")
    comps = list(msg.components)
    if len(comps) != 3:
        raise ColorError(
            "INVALID_COLOR",
            f"{label}.components has {len(comps)} value(s); a colour needs "
            f"exactly 3 (space {space!r} expects {_component_names(space)})",
        )
    for i, c in enumerate(comps):
        try:
            c = float(c)
        except (TypeError, ValueError):
            raise ColorError(
                "INVALID_COLOR", f"{label}.components[{i}] is not a number"
            )
        if not math.isfinite(c):
            raise ColorError(
                "INVALID_COLOR",
                f"{label}.components[{i}] must be finite, got {c}",
            )
        comps[i] = c
    return space, _to_native(space, comps)


def _component_names(space: str) -> str:
    return {
        "srgb": "[R, G, B]",
        "hsl": "[H, S, L]",
        "hsv": "[H, S, V]",
        "xyz": "[X, Y, Z]",
        "lab": "[L, a, b]",
        "lch": "[L, C, H]",
        "oklab": "[L, a, b]",
        "oklch": "[L, C, H]",
    }[space]


def _guard(fn, what: str):
    """Run a colour-science computation, mapping numeric blow-ups to ColorError."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return fn()
    except ColorError:
        raise
    except (OverflowError, ValueError, ZeroDivisionError, FloatingPointError) as exc:
        raise ColorError("INTERNAL", f"{what} failed numerically: {exc}")


# Two hubs, one per family, to avoid needless lossy round-trips. srgb/hsl/hsv
# interconvert through gamma-encoded sRGB directly; xyz/lab/lch/oklab/oklch
# interconvert through CIE XYZ. Only a CROSS-family conversion crosses the one
# bridge, sRGB<->XYZ. Routing srgb->hsl through XYZ (as a single universal hub
# would) forces an sRGB->XYZ->sRGB round-trip whose ~1e-3 error is visible in
# the result — so the families are kept separate on purpose.
_SRGB_FAMILY = frozenset({"srgb", "hsl", "hsv"})


def _srgb_family_to_srgb01(space: str, native: np.ndarray) -> np.ndarray:
    if space == "srgb":
        return np.asarray(native, dtype=float)
    if space == "hsl":
        return colour.HSL_to_RGB(native)
    if space == "hsv":
        return colour.HSV_to_RGB(native)
    raise ColorError("INTERNAL", f"{space!r} is not an sRGB-family space")


def _srgb01_to_srgb_family(space: str, srgb01: np.ndarray) -> np.ndarray:
    if space == "srgb":
        return np.asarray(srgb01, dtype=float)
    if space == "hsl":
        return colour.RGB_to_HSL(srgb01)
    if space == "hsv":
        return colour.RGB_to_HSV(srgb01)
    raise ColorError("INTERNAL", f"{space!r} is not an sRGB-family space")


def _xyz_family_to_xyz(space: str, native: np.ndarray) -> np.ndarray:
    if space == "xyz":
        return np.asarray(native, dtype=float)
    if space == "lab":
        return colour.Lab_to_XYZ(native)
    if space == "lch":
        return colour.Lab_to_XYZ(colour.LCHab_to_Lab(native))
    if space == "oklab":
        return colour.Oklab_to_XYZ(native)
    if space == "oklch":
        return colour.Oklab_to_XYZ(colour.Oklch_to_Oklab(native))
    raise ColorError("INTERNAL", f"{space!r} is not an XYZ-family space")


def _xyz_to_xyz_family(space: str, xyz: np.ndarray) -> np.ndarray:
    if space == "xyz":
        return np.asarray(xyz, dtype=float)
    if space == "lab":
        return colour.XYZ_to_Lab(xyz)
    if space == "lch":
        return colour.Lab_to_LCHab(colour.XYZ_to_Lab(xyz))
    if space == "oklab":
        return colour.XYZ_to_Oklab(xyz)
    if space == "oklch":
        return colour.Oklab_to_Oklch(colour.XYZ_to_Oklab(xyz))
    raise ColorError("INTERNAL", f"{space!r} is not an XYZ-family space")


def _get_srgb01(space: str, native: np.ndarray) -> np.ndarray:
    """The colour as gamma-encoded sRGB in 0..1, from any space."""
    if space in _SRGB_FAMILY:
        return _srgb_family_to_srgb01(space, native)
    return colour.XYZ_to_sRGB(_xyz_family_to_xyz(space, native))


def _get_xyz(space: str, native: np.ndarray) -> np.ndarray:
    """The colour as CIE XYZ, from any space."""
    if space in _SRGB_FAMILY:
        return colour.sRGB_to_XYZ(_srgb_family_to_srgb01(space, native))
    return _xyz_family_to_xyz(space, native)


def _check_finite(native: np.ndarray, what: str) -> np.ndarray:
    arr = np.asarray(native, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise ColorError(
            "OVERFLOW",
            f"{what} produced a non-finite component {list(arr)}; the input is "
            f"too extreme to represent in the target space",
        )
    return arr


def _convert_native_impl(space: str, native: np.ndarray, target: str) -> np.ndarray:
    # Identity: never round-trip a space to itself.
    if space == target:
        return np.asarray(native, dtype=float)
    if target in _SRGB_FAMILY:
        return _srgb01_to_srgb_family(target, _get_srgb01(space, native))
    return _xyz_to_xyz_family(target, _get_xyz(space, native))


def convert_native(space: str, native: np.ndarray, target: str) -> list:
    """Convert native components in `space` to human components in `target`."""
    out = _guard(lambda: _convert_native_impl(space, native, target), f"conversion to {target}")
    out = _check_finite(out, "the conversion")
    return _from_native(target, out)


def to_lab(space: str, native: np.ndarray) -> np.ndarray:
    """Native components -> CIE L*a*b* array (for colour-difference)."""
    lab = _guard(lambda: _xyz_to_xyz_family("lab", _get_xyz(space, native)), "conversion to Lab")
    return _check_finite(lab, "conversion to Lab")


def to_srgb01(space: str, native: np.ndarray) -> np.ndarray:
    """Native components -> gamma-encoded sRGB array in 0..1."""
    srgb = _guard(lambda: _get_srgb01(space, native), "conversion to sRGB")
    return _check_finite(srgb, "conversion to sRGB")


def delta_e(lab1: np.ndarray, lab2: np.ndarray, method: str) -> float:
    """CIEDE2000 (or the chosen formula) between two Lab colours."""
    value = _guard(
        lambda: float(colour.delta_E(lab1, lab2, method=method)),
        f"the {method} colour difference",
    )
    if not math.isfinite(value):
        raise ColorError("OVERFLOW", "the colour difference is not a finite number")
    return value


def normalise_method(method: str) -> str:
    """Validate a colour-difference method name, defaulting to CIE 2000."""
    if not method:
        return "CIE 2000"
    if not isinstance(method, str):
        raise ColorError("INVALID_ARGUMENT", "method must be a string")
    # Accept a couple of common spellings, canonicalised to colour's names.
    canon = {
        "cie 2000": "CIE 2000", "cie2000": "CIE 2000", "ciede2000": "CIE 2000",
        "cie 1976": "CIE 1976", "cie1976": "CIE 1976", "cie76": "CIE 1976",
        "cie 1994": "CIE 1994", "cie1994": "CIE 1994", "cie94": "CIE 1994",
        "cmc": "CMC",
    }.get(method.strip().lower())
    if canon is None:
        raise ColorError(
            "INVALID_ARGUMENT",
            f"method {method!r} is not supported; use one of "
            f"{', '.join(DELTA_E_METHODS)}",
        )
    return canon


def wcag_relative_luminance(srgb01: np.ndarray) -> float:
    """WCAG 2.x relative luminance of a gamma-encoded sRGB colour.

    Uses the exact WCAG linearisation (threshold 0.03928, exponent 2.4) rather
    than colour-science's sRGB decode, because WCAG conformance is defined
    against this specific piecewise formula. Channels are clamped to 0..1 first
    so an out-of-gamut colour still yields a defined luminance.
    """
    c = np.clip(np.asarray(srgb01, dtype=float), 0.0, 1.0)
    lin = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])


def contrast_ratio(lum_a: float, lum_b: float) -> float:
    """The WCAG contrast ratio between two relative luminances (order-free)."""
    hi, lo = (lum_a, lum_b) if lum_a >= lum_b else (lum_b, lum_a)
    return (hi + 0.05) / (lo + 0.05)


def wcag_flags(ratio: float) -> dict:
    """The four WCAG pass/fail flags for a contrast ratio."""
    return {
        "aa_normal": ratio >= _WCAG["aa_normal"],
        "aa_large": ratio >= _WCAG["aa_large"],
        "aaa_normal": ratio >= _WCAG["aaa_normal"],
        "aaa_large": ratio >= _WCAG["aaa_large"],
    }


def srgb01_to_hex(srgb01: np.ndarray) -> str:
    """Gamut-clamp a 0..1 sRGB colour and render it as "#rrggbb".

    Quantises with round-to-NEAREST, deliberately not colour-science's
    ``RGB_to_HEX``, which TRUNCATES: a round-tripped 0.9999996 would floor to
    254 (#fe) instead of the correct 255 (#ff). Rounding is the standard 8-bit
    quantisation and makes round trips land where a caller expects.
    """
    clamped = np.clip(np.asarray(srgb01, dtype=float), 0.0, 1.0)
    ints = [int(round(float(c) * 255.0)) for c in clamped]
    return "#{:02x}{:02x}{:02x}".format(*ints)


def parse_hex(hexstr: str) -> list:
    """Parse a #RGB / #RRGGBB string to human sRGB components [0..255]."""
    if not isinstance(hexstr, str):
        raise ColorError("INVALID_HEX", "hex must be a string")
    s = hexstr.strip()
    if not _HEX_RE.match(s):
        raise ColorError(
            "INVALID_HEX",
            f"{hexstr!r} is not a hex colour; write '#RGB' or '#RRGGBB' "
            f"(e.g. '#ff6347')",
        )
    digits = s.lstrip("#")
    # Expand CSS 3-digit shorthand ("#f00" -> "#ff0000") OURSELVES: the wrapped
    # library's HEX_to_RGB does NOT expand shorthand — it misreads "#f00" as
    # 0x0f rather than 0xff — so doing it here is a correctness fix, not a
    # convenience. Each digit is doubled, per the CSS spec.
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    s = "#" + digits
    rgb01 = _guard(lambda: HEX_to_RGB(s), "hex parsing")
    rgb01 = _check_finite(rgb01, "hex parsing")
    return _from_native("srgb", rgb01)


def lab_from_hex(hexstr: str) -> np.ndarray:
    """CIE L*a*b* of a #RRGGBB colour — used to precompute the named-colour table."""
    human = parse_hex(hexstr)
    native = _to_native("srgb", human)
    return to_lab("srgb", native)


def nearest_delta_e(lab, labs: np.ndarray, method: str = "CIE 2000") -> np.ndarray:
    """CIEDE2000 from one Lab colour to each row of an (N, 3) Lab array."""
    query = np.tile(np.asarray(lab, dtype=float), (labs.shape[0], 1))
    return _guard(
        lambda: np.asarray(colour.delta_E(query, labs, method=method), dtype=float),
        "the nearest-colour search",
    )


def to_error(exc: ColorError) -> dict:
    """Render a ColorError as an `Error` message kwargs dict."""
    return {"code": exc.code, "message": exc.message}
