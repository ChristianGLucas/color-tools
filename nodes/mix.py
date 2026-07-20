import math

from gen.axiom_context import AxiomContext
from gen.messages_pb2 import MixRequest, Color
from nodes._color import (
    ColorError,
    RECTANGULAR_SPACES,
    convert_native,
    normalise_space,
    read_color,
    to_error,
)


def mix(ax: AxiomContext, input: MixRequest) -> Color:
    """Blend two colours by a weight from 0 (all of the first) to 1 (all of the
    second), interpolating in a rectangular space — Oklab by default for a
    perceptually even blend, or srgb/xyz/lab. Cylindrical spaces are refused
    because interpolating a hue angle is ambiguous. The result is returned in
    the space it was mixed in.
    """
    try:
        raw = input.space.strip().lower() if input.space else ""
        space = normalise_space(raw or "oklab", "space", "INVALID_ARGUMENT")
        if space not in RECTANGULAR_SPACES:
            raise ColorError(
                "INVALID_ARGUMENT",
                f"cannot mix in the cylindrical space {space!r}; interpolating a "
                f"hue angle is ambiguous. Mix in a rectangular space instead: "
                f"{', '.join(RECTANGULAR_SPACES)}",
            )
        weight = input.weight
        try:
            weight = float(weight)
        except (TypeError, ValueError):
            raise ColorError("INVALID_ARGUMENT", "weight is not a number")
        if not math.isfinite(weight) or weight < 0.0 or weight > 1.0:
            raise ColorError(
                "INVALID_ARGUMENT",
                f"weight must be between 0 and 1, got {weight}",
            )
        space_a, native_a = read_color(input.a, "a")
        space_b, native_b = read_color(input.b, "b")
        ca = convert_native(space_a, native_a, space)
        cb = convert_native(space_b, native_b, space)
        mixed = [(1.0 - weight) * ca[i] + weight * cb[i] for i in range(3)]
        return Color(space=space, components=mixed)
    except ColorError as exc:
        ax.log.info("mix rejected input", code=exc.code)
        return Color(error=to_error(exc))
    except Exception as exc:
        ax.log.error("mix faulted", error=str(exc))
        return Color(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
