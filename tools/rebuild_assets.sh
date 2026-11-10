#!/usr/bin/env bash
# pixel-assets 的 make_*.py 改過之後，重新產生 assets/ 裡的 PNG（需要 Pillow）。
# 用法：bash tools/rebuild_assets.sh            （用 repo 裡的 art/）
#       bash tools/rebuild_assets.sh <資料夾>   （用別的 pixel-assets 資料夾）
set -e
cd "$(dirname "$0")/.."
P="$(cd "${1:-art}" && pwd)"
python3 tools/build_girl.py "$P" assets
python3 "$P/make_desktop.py" assets
python3 - <<'PY'
import json, glob, os
d = {}
for f in sorted(glob.glob("assets/anims_*.json")):
    d.update(json.load(open(f))); os.remove(f)
json.dump(d, open("assets/anims.json", "w"), indent=1)
print("ok", len(d), "個動作")
PY
