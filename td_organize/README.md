# td-organize

Lays out TouchDesigner networks so no nodes overlap and the network reads left to right by data flow.
The core (`layout.py`, `overlap.py`) is pure Python with no TouchDesigner dependency; `td_adapter.py` runs inside TD.

## Install / test
```
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

## Use inside TouchDesigner
```python
exec(open(__import__('os').path.expanduser('~/software/td-plugins/td_organize/td_runtime.py')).read())
organize(op('/project1/foo'))     # recursive=True, annotate_groups=True by default
check(op('/project1/foo'))        # [] when clean
```
`td_runtime.py` is generated (`python tools/bundle_organize.py`; a test fails if stale). Or drop `tox/UTIL/UTIL_auto_arrange.tox` into a network and use its `Arrange` / `Check` pulses (`Target` empty = parent COMP).

## CLI (via td-mcp)
```
td-organize organize --inst NAME /project1/foo      # ~/.tdctl/NAME/connection.json
td-organize check --connection conn.json /project1/foo [--no-recursive]
python -m td_organize ...                           # same thing
```
`organize` options: `--no-recursive`, `--no-annotate`, `--json`. `check` exits 1 if overlaps remain.
td-mcp is found via `$TD_MCP_HOME` (default `~/software/td-mcp`).

## Behaviour
- Columns = longest path from sources; rows ordered by barycenter sweeps; feedback loops are ignored for layout.
- In ops leftmost, Out ops rightmost. Gaps: 60 px columns/rows.
- Docked nodes are stacked under their host as one block. Unwired nodes go in a grid below.
- Annotate COMPs: enclosed nodes (`enclosedOPs`; innermost annotate wins) form groups laid out independently, left to right; each Annotate is resized to the group box (+30 px padding, +60 px title bar). Nested annotates are not re-wrapped.
- Recursion skips COMPs with an `externaltox` and Annotates. Only node positions and Annotate geometry are written.

## Library
```python
from td_organize import layout, find_overlaps, outside_groups
pos, boxes = layout(nodes, edges, return_groups=True)   # {id: (x, y)}, {group: (x, y, w, h)}
```

## Rebuilding the tox
Real-TD check: `tools/tdctl.py start NAME`, then `python tools/organize_verify_td.py NAME some.tox ...`. The TouchDesigner component is `UTIL_auto_arrange` (built by `tools/build.sh`).
