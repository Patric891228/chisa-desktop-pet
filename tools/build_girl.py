import os, sys, json
from PIL import Image
G, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, G)
import make_sleepy as ms
v7 = ms.v7; v4 = v7.v4
S = v4.scenes()
S["sleepy"] = [v7.half([[3 if c == 13 else c for c in row] for row in f]) for f in ms.sleepy()]
meta = {}
for n, fr in S.items():
    w, h = len(fr[0][0]), len(fr[0])
    strip = Image.new("RGBA", (w * len(fr), h))
    for i, f in enumerate(fr):
        strip.alpha_composite(v4.to_img(f), (i * w, 0))
    strip.save(os.path.join(OUT, n + ".png"))
    meta[n] = {"w": w, "h": h, "frames": len(fr), "ms": list(getattr(v4, "FRAME_MS", {}).get(n) or [v4.DUR.get(n, ms.MS)] * len(fr))}
json.dump(meta, open(os.path.join(OUT, "anims_girl.json"), "w"), indent=1)
