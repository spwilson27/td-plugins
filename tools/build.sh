#!/bin/bash
# build.sh <inst> <NAME>   full pipeline: build.py -> tox/_raw/<NAME>.tox -> conform -> tox/<FAM>/<NAME>.tox -> validate
#                          -> snippets/src/<NAME>.py (if present) -> snippets/<NAME>.tox -> validate_snippet
set -e
cd "$(dirname "$0")/.."; PY=${PY:-${TD_MCP_HOME:-$HOME/software/td-mcp}/.venv/bin/python}; inst=$1; n=$2
mkdir -p tox/_raw
$PY tools/tdctl.py exec $inst components/$n/build.py 120 | grep -q '"ok": true' || { echo "BUILD FAILED: $n"; $PY tools/tdctl.py exec $inst components/$n/build.py 120 | tail -20; exit 1; }
[ -f tox/_raw/$n.tox ] || { echo "build.py must save tox/_raw/$n.tox"; exit 1; }
$PY tools/conform.py $inst $n
timeout 180 $PY tools/validate.py $inst $n > validation/final/$n.json || { echo "VALIDATE FAILED: $n"; tail -40 validation/final/$n.json; exit 1; }
echo "component OK: $n"
if [ -f snippets/src/$n.py ]; then
  $PY tools/tdctl.py exec $inst snippets/src/$n.py 120 | grep -q '"ok": true' || { echo "SNIPPET BUILD FAILED: $n"; $PY tools/tdctl.py exec $inst snippets/src/$n.py 120 | tail -20; exit 1; }
  timeout 180 $PY tools/validate_snippet.py $inst $n > validation/final/${n}_snippet.json || { echo "SNIPPET VALIDATE FAILED: $n"; tail -40 validation/final/${n}_snippet.json; exit 1; }
  echo "snippet OK: $n"
else
  echo "NO SNIPPET: $n"; exit 1
fi
