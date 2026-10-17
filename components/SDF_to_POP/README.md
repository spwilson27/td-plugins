# SDF_to_POP

Polygonizes an SDF wire into a mesh POP (lossy; marching cubes on a baked 3D texture with the Polygonize POP).

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- **in1** SDF (DAT) (unconnected: a built-in sphere).

## Outputs
- **out1** mesh (POP), positions in the Bounds space, with normals.

## Parameters
- **Resolution** voxels per side, **Bounds Center / Size**, **Inflate** (iso offset: positive grows the mesh), **Normals** (None, smooth gradient, flat surface).
- Colour is not carried to the mesh. Surfaces clipped by the bounds are open.
- The bake is a compute dispatch, so scenes with texture / buffer references (`SDF_from_POP`) convert correctly too.
