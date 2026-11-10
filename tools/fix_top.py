"""補回頭頂：原本的圖是 32 格高，角色往上起伏（dy=-1）時呆毛、頭頂和蝴蝶結的外框會超出畫布被切掉。
這裡在每張圖上面加 PAD 格透明空間，補上被切掉的外框和呆毛，並更新 anims.json 的高度。
用法：python3 tools/fix_top.py assets   （由 rebuild_assets.sh 呼叫；已處理過的動作會跳過）
"""
import json, os, sys
from PIL import Image

PAD = 3
INK = (16, 12, 24, 255)
HAIR = (46, 42, 72, 255)


def fix_frame(fr):
    w, h = fr.size
    im = Image.new("RGBA", (w, h + PAD))
    im.paste(fr, (0, PAD))
    P = im.load()
    solid = lambda x, y: 0 <= x < w and 0 <= y < h + PAD and P[x, y][3] > 0
    # 呆毛：找頭髮最上面一列（連續 4 格以上），在中心右上補兩格
    top = None
    for y in range(PAD, PAD + 8):
        run = best = 0
        xs = []
        for x in range(w):
            if P[x, y] == HAIR:
                run += 1
                xs.append(x)
                best = max(best, run)
            else:
                run = 0
        if best >= 4:
            top = (y, xs)
            break
    if top and top[0] - PAD <= 1:
        y, xs = top
        run_xs = [x for x in xs if abs(x - (min(xs) + max(xs)) / 2) <= 6]
        c = (min(run_xs) + max(run_xs)) / 2
        for ax, ay in ((round(c + 1.5), y - 1), (round(c + 2.5), y - 2)):
            P[ax, ay] = HAIR
    # 新加的上方空間：描外框
    for y in range(0, PAD + 1):
        for x in range(w):
            if P[x, y][3] == 0 and any(solid(nx, ny) and P[nx, ny] != INK
                                       for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                P[x, y] = INK
    return im


def main(d):
    meta_p = os.path.join(d, "anims.json")
    meta = json.load(open(meta_p))
    for name, m in meta.items():
        if m.get("pad_top"):
            continue
        sheet = Image.open(os.path.join(d, name + ".png")).convert("RGBA")
        out = Image.new("RGBA", (sheet.width, m["h"] + PAD))
        for i in range(m["frames"]):
            fr = sheet.crop((i * m["w"], 0, (i + 1) * m["w"], m["h"]))
            out.paste(fix_frame(fr), (i * m["w"], 0))
        out.save(os.path.join(d, name + ".png"))
        m["h"] += PAD
        m["pad_top"] = PAD
    json.dump(meta, open(meta_p, "w"), indent=1)
    print("ok fix_top", len(meta))


if __name__ == "__main__":
    main(sys.argv[1])
