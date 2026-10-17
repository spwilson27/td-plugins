#!/bin/bash
# build_all.sh [build_all.py args]  -- parallel, hash-skipping rebuild of the whole library (see tools/build_all.py)
cd "$(dirname "$0")/.."
PY=${PY:-${TD_MCP_HOME:-$HOME/software/td-mcp}/.venv/bin/python}
exec "$PY" tools/build_all.py "$@"
