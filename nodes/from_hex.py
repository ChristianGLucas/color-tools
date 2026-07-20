from gen.axiom_context import AxiomContext
from gen.messages_pb2 import HexInput, Color
from nodes._color import ColorError, parse_hex, to_error


def from_hex(ax: AxiomContext, input: HexInput) -> Color:
    """Parse a CSS hex colour ("#RGB" or "#RRGGBB") into an sRGB colour with
    components in 0..255, ready to feed into any other node. Malformed hex is
    rejected with a structured error rather than guessed at.
    """
    try:
        components = parse_hex(input.hex)
        return Color(space="srgb", components=components)
    except ColorError as exc:
        ax.log.info("from_hex rejected input", code=exc.code)
        return Color(error=to_error(exc))
    except Exception as exc:
        ax.log.error("from_hex faulted", error=str(exc))
        return Color(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
