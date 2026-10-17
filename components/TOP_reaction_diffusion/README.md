# TOP_reaction_diffusion

Gray-Scott reaction-diffusion driven by an image. The input image seeds chemical B when the sim is reset, its
luminance shifts Feed/Kill per pixel (so the pattern changes character with the picture) and, optionally, bright
areas keep injecting B while the sim runs. `out1` is the input image stylised by the pattern, `out2` is the raw field.
32-bit float state (R = A, G = B), `Steps` solver iterations per frame (GLSL TOP Num Passes) around a Feedback TOP.

**Inputs**: `in1` image (unconnected: a built-in animated test image in the `demo` COMP, not cooked when connected);
`in2` modulation CHOP (last input, optional): `band1` Feed +0.01, `band2` Kill +0.004, `band3` Bump +50%, `beat` injection pulse. Other channels ignored.

**Outputs**: `out1` stylised image, `out2` A/B chemical field (rgba32float, R = A, G = B; at sim resolution).

| Page | Param | Notes |
|---|---|---|
| Controls | Mix, Bypass | dry/wet against the input; Bypass passes the input |
| | Resolutionmode, Resolution | follow in1 or custom (sim and output size). Reset after changing |
| | Preset | custom / coral / mitosis / labyrinth / spots / worms (sets Feed, Kill) |
| | Feed, Kill, Steps, Play, Reset | base rates, iterations per frame, freeze, re-seed |
| Drive | Feedmod, Killmod | how strongly luminance shifts Feed (+-0.03 x mod) and Kill (+-0.012 x mod) |
| | Inject | continuous injection of B where the image is brighter than Seedthreshold |
| | Seedamount, Seedthreshold, Invert | Reset seeding from the image; Invert lets dark areas drive |
| | Sprinkle | random blobs at Reset so flat images still grow a pattern |
| Render | Colormode | tint, multiply, emboss, pattern ramp, field (grey), warp (refracts the image) |
| | Strength, Contrast, Bump, Color1-4 | pattern strength, B gain, relief strength, 4-stop ramp |
| Sim | Diffa, Diffb, Dt, Seed | diffusion rates, time step (<= 1), random seed |

Tips: the interesting Feed/Kill band is thin; use presets, then Feedmod/Killmod. Bright image areas have higher feed, which kills the
pattern there; Invert flips that. Reset after changing Resolution.

## Using out2 (field)
- **Mask**: `out2` green = B (0 to ~0.4). Feed it to a GLSL TOP / Level / Reorder (`G` to alpha) and use it as a Matte or Composite mask.
  Snippet example 2 reveals a second picture only inside the pattern.
- **Displacement**: Displace TOP, `Horizontal source = red`, `Vertical source = green`, midpoint X = 1, midpoint Y = 0 (A is ~1, B ~0 at rest), then raise
  the weights. Snippet example 3.

Snippets: `snippets/TOP_reaction_diffusion.tox` (About > Snippets). Note: the `src` Switch gating the demo evaluates its index from the input connection.

## Implementation

### Preview source (demo)
The `demo` COMP used when `in1` is unconnected is built only from native operators, no GLSL: a horizontal Ramp TOP ground, four soft Circle TOP blobs and a pulsing Circle TOP ring, stacked by a Composite TOP. It sits behind the Switch, so it does not cook when an input is connected.

