# GEN_text_fluid
(Library name `GEN_text_fluid`, formerly `text_fluid`. Shipped as `tox/GEN/GEN_text_fluid.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| (none) | No inputs, self-contained generator (Text parameter sets the word) |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: tinted fluid-smeared text (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.


A `Text` mask is injected as dye (and, through its luminance gradient, as velocity) into an embedded copy of `GEN_fluid_2d` (`tox/GEN/GEN_fluid_2d.tox`) (loaded at build time, lives at `fluid`), so the letters smear, swirl and dissolve, then are re-injected periodically so they reform. Two internal emitters stir the field. Monochrome (tinted) output on black.

| Page | Param | Notes |
|---|---|---|
| Controls | Text, Fontsize (fraction of width), Fontname | the mask |
| | Play, Reset (pulse), Speed, Resolution | Reset clears the fluid and re-injects the text |
| | Inject, Push | dye amount / velocity coupling during injection |
| | Cycles, Injectfrac | re-injections per loop; fraction of each cycle that injects |
| | Smear, Emitters, Vorticity | stirring strength |
| | Dissipation, Exposure, Tint | look |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm | |

Loop: the injection envelope is a pure function of loop phase (`(p*Cycles) mod 1 < Injectfrac`), so letters always re-form at the same loop phase. The fluid itself is a stateful simulation and is NOT bitwise periodic; with dissipation the look at the injection moment repeats, the smear in between is only statistically similar. Use Cycles to retrigger as often as you like.
