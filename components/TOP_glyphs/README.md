# TOP_glyphs
Glyph / ASCII rendering **of the input image**: the image is divided into cells, cell luminance picks the glyph from `Charset` (dark to bright), the cell colour comes from the input. Layouts: grid, rain, tunnel.
(Library name `TOP_glyphs`, formerly `GEN_glyph_tunnel`. Shipped as `tox/TOP/TOP_glyphs.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | image (In TOP). Unconnected: an internal animated demo picture (inside `demo`, only cooks when nothing is connected) |
| in2 | modulation CHOP (optional): `band1` pumps Contrast, `band2` Brightness, `band3` rain Tail, `beat` flashes the glyphs |

## Outputs
| Output | Label / content |
|---|---|
| out1 | glyph image (rgba16float) |
| out2 | glyph index field: r = glyph index / (N-1), g = quantised cell luminance, b = per-cell hash (constant over each cell) |

## Parameters
| Page | Param | Notes |
|---|---|---|
| Controls | Layout | `grid` (regular cells), `rain` (falling columns with trails that reveal the picture), `tunnel` (polar remap: cells = angle x depth around the vanishing point) |
| | Charset | glyphs ordered dark to bright (default ` .:-=+*#%@`); `Fontname` picks the (monospace) font |
| | Cols | columns of cells (cell size); rows follow the aspect, cells are 1:2 |
| | Speed | scroll speed for rain and tunnel |
| | Contrast, Invert | luminance to glyph mapping |
| | Brightness, Background | glyph gain; amount of dim original image behind the glyphs |
| | Tail, Trailfloor | rain trail length (rows) and minimum visibility between tails |
| | Twist | tunnel spiral |
| | Seed | hash seed |
| | Mix, Bypass, Resolutionmode, Resolution | standard TOP controls (`input` follows in1) |
| Look | Look, Accent | `original` = input colours; `mono` = bone-white / grey glyphs with an optional red Accent fraction |

No Loop page: time only drives the rain / tunnel scroll.
