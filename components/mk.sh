#!/bin/sh
# usage: mk.sh name  -> build.py = helpers + loop + body
cd ~/software/td-plugins/components
cat _helpers.py _loop.py $1/body.py > $1/build.py
