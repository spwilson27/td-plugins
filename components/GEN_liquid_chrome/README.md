# GEN_liquid_chrome
(Library name `GEN_liquid_chrome`, formerly `liquid_chrome`. Shipped as `tox/GEN/GEN_liquid_chrome.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | In TOP (optional) equirectangular environment map, procedural studio when unconnected |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: chrome blob (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.

Raymarched (GLSL TOP) metaball blob with noise-style displacement, slowly morphing, chrome shaded against a procedural studio environment (gradient sky, softbox strips, red accent) or an equirect env TOP on `in1`. Optional thin-film iridescence. 

| Param | Meaning |
|---|---|
| Blobs | number of metaballs (1-8) |
| Morphspeed | morph cycles per loop (integer; 0 freezes) |
| Displacement | amplitude of the periodic surface displacement |
| Roughness | blurs the environment reflection |
| Iridescence | thin-film rainbow amount on the reflection |
| Envrotation | rotates env (turns) |
| Camdistance / Camrotate / Camheight | camera orbit |
| Resolution | output size |

**Loop page** (all components): `Timesource` (`abstime` | `phase`), `Phase` (0-1), `Loopseconds`, `Loopbeats` (0 = use seconds, else beats at `Bpm`), `Bpm`. In `phase` mode, every motion is a function of `Phase` only; abstime mode just advances the same phase at 1/loop-duration.

**Loop seamlessness:** blob paths and displacement use only sin/cos of `2*pi*Phase*k` with integer k (Morphspeed scales k), so Phase 0 == 1 exactly.
