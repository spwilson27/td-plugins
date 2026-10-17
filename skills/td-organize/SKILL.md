---
name: td-organize
description: Lay out or check a TouchDesigner network so no nodes overlap and data flows left to right. Use after building or editing a COMP/tox programmatically, before saving a tox, or when a network looks messy or has overlapping nodes.
---

# td-organize

Layered layout for TouchDesigner networks (checkout: `~/software/td-plugins`).

## Rules the layout enforces
- No two nodes overlap (10 px clearance); `check` fails otherwise.
- Data flows left to right: every wire goes from a lower column to a higher one (longest path from sources). In ops are leftmost, Out ops rightmost.
- Docked nodes (GLSL pixel/compute/info DATs, anything with `op.dock`) are stacked directly under their host and move with it.
- Unwired nodes (callback/text/execute DATs, loose COMPs) sit in a tidy grid band below the main graph.
- Annotate COMPs are never laid out as nodes; the nodes they enclose form a group, groups are placed left to right, and each Annotate is resized to wrap its group (60 px title bar room).
- Child COMPs are organized recursively, except COMPs with an `externaltox` and Annotates.
- Only `nodeX/nodeY` (and Annotate geometry) change. Wiring and parameters are never touched.

## CLI (needs a running TD with td-mcp)
```
cd ~/software/td-plugins
.venv/bin/python -m td_organize check    --inst NAME /project1/my_comp     # exit 1 if overlaps
.venv/bin/python -m td_organize organize --inst NAME /project1/my_comp
.venv/bin/python -m td_organize organize --connection /path/connection.json /project1/my_comp --no-recursive --no-annotate
```
`--inst NAME` uses the td-plugins scratch instance `~/.tdctl/NAME/connection.json`. Never use the user's own TD (`~/.td-mcp/connection.json`) unless asked.

## Inside TD (execute_python / textport)
```python
exec(open(__import__('os').path.expanduser('~/software/td-plugins/td_organize/td_runtime.py')).read())
print(check(op('/project1/my_comp')))      # list of {comp, a, b, kind}
print(organize(op('/project1/my_comp')))   # per-COMP stats (overlaps before/after)
```
`tox/td_organize.tox` offers the same via custom pars (Target, Organize, Check, Recursive) without the checkout.

## Workflow
1. Build the network; 2. `organize`; 3. `check` must report 0 overlaps; 4. save. Re-run after adding nodes.
