"""v7：板子是 64x32，所有動作改成 1 倍輸出（32 格就是 32 像素，不再放大）。
畫法完全沿用 v6，只在輸出前把 2 倍的圖縮回 1 倍（每 2x2 取一格，無損）。
用法：python3 make_girl_v7.py → girl_v7/
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_girl_v6 as v6

v4 = v6.v4
HERE = os.path.dirname(os.path.abspath(__file__))
v4.OUT = os.path.join(HERE, "girl_v7")
ZOOM = 6  # 預覽圖放大倍數（只影響 GIF／PNG 預覽，不影響 .h）

_v6_scenes = v4.scenes
v3, v5 = v6.v3, v6.v5
px, rect = v5.px, v5.rect


# ---------- 新眼神：放空（blank）、嚴肅（stern） ----------
_head_front = v3.head_front


def head_front(g, hx, hy, eyes, mouth, look, blush=False):
    _head_front(g, hx, hy, eyes if eyes in ("open", "closed", "glow", "down") else "none",
                mouth if mouth in ("dot", "open") else "none", look, blush)
    ey = hy + 2
    if mouth == "wavy":          # 嫌棄的波浪嘴
        for i, x in enumerate(range(hx - 2, hx + 3)):
            px(g, x, hy + 7 + (i % 2), 10)
    if eyes == "disgust":        # 嫌棄：臉上半部發黑的直線
        for x in range(hx - 7, hx + 8, 2):
            rect(g, x, hy, x, hy + 2, 12)
    for k, ex in enumerate((hx - 6, hx + 3)):
        e = ex + look
        if eyes == "blank":      # 眼神清空：白眼、只剩一個小點
            rect(g, e, ey, e + 2, ey, 1)
            rect(g, e, ey + 1, e + 2, ey + 3, 6)
            rect(g, e, ey + 4, e + 2, ey + 4, 1)
            px(g, e + 1, ey + 2, 8)
        elif eyes == "disgust":  # 嫌棄：上眼皮壓很低、斜眼瞄過來
            rect(g, e, ey + 1, e + 2, ey + 2, 1)
            px(g, e + (0 if k == 0 else 2), ey + 1, 4)
            rect(g, e, ey + 3, e + 2, ey + 3, 9)
            rect(g, e, ey + 4, e + 2, ey + 4, 1)
            px(g, e + (0 if look < 0 else 2), ey + 3, 10)
        elif eyes == "stern":    # 嚴肅：眉毛往中間壓、半閉眼
            px(g, e + (2 if k == 0 else 0), ey, 1)
            px(g, e + 1, ey - 1 if False else ey, 1)
            px(g, e + (0 if k == 0 else 2), ey - 1, 1)
            rect(g, e, ey + 2, e + 2, ey + 2, 1)
            rect(g, e, ey + 3, e + 2, ey + 4, 9)
            px(g, e + (2 if k == 0 else 0), ey + 3, 10)


v3.head_front = head_front


# ---------- 被摸頭：系統當機 ----------
def pat_hand(y, x=13):
    """（目前沒用到）漂泊者的手。摸頭由按鈕觸發，畫面上不畫手。"""
    def f(g):
        rect(g, x - 1, y - 1, 31, y + 4, 1)
        rect(g, x, y, x + 8, y + 3, 4)          # 手掌
        rect(g, x, y + 3, x + 8, y + 3, 5)      # 手掌陰影
        for fx_ in (x + 2, x + 4, x + 6):       # 指縫
            px(g, fx_, y + 2, 5); px(g, fx_, y + 3, 1)
        rect(g, x + 9, y, 31, y + 3, 8)         # 袖子
        rect(g, x + 9, y + 3, 31, y + 3, 11)
    return f


def ears(g, dy=0):
    """耳朵（側髮縫裡露出一點）染紅。"""
    for x in (7, 25):
        rect(g, x, 14 + dy, x, 15 + dy, 9)


def steam(n):
    """頭頂右側冒過熱的白煙，n 越大煙越多。"""
    puffs = [((28, 8), (29, 8), (28, 7), (29, 7)), ((30, 5), (31, 5), (30, 4), (31, 4)),
             ((28, 2), (29, 2), (28, 1), (29, 1), (30, 1)), ((1, 0), (2, 0), (1, 1))]
    def f(g):
        for i, puff in enumerate(puffs[:n]):
            for x, y in puff:
                px(g, x, y, 6 if i < 2 else 3)
    return f


def messy(g, dy=0):
    for x, y in ((5, 5), (6, 3), (26, 4), (27, 6), (17, 0)):
        px(g, x, y + dy, 2)


def fix_hair(g):
    """右手（觀眾右邊）舉到側髮整理頭髮。"""
    rect(g, 23, 16, 27, 22, 1)
    rect(g, 24, 17, 26, 21, 11)
    rect(g, 26, 14, 28, 17, 1)
    rect(g, 27, 15, 27, 16, 4)


def paper(g):
    """「申請書」小圖示（右上角）。"""
    rect(g, 26, 0, 31, 6, 1)
    rect(g, 27, 1, 30, 5, 6)
    rect(g, 27, 2, 29, 2, 3); rect(g, 27, 4, 30, 4, 3)
    px(g, 30, 1, 9)


def qmark(x=25, y=0, col=6):
    """頭上冒出的大問號：白字黑框（當機中）。"""
    Q = [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."]
    def f(g):
        pts = [(x + 1 + i, y + 1 + j) for j, row in enumerate(Q) for i, ch in enumerate(row) if ch == "#"]
        for qx, qy in pts:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    px(g, qx + dx, qy + dy, 1)
        for qx, qy in pts:
            px(g, qx, qy, col)
    return f


def both(*fs):
    def f(g):
        for k in fs:
            if k:
                k(g)
    return f


def headpat():
    F = v6.front
    return [
        F(dy=1, eyes="closed"),                                      # 按鈕觸發：頭被壓一下
        F(eyes="blank", fx=qmark()),                                 # 眼神清空、頭上冒問號
        F(dy=1, eyes="blank", fx=qmark(y=1)),                        # 再被摸一下
        F(eyes="blank", fx=qmark()),
        F(eyes="blank", arms="grip", extra=messy, fx=qmark(col=9)),  # 身體僵直（問號變紅）
        F(eyes="blank", arms="grip", extra=lambda g: (messy(g), ears(g)), fx=steam(2)),   # 耳朵染紅、冒煙
        F(eyes="blank", arms="grip", blush=True, extra=lambda g: (messy(g), ears(g)), fx=steam(4)),
        F(eyes="down", blush=True, extra=lambda g: (messy(g), ears(g), fix_hair(g))),     # 整理頭髮
        F(eyes="down", blush=True, extra=lambda g: (ears(g), fix_hair(g))),
        F(eyes="stern", blush=True, extra=ears, fx=paper),           # 嚴肅警告：請先提交申請書
        F(eyes="stern", mouth="open", blush=True, dy=-1, extra=lambda g: ears(g, -1), fx=paper),
        F(eyes="stern", blush=True, extra=ears, fx=paper),
    ]


def half(f):
    return [row[::2] for row in f[::2]]


def scenes_x1():
    S = _v6_scenes()
    for n in ("desk_sleep_l", "bed_sleep_l"):  # 使用者要求移除朝左版本（需要時在 ESP32 上水平翻轉 _r）
        S.pop(n, None)
    base = v3.girl()
    up = v4.stretch(base, 0)          # 腰以上往上 1 格，腳不動
    S["idle"] = [[[3 if c == 13 else c for c in row] for row in f] for f in (base, up, base, up)]  # 單純上下呼吸
    S["headpat"] = [[[3 if c == 13 else c for c in row] for row in f] for f in headpat()]
    return {n: [half(f) for f in fr] for n, fr in S.items()}


v4.DUR["headpat"] = 300


v4.scenes = scenes_x1


def previews():
    S = v4.scenes()
    names = list(S)
    sw, sh = 64, 32  # 板子大小
    frames, durs = [], []
    for n in names:
        reps = max(2, 8 // len(S[n]))
        for _ in range(reps):
            for f in S[n]:
                bg = Image.new("RGBA", (sw, sh), (24, 26, 38, 255))
                im = v4.to_img(f)
                bg.alpha_composite(im, ((sw - im.width) // 2, sh - im.height))
                frames.append(bg.convert("RGB").resize((sw * ZOOM, sh * ZOOM), Image.NEAREST))
                durs.append(v4.DUR[n])
    frames[0].save(os.path.join(v4.OUT, "girl_preview.gif"), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0)
    sheet = Image.open(os.path.join(v4.OUT, "girl_sheet.png"))
    os.remove(os.path.join(v4.OUT, "girl_sheet_x3.png")) if os.path.exists(os.path.join(v4.OUT, "girl_sheet_x3.png")) else None
    sheet.resize((sheet.width * ZOOM, sheet.height * ZOOM), Image.NEAREST).save(os.path.join(v4.OUT, "girl_sheet_x6.png"))


if __name__ == "__main__":
    v4.export()
    p = os.path.join(v4.OUT, "pet_sprites.h")
    txt = open(p).read().replace("由 make_girl_weapon.py 產生", "由 make_girl_v7.py 產生（1 倍，板子 64x32）")
    open(p, "w").write(txt)
    previews()
