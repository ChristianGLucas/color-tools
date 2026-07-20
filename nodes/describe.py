from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Color, Description
from nodes._color import (
    ColorError,
    contrast_ratio,
    convert_native,
    read_color,
    srgb01_to_hex,
    to_error,
    to_srgb01,
    wcag_relative_luminance,
)


def describe(ax: AxiomContext, input: Color) -> Description:
    """Summarise a colour across the representations agents most often need at
    once: its hex, its sRGB / HSL / Oklch components, its WCAG relative
    luminance, and whether it is dark enough to want white text on it. One call
    instead of several conversions.
    """
    try:
        space, native = read_color(input)
        srgb = convert_native(space, native, "srgb")
        hsl = convert_native(space, native, "hsl")
        oklch = convert_native(space, native, "oklch")
        srgb01 = to_srgb01(space, native)
        luminance = wcag_relative_luminance(srgb01)
        # "Dark" = white text reads better on it than black text does. Contrast
        # against white uses luminance 1.0; against black, 0.0.
        contrast_white = contrast_ratio(luminance, 1.0)
        contrast_black = contrast_ratio(luminance, 0.0)
        is_dark = contrast_white > contrast_black
        return Description(
            hex=srgb01_to_hex(srgb01),
            srgb=srgb,
            hsl=hsl,
            oklch=oklch,
            relative_luminance=luminance,
            is_dark=is_dark,
        )
    except ColorError as exc:
        ax.log.info("describe rejected input", code=exc.code)
        return Description(error=to_error(exc))
    except Exception as exc:
        ax.log.error("describe faulted", error=str(exc))
        return Description(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
