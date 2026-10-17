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
- **GPU-first:** GLSL TOP/POP/MAT, POPs, Feedback TOP. No per-frame Python loops.
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
(Owned by the SDF_ family; documented by its author.) The SDF wire format, how parameters reach the shader without recompiling, `tools/fixtures/SDF_input.txt` (what validation feeds an SDF input), and how `SDF_render` / converters consume it.
