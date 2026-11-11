#!/usr/bin/env bash
# 第一次執行會在這個資料夾建立 .venv 並安裝 PySide6（約 200 MB），之後直接啟動。
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv || { echo "請先安裝：sudo apt install python3-venv"; exit 1; }
  .venv/bin/pip install -r requirements.txt || exit 1
fi
if ! ldconfig -p 2>/dev/null | grep -q libxcb-cursor.so.0; then
  echo "缺少 libxcb-cursor0（Qt 6.5 以後需要），請先執行：sudo apt install libxcb-cursor0"; exit 1
fi
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
exec .venv/bin/python desktop_pet.py "$@"
