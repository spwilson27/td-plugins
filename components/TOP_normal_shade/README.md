# TOP_normal_shade
Shade a normal map: either a **matcap** lookup (built-in matcap or your own image) or procedural **key / fill / rim lights** with specular and wrap lighting. Optionally multiplied by a colour/albedo image.

## Inputs / outputs
| Connector | Type | Use |
|---|---|---|
| in1 | In TOP | **view-space normals**, XYZ in RGB, -1..1 (+Z toward the camera). `Normalenc = packed` accepts 0..1 encoded normals. Zero-length normals = background. Unconnected: built-in G-buffer demo scene (Sphere/Torus/Box POPs, preview only) |
| in2 | In TOP | optional matcap image (sphere filling the frame; normal XY picks the pixel). Unconnected: built-in studio matcap |
| in3 | In TOP | optional colour / albedo, multiplied in (`Colormix`); also the background when `Background = in3 colour`. Unconnected: white |
| out1 | Out TOP | shaded image |

Normals come from e.g. a GLSL MAT writing `mat3(cameraMatrix) * worldNormal` to an extra Render TOP colour buffer (Render TOP `Num Color Buffers`, Render Select TOP), or from `SDF_render`'s normal output. No depth is needed.

## Parameters
| Name | Meaning |
|---|---|
| Mode | `matcap` or `lights` |
| Normalenc | signed (-1..1) / packed (0..1) |
| Colormix | how much in3 multiplies the shading |
| Brightness | output gain |
| Background | where normals are empty: transparent black, or the in3 colour |
| Matcaprotate, Matcapflip | orient the matcap lookup |
| Lights page | Keyazimuth, Keyelevation, Keyintensity, Keycolor; Fillintensity, Fillcolor (opposite side, low); Rimintensity, Rimcolor, Rimpower; Ambient; Specamount, Specpower; Wrap |
| Mix, Bypass, Resolutionmode, Resolution | standard TOP_ controls (Mix blends with the in1 normals) |


## Implementation
Native nodes (preview only, they do not cook when `in1` is connected):
- **demo** COMP: a bumpy height field (Circle and Rectangle TOPs, animated by absolute time, merged with a Composite TOP in `maximum` mode) goes through a **Normal Map TOP**; a Channel Mix TOP unpacks the result to -1..1 and a Threshold TOP mask zeroes the background (zero-length normals = empty).
- **defmatcap** COMP (used while `in2` is unconnected): the built-in studio matcap is painted from Circle TOPs (an off-centre soft disc for the clay body, a Level TOP shaped ring for the cool rim, a small disc for the specular) added together with a Composite TOP.
- `src`, `matcapsrc` and `colorsrc` are Switch TOPs between the inputs and those defaults.

GLSL kept: **`shade.glsl`**, one small pass doing the matcap lookup (normal XY to matcap UV with rotate / flip) and the key / fill / rim lighting with wrap and specular, plus the albedo tint, brightness and background. Why: a fully native version was built and measured (Remap TOP with the UVs made by a Channel Mix TOP for the matcap, Channel Mix dot products + Level TOP power curves + Composite for the lights, Math TOP length + Composite divide to normalise, Threshold TOP for the background). It works and looks the same, but needs 8 to 14 full-screen passes instead of 1, and every native pass has a fixed GPU cost that dwarfs this arithmetic: it benched +60 to +85 % GPU against the single GLSL pass, far over the 20 % budget. Even the leanest hybrid (Channel Mix UVs + Remap TOP + a tiny GLSL finish pass for background / tint / brightness) was about +40 % in the profile.

Bench (GPU, interleaved medians, noisy because other TouchDesigner instances were running): 720p 2.38 -> 2.24 ms (-6 %), 1080p 2.39 -> 2.46 ms (+3 %): same shader, noise only (native variant: +62 to +85 %)
