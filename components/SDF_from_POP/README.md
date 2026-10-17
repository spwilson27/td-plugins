# SDF_from_POP

Turns POP geometry into an SDF that plugs into the chain like any primitive, e.g. `POP_boids -> SDF_from_POP -> SDF_combine (with SDF_gyroid) -> SDF_render`.

Two modes (**Mode**):

| Mode | What it does | Cost | Exactness |
|---|---|---|---|
| **points** | Every input point is a sphere (metaball). The field is the smooth union of all spheres, `|p - P_i| - r_i`, looked up through a uniform grid that is rebuilt on the GPU every frame. | live, a few ms per frame for 100k points | exact (sphere union) |
| **mesh** | The input triangles are voxelized into a 3D signed-distance texture (narrow band + ray parity) which the SDF samples with trilinear filtering. | 2-7 ms for a full bake, once or every frame | lossy: resolution-limited, needs a closed (watertight) mesh |

Wire format: see the SDF section of `CONVENTIONS.md`. This node is the first one to use the `@tex` record: it hands the point buffers / the baked volume to the consumer as extra buffers and samplers, so moving points or an animated mesh never recompile any shader.

## Inputs
- **in1** points / mesh (POP). Unconnected: a built-in demo (a bumpy animated blob of 640 points, or a torus) in the gated `demo` Base COMP.
- **in2** optional modulation CHOP (last input): `band1` adds up to 2x to Blend (points), `beat` pulses the sphere Radius by up to 60 % (points).

## Outputs
- **out1** SDF (DAT), including all upstream SDF nodes (none here: this is a primitive).
- The node viewer shows an internal `preview` TOP (orbiting raymarch of the node's own SDF).

## Parameters
- **Mode**: points or mesh.
- Points page: **Radius** (world units; times the `PointScale` attribute when **Use PointScale** is on and the points have it), **Blend** (smooth-union K; 0 = hard union), **Use Color Attribute** (per-point `Color` attribute if present, else the Color parameter), **Max Points** (only the first N points are used), **Grid Resolution** (cells per side of the acceleration grid) and **Cell Capacity** (points kept per cell).
- Mesh page: **Resolution** (32 - 256 voxels per side), **Bounds** (auto: a cube around the mesh bounding box plus **Padding**, or manual center/size), **Narrow Band** (voxels with exact distance on each side of the surface), **Update** (menu below), **Bake Now**.
- **Color**: fallback colour of points without a Color attribute, and the colour of a baked mesh.
- **Preview Framing Scale**: zoom of the node-viewer preview (the camera sits at 3 world units times this).

### Update (mesh)
- **Once**: the input mesh is captured on load, on **Bake Now**, when the input wiring changes or when Mode / Update change. After that the mesh is frozen (a locked POP, so the input network stops cooking) and only Resolution, Padding, Bounds and Band re-bake that copy. Use it for static meshes or to stop an animated input.
- **Every frame**: bake the live input every frame (the input is pulled by the renderer anyway).
- A locked frozen copy is stored in a saved .toe (point data only, a few hundred KB).

## Using it
- Points: choose Radius and Blend relative to the point spacing (radius about the spacing, blend about half). Rays only test the points listed in their grid cell, so the cost depends on how many spheres reach a cell, not on the total. If you see holes or flicker in dense clouds, raise **Cell Capacity** or **Grid Resolution**.
- Mesh: feed closed triangle or quad meshes (Torus, Box, Sphere, Tube POPs, a File In POP with a closed model). The sign comes from ray parity along +Z, so open surfaces, self-intersections and inverted/duplicated shells give wrong inside/outside. Polygons with more than four vertices must go through a Triangulate POP first.
- Outside the volume the field is the distance to the volume box plus the edge value, so rays always converge; objects bigger than the bounds are clipped to them (give manual bounds a margin).
- Combine, transform, repeat and deform nodes forward the `@tex` records, so `SDF_from_POP -> SDF_repeat` (infinite grid), `-> SDF_to_MAT`, `-> SDF_to_TOP / SDF_to_POP` all work with both modes.

## Implementation
Native-first: the network is native POPs (Switch, Convert, Facet, Point Generator) plus Parameter/OP Execute DATs; GLSL is used only for the parts that have no native operator. A probe of the build's operator types for sdf / volume / distance / voxel found only the opposite direction (Polygonize POP: volume to mesh), analytic Field POP shapes and Texture 3D TOP (stacking 2D slices). Neighbor/Proximity POPs give per-point neighbour lists, but not a lookup at arbitrary ray positions, and no operator turns a mesh into a distance volume. So this is a "mathy" exception to the native-first rule:
- `pack` (GLSL POP): packs P, radius and colour of every point into one attribute buffer (variants selected by the attributes the input has).
- `grid` (GLSL POP, 3 passes): atomic bounds reduction, bounds finalize, then each point is appended to the cells its sphere of influence (radius + blend + half a cell) touches (`cell[c] = count, indices...`). Threads follow the points, so it is O(N).
- `vox` (GLSL POP, 3 passes): bounds reduction, then per triangle an atomic min of the exact point-to-triangle distance on the voxels within the narrow band, and an atomic xor of the ray-parity bit where the +Z ray through each voxel column enters the mesh. Data lives on a column POP (resolution^2 points, a `dist` array and a `par` bit mask each), so 256^3 needs 65k points, not 16M.
- `bake` (GLSL TOP, compute, 3D): turns those columns into the signed-distance texture (distance / band width in fp16, colour in GBA). A compute pass, because a 3D pixel shader only binds POP buffers on some slices (measured: random whole slices came out empty).
- `mbnd` (GLSL TOP, 2x1): the volume bounds as a texture, so the wire only references TOPs for meshes.
- The sdf node (Script DAT) writes the wire with `@tex` records: points = 3 buffers (`pts`, `cell`, `bnd`), mesh = a 2D bounds texture and the 3D volume. The shader code is `node_points.glsl` / `node_mesh.glsl`.
- Smooth union of the spheres in reach: `m` = the smallest distance, `S = sum (1 - (d_i - m)/k)^2` over spheres within k of it, `f = m - (k/4) * g(S - 1)` with `g(x) = x / (1 + x/4)`. For two spheres that is exactly the polynomial smooth minimum; it does not depend on the order of the points (the atomic scatter order is random), has compact support, and saturates at k below the nearest sphere. Colours are blended with the same weights.
- Cells with no sphere in reach return half a cell as a safe lower bound; outside the grid the distance to its box is returned, so the march always converges.

## Performance (Apple GPU, shared with other work, 1280x720 SDF_render with default shadows + AO)
Points (volume-filled cloud, sphere radius about the point spacing, grid 32-64, capacity 48, points moving every frame so the grid is rebuilt every frame):

| points | render | grid build | frame rate |
|---|---|---|---|
| 1 000 (no shadow / AO) | 4.1 ms | negligible | 60 |
| 20 000 | 7.8 ms | negligible | 60 |
| 100 000 | 11.0 ms | about 1 ms or less | about 55 - 60 |
| 1 000 000 (no shadow / AO) | 10.3 ms | about 1 ms or less | about 42 |

So the point count stays real-time (>= 55 fps) up to about 100 000 points with full shading and about 500 000 without shadows / AO. The time is bounded by the grid (rays test at most Cell Capacity spheres per step), so what limits you is quality: when more than Cell Capacity spheres reach one cell the extras are dropped. Keep radius + blend about the point spacing.

Mesh (whole chain from touching the input to the finished volume, GPU-synchronised, median of 12):

| triangles | 32 | 64 | 96 | 128 | 192 | 256 (resolution) |
|---|---|---|---|---|---|---|
| 4 096 | 1.5 ms | 1.6 | 1.8 | 3.0 | 2.8 | 4.2 |
| 40 000 | 7.1 | 5.8 | 4.6 | 4.6 | 5.6 | 6.8 |

Accuracy at resolution 96 (torus, 4 096 triangles): mean error 0.05 voxel, max 0.1 voxel against the analytic distance, inside the band. The volume costs resolution^3 x 8 bytes (fp16 RGBA): 134 MB at 256.

SDF_render itself is not slowed by the `@tex` plumbing (about +3 % on a sphere + torus + deform scene, inside the +-10 % noise of the benchmark).

## Limitations
- Points mode: dense clusters beyond **Cell Capacity** drop spheres (flicker / holes); spheres much larger than the grid cells list in many cells (slower build). One radius scale per cloud (plus PointScale).
- Mesh mode: closed triangle/quad meshes only (see above); lossy at the chosen resolution; thin features below a voxel disappear; bounds are a cube in auto mode.
- A scene can reference at most 6 buffer, 3 2D and 3 3D records (two SDF_from_POP nodes in one scene is fine, three meshes are not). The SDF wire carries absolute operator paths; renaming or moving the component re-writes it.
- Colour of a baked mesh is one constant (no vertex colours).
