import numpy as np

from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Color, NamedColor
from nodes._color import (
    ColorError,
    lab_from_hex,
    nearest_delta_e,
    read_color,
    to_error,
    to_lab,
)
from nodes._names import CSS_NAMED_COLORS

# Precompute the named colours' Lab coordinates once, at import. The table is
# fixed data, so this never changes between invocations and keeps each call to
# a single vectorised CIEDE2000 pass over ~150 rows.
_NAMES = list(CSS_NAMED_COLORS.keys())
_HEXES = [CSS_NAMED_COLORS[n] for n in _NAMES]
_LABS = np.array([lab_from_hex(h) for h in _HEXES], dtype=float)


def nearest_name(ax: AxiomContext, input: Color) -> NamedColor:
    """Find the nearest CSS named colour to a given colour, by CIEDE2000
    distance in CIE L*a*b* — turning an arbitrary colour into a human-readable
    name like "tomato" plus how close that name is. An exact CSS colour returns
    its own name with a difference of 0.
    """
    try:
        space, native = read_color(input)
        lab = to_lab(space, native)
        distances = nearest_delta_e(lab, _LABS)
        idx = int(np.argmin(distances))
        return NamedColor(
            name=_NAMES[idx],
            hex=_HEXES[idx],
            delta_e=float(distances[idx]),
        )
    except ColorError as exc:
        ax.log.info("nearest_name rejected input", code=exc.code)
        return NamedColor(error=to_error(exc))
    except Exception as exc:
        ax.log.error("nearest_name faulted", error=str(exc))
        return NamedColor(
            error={
                "code": "INTERNAL",
                "message": (
                    f"the node faulted while handling this input "
                    f"({type(exc).__name__}); the input may be valid"
                ),
            }
        )
