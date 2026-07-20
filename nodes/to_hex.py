from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Color, HexResult
from nodes._color import ColorError, read_color, srgb01_to_hex, to_error, to_srgb01


def to_hex(ax: AxiomContext, input: Color) -> HexResult:
    """Render any colour as a "#rrggbb" hex string. The colour is converted to
    sRGB and clamped into the displayable gamut, so even an out-of-gamut Lab or
    Oklch colour yields a valid, usable hex value.
    """
    try:
        space, native = read_color(input)
        srgb01 = to_srgb01(space, native)
        return HexResult(hex=srgb01_to_hex(srgb01))
    except ColorError as exc:
        ax.log.info("to_hex rejected input", code=exc.code)
        return HexResult(error=to_error(exc))
    except Exception as exc:
        ax.log.error("to_hex faulted", error=str(exc))
        return HexResult(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
