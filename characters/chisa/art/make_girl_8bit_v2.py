"""8-bit 二頭身 v2：依 Q 版參考圖調整（寬袖外套、黑襪、髮帶垂帶、呆毛、背後紅色大刃）。
在 32x32 畫，再 2 倍放大成 64x64。用法：python3 make_girl_8bit_v2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_cat as mc
import make_girl_8bit as b8
from make_girl_8bit import blank, px, rect, ellipse, outline, sprite, heart, zz, star, up2

PAL = list(b8.PAL)
PAL[11] = (100, 100, 148)   # 外套（比頭髮亮，手臂才看得出來）
PAL[12] = (34, 34, 56)    # 內襯、裙子、黑襪
PAL[3] = (110, 108, 160)  # 頭髮亮部


def line(g, x0, y0, x1, y1, c, w=1):
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = y0 + (y1 - y0) * i / n
        for k in range(w):
            px(g, x, y + k, c)


def girl(dy=0, eyes="open", mouth="dot", sway=0, look=0, arms="down", tilt=0, blade=False, fx=None):
    g = blank()
    hx, hy = 16 + tilt, 11 + dy
    rect(g, 7, 31, 24, 31, 14)
    # 後髮：長直髮，髮尾分岔
    for y in range(hy, 30):
        off = sway if y >= 23 else 0
        cx = 16 + tilt * (y < 21) + off
        for x in range(cx - 11, cx + 11):
            if y >= 26 and (x - cx) % 4 == 0:
                continue
            px(g, x, y, 2)
    # 背後的紅色大刃
    if blade:
        line(g, 2, 28, 28, 15 + dy, 10, 3)
        line(g, 2, 28, 28, 15 + dy, 9, 2)
        ellipse(g, 28.5, 13.5 + dy, 2.5, 2.5, 12)
        px(g, 28, 13 + dy, 9)
    # 伸懶腰：舉起的袖子在頭後面
    if arms == "up":
        for ax in (4, 27):
            rect(g, ax - 1, hy - 3, ax + 1, 23 + dy, 11)
            rect(g, ax - 1, hy - 4, ax + 1, hy - 4, 4)
    # 外套與內襯（身體縮短）
    rect(g, 10, 20 + dy, 21, 26 + dy, 11)
    rect(g, 13, 20 + dy, 18, 24 + dy, 12)
    rect(g, 12, 24 + dy, 19, 27, 12)
    # 黑襪與鞋
    for lx in (13, 17):
        rect(g, lx, 28, lx + 1, 28, 12)
        rect(g, lx, 29, lx + 1, 30, 1)
    # 寬袖
    if arms in ("down", "wave", "front"):
        rect(g, 7, 21 + dy, 9, 25 + dy, 11)
        px(g, 8, 26 + dy, 4)
    if arms in ("down", "front"):
        rect(g, 22, 21 + dy, 24, 25 + dy, 11)
        px(g, 23, 26 + dy, 4)
    if arms == "wave":
        rect(g, 24, 16 + dy, 26, 21 + dy, 11)
        rect(g, 24, 15 + dy, 26, 15 + dy, 4)
    if arms == "front":
        rect(g, 12, 24 + dy, 19, 25 + dy, 11)
        rect(g, 15, 26 + dy, 16, 26 + dy, 4)
    # 大頭
    ellipse(g, hx, hy, 12.5, 10.5, 2)
    ellipse(g, hx, hy + 2, 9.5, 7.5, 4, ymin=hy - 1)
    # 呆毛
    px(g, hx + 1, hy - 11, 2); px(g, hx + 2, hy - 12, 2)
    # 齊瀏海鋸齒
    for x in range(hx - 8, hx + 9, 3):
        px(g, x, hy - 1, 2)
    # 公主切側髮
    for s in (-1, 1):
        rect(g, hx + s * 9 - (0 if s > 0 else 1), hy, hx + s * 9 + (1 if s > 0 else 0), hy + 10, 2)
    # 頭髮光澤
    for x in range(hx - 7, hx + 5):
        if x % 3:
            px(g, x, hy - 7, 3)
    # 水手領、紅領巾（在下巴下方）
    rect(g, 12, 20 + dy, 19, 20 + dy, 6)
    px(g, 13, 21 + dy, 6); px(g, 18, 21 + dy, 6)
    rect(g, 15, 21 + dy, 16, 22 + dy, 9); px(g, 15, 23 + dy, 10); px(g, 16, 23 + dy, 9)
    # 紅髮帶
    sprite(g, hx - 13, hy - 7, ["##.##", "#####", "##.##"], 9)
    px(g, hx - 11, hy - 6, 10)
    for i in range(3):
        px(g, hx - 12, hy - 4 + i, 9)
    # 大眼睛（3x4）
    ey = hy + 2
    for ex in (hx - 6, hx + 3):
        e = ex + look
        if eyes == "open":
            rect(g, e, ey, e + 2, ey, 1)
            rect(g, e, ey + 1, e + 2, ey + 1, 8)
            rect(g, e, ey + 2, e + 2, ey + 4, 7)
            px(g, e, ey + 1, 6); px(g, e + 2, ey + 3, 9)
        elif eyes == "half":
            rect(g, e, ey + 3, e + 2, ey + 3, 1)
            rect(g, e, ey + 4, e + 2, ey + 4, 7)
        elif eyes == "closed":
            rect(g, e, ey + 4, e + 2, ey + 4, 1)
        elif eyes == "happy":
            px(g, e + 1, ey + 2, 1); px(g, e, ey + 3, 1); px(g, e + 2, ey + 3, 1)
    # 腮紅
    rect(g, hx - 8, ey + 5, hx - 7, ey + 5, 13); rect(g, hx + 6, ey + 5, hx + 7, ey + 5, 13)
    # 嘴
    my = hy + 8
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


def scenes():
    S = {}
    S["idle"] = [girl(), girl(dy=1), girl(dy=1, sway=1), girl(sway=1)]
    S["blink"] = [girl(), girl(eyes="half"), girl(eyes="closed"), girl(eyes="half")]
    S["happy"] = [
        girl(eyes="happy", mouth="open", arms="wave", fx=lambda g: heart(g, 25, 2)),
        girl(dy=-1, eyes="happy", mouth="open", arms="wave", sway=-1, fx=lambda g: heart(g, 25, 1)),
        girl(dy=-2, eyes="happy", mouth="open", arms="wave", sway=-1, fx=lambda g: (heart(g, 25, 0), star(g, 1, 17))),
        girl(dy=-1, eyes="happy", mouth="open", arms="wave", fx=lambda g: star(g, 1, 15)),
    ]
    S["sleep"] = [
        girl(eyes="closed", arms="front", fx=lambda g: zz(g, 24, 3)),
        girl(dy=1, eyes="closed", arms="front", fx=lambda g: (zz(g, 24, 3), zz(g, 28, -1))),
        girl(dy=1, eyes="closed", arms="front", tilt=-1, fx=lambda g: zz(g, 26, 0)),
        girl(eyes="closed", arms="front", tilt=-1),
    ]
    S["stretch"] = [girl(), girl(eyes="half", arms="up", dy=-1), girl(eyes="closed", mouth="yawn", arms="up", dy=-1),
                    girl(eyes="half", mouth="yawn", arms="up")]
    S["look"] = [girl(look=-1), girl(look=-1, tilt=-1), girl(look=1), girl(look=1, tilt=1)]
    return S


if __name__ == "__main__":
    mc.PAL[:] = PAL
    mc.scenes = scenes
    mc.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_8bit_v2")
    os.makedirs(mc.OUT, exist_ok=True)
    mc.main()
    for f in os.listdir(mc.OUT):
        if f.startswith("cat_"):
            os.replace(os.path.join(mc.OUT, f), os.path.join(mc.OUT, "girl8v2_" + f[4:]))
