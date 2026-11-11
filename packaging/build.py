"""打包成免安裝執行檔（PyInstaller）。在哪個系統執行，就產生那個系統的版本。
用法：pip install PySide6-Essentials pyinstaller && python packaging/build.py
輸出：dist/ChisaDesktopPet（Linux）、dist/ChisaDesktopPet.exe（Windows）、dist/ChisaDesktopPet.app（macOS）
"""
import os, sys
import PyInstaller.__main__

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
args = ["desktop_pet.py", "--name", "ChisaDesktopPet", "--noconfirm", "--clean", "--windowed",
        "--add-data", "characters:characters", "--add-data", "fonts:fonts",
        "--exclude-module", "tkinter"]
if sys.platform == "darwin":
    args += ["--icon", "packaging/icon.icns", "--osx-bundle-identifier", "com.chisa-desktop-pet"]
else:
    args += ["--onefile", "--icon", "packaging/icon.ico" if sys.platform == "win32" else "packaging/icon.png"]
PyInstaller.__main__.run(args)

if sys.platform == "darwin":                       # 不在 Dock 顯示圖示（像常駐小工具）
    import plistlib
    p = os.path.join("dist", "ChisaDesktopPet.app", "Contents", "Info.plist")
    with open(p, "rb") as f:
        info = plistlib.load(f)
    info["LSUIElement"] = True
    with open(p, "wb") as f:
        plistlib.dump(info, f)
