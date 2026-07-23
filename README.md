# color-tools

Composable colour-science nodes for the [Axiom](https://axiomide.com) marketplace,
published under the `christiangeorgelucas` handle. Every node consumes and/or
emits a single `Color` envelope — a point in a named colour space — so colours
flow cleanly from one node into the next.

Built for the Axiom marketplace. Fully offline and deterministic, wrapping the
BSD-3-Clause [colour-science](https://www.colour-science.org/) library, which
owns the algorithmically hard parts: the sRGB transfer function, the XYZ
matrices, the CIE L\*a\*b\*/Oklab transforms, and the CIEDE2000 colour
difference.

## The `Color` envelope

A colour is a space name plus three components, written in human-facing units:

| space   | components   | units                                        |
|---------|--------------|----------------------------------------------|
| `srgb`  | `[R, G, B]`  | each 0–255                                    |
| `hsl`   | `[H, S, L]`  | H 0–360, S,L 0–100                            |
| `hsv`   | `[H, S, V]`  | H 0–360, S,V 0–100                            |
| `xyz`   | `[X, Y, Z]`  | CIE 1931, ~0–1, Y=1 for reference white       |
| `lab`   | `[L, a, b]`  | CIE L\*a\*b\*, L 0–100                         |
| `lch`   | `[L, C, H]`  | CIE LCh(ab), H in degrees                     |
| `oklab` | `[L, a, b]`  | Oklab, L 0–1                                  |
| `oklch` | `[L, C, H]`  | Oklch, L 0–1, H in degrees                    |

Colorimetry uses the CIE 1931 2° standard observer and the D65 white point,
which is what sRGB is defined against.

## Nodes

- **Convert** — convert a colour between any two supported spaces.
- **DeltaE** — perceptual difference (Delta E) between two colours: CIEDE2000
  (default), CIE 1976, CIE 1994, CMC.
- **Contrast** — WCAG 2.x contrast ratio (1–21) plus AA/AAA pass flags for
  normal and large text.
- **FromHex** — parse `#RGB` / `#RRGGBB` into an sRGB colour.
- **ToHex** — render any colour as `#rrggbb` (gamut-clamped).
- **Mix** — blend two colours by weight in a rectangular space (Oklab by
  default for a perceptually even blend).
- **Describe** — one-shot summary: hex, sRGB, HSL, Oklch, WCAG luminance, and
  whether the colour wants white text.
- **NearestName** — the nearest CSS named colour, by CIEDE2000 distance.

Every node returns a structured `error` (never a crash) for malformed input,
and correctness is checked against the published Sharma et al. (2005) CIEDE2000
reference table and the WCAG contrast specification.

## License

MIT © 2026 Christian George Lucas. The wrapped `colour-science` and `numpy`
libraries are BSD-3-Clause.
