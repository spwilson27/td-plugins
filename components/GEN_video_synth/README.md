# GEN_video_synth
(Library name `GEN_video_synth`, formerly `video_synth`. Shipped as `tox/GEN/GEN_video_synth.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | In TOP (optional) displaces coordinates and blends into the colour (Inputdisplace / Inputmix); black when unconnected |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: synth image (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.

LZX/Hydra-style oscillator patching generator. `in1` TOP is optional (displaces coordinates and can modulate colour via Inputdisplace/Inputmix). Output `out1`.

Chain: global rotate -> kaleid -> osc A -> (A displaces B) -> osc B -> (B displaces C) -> osc C -> blend -> contrast/gamma -> palette/colorize -> echo feedback.

| Param | Meaning |
|---|---|
| Mode | Custom or preset (Bone Waves, Chrome Moire, Red Kaleid, Acid Mod, Scanner, Tunnel). Choosing a preset writes the params below; tweak freely afterwards |
| Freq/Sync/Rot/Shape a,b,c | per-oscillator spatial freq, sync (integer cycles per loop, signed), rotation deg, sine/square/saw |
| Modulate | displacement strength between oscillators |
| Kaleid | mirror segments (0/1 = off) |
| Feedback, Echozoom, Echorot, Echospacing | 7-tap echo trail (screen-blended), zoom and rotation per tap, tap time spacing |
| Colorize, Palette, Hue | colour mix, palette (bone/chrome/red/rainbow/acid), hue offset |
| Contrast, Gamma, Scale, Rotspeed | look / global frequency scale / integer global rotation cycles per loop |
| Inputmix, Inputdisplace | in1 influence |

**Loop page** (all four): `Timesource` (abstime/phase), `Phase` (0-1), `Loopbeats` (default 8) with `Bpm` (120), or `Loopseconds` (>0 overrides beats). Internally one phase value P=fract(time/loop) (or `Phase`) drives everything.

**Seamless loop:** oscillator sync and rotspeed are integers (cycles per loop). "Feedback" is an analytic unrolled echo (the scene is re-evaluated at earlier phases) instead of a Feedback TOP, so it is exactly periodic and needs no Reset. A connected in1 is not periodic unless the input is.
