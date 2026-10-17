# GEN_lsystem
L-system / turtle trees as **line geometry**. The string is expanded in Python only when a parameter changes (a Script DAT `segs` re-cooks), giving one template tree (two points per segment). A GLSL POP animates growth, colour and line width on the GPU, and a Copy POP plants a copy of the tree at every planting point.

## Inputs
| Input | Label | Meaning |
|---|---|---|
| in1 (POP, optional) | planting points (POP) | A tree grows from each point (thinned to `Maxtrees`). Unconnected: one tree at the origin from the internal `demo` COMP. |
| in2 (CHOP, optional, last) | modulation CHOP | `band1` thickens lines, `beat` flashes growing tips. Other channels are ignored. |

## Outputs
| Output | Label |
|---|---|
| out1 | lines (POP): line primitives with `P`, `Color`, `LineWidth` |

No render output. The node viewer shows an internal `preview` TOP (Line MAT render of out1). Render out1 yourself with a Geometry COMP + **Line MAT** (it reads `LineWidth` and `Color`); see the snippets.

## Parameters
- **Controls**: Preview Resolution, Preset (plant, tree, bush, koch, dragon, custom), Growth (0-1), Animate Growth + Grow Speed (absTime saw: grows, holds, restarts), Tree Size, Max Trees, Variation (random spin about Y and size), Align To Normal (tilt trees along the `N` attribute of the points), Seed, Line Width (pixels with the Line MAT), Branch Taper, Root / Tip Color.
- **Lsystem**: Axiom, Rule 1-3 (`X=F+[X]-X`), Iterations, Angle, Branch Length Scale, Start Heading, Anchor (root at the planting point, or centered), Regenerate.
- **Preview**: camera distance, target height, field of view, background.
- **Look**: Original or Mono (bone-white and grey, optional red Accent on tips).

Symbols: `F G A B 0 1` draw, `f` move, `+`/`-` turn, `|` reverse, `[` `]` push/pop. A preset overwrites the Lsystem page; choose `custom` to keep your own text. Capped at 6000 segments per tree and 600k string characters. Trees live in the XY plane (Y up) and are spun about Y per tree.

Snippets: `snippets/GEN_lsystem.tox` (About > Snippets).
