# POP_cloth
GPU Verlet cloth for any polygon mesh. POP in -> POP out filter: the input mesh is simulated as cloth and `out1` is the deformed mesh (original attributes such as `Tex`/`Color` kept, normals recomputed).

## How it works
1. `neighbors` (Neighbor POP, *Connected*) stores each point's edge neighbours (`Nebr`, `NumNebrs`), so **any topology** works (grids, spheres, imported meshes).
2. `pin_attr` / `pin_group` / `init` build the state attributes `RestP`, `PrevP` and `Pin` (pinned = 1).
3. A Feedback POP loop (`fb` -> `integrate` -> `constraints` -> `sim`): `integrate` is a Verlet step (gravity, noise-modulated wind, damping, sphere collision; pinned points follow the live input mesh), `constraints` is a Jacobi relaxation of every edge's rest length run `Iterations` times (GLSL POP Passes).
4. `normals` + `cleanup` -> `out1`.
An internal `preview` TOP (checker cloth + sphere) feeds the node viewer; it is not an output.

## Inputs / outputs
| | |
|---|---|
| in1 (POP) | mesh to simulate. Not connected: a demo Grid POP (inside the `demo` COMP, switched off when in1 is connected) |
| in2 (CHOP) | optional modulation, last input: `band1` + `beat` scale Wind, `band2` adds Turbulence, `band3` lifts against Gravity; `Modgain` scales all (`band4` unused) |
| out1 (POP) | cloth mesh |

## Parameters
| Par | Meaning |
|---|---|
| Pinmode | Top Row (points within `Pinthickness` of the highest Y), Pin Attribute (point attribute `Pin` > 0.5), Point Group (group named `Pingroup`, e.g. from a Group POP), None |
| Gravity, Wind, Winddir, Turbulence, Damping | forces |
| Stiffness, Iterations | constraint strength and relaxation passes per frame (more = less stretch; dense meshes need more) |
| Collider, Spherepos, Sphereradius | sphere collider (drawn in the preview) |
| Speed | time step scale (keep <= ~1.5) |
| Play, Reset | Reset re-initialises from the current input |
| Maxneighbors (Sim) | neighbour array size; raise above the highest vertex valence in your mesh (grids: 6) |
| Demogrid, Demosize (Sim) | demo mesh only |
| Color1/2, Checker, Spherecolor, Cam*, Background (Look) | preview only |

## Limitations
- Needs polygons (edges come from primitives); a pure point cloud has no neighbours and simply falls.
- Edge (structural) constraints only, no self-collision, collider is one sphere.
- The sim state is initialised from the input at start / `Reset`; changing the mesh topology needs a `Reset`. Pinned points follow the live input every frame.
- Jacobi relaxation is slow to converge on very dense meshes: raise `Iterations` (max 128).
- The sim only advances while something downstream cooks `out1`.
