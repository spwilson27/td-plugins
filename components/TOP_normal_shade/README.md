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
