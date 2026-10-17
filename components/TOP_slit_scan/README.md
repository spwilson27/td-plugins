# TOP_slit_scan

Time-displacement (slit-scan) effect. `in1` TOP = video (unconnected = animated default shapes), optional `in2` TOP = displacement map (used when Mode = "In2 TOP map"; unconnected in2 = horizontal ramp). Output `out1`.

How it works: `in1` is downscaled (Buffer scale, default 0.5 x Resolution) into rgba8 and written by a **Texture 3D TOP** into slice `absTime.frame % Buffersize` (Replace-Single mode driven by expression = a deterministic ring buffer, so the shader knows exactly which slice is which age). The GLSL TOP builds a map value d in [0,1] per pixel, scrolls it with a triangle wave (Speed), and samples the frame `d * Frames` frames ago (optionally blended between adjacent frames).

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
