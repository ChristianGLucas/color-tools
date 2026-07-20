from gen.axiom_context import AxiomContext
from gen.messages_pb2 import PairRequest, Difference
from nodes._color import (
    ColorError,
    delta_e as compute_delta_e,
    normalise_method,
    read_color,
    to_error,
    to_lab,
)


def delta_e(ax: AxiomContext, input: PairRequest) -> Difference:
    """Measure the perceptual difference (Delta E) between two colours, using
    CIEDE2000 by default (also CIE 1976, CIE 1994 and CMC). Both colours are
    converted to CIE L*a*b* first, so any two colours in any supported spaces
    can be compared — the number tells you how different they look, not just
    whether their coordinates differ.
    """
    try:
        method = normalise_method(input.method)
        space_a, native_a = read_color(input.a, "a")
        space_b, native_b = read_color(input.b, "b")
        lab_a = to_lab(space_a, native_a)
        lab_b = to_lab(space_b, native_b)
        value = compute_delta_e(lab_a, lab_b, method)
        return Difference(delta_e=value, method=method)
    except ColorError as exc:
        ax.log.info("delta_e rejected input", code=exc.code)
        return Difference(error=to_error(exc))
    except Exception as exc:
        ax.log.error("delta_e faulted", error=str(exc))
        return Difference(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
