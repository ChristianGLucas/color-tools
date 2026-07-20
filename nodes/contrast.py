from gen.axiom_context import AxiomContext
from gen.messages_pb2 import ContrastRequest, Contrast
from nodes._color import (
    ColorError,
    contrast_ratio,
    read_color,
    to_error,
    to_srgb01,
    wcag_flags,
    wcag_relative_luminance,
)


def contrast(ax: AxiomContext, input: ContrastRequest) -> Contrast:
    """Compute the WCAG 2.x contrast ratio between a foreground and background
    colour (1.0 to 21.0) and report whether it meets the AA and AAA thresholds
    for normal and large text. Colours in any supported space are reduced to
    sRGB and linearised with the exact WCAG luminance formula, so the answer is
    the one an accessibility audit expects.
    """
    try:
        fg_space, fg_native = read_color(input.foreground, "foreground")
        bg_space, bg_native = read_color(input.background, "background")
        lum_fg = wcag_relative_luminance(to_srgb01(fg_space, fg_native))
        lum_bg = wcag_relative_luminance(to_srgb01(bg_space, bg_native))
        ratio = contrast_ratio(lum_fg, lum_bg)
        return Contrast(ratio=ratio, **wcag_flags(ratio))
    except ColorError as exc:
        ax.log.info("contrast rejected input", code=exc.code)
        return Contrast(error=to_error(exc))
    except Exception as exc:
        ax.log.error("contrast faulted", error=str(exc))
        return Contrast(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
