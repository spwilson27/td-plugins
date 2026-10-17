#!/bin/bash
# build_all.sh <inst> : rebuild + validate every component and snippet (fresh instance recommended).
cd "$(dirname "$0")/.."; inst=$1
PY=${TD_MCP_HOME:-$HOME/software/td-mcp}/.venv/bin/python
$PY tools/tdctl.py start $inst >/dev/null
names=$(python3 -c "import json; n=[m['name'] for m in json.load(open('components.json'))]; n.sort(key=lambda x: x!='GEN_fluid_2d'); print(' '.join(n))")
pass=0; fail=0
for n in $names; do
  out=$(tools/build.sh $inst $n 2>&1)
  if echo "$out" | grep -q "snippet OK: $n"; then pass=$((pass+1)); echo "PASS $n"; else fail=$((fail+1)); echo "FAIL $n :: $(echo "$out" | tail -8 | tr '\n' ' ' | cut -c1-600)"; fi
done
echo "TOTAL pass=$pass fail=$fail"
