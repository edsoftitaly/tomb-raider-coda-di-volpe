#!/bin/bash
# Usage: render_view.sh level.prj2 out_prefix "views json" [query] [room prefixes...]
set -e
PRJ=$1; OUT=$2; VIEWS=$3; Q=${4:-}; shift 4 || true
python3 "$(dirname "$0")/prj2_mesh.py" "$PRJ" /home/claude/render/mesh.json "$@" >/dev/null
cd /home/claude/render && node shot.js "$VIEWS" "$Q" >/dev/null 2>&1
for f in $(echo "$VIEWS" | python3 -c "import json,sys;print(' '.join(json.load(sys.stdin)))"); do mv "/home/claude/render/$f.png" "$OUT$f.png"; done
