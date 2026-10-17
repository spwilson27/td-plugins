#!/bin/bash
# mkv2.sh <NAME> : build.py = components/_v2/hdr_v2.py + COMP + components/<NAME>/body.py
cd ~/software/td-plugins
{ cat components/_v2/hdr_v2.py; echo; echo "COMP = '$1'"; cat components/$1/body.py; } > components/$1/build.py
