#!/usr/bin/env bash
# 千咲的動作圖：改過 art/ 裡的畫圖程式之後執行，重新產生 assets/（需要 Pillow）。
# 用法（在 repo 根目錄）：bash characters/chisa/build_assets.sh
set -e
cd "$(dirname "$0")"
python3 art/build_girl.py art assets
python3 art/make_desktop.py assets
python3 art/make_transitions.py assets
python3 ../../tools/finish_assets.py assets --fix-top
