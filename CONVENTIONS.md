# td-plugins component conventions (v3)

Machine-checked by `tools/validate.py` (component) and `tools/validate_snippet.py` (snippet).
`tools/build.sh <inst> <NAME>` runs the whole pipeline and must print `component OK` and `snippet OK`.

## 1. Naming and layout
- **Name** = `<FAMILY>_<snake_name>`. FAMILY is the family of the **primary input**:
  - `TOP_`: processes an image (in1 = In TOP)
  - `POP_` / `SOP_`: processes geometry (in1 = In POP / In SOP)
  - `CHOP_`: driven by channels (in1 = In CHOP)
  - `GEN_`: no required input; outputs data (POP geometry, or a TOP *field*), never its own scene render other than the internal preview (e.g. `GEN_lsystem`, `GEN_kinetic_type`)
  - `SDF_`: signed-distance-field building blocks that pass SDFs between each other (primitives, operations), render them (`SDF_render`) or convert them to native types (`SDF_to_POP`/`SDF_to_TOP`/`SDF_to_MAT`, lossy). See the SDF section.
  - `UTIL_`: a utility that acts on your network rather than producing media (e.g. `UTIL_auto_arrange`). No required input; out1 may be a DAT (e.g. a report), no Loop page, no image requirement.
  - `MAT_`: a material. **out1 is an Out MAT** (the material, from `<comp>/mat`); the preview render is an internal `preview` TOP shown in the node viewer, not an output. The first Material parameter is **Apply To** (`Applyto`, section 3)
- The canonical names, descriptions and versions are in `components.json` (single source of truth).
- **Files:**
  - `components/<NAME>/build.py`: runs inside TD, builds `/build/<NAME>` and saves **`tox/_raw/<NAME>.tox`**.
  - `components/<NAME>/README.md`: documentation, plus any `*.glsl` files.
  - `tox/<FAMILY>/<NAME>.tox`: the shipped component, written by `tools/conform.py`. Never hand-save here. Add `tox/` as a TouchDesigner Palette folder.
  - `snippets/src/<NAME>.py` → `snippets/<NAME>.tox`: example networks (section 6).

## 2. Inputs and outputs
- **Inputs:** real In operators, ordered by name: `in1` is the primary input of the prefix family, then secondary inputs (depth, maps, env), then the **optional modulation In CHOP last**.
  - The modulation CHOP takes channels `band1`–`band4` (0–1) and `beat` (pulse). Use whichever channels exist and ignore the rest.
- **Outputs:** real Out operators, at least one. `out1` is the primary output: an **Out TOP** for image components, an **Out POP** allowed for geometry components (`GEN_`/`POP_`, e.g. `GEN_boids`), and the **Out MAT** for `MAT_`. Don't render geometry just to output a TOP when the geometry is the product: output the POP and let the user render it.
- **Preview (every component):** the node viewer always shows a TOP. If `out1` is a TOP, the viewer shows `out1`. Otherwise the component has an internal `preview` TOP (its own small render; not an output) and the viewer shows that. Validation fails if the viewer is missing, not a TOP, or blank. Extras are `out2`, `out3`, …, ordered TOPs first, then POP/SOP/CHOP.
  - **Hover labels:** every In and Out op has a short descriptive `label` (2–5 words, e.g. `image`, `depth map`, `modulation CHOP`, `velocity`, `particles (POP)`). That label is what TouchDesigner shows when you hover the connector. The labels live in `io_labels.json` (keyed by component and op name); `conform.py` applies them, and falls back to the op's comment. Add an entry whenever you add or rename an input or output; generic labels (`output2`) fail validation.
  - In build.py you may create Null ops named `out*`. `conform.py` converts them to Out OPs.
- **No inputs connected:** every component must still produce a sensible, animated output. Use an internal default source and detect connection with `len(parent().inputConnectors[0].connections)`.
- **No per-frame Python keep-alives.** Real Out OPs are pulled by whatever is downstream.

## 3. Parameters
- **Page order:** `Controls` (or `Material` for MAT_) → component-specific pages → `Look` → `About`. `conform.py` sorts and adds About.
- **Common names:** use these exact names when the concept exists: `Reset` (pulse), `Play` (toggle), `Speed`, `Seed`, `Resolutionw`/`Resolutionh`.
- **TOP_ effects must have:**
  - `Mix` (float 0–1, default 1: dry/wet against the input)
  - `Bypass` (toggle: passes in1 straight through, cheaply via a Switch TOP)
  - `Resolutionmode` (menu `input` | `custom`, default `input`). `input` follows in1's resolution, or the default source's when unconnected. `custom` uses `Resolutionw`/`Resolutionh`.
- **No Loop page / loop parameters.** Time-based behaviour exists only to make the built-in preview example move; components are effects, not VJ loops. (Validation fails on `Timesource`, `Phase`, `Clock`, `Loopseconds`, `Loopbeats`, `Loopreset`.)
- **Demo sources are gated.** Every preview-only source (test patterns, demo geometry, animated example input) lives inside a Base COMP named `demo` and feeds the network through a Switch whose index is "is in1 connected". When inputs are connected the demo branch is not selected, so it does not cook. Validation connects test inputs and fails if anything inside `demo` still cooks.
- **Look page / menu:** where a component has a Look menu, `Mono` = black, bone-white and grey with an optional red `Accent`.
- **Apply To** (`MAT_` only, added by conform as the first Material parameter): an operator-list field. Dragging Geometry COMPs or Render TOPs onto it assigns `<comp>/mat` to them (Geometry `Material`, Render TOP `Override Material`). Removing an op from the field clears its material, and renaming or moving the component re-applies it (`applyto_callbacks` Parameter Execute DAT + `applyto_watch` OP Execute DAT).
- **About page** (added by conform): `Version`, `Description` and `Family` (read-only, from components.json), `Libraryroot`, a `Help` pulse that opens the README, and a `Snippets` pulse that opens the snippet.

## 4. Look of the node and layout
- **No overlapping nodes** anywhere: in every component network (recursively) and every snippet. `tools/conform.py` and `_snip.finish()` run `td_organize` (left→right data flow, docked DATs stacked under their host, unwired nodes in a band below, Annotate boxes as groups), and both validators fail on any overlap. Tag a COMP `no_arrange` only for deliberately messy demo networks.
`conform.py` colours the node by family (TOP blue, GEN green, POP purple, MAT orange), turns the node viewer on to show `out1` (or `preview`), and puts the description in the node comment.

## 5. Rendering and technique
- **Native nodes first:** build with built-in TouchDesigner operators (Blur, Level, Lookup, Displace, Composite, Feedback, Time Machine, Luma Blur, Bloom, Remap, Edge, Noise/Ramp, POPs such as Noise, Math, Lookup Texture, Proximity, Particle...) so a non-programmer can read the network. Use GLSL only for genuinely mathy algorithms (simulations, sorting, coordinate warps, SDFs, custom shading models) or when the native network would be more than 20 % slower on the GPU. Decide with `tools/bench.py <inst> <NAME> --against <old.tox>` (interleaved medians) and record the result in the component README ("Implementation" section).
- **GPU work, no per-frame Python loops.**
- **Pixel formats:** `rgba16float` outputs, and `rgba32float` for simulation state.
- **No absolute paths in the tox.** Use relative or `parent()` references. GLSL is embedded in DATs. `validate.py` fails any `/build/` reference.

## 6. Snippets (example networks, like Derivative's OP Snippets)
- Build them with `snippets/src/_snip.py` (see its header). Each `snippets/src/<NAME>.py` produces `snippets/<NAME>.tox` with 1–3 examples.
- **Each example:**
  - sits inside its own **Annotate COMP**, with a numbered title and a 2–5 line explanation of what to try
  - uses the component via `instance()`, which references the library tox through `externaltox`, so snippets always show the current version
  - uses only TouchDesigner built-ins and Samples media (`sample_expr('Map/Banana.tif')`, `Map/Count.mov`, `Geo/...`) or other library components
  - ends in a Null TOP named `exampleN` (via `out()`) whose image clearly shows the effect
- **POP outputs** are rendered in snippets with `render_pop(ex, inst.op('out1'))` (Geometry COMP + Camera + Light + Render TOP).
- **Typical set:** (1) the effect on real input (Samples media or library geometry), (2) a parameter recipe, (3) a combination with another library component or modulation (LFO / Beat CHOP into the mod input).
- **Opening:** the component's About ▸ Snippets pulse loads the file into `/local/td_plugins_snippets/<NAME>_snippet` and opens it in a floating network editor.

## 7. Validation (both must pass, with no errors or warnings)
- **Zero warnings and errors in every supported configuration:** nothing connected (preview), primary input only, and every input connected (test sources: animated noise TOP, sphere POP, modulation CHOP, SDF fixture). Warnings fail validation.
- `tools/validate.py <inst> <NAME>`: runtime errors and warnings, GLSL compiles, expression errors, `/build/` references, animation, plus every rule above (`conventions: []`).
- `tools/validate_snippet.py <inst> <NAME>`: snippet loads cleanly, contains an externaltox instance, has an annotated, non-blank `exampleN` per example.
- Always **look** at `validation/<NAME>.png` and `validation/snippets/<NAME>_exampleN.png`.

## Gotchas (learned)
- **Headless cooking:** an unviewed network only cooks what is pulled. The validators install frame-end drivers to compensate; in real use, outputs are pulled downstream.
- **Feedback TOP** needs an input (initial frame) or it errors.
- **GLSL TOP inputs:** only 3 can be wired. Extra textures go in the `tops` parameter (`sTD2DInputs[3..]`).
- **Expressions:** `radians()` is not in the expression namespace; use `math.radians`.
- **Menus:** invalid menu values fail silently. Set menus by name and read them back.
- **Draw order:** in one Render TOP it is not the Geometry list order, and polygon offset is ignored on macOS/Metal. Use Geometry COMP `drawpriority` (lower = drawn later).
- **Renders after parameter changes:** a MAT parameter change needs a frame before re-render. Split change and capture into separate exec calls.
- **Connector order** follows the In/Out op name and the `connectorder` parameter (conform sets it).
- **Connecting COMPs:** to wire from a COMP instance, use `comp.outputConnectors[i]` (`_snip.connect()` does this).
- **OP references in COMP parameters** resolve from the COMP's *parent*: a component's `opviewer` must be `./out1`, not `out1` (the latter silently shows nothing).
- **A MAT parameter pointing at a COMP** (even one containing an Out MAT) renders with the default material, without error. Hence Apply To.
- **Parameter/OP Execute callbacks** run a frame after the change, and not in the frame a tox was loaded. Snippets call `applyto_callbacks.module.apply()` explicitly (`_snip.apply_material`).
- **Constant OP-path parameters are not updated when an op is renamed by script.** Components that hand out references to their internals must re-apply on rename (OP Execute DAT `onNameChange`/`onPathChange`).

## SDF section
(Owned by the SDF_ family.) SDF_ components are nodes that pass signed distance fields to each other like POPs. Primitives (`SDF_sphere/box/torus/plane/gyroid/fractal`, and `SDF_from_POP`, which takes POP geometry) have no SDF input, operations (`SDF_combine/transform/repeat/deform`) have one or two, `SDF_render` renders, and `SDF_to_TOP/POP/MAT` convert (lossy) to native TouchDesigner types.

**Wire = a DAT.** Every SDF_ node outputs (`out1`, an Out DAT) a text DAT in "SDF wire v1". It always contains the complete scene up to that node (upstream records first), so the last DAT of a chain is a self-contained scene:

```
#SDF 1
@node n123 sphere          # one record per node: unique id (n<op id>), free-form kind
@vals                      # the node's parameters, one vec4 per line (these animate)
0.7 0 0 0
0.85 0.85 0.85 0
@code                      # GLSL for the node; vec4 sdf_<id>(vec3 p) = (distance, albedo.rgb)
vec4 sdf_n123(vec3 p){ return vec4(length(p) - P_n123_0.x, P_n123_1.xyz); }
@end
@scene n123                # id of the final node; the scene function is sdf_<id>
```
**Texture / buffer references (`@tex`, optional, backward compatible).** A node record may start with `@tex` lines (right after `@node`, so older parsers ignore them): `@tex <name> <type> <oppath> [<attr> [<class>]]`. `<name>` is a GLSL-safe identifier unique in the scene (`T_<id>_<k>`; node code writes `T_@ID@_<k>`), `<type>` is `2d` or `3d` (a TOP at `<oppath>`) or `buffer` (one attribute `<attr>`, default `P`, of the POP at `<oppath>`, class `<class>`, default `point`). The consumer binds them as extra inputs of its GLSL TOP / MAT:
```
@node n7 from_pop
@tex T_n7_p buffer /proj/SDF_from_POP1/pack pts point     # POP attribute buffer -> TDBuffer_T_n7_p(i[, k]) in GLSL
@tex T_n7_v 3d /proj/SDF_from_POP1/volume P point         # TOP -> #define T_n7_v sTD3DInputs[<slot>]  (GLSL MAT: uniform sampler3D T_n7_v)
```
Paths are absolute operator paths, so a node that writes `@tex` re-writes its payload when it is renamed or moved (OP Execute `onNameChange` / `onPathChange`). Operations (combine / transform / repeat / deform) forward the records of their inputs like `@node` records (de-duplicated by name). A scene may reference at most `MAXBUF` = 6 buffers and `MAXTOP` = 3 2D and 3 3D textures (`sdflib.py`).
- Node code references its own parameter vec4s as `P_<id>_<k>` (k = line in `@vals`) and its upstream scenes by the upstream function names (`sdf_<upstream id>`). Any helper function must be uniquely named (suffix with the id).
- Fan-in (SDF_combine) merges the records of both inputs; records are de-duplicated by id. Unconnected inputs use a built-in default (a sphere for A, a box for B), so every node works standalone.
- A consumer (SDF_render, converters, node previews) assembles the shader from the payload: `uniform vec4 uSdf[128]` (`MAXV` = 128 vec4s per scene), a `#define P_<id>_<k> uSdf[<global index>]` per value, the node functions in order, and `vec4 sdScene(vec3 p)`. A Script DAT writes the shader text **only when it changes**; a Script DAT + DAT to CHOP turns the `@vals` into the uniform array (channels r,g,b,a x 128 samples, GLSL TOP/MAT array `uSdf`, type vec4); a third Script DAT (`<pfx>tex`) lists the `@tex` records as a table. Consequence: **animating parameters never recompiles anything**; the shader recompiles only when the graph structure changes (nodes, menu modes). Each node's Script DAT re-cooks when its parameters or input change, so animation flows through the chain.
  - **Binding `@tex` (`bind_tex` in `components/_sdf/helpers.py`, `tex_par` in `sdflib.py`):** purely by parameter expressions on the consumer GLSL TOP / MAT that read the table, never by writing parameters from a cook (that is a cook dependency loop). A GLSL TOP gets a fixed `tops` list of `MAXTOP` 2D then `MAXTOP` 3D slots (placeholders `notex` / `notex3` for unused ones) because it does not recompile when only its input list changes (`sTD3DInputs` stayed undeclared), and fixed `MAXBUF` buffer blocks (`nobuf` placeholders; named `TDBuffer_<name>`); a GLSL MAT gets named sampler blocks. Texture slots are counted per type after the wired inputs (SDF_render's environment is 2D slot 0, so its scene textures start at 1).
  - Why not a parameter texture / graph walk: the payload is self-describing text, so it also works from plain Text DATs (the validation fixture), a DAT you write by hand, or another tool; no walking of upstream operators.
  - 3D GLSL TOPs (`SDF_to_TOP`, `SDF_to_POP`) pass uSdf as an array type `texturebuffer` (`uniform samplerBuffer uSdf`, `P_` macros use `texelFetch`) because plain uniform arrays are only applied to some slices of 3D GLSL TOPs. `sdflib.assemble(text, tb=True)`. They bake in **compute mode** (one dispatch writes the whole volume with `TDImageStoreOutput`): a 3D *pixel* shader also binds POP buffers only on some slices, which would leave random slices of a `@tex` buffer scene empty. Use `textureLod(.., 0.0)`, not `texture()`, in node code (no derivatives in compute).
- Shared code: **one source in `components/_sdf/`** (`sdflib.py`: parse/emit, `build_node`, `assemble`, `tex_par`, camera helper; `lib.glsl`: raymarch / normal / soft shadow / AO / lighting; `preview.glsl`; `helpers.py`: the build helpers `node`, `preview`, `scene_feed`, `bind_tex`, ...). Every SDF_ `build.py` starts with `exec(open('~/software/td-plugins/components/_sdf/helpers.py').read())` and `rd(NAME, 'sdflib.py' | 'lib.glsl' | 'preview.glsl')` reads the shared copy at build time, so the built tox stays self-contained (sdflib lives in a Text DAT `sdflib` in each tox). Change the wire format or the raymarch library once, then rebuild all SDF_ components (`tools/build_all.sh` hashes `components/_*`). Component-specific GLSL (`node.glsl`, ...) stays in the component folder.
- `SDF_from_POP` (POP geometry -> SDF): `points` mode (metaballs through a GPU grid, buffers) and `mesh` mode (baked 3D distance volume, texture); see its README. It is also the reference for writing a node with `@tex` records: `node(c, kind, code, vals_py, tex_py=...)`.
- `tools/fixtures/SDF_input.txt` is a minimal valid wire (one sphere, node id `fx0`, default values); validation feeds it to every SDF input via a Text DAT.
- Previews: every SDF_ node has an internal `preview` TOP (small orbiting raymarch of its own scene) shown in the node viewer. `preview(c, scale=...)` frames content larger than the default orbit radius (3). `SDF_to_TOP` previews by raymarching the baked volume, `SDF_to_POP` renders the mesh, `SDF_to_MAT` renders a box with the material.
- `SDF_render` outputs: out1 colour; out2 linear eye-space depth in R (distance along the camera forward axis in world units, G = B = R, alpha 1 on hit, `Max Distance` with alpha 0 on miss); out3 view-space normals RGB in -1..1 (x right, y up, z toward camera); out4 world position. Its `Camera` parameter takes a Camera COMP (position/rotation/FOV read live; horizontal and vertical FOV methods); empty = built-in orbiting default camera. The optional in2 is an equirectangular environment TOP.
- `SDF_to_MAT` marches the SDF in the object space of the geometry that carries the material, inside the `Bounds` box (the proxy geometry should be a box covering it), writes `gl_FragDepth`, and has an Apply To field like MAT_ components.
- Limits: 128 vec4 parameter slots per scene; the SDF distance is exact only for rigid transforms and primitives (twist/noise/repeat are approximate, hence SDF_render `Step Scale`); lighting is built in (no TD lights or materials in SDF_render).
- **Expressions on a component's own custom parameters** (enable / default / bind) run with `me` = the component, so `parent()` is the network *above* it. Use `me.par.X`. TouchDesigner evaluates enable expressions only when drawing the parameter panel, so a broken one appears as a warning in the UI only; validation now evaluates them all.
- **Parameter help:** every custom parameter has help text (what TouchDesigner shows on Alt+hover). Write it in `components/<NAME>/help.json` (`{"Par": "1-2 sentences"}`, tuplet names, e.g. `Resolution`); `conform.py` applies it and adds the About/Apply To help. `tools/check_help.py` checks coverage offline against `validation/parlist.json`; validation fails on any parameter without help.
- **Snippet text:** `td_organize` reserves room for each Annotate's title and wrapped description, so nodes never sit on top of the text; `validate_snippet.py` fails if any node in a box reaches into its text area.
- **GLSL POP / POP buffers (learned with `SDF_from_POP`):** a GLSL TOP / MAT reads a POP attribute with `TDBuffer_<name>(i)` or `TDBuffer_<name>(i, k)` for array attributes (block parameters `buffer<i>pop|attrclass|attr|name`); a GLSL POP reads inputs with `TDIn_<attr>(input, i[, k])`, writes new attributes declared in `attr<i>name = custom` + `customname` (arrays via `isarray` / `arraysize`, usable as `cell[c][k]`), supports `atomicAdd/Max/Xor` on `uint` output attributes (`outputaccess = readwrite`), runs several passes (`npasses`, `TDPassIndex()`), and takes its thread count from another input (`numthreadsmode = otherinputelements`). New attributes start at 0 every cook. Standard attribute names are `PointScale`, `Color`, `N`, `Tex`. **Lock** on a POP freezes it and stops its upstream from cooking; locking a 3D TOP does not keep the volume. A time-dependent expression (`+ 0*absTime.frame`) on a Switch makes everything downstream cook every frame, and a Cache POP or Feedback POP wired to such a source does not stop that.

