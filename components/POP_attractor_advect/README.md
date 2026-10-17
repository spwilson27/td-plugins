# POP_attractor_advect

Advects the input points along a strange-attractor vector field (Lorenz, Aizawa, Thomas, Halvorsen, Dadras). The points flow from wherever they start onto the attractor. Output is a POP, optionally as trail polylines.

Technique: a Feedback POP holds the advected points. Every frame a GLSL POP maps each point into normalised attractor space (`q = (P - Center) / Field Size`), integrates it (RK2, `Substeps` per frame) and maps it back. Points that diverge, or are re-seeded by `Rebirth`, jump back to their source position. `Reset` re-captures in1, and a `Preroll` pre-advances the flow when the state is (re)initialised. Because the state is kept, an animated in1 only feeds new positions through `Rebirth`/`Reset`.

## Inputs
| Connector | Label | Notes |
|---|---|---|
| in1 | points (POP) | points or mesh to advect (all attributes kept; `Color` is overwritten by the speed ramp when Color Mix > 0). With nothing connected, a gated `demo` (Sphere or Box scatter) is used. |
| in2 | modulation CHOP | optional: `band1` (coef wobble), `band2` (speed), `beat` (speed kick). `band3`/`band4` are unused. |

## Outputs
| Connector | Label | Notes |
|---|---|---|
| out1 | advected points (POP) | advected points, or trail polylines when Trails is on. |

The node viewer shows an internal `preview` TOP (additive point/line render with a slow orbit camera; not an output). Render out1 yourself, e.g. a Geometry COMP with a Select POP and a Point Sprite MAT (points) or Constant MAT with Apply Point Color (trail lines).

## Parameters
- **Controls**: Attractor A / B, Morph (share of points following B), Speed, Play, Reset, Field Size, Center XYZ, Coef Animate / Coef Rate (wobbles the attractor coefficients), Substeps, Rebirth, Seed, Preroll.
- **Trails**: Trails toggle (out1 becomes polylines), Trail Length (seconds of history).
- **Demo**: demo shape (sphere/box) and number of points, used only with in1 unconnected.
- **Look**: Color Mix, Color Slow, Color Fast, Color Speed Scale (colors the `Color` attribute by speed), Preview Point Size.

There is no Loop page; time only animates the coefficient wobble and the preview camera.
