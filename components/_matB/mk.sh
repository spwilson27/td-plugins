#!/bin/sh
# usage: mk.sh name -> composes components/name/build.py = _matB/lib.py + name/body.py (GLSL read at build time from files)
cd ~/software/td-plugins/components
cat _matB/lib.py $1/body.py > $1/build.py
