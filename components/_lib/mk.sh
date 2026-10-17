#!/bin/bash
# usage: mk.sh <comp>  -> concatenates lib.py + body.py into components/<comp>/build.py
cd ~/software/td-plugins/components
{ cat _lib/lib.py; echo; echo "COMP = '$1'"; cat $1/body.py; } > $1/build.py
