# TOP_type_overlay

Monospace layout / type overlay TOP in the Rendah-Mag manner: title card with a bold/regular mono mix, corner telemetry read-outs (timecode, frame counter, ticking random numeric columns), crop marks, thin border, edge ticks, centre cross, optional red accent. Works over `in1` or black.

| Input | Type | Notes |
|---|---|---|
| in1 | TOP | optional background; unconnected -> black base |
| in2 | CHOP | optional modulation: `band1` -> title size, `band2` -> telemetry size (scaled by Modamount) |

| Output | Label |
|---|---|
| out1 | result (overlay over base) |

Resolution: `Resolutionmode` = `input` follows in1 when connected, otherwise `Resolutionw`/`Resolutionh` (default 1280x720); `custom` always uses them. `Mix` crosses the base (black or in1) with the overlaid result; `Bypass` outputs the base only.

* All text is Text TOPs (8 total: 3 faux-bold title copies + 1 regular title + 5 telemetry blocks) driven by a small Python helper in the `lib` Text DAT. The helper only builds a short string per cook; the marks (border, crop marks, ticks, cross) are one GLSL TOP. Nothing is done per glyph.

## Controls page
| Par | Meaning |
|---|---|
| Layout | `rendah` (title bottom-left, telemetry in corners), `center`, `poster` (huge title top-left), `minimal`, `data` (heavy telemetry, mid-left TC) |
| Title | multi-line text; a line starting with `*` is rendered bold, others regular. The two-character sequence `\n` is also accepted as a line break |
| Titlesize | title font size as fraction of frame height (layouts scale it) |
| Telemetry, Telesize, Telelines | telemetry toggle, size multiplier, rows in the random column block |
| Tickrate, Fps | how often the random numbers re-roll (Hz); timecode frame rate |
| Marks, Border, Edgeticks, Crosshair, Borderwidth | frame graphics |
| Margin | inset as fraction of height |
| Textcolor, Accent (toggle), Accentcolor | bone-white text; red accent used for the REC dot and top-left crop mark |
| Opacity | overall opacity of overlay |
| Modamount | strength of mod CHOP on sizes |
| Mix / Bypass / Resolutionmode / Resolution | common TOP controls |

## Notes
* TD cannot select a Menlo Bold face, so bold is faux-bold (three copies offset about 2% of the font size).
* Text is flat colour: over very bright footage add your own darkening underneath.
* The title can be edited in the parameter field with `\n` for new lines, or pasted with real line breaks.

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.
