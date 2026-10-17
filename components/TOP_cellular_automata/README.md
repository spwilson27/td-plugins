# TOP_cellular_automata

A cellular automaton driven by an image. Bright pixels of `in1` seed live cells (and, with `Inject`, keep spawning new ones while the sim runs). The cells take the colours of the picture beneath them and are composited over the input. Without an input, a built-in animated demo image drives it.

Ping-pong (Feedback TOP + GLSL TOP) simulation on a float state texture (r = state, g = age, b = ghost fade). The grid is `Resolution / Cellsize`.

## Inputs
| In | Label | Notes |
|---|---|---|
| in1 | image | seeds and feeds the automaton (luminance vs `Threshold`) |
| in2 | modulation CHOP | optional, last input: `band1` scales `Inject` (x1..x3), `beat` adds a burst of cells |

## Outputs
| Out | Label |
|---|---|
| out1 | cells over input (Mix / Bypass applied) |
| out2 | raw cell state (r: 0/1 life, 0/1/2 brain, 0-3 wireworld; g: age; b: ghost) at grid resolution |

## Parameters
Controls: `Mix` (dry input vs result), `Bypass`, `Resolutionmode` (input|custom) + `Resolutionw/h`, `Rule` (Life / Brian's Brain / Wireworld / Larger than Life / Custom B/S), `Rulestring` (`B36/S23` or `23/3`), `Play`, `Rate`, `Stepsperframe`, `Reset` (restart: reseeds from the current input).

Input: `Threshold` (luminance that counts as a seed), `Invert` (seed from dark), `Density` (fraction of bright pixels that become cells at Reset; Wireworld: conductors fill the whole mask), `Inject` (per-step probability that bright input pixels spawn a cell; 0 = seed only), `Seed`.

Render: `Cellsize`, `Coloring` (input colours / by age / flat), `Backdrop` (how much of the input shows behind dead cells), `Vivid`, `Cellgap`, `Agerange`, `Ghost` and `Ghostdecay` (fading afterimage), Dead/Alive/Old/Aux colours (age and flat modes; Aux = Brian dying / Wireworld conductor).

Sim: `Radius` and birth/survive ranges for Larger than Life.

Wireworld: input mask = conductors with a few electron heads; Inject fires heads on conductors.

## Notes
The sim only reseeds on Reset or on first cook; after changing the input, press Reset. No Loop page: the demo animates with absTime and cooks only when `in1` is unconnected.
