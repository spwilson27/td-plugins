#!/bin/bash
# revalidate.sh <inst> name... -> one summary line per component; JSON in validation/final/
cd "$(dirname "$0")/.."; PY=${TD_MCP_HOME:-$HOME/software/td-mcp}/.venv/bin/python; inst=$1; shift
mkdir -p validation/final
for n in "$@"; do
  timeout 150 $PY tools/validate.py $inst $n 4 > validation/final/$n.json 2>&1
  python3 - "$n" <<'P'
import json,sys
n=sys.argv[1]; s=open(f'validation/final/{n}.json').read()
try:
    j=json.loads(s[s.index('{'):])
    print(f"{n:22s} pass={j['pass']!s:5} anim={j.get('animating')!s:5} diff={j.get('frame_diff')} probs={[(p[0],p[1].split('/')[-1],p[2][:100]) for p in j['problems']]}")
except Exception: print(f"{n:22s} FAILED", s[-300:].replace(chr(10),' '))
P
done
