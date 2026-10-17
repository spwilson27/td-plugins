# td-plugins

70 reusable TouchDesigner components (`.tox`) for VJ work, generative visuals and post effects. They were built and tested on TouchDesigner 2025.32820 (macOS).

**Using a component:** add `~/software/td-plugins/tox` as a Palette folder (or drag `tox/<FAMILY>/<NAME>.tox` into your network). The name prefix tells you what it takes: `TOP_` an image, `POP_` geometry, `GEN_` nothing (generator), `MAT_` a material at `<comp>/mat`. Output connectors are labelled; `out1` is always the final image.
**Examples:** every component has 1–3 example networks, like TouchDesigner's OP Snippets. Pulse About ▸ Snippets on the component, or open `snippets/<NAME>.tox`.
**Docs:** About ▸ Help, or `components/<NAME>/README.md`, covers its inputs, outputs, parameters and limitations.
**Contact sheets:** `validation/sheet_batch1.png`, `sheet_mono_batch1.png`, `sheet_batch2.png` and `sheet_batch3.png`.

## Shared conventions (see CONVENTIONS.md)
- **Previews:** every component's node viewer shows a live preview. Geometry-only components (e.g. `GEN_boids`, out1 = POP) and materials render an internal preview for it.
- **Tidy networks:** component internals and snippets are laid out by `td_organize` (in this repo; also usable on your own networks via `UTIL_auto_arrange`): left→right data flow, no overlapping nodes (validated).
- **Outputs:** `out1` TOP is always the rendered result. Extras are on `out2`, `out_pop` and similar. Material components also expose their GLSL MAT at `<comp>/mat`.
- **Inputs:** effects process `in1`. With nothing connected, they fall back to an internal animated test source.
- **Loop page:** `Timesource` is either `abstime` or `phase`. In phase mode the `Phase` param (0–1) drives all motion. Stateless generators loop seamlessly. Stateful sims drive their forcing from Phase and have a `Loopreset` toggle that restarts them at the wrap, so a recorded loop restarts identically. Each README says how seamless that component's loop is.
- **Look:** where a component has a `Look` menu, `Mono` gives black, bone-white and grey with an optional red `Accent` (Rendah-style). Batch-2 and batch-3 components default to that palette.

## Components

### Image filters (TOP_, process in1)
| tox | what |
|---|---|
| TOP_cellular_automata | Cellular automaton driven by an image: bright pixels seed (and keep injecting) cells; cells take the input colours. Life, Brians Brain, Wireworld, Larger than Life, custom B/S. out2 = raw state. |
| TOP_depth_fog | Depth fog and horizon glow from a depth map (any Render TOP / SDF_render depth) |
| TOP_dof_motionblur | Depth of field (depth/luma/radial) and motion blur |
| TOP_droste_zoom | Log-polar Droste infinite zoom |
| TOP_env_reflect | Environment reflection (chrome / glass look) from normals and an env map |
| TOP_false_color | Thermal / x-ray / night-vision false colour with HUD |
| TOP_feedback_trails | Feedback trails with transform, hue drift and displacement |
| TOP_filmic_look | Bloom, glare, chromatic aberration, ACES tonemap, grain, vignette |
| TOP_flow_field_lines | Long-exposure strokes advected along a field derived from the input image (edge contours, gradient, luminance or hue angle), coloured by the image. out2 = the field (direction in RG, strength in B). |
| TOP_fluid | 2D stable fluid that advects and smears the input image as dye (inject or seed), with an optional velocity/force TOP; outputs smeared image, velocity and dye fields. Feed a Text TOP for fluid text. |
| TOP_glass_refraction | Moving glass shape refracting the input with dispersion |
| TOP_glitch | RGB split, block shift, scanline tears, streaks, compression hold |
| TOP_glyphs | Glyph / ASCII rendering of the input image (grid, rain, tunnel layouts) |
| TOP_halftone | Halftone (CMYK/mono), Bayer/error-diffusion dither and ASCII |
| TOP_instance_grid | Image to a 3D field of instanced boxes, spheres or cones |
| TOP_kaleidoscope | Radial, tiled and hyperbolic kaleidoscope |
| TOP_normal_shade | Shade a normal map with a matcap or key/rim lights |
| TOP_optical_flow | GPU optical flow driving smear, warp or flow visualization |
| TOP_physarum | Slime-mold agents that follow the input image brightness; outputs the trail map |
| TOP_pixel_sort | True GPU pixel sort, bytebeat bands, channel shuffle |
| TOP_pixel_stretch | Directional pixel-drag smear from a luminance threshold |
| TOP_reaction_diffusion | Gray-Scott reaction-diffusion grown from / fed by the input image; outputs the chemical field |
| TOP_slit_scan | Slit-scan time displacement from a frame ring buffer |
| TOP_ssao | Screen-space ambient occlusion from depth + normals |
| TOP_toon_outline | Posterize with ink or neon edge lines |
| TOP_tracker_hud | Tracking HUD: feature boxes, ID/coordinate labels, links, grid |
| TOP_type_overlay | Monospace title card, telemetry read-outs and crop marks |
| TOP_vhs_crt | VHS/CRT emulation: wobble, chroma bleed, tracking noise, mask, curvature |
| TOP_video_synth | LZX/Hydra-style oscillators that modulate, displace and colorise the input image |
| TOP_voronoi | Voronoi cells / cracked & stained glass coloured by sampling the input image at each cell site; density can follow luminance or edges. out2 = cell id colour with edge distance in alpha |

### Geometry filters (POP_, process in1 geometry)
| tox | what |
|---|---|
| POP_attractor_advect | Advect the input points along a strange-attractor field (Lorenz, Aizawa, Thomas, Halvorsen, Dadras), optionally with trails |
| POP_boids | Flock the input points (boids); outputs the moving points and an instanced cone mesh |
| POP_cloth | Verlet cloth simulation of the input mesh, pinned by group/attribute, wind, sphere collider |
| POP_mesh_deformer | Twist, bend, inflate, noise and ripple deformer stack |
| POP_particle_emitter | Emit GPU particles from the input geometry (points/surface) with curl noise, gravity, attractors |
| POP_plexus_points | Scan-strata point cloud with plexus lines and grid |
| POP_pointcloud_dissolve | Mesh to points that erode into curl-noise dust and re-form |
| POP_tentacles | Grow writhing tubes from the input points |
| POP_terrain | Displace the input grid by a heightmap TOP: scrolling retro terrain geometry |

### Generators (GEN_, output geometry, no render)
| tox | what |
|---|---|
| GEN_kinetic_type | Per-glyph 3D kinetic typography |
| GEN_lsystem | L-system branching growth with presets |

### Signed distance fields (SDF_)
| tox | what |
|---|---|
| SDF_box | SDF primitive: rounded box (size, roundness, colour). |
| SDF_combine | SDF operation: union, subtract, intersect or morph two SDFs with smooth blending. |
| SDF_deform | SDF operation: twist, bend, noise-displace, round or hollow out (onion) an SDF. |
| SDF_fractal | SDF primitive: Mandelbulb, Menger sponge or kaleidoscopic IFS fractal distance estimator. |
| SDF_gyroid | SDF primitive: gyroid / Schwarz-P / diamond triply periodic minimal surface, optionally bounded by a sphere. |
| SDF_plane | SDF primitive: infinite plane with optional checker. |
| SDF_render | SDF renderer: raymarches an SDF wire into color, linear depth, view normals and world position, using a Camera COMP. |
| SDF_repeat | SDF operation: repeat an SDF on an infinite or finite grid, or around an axis (polar). |
| SDF_sphere | SDF primitive: sphere (radius, colour). Wire its SDF output into other SDF_ nodes. |
| SDF_to_MAT | SDF converter (lossy): a GLSL MAT that raymarches an SDF wire inside proxy box geometry and writes depth, so it composites with Render TOP scenes. Use Apply To like the MAT_ components. |
| SDF_to_POP | SDF converter (lossy): polygonize an SDF wire into a mesh POP over chosen bounds and resolution (marching cubes). |
| SDF_to_TOP | SDF converter (lossy): bake an SDF wire into a 3D texture TOP (R = distance, GBA = color) over chosen bounds and resolution. |
| SDF_torus | SDF primitive: torus (major/minor radius, axis, colour). |
| SDF_transform | SDF operation: translate, rotate and uniformly scale an SDF. |

### Materials (MAT_, out1 = the material; Apply To)
| tox | what |
|---|---|
| MAT_brushed_metal | Anisotropic brushed and anodized metal |
| MAT_crystal | Faceted crystal refraction with dispersion |
| MAT_decay | Rust and corrosion weathering |
| MAT_ferrofluid | Ferrofluid spikes pulled by an attractor |
| MAT_hologram_scan | Hologram wire lattice with scan sweep and dropout |
| MAT_iridescent | Thin-film iridescence, fresnel rainbow, anisotropic sheen |
| MAT_jelly | Gummy fake-subsurface material with rim glow |
| MAT_matcap | Procedural matcap library with switcher |
| MAT_molten | Emissive molten cracks in cooling crust |
| MAT_porcelain | Porcelain, marble or bone with veins and cracks |
| MAT_screen_stylize | Per-object dither, halftone or ASCII shading |
| MAT_triplanar | UV-less triplanar procedural texturing |
| MAT_velvet | Velvet sheen or shell fur |
| MAT_wet_black | Wet black oil/tar clearcoat with drips |

### Utilities
| tox | what |
|---|---|
| UTIL_auto_arrange | Arrange a network: left-to-right flow, no overlapping nodes (td_organize) |

## Building and validating
**Requires:** TouchDesigner 2025.32820+, [td-mcp](https://github.com/spwilson27/td-mcp) checked out at `~/software/td-mcp` (or `TD_MCP_HOME`) with its `.venv`, and this repo's `td_organize` package (bundled; see `td_organize/README.md`), which lays out every network so no nodes overlap. Components find the library through `TD_PLUGINS_HOME` (default `~/software/td-plugins`) for Help and Snippets.

Rebuilding needs the td-mcp repo at `~/software/td-mcp` with its `.venv`. Set `PY=~/software/td-mcp/.venv/bin/python`, then:

```bash
$PY tools/tdctl.py start dev
```

```bash
$PY tools/tdctl.py exec dev components/<NAME>/build.py
```

```bash
$PY tools/validate.py dev <NAME> 4
```

```bash
$PY tools/tdctl.py stop dev
```

- **`tdctl.py start dev`:** launches a private scratch TouchDesigner with its own port and connection file. It never touches your open TouchDesigner.
- **`tdctl.py exec ... build.py`:** writes `tox/_raw/<NAME>.tox`; run `tools/conform.py dev <NAME>` to produce the shipped tox (or just use `tools/build.sh`).
- **`validate.py`:** checks for errors, warnings, GLSL compile failures, broken expressions and stale `/build/` paths. It also checks that the output animates, and writes `validation/<NAME>.png`. It also enforces CONVENTIONS.md.
- **Waits are in cooked frames** (`tools/tdwait.py`), not seconds, so validation is exact on a loaded machine. `tools/contact_sheets.py` makes the PNG grids.

- `tools/build.sh <inst> <NAME>`: the full pipeline for one component (build.py → `tox/_raw` → `tools/conform.py` → `tox/<FAMILY>/<NAME>.tox` → validate → snippet build → snippet validate).
- `tools/build_all.sh [-j N] [--force] [--only NAME ...]`: the whole library in parallel across N private scratch TouchDesigner instances (default ~half the CPU cores, max 6). Components whose sources and shared tooling are unchanged since their last passing build are skipped (hash in `validation/final/<NAME>.hash`); `--force` rebuilds everything. A full forced run of 70 components takes about 3.5 minutes with `-j 6`.

Each `components/<NAME>/build.py` is self-contained (all 57 rebuilt from source in a clean instance). Where a `body.py` exists, `build.py` is generated from it: `components/_v2/mkv2.sh <NAME>` for the TOP_ effects that have one, older `mk*.sh` scripts for a few others. Otherwise edit `build.py` directly. Names, descriptions and versions live in `components.json`.

## td_organize (network layout)
`td_organize/` is the layout engine behind `UTIL_auto_arrange` and the build pipeline: a layered left→right layout with docked DATs under their hosts, unwired nodes in a band below, Annotate boxes laid out and resized as groups, and an overlap checker. Pure Python, tested without TouchDesigner (`.venv/bin/python -m pytest`).
- Inside TouchDesigner: `exec(open(<repo>/td_organize/td_runtime.py).read())`, then `organize(op('/project1/x'))` or `check(...)`. `td_runtime.py` is generated by `tools/bundle_organize.py` (a test fails if stale).
- From a shell, against a running TD with td-mcp: `.venv/bin/td-organize organize --inst NAME /project1/x` (`check` exits 1 on overlaps).
- COMPs tagged `no_arrange` are skipped. The repo is also a Claude Code plugin (`.claude-plugin/`, skill `skills/td-organize`).
