#!/bin/bash
cd ~/software/td-plugins/components
{ cat _lib/lib.py; echo; cat _lib/loop.py; echo; echo "COMP = '$1'"; cat $1/body.py; } > $1/build.py
