# td-plugins

57 reusable TouchDesigner components plus the `UTIL_auto_arrange` utility (`.tox`) for VJ work, generative visuals and post effects. They were built and tested on TouchDesigner 2025.32820 (macOS).

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

### Simulations
| tox | what |
|---|---|
| GEN_gpu_particles | About 200k POP particles: emitter, curl noise, gravity, 2 attractors |
| GEN_reaction_diffusion | Gray-Scott with presets (coral, mitosis, labyrinth, spots, worms) and an optional `in1` seed mask |
| GEN_fluid_2d | Stable fluids with vorticity and animated emitters; `in1` adds dye and velocity. `out2` = velocity |
| GEN_boids | GPU flocking; outputs geometry only: boid points (P, N, Color) and an instanced cone mesh (POPs) |
| GEN_physarum | Slime-mold agents with a trail map |
| GEN_cellular_automata | Game of Life, Brian's Brain, Wireworld, Larger-than-Life, and custom `B/S` rules |
| GEN_verlet_cloth | Pinned cloth with wind and a sphere collider |
| GEN_strange_attractors | Lorenz, Aizawa, Thomas, Halvorsen and Dadras, with morph and trails |

### Generative and geometry
| tox | what |
|---|---|
| GEN_sdf_raymarch | Modular SDF scene: smooth union, repetition, soft shadows, AO |
| TOP_instance_grid | Any TOP → a 3D field of instanced boxes, spheres or cones |
| GEN_lsystem | L-system presets with animated growth |
| GEN_voronoi | Cells, edge glow, cracked glass and stained glass, with a Delaunay overlay |
| GEN_flow_field_lines | Long-exposure strokes along a curl-noise or image field |
| TOP_kaleidoscope | N-fold radial, square/triangle/hex tile and hyperbolic modes |
| GEN_fractal_zoom | Mandelbulb or Menger dive that loops seamlessly |
| GEN_infinite_tunnel | Raymarched corridor with segment variations |
| GEN_mirror_room | Kaleidoscopic mirror box with a chrome centre object |
| GEN_terrain_flyover | Retro wireframe or solid terrain with horizon glow |
| GEN_tentacles | Writhing tube splines |
| POP_mesh_deformer | Twist, bend, inflate, noise and ripple, driven by an optional band CHOP |
| POP_pointcloud_dissolve | Mesh or depth image → points that erode into curl dust and re-form |
| POP_plexus_points | Scan-strata point cloud with plexus lines and long lines over a grid |
| GEN_video_synth | LZX/Hydra-style oscillator patches with presets |

### Type and HUD
| tox | what |
|---|---|
| GEN_kinetic_type | Per-glyph 3D type: scatter, slit-stretch, warp, depth stack |
| GEN_glyph_tunnel | Character tunnel, wall or rain |
| GEN_text_fluid | Text injected into `fluid_2d`, smearing and re-forming |
| TOP_tracker_hud | Feature boxes, ID or coordinate labels, links, grid and scanlines over any input |
| TOP_type_overlay | Monospace title card, telemetry, crop marks |

### Post effects (process `in1`)
| tox | what |
|---|---|
| TOP_feedback_trails | Transform, hue-drift and displacement feedback |
| TOP_glitch | RGB split, block shift, tears, streaks, compression hold |
| TOP_pixel_sort | True odd-even GPU pixel sort, bytebeat bands, channel shuffle |
| TOP_pixel_stretch | Directional pixel-drag smear from a luminance threshold |
| TOP_filmic_look | Bloom, glare, chromatic aberration, ACES, grain, vignette |
| TOP_halftone | CMYK or mono halftone, Bayer and error-diffusion dither, ASCII |
| TOP_toon_outline | Posterize with ink or neon edges |
| TOP_slit_scan | Time displacement from a frame ring buffer |
| TOP_optical_flow | GPU optical flow → smear, warp or flow visualization. `out2` = flow |
| TOP_droste_zoom | Log-polar Droste infinite zoom |
| TOP_dof_motionblur | Depth of field (from depth, luma or radial) plus motion blur |
| TOP_vhs_crt | Tape wobble, chroma bleed, tracking noise, interlace, shadow mask, curvature |
| TOP_false_color | Thermal, x-ray, night-vision or custom maps with a HUD |
| TOP_glass_refraction | Moving glass shape refracting the input, with dispersion and frost |

### Utilities
| tox | what |
|---|---|
| UTIL_auto_arrange | Arrange a network: left-to-right data flow, docked DATs under hosts, no overlapping nodes. Set Target (empty = this network), pulse Arrange or Check; out1 = report table |

### Materials (`<comp>/mat`, with a preview on `out1`)
| tox | what |
|---|---|
| GEN_liquid_chrome | Raymarched morphing chrome blob, with optional thin-film |
| MAT_iridescent | Thin-film interference, fresnel rainbow, anisotropic sheen |
| MAT_jelly | Gummy fake-SSS with rim glow and wobble |
| MAT_wet_black | Oil or tar clearcoat with flowing drips |
| MAT_brushed_metal | Anisotropic brushed and anodized metal |
| MAT_crystal | Faceted refraction with dispersion and sparkle |
| MAT_ferrofluid | Rosensweig spikes pulled by an attractor or CHOP |
| MAT_porcelain | Porcelain, marble or bone, with veins and cracks |
| MAT_velvet | Sheen lobe or shell fur |
| MAT_molten | Emissive cracks through a cooling crust |
| MAT_decay | Clean → rust → pitted weathering |
| MAT_hologram_scan | Wire lattice, scan sweep, data dropout |
| MAT_matcap | 8 procedural matcaps, or a custom `in1` |
| MAT_triplanar | UV-less noise, voronoi, stripes, grid, checker or texture |
| MAT_screen_stylize | Per-object dither, halftone or ASCII |

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
- **`tools/revalidate.sh <inst> <names...>`:** a batch summary. `tools/contact_sheet.py` makes PNG grids.

- `tools/build.sh <inst> <NAME>`: the full pipeline (build.py → `tox/_raw` → `tools/conform.py` → `tox/<FAMILY>/<NAME>.tox` → validate → snippet build → snippet validate). `tools/build_all.sh <inst>` does all 57.

Each `components/<NAME>/build.py` is self-contained (all 57 rebuilt from source in a clean instance). Where a `body.py` exists, `build.py` is generated from it: `components/_v2/mkv2.sh <NAME>` for the TOP_ effects that have one, older `mk*.sh` scripts for a few others. Otherwise edit `build.py` directly. Names, descriptions and versions live in `components.json`.

## td_organize (network layout)
`td_organize/` is the layout engine behind `UTIL_auto_arrange` and the build pipeline: a layered left→right layout with docked DATs under their hosts, unwired nodes in a band below, Annotate boxes laid out and resized as groups, and an overlap checker. Pure Python, tested without TouchDesigner (`.venv/bin/python -m pytest`).
- Inside TouchDesigner: `exec(open(<repo>/td_organize/td_runtime.py).read())`, then `organize(op('/project1/x'))` or `check(...)`. `td_runtime.py` is generated by `tools/bundle_organize.py` (a test fails if stale).
- From a shell, against a running TD with td-mcp: `.venv/bin/td-organize organize --inst NAME /project1/x` (`check` exits 1 on overlaps).
- COMPs tagged `no_arrange` are skipped. The repo is also a Claude Code plugin (`.claude-plugin/`, skill `skills/td-organize`).
