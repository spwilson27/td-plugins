# SDF_to_TOP

Bakes an SDF wire into a 3D texture TOP (lossy).

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- **in1** SDF (DAT) (unconnected: a built-in sphere).

## Outputs
- **out1** 3D TOP (Resolution^3): R = signed distance in world units, GBA = albedo. Sample it from a GLSL TOP with `sTD3DInputs`.

## Parameters
- **Resolution** voxels per side, **Bounds Center / Size** world-space box that is baked (outside the box the field is not defined), **Precision** 16 or 32-bit float.
- Preview: a raymarch of the baked volume itself, so you see what the texture holds.
- The bake is a compute dispatch, so scenes with texture / buffer references (`SDF_from_POP`) bake correctly too.
