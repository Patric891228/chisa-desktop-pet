"""8-bit 二頭身版：在 32x32 畫粗像素，再 2 倍放大成 64x64（螢幕上仍是 64x64 素材）。
用法：python3 make_girl_8bit.py   （需要 Pillow；共用 make_cat.py 的輸出流程）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_cat as mc

N = 32
# 偏紅白機風格的少色調色盤（實際只用約 10 色）
PAL = [
    (0, 0, 0),        # 0 透明
    (16, 12, 24),     # 1 外框黑
    (40, 40, 72),     # 2 頭髮
    (88, 88, 140),    # 3 頭髮亮部
    (252, 216, 168),  # 4 皮膚
    (228, 160, 136),  # 5 皮膚陰影/腮紅
    (252, 252, 252),  # 6 白
    (216, 40, 0),     # 7 眼睛紅
    (120, 0, 16),     # 8 眼睛深紅
    (248, 56, 56),    # 9 紅（髮帶、領巾、愛心）
    (168, 16, 32),    # 10 紅陰影
    (60, 60, 92),     # 11 制服
    (32, 32, 56),     # 12 制服陰影/裙
    (248, 120, 152),  # 13 粉紅
    (80, 64, 96),     # 14 地面影子
    (104, 160, 252),  # 15 Z 藍
]


def blank():
    return [[0] * N for _ in range(N)]


def px(g, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < N and 0 <= y < N:
        g[y][x] = c


def rect(g, x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            px(g, x, y, c)


def ellipse(g, cx, cy, rx, ry, c, ymin=-99):
    for y in range(N):
        for x in range(N):
            if y >= ymin and ((x - cx + .5) / rx) ** 2 + ((y - cy + .5) / ry) ** 2 <= 1:
                g[y][x] = c


def outline(g):
    o = [r[:] for r in g]
    for y in range(N):
        for x in range(N):
            if g[y][x] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < N and 0 <= ny < N and g[ny][nx] not in (0, 1, 14, 15):
                        o[y][x] = 1
                        break
    return o


def sprite(g, x, y, rows, c):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                px(g, x + dx, y + dy, c)


def heart(g, x, y):
    sprite(g, x, y, ["##.##", "#####", ".###.", "..#.."], 9)


def zz(g, x, y):
    sprite(g, x, y, ["####", "..#.", ".#..", "####"], 15)


def star(g, x, y):
    sprite(g, x, y, [".#.", "#.#", ".#."], 13)


def girl(dy=0, eyes="open", mouth="dot", sway=0, look=0, arms="down", tilt=0, fx=None):
    g = blank()
    hx, hy = 16 + tilt, 10 + dy
    rect(g, 8, 30, 23, 30, 14)
    # 後髮
    for y in range(hy, 28):
        off = sway if y >= 22 else 0
        rect(g, 16 + tilt * (y < 20) - 9 + off, y, 16 + tilt * (y < 20) + 8 + off, y, 2)
    # 舉手（伸懶腰）在身體後面
    if arms == "up":
        for ax in (7, 24):
            rect(g, ax, hy - 3, ax, 20 + dy, 11)
            px(g, ax, hy - 4, 4)
    # 身體
    rect(g, 11, 18 + dy, 20, 23 + dy, 11)
    rect(g, 19, 19 + dy, 20, 23 + dy, 12)
    # 裙子
    rect(g, 10, 24 + dy, 21, 26, 12)
    for x in (12, 15, 18):
        px(g, x, 25, 11)
    # 腿與鞋
    for lx in (13, 17):
        rect(g, lx, 27, lx + 1, 28, 4)
        rect(g, lx, 29, lx + 1, 29, 1)
    # 手
    if arms == "down":
        for ax in (10, 21):
            rect(g, ax, 19 + dy, ax, 22 + dy, 11)
            px(g, ax, 23 + dy, 4)
    elif arms == "wave":
        rect(g, 10, 19 + dy, 10, 22 + dy, 11); px(g, 10, 23 + dy, 4)
        rect(g, 22, 15 + dy, 22, 19 + dy, 11); px(g, 22, 14 + dy, 4); px(g, 21, 19 + dy, 11)
    elif arms == "front":
        rect(g, 12, 21 + dy, 19, 21 + dy, 11); px(g, 15, 22 + dy, 4); px(g, 16, 22 + dy, 4)
    # 水手領與紅領巾
    rect(g, 12, 18 + dy, 19, 18 + dy, 6)
    px(g, 13, 19 + dy, 6); px(g, 18, 19 + dy, 6)
    rect(g, 15, 19 + dy, 16, 20 + dy, 9); px(g, 15, 21 + dy, 10); px(g, 16, 21 + dy, 9)
    # 頭（大頭：二頭身）
    ellipse(g, hx, hy, 9, 8.5, 2)
    ellipse(g, hx, hy + 1, 7, 6.5, 4, ymin=hy - 1)
    # 齊瀏海鋸齒
    for x in range(hx - 6, hx + 7, 3):
        px(g, x, hy - 1, 2)
    # 側髮（公主切）
    for s in (-1, 1):
        rect(g, hx + s * 7 - (1 if s > 0 else 0), hy, hx + s * 7 + (0 if s > 0 else 0), hy + 8, 2)
    # 頭髮光澤
    for x in range(hx - 5, hx + 3):
        if x % 3:
            px(g, x, hy - 6, 3)
    # 頸圈
    rect(g, hx - 1, hy + 7, hx + 1, hy + 7, 1)
    # 紅髮帶
    sprite(g, hx - 10, hy - 6, ["##.##", "#####", "##.##", ".#.#."], 9)
    px(g, hx - 8, hy - 5, 10)
    # 眼睛
    ey = hy + 1
    for ex in (hx - 4, hx + 2):
        e = ex + look
        if eyes == "open":
            rect(g, e, ey, e + 1, ey, 8)
            rect(g, e, ey + 1, e + 1, ey + 2, 7)
            px(g, e, ey + 1, 6)
        elif eyes == "half":
            rect(g, e, ey + 1, e + 1, ey + 1, 1)
            rect(g, e, ey + 2, e + 1, ey + 2, 7)
        elif eyes == "closed":
            rect(g, e, ey + 2, e + 1, ey + 2, 1)
        elif eyes == "happy":
            rect(g, e, ey + 1, e + 1, ey + 1, 1)
            px(g, e - 1 if ex < hx else e + 2, ey + 2, 1)
            px(g, e + 2 if ex < hx else e - 1, ey + 2, 1)
    # 腮紅
    px(g, hx - 5, ey + 3, 13); px(g, hx + 4, ey + 3, 13)
    # 嘴
    my = hy + 5
    if mouth == "dot":
        px(g, hx, my, 5)
    elif mouth == "open":
        rect(g, hx - 1, my, hx, my, 10)
    elif mouth == "yawn":
        rect(g, hx - 1, my - 1, hx, my, 10)
    g = outline(g)
    if fx:
        fx(g)
    return up2(g)


def up2(g):
    return [[g[y // 2][x // 2] for x in range(N * 2)] for y in range(N * 2)]


def scenes():
    S = {}
    S["idle"] = [girl(), girl(dy=1), girl(dy=1, sway=1), girl(sway=1)]
    S["blink"] = [girl(), girl(eyes="half"), girl(eyes="closed"), girl(eyes="half")]
    S["happy"] = [
        girl(eyes="happy", mouth="open", arms="wave", fx=lambda g: heart(g, 25, 4)),
        girl(dy=-1, eyes="happy", mouth="open", arms="wave", sway=-1, fx=lambda g: heart(g, 25, 2)),
        girl(dy=-2, eyes="happy", mouth="open", arms="wave", sway=-1, fx=lambda g: (heart(g, 26, 0), star(g, 2, 6))),
        girl(dy=-1, eyes="happy", mouth="open", arms="wave", fx=lambda g: star(g, 3, 4)),
    ]
    S["sleep"] = [
        girl(eyes="closed", arms="front", fx=lambda g: zz(g, 25, 5)),
        girl(dy=1, eyes="closed", arms="front", fx=lambda g: (zz(g, 25, 4), zz(g, 28, -1))),
        girl(dy=1, eyes="closed", arms="front", tilt=-1, fx=lambda g: zz(g, 27, 1)),
        girl(eyes="closed", arms="front", tilt=-1),
    ]
    S["stretch"] = [girl(), girl(eyes="half", arms="up", dy=-1), girl(eyes="closed", mouth="yawn", arms="up", dy=-1),
                    girl(eyes="half", mouth="yawn", arms="up")]
    S["look"] = [girl(look=-1), girl(look=-1, tilt=-1), girl(look=1), girl(look=1, tilt=1)]
    return S


if __name__ == "__main__":
    mc.PAL[:] = PAL
    mc.scenes = scenes
    mc.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_8bit")
    os.makedirs(mc.OUT, exist_ok=True)
    mc.main()
