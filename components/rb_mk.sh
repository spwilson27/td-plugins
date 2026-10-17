#!/bin/sh
# rb_mk.sh name [fx]: fx = effects group (lib.py based), else batch-1 _helpers based
cd ~/software/td-plugins/components
if [ "$2" = "fx" ]; then { cat _lib/lib.py; echo; cat _rb2.py; echo; echo "COMP = '$1'"; cat $1/body.py; } > $1/build.py
else cat _helpers.py _loop.py _rb.py $1/body.py > $1/build.py; fi
