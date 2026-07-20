from gen.axiom_context import AxiomContext
from gen.messages_pb2 import ConvertRequest, Color
from nodes._color import (
    ColorError,
    convert_native,
    normalise_space,
    read_color,
    to_error,
)


def convert(ax: AxiomContext, input: ConvertRequest) -> Color:
    """Convert a colour from one space to another — sRGB to CIE L*a*b*, HSL to
    Oklch, and any other pair among srgb/hsl/hsv/xyz/lab/lch/oklab/oklch —
    routing through CIE XYZ so every conversion is colorimetrically correct
    under the D65 white point.
    """
    try:
        space, native = read_color(input.color)
        target = normalise_space(input.to_space, "to_space", "INVALID_ARGUMENT")
        components = convert_native(space, native, target)
        return Color(space=target, components=components)
    except ColorError as exc:
        ax.log.info("convert rejected input", code=exc.code)
        return Color(error=to_error(exc))
    except Exception as exc:  # never surface a traceback to the caller
        ax.log.error("convert faulted", error=str(exc))
        return Color(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
