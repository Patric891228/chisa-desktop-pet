"""角色包素材的最後一步（通用）：合併各個 anims_*.json 成 anims.json，再補上方留白（fix_top）。
用法：python3 tools/finish_assets.py characters/<角色>/assets [--fix-top]
--fix-top 只給千咲用（補她被切掉的呆毛）；新角色請直接在圖上方留空間，不要加這個參數。
各畫圖程式輸出的 anims_*.json 會被合併後刪掉；裡面的 "_ax" 表（寬圖裡角色中心的 x）會寫進對應動作。
"""
import glob, json, os, subprocess, sys

out = sys.argv[1]
fix_top = "--fix-top" in sys.argv[2:]
d = {}
for f in sorted(glob.glob(os.path.join(out, "anims_*.json"))):
    d.update(json.load(open(f, encoding="utf-8")))
    os.remove(f)
for k, ax in d.pop("_ax", {}).items():
    if k in d:
        d[k]["ax"] = ax
json.dump(d, open(os.path.join(out, "anims.json"), "w", encoding="utf-8"), indent=1)
print("ok", len(d), "個動作")
if fix_top:
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_top.py"), out], check=True)
