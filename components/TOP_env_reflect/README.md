# TOP_env_reflect
Chrome / glass reflections from a normal map and an equirectangular environment map: per-pixel view ray, reflection vector, Fresnel, roughness-blurred (mip) environment lookup, optional refraction of the colour behind.

## Inputs / outputs
| Connector | Type | Use |
|---|---|---|
| in1 | In TOP | colour image. Unconnected: built-in G-buffer demo scene (Sphere/Torus/Box POPs, preview only) |
| in2 | In TOP | **view-space normals**, XYZ in RGB, -1..1 (+Z toward the camera). `Normalenc = packed` accepts 0..1 encoded. Zero-length normals = no geometry, colour passes through unchanged |
| in3 | In TOP | environment map, **equirectangular** (lat-long, full 360x180). Unconnected: built-in studio / dusk environment |
| in4 | In TOP | optional mask / roughness map (R). Unconnected: white. Meaning set by `Maskmode` |
| out1 | Out TOP | reflective image |

Normals come from e.g. a GLSL MAT writing `mat3(cameraMatrix) * worldNormal` to a second Render TOP colour buffer (Render TOP `Num Color Buffers`, Render Select TOP), or from `SDF_render`'s normal output. Depth is not needed.

## Parameters
| Name | Meaning |
|---|---|
| Mode | `chrome` (reflection blended over the colour) or `glass` (refracted colour + reflection) |
| Reflectivity | reflection weight when Fresnel = 0 |
| Fresnel | 0 = constant Reflectivity, 1 = Schlick fresnel from `Ior` (edge-strong) |
| Roughness | blur of the environment (mip level); scaled by the mask in `Maskmode = roughness` |
| Ior | index of refraction for Fresnel and glass bend |
| Refraction | glass: screen-space offset of the colour behind the surface |
| Maskmode | in4 scales `roughness`, scales `reflectivity`, or `off` |
| Normalenc | signed / packed normals |
| Fov | vertical FOV (deg) of the camera for per-pixel view rays; 0 = orthographic |
| Look: Envrotate, Envtilt, Envgain, Tint | environment yaw / tilt (degrees), gain, reflection tint (glass: transmission tint) |
| Mix, Bypass, Resolutionmode, Resolution | standard TOP_ controls |

The demo uses the normals alpha as an "objects only" mask in in4 so the floor stays matte.
