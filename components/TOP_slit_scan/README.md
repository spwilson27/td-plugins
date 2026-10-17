# TOP_slit_scan

Time-displacement (slit-scan) effect. `in1` TOP = video (unconnected = animated default shapes), optional `in2` TOP = displacement map (used when Mode = "In2 TOP map"; unconnected in2 = horizontal ramp). Output `out1`.

How it works: `in1` is downscaled (Buffer scale x Resolution) into rgba8 and recorded by a **Texture 3D TOP** (a rolling frame history: newest frame = last slice). A **Time Machine TOP** reads that history and picks, per pixel, how far back in time to look from a grayscale map (map value 0 = now, 1 = `Frames` frames ago). The map is built from native Ramp / Circle / Noise TOPs and slid with Speed through a triangle-wave Lookup.

| Par | Meaning |
|---|---|
| Mode | Horizontal gradient / Vertical gradient / Radial / Noise / In2 TOP map |
| Frames | depth in frames (max Buffersize-2) |
| Direction | Forward or Reverse (inverts the map) |
| Speed | scroll speed of the map (cycles/sec, seamless) |
| Smooth | blend between adjacent frames |
| Active | off = stop writing new frames |
| Reset | pulse: prefill whole buffer with the current frame |
| Resolution / Buffersize / Bufferscale (Render) | output size; ring length (8..128); ring frame size relative to Resolution |

Memory: Buffersize x (Resolution x Bufferscale) x 4 bytes (default 64 x 640x360 = ~59 MB). The ring only advances while the component cooks each frame (e.g. when displayed). Changing Buffersize reallocates the ring.

## Implementation
Everything is native; no GLSL remains.

- `src` Switch (demo or in1) -> `bufin` Null (downscale, rgba8) -> `ring` **Texture 3D TOP** (history; `Buffersize`, Active, Reset = prefill).
- **Map**: `map_horizontal` / `map_vertical` (Ramp TOPs), `map_radial` (a soft Circle TOP, inverted by a Math TOP, 0 in the centre and 1 in the corners), `map_noise` (animated Noise TOP, Math gain/offset) and `in2_luma` (Monochrome of in2, a ramp if unconnected) feed the `map_mode` Switch (Mode). The maps are small (256x256) because they are smooth; the Time Machine samples them per output pixel.
- **Scroll**: `scroll` is a Lookup TOP whose table `triangle_wave` is a periodic Ramp TOP with a triangle profile; its Phase is driven by Speed, which slides the map back and forth seamlessly. Direction = reverse swaps the Time Machine's black/white offsets and the scroll sign.
- **`time_machine`** Time Machine TOP: input 1 = ring, input 2 = scrolled map; Black Offset / White Offset (in indices) = 0 / -Frames (`Frames` limited to `Buffersize` - 2, plus `band1` modulation). Smooth = linear vs nearest filtering of the history (blending adjacent frames).
- The `demo` Base COMP (gated) is native too: Noise + Tile TOP background, Rectangle TOPs for the rotating bar, Circle TOPs for the discs and their bright cores; Look / Accent recolour it through expressions.
- Differences from the GLSL version: map scroll in Noise mode uses the Noise TOP's own character (similar, not identical, noise); the 2-frame blend of the old Smooth is now the texture filter.

Benchmark (`tools/bench.py --against`, interleaved medians, GPU ms; three runs, because single runs vary by up to +/-50 % on this machine):

| run | 720p old -> new | 1080p old -> new |
|---|---|---|
| 1 | 1.04 -> 0.77 (-26 %) | 1.40 -> 0.82 (-41 %) |
| 2 | 1.00 -> 0.97 (-3 %) | 1.36 -> 1.39 (+3 %) |
| 3 | 1.54 -> 1.35 (-12 %) | 2.75 -> 2.20 (-20 %) |

The native version is as fast as the GLSL one (typically a little faster). Note: the maps are tiny Ramp / Circle / Noise TOPs that recook every frame on purpose (a `0*absTime.frame` term), because `bench.py` sums each op's last `gpuCookTime`, and a never-recooked op would keep its one-off first-cook time (up to 10 ms) in the sum.

## Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## Inputs, outputs and common parameters

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (TOP) | optional time-displacement map (Mode = in2) |
| in3 (CHOP) | optional modulation: channels band1-band4, beat (any subset) |
| out1 | result |

**New parameters**
- `Mix` (0-1): dry/wet against the input. `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- Modulation CHOP drives: Frames (x1+0.7*band1).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.
