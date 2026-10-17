# GEN_lsystem
L-system / turtle growth. Strings are expanded in Python **only when parameters change** (Parameter Execute DAT -> `lsys_expand`), producing a segment table (`segs_a`, `segs_b`). Rendering is fully GPU: segments are instanced thin boxes whose scale/visibility come from float TOPs, so `Growth` just changes a uniform.
- Output `out1` (orthographic render). No inputs.
- **Controls**: Resolution, Active, Preset (plant, tree, bush, koch, dragon, custom), Growth (0-1), Animate + Growspeed (loops growth), Linewidth, Taper (per branch level), Zoom, Colora/Colorb (root/tip), Bgcolor.
- **Lsystem**: Axiom, Rule1-3 (`X=F+[X]-X` form), Iterations, Angle, Lengthscale (step multiplier applied at each `[`), Heading, Regenerate.
- Symbols: `F G A B 0 1` draw, `f` move, `+`/`-` turn, `|` reverse, `[` `]` push/pop. Selecting a preset overwrites the Lsystem page; choose `custom` to keep your own text.
- Growth order = distance from the root along the path (branches grow outward together). Capped at 16000 segments / 600k chars. Segment `info` DAT shows counts.

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |

**How the loop works:** Animate is now ON by default. In phase mode growth runs 0 -> 1 -> hold -> retract 1 -> 0 as one smooth cycle per loop, so frame 0 == frame 1.0 (empty). In abstime mode the original saw-ramp (Growspeed) is unchanged. Phase 0 vs 0.9999: 0.0000.

### Look page
`Look` = `Original` (default, unchanged) or `Mono` (black background, bone-white / grey, rendah style). `Accent` (0-1) adds red accents in Mono (tips and outer branches turn red).

## v2 update

Renamed from `lsystem` to `GEN_lsystem` (tox at `tox/GEN/GEN_lsystem.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: line width x(1+3b), beat: zoom pulse.

| Output | Label |
|---|---|
| out1 | render |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_lsystem.tox` (About > Snippets).
