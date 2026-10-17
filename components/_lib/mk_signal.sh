#!/bin/bash
cd ~/software/td-plugins/components
{ cat _lib/lib.py; echo; cat _lib/signal_lib.py; echo; echo "COMP = '$1'"; echo "c = new_comp(COMP)"; cat $1/body.py; } > $1/build.py
