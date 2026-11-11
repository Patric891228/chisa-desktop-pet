"""動畫 v3：idle（原位/右上/原位/左上）、側面走路 4 幀、側面跑步 2 幀、打呼（鼻涕泡變大後破掉）。
32x32 繪製，2 倍放大成 64x64。用法：python3 make_girl_anim.py
側面只畫朝右，朝左時在 ESP32 上水平翻轉即可。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_cat as mc
import make_girl_8bit_v2 as v2
from make_girl_8bit import blank, px, rect, ellipse, outline, sprite, up2

girl = v2.girl
line = v2.line


# ---------- 側面（朝右） ----------
def leg(g, hip, dy, s, lift, shoe):
    top, bot = 27 + dy, 29 - lift
    n = bot - top + 1
    x = hip
    for i, y in enumerate(range(top, bot + 1)):
        x = round(hip + s * (i + 1) / n)
        rect(g, x, y, x + 1, y, 12)
    rect(g, x, bot + 1, x + 2, bot + 1, shoe)


def arm(g, sx, sy, a, border=False):
    ex, ey = sx + a, sy + 3
    n = 3
    pts = [(round(sx + (ex - sx) * i / n), round(sy + (ey - sy) * i / n)) for i in range(n + 1)]
    if border:
        for x, y in pts:
            rect(g, x - 2, y - 1, x + 2, y + 1, 1)
        rect(g, ex - 1, ey + 2, ex + 1, ey + 2, 1)
    for x, y in pts:
        rect(g, x - 1, y, x + 1, y, 11)
    px(g, ex, ey + 1, 4)


def side(dy=0, near=0, far=0, near_lift=0, far_lift=0, arm_near=0, arm_far=0,
         lean=0, flow=0, eyes="open", mouth="dot", fx=None):
    g = blank()
    hx, hy = 15 + lean, 11 + dy
    hip = 14 + lean
    rect(g, 8, 31, 23, 31, 14)
    # 後髮：往後（左）飄
    for y in range(hy, 26 + dy):
        k = (y - hy) / 14
        off = -round(flow * k * 2)
        for x in range(hx - 11 + off, hx + 1 - (3 if y > 20 + dy else 0)):
            if y >= 23 + dy and (x - hx) % 4 == 0:
                continue
            px(g, x, y, 2)
    # 遠側手腳
    arm(g, hip + 2, 21 + dy, arm_far)
    leg(g, hip, dy, far, far_lift, 1)
    # 身體
    rect(g, 11 + lean, 20 + dy, 18 + lean, 25 + dy, 11)
    rect(g, 10 + lean, 24 + dy, 19 + lean, 26 + dy, 12)
    rect(g, 12 + lean, 20 + dy, 18 + lean, 20 + dy, 6)
    rect(g, 18 + lean, 21 + dy, 19 + lean, 22 + dy, 9)
    px(g, 19 + lean, 23 + dy, 10)
    # 近側腳
    leg(g, hip + 1, dy, near, near_lift, 1)
    # 頭
    ellipse(g, hx, hy, 12, 10.5, 2)
    face = blank()
    ellipse(face, hx + 3, hy + 2, 8.5, 7.5, 4, ymin=hy - 1)
    for y in range(32):
        for x in range(32):
            if face[y][x] and x >= hx - 1:
                g[y][x] = 4
    for x in range(hx, hx + 12, 3):  # 瀏海
        px(g, x, hy - 1, 2)
    rect(g, hx - 2, hy, hx - 1, hy + 9, 2)  # 耳側頭髮
    px(g, hx + 1, hy - 11, 2); px(g, hx + 2, hy - 12, 2)  # 呆毛
    for x in range(hx - 7, hx + 5):
        if x % 3:
            px(g, x, hy - 7, 3)
    sprite(g, hx - 9, hy - 8, ["##.##", "#####", "##.##"], 9)
    px(g, hx - 7, hy - 7, 10)
    # 眼睛（只看到一隻）
    e, ey = hx + 6, hy + 2
    if eyes == "open":
        rect(g, e, ey, e + 1, ey, 1)
        rect(g, e, ey + 1, e + 1, ey + 1, 8)
        rect(g, e, ey + 2, e + 1, ey + 4, 7)
        px(g, e, ey + 1, 6)
    elif eyes == "closed":
        rect(g, e - 1, ey + 4, e + 1, ey + 4, 1)
    rect(g, hx + 4, ey + 5, hx + 5, ey + 5, 13)
    if mouth == "dot":
        px(g, hx + 8, hy + 7, 5)
    elif mouth == "open":
        rect(g, hx + 7, hy + 7, hx + 8, hy + 7, 10)
    # 近側手（畫在最前面）
    arm(g, hip + 2, 21 + dy, arm_near, border=True)
    g = outline(g)
    if fx:
        fx(g)
    return up2(g)


def speed_lines(g, k):
    for y, x0, n in ((13, 0 + k, 3), (19, 1 - k, 4), (25, 0 + k, 3)):
        rect(g, x0, y, x0 + n - 1, y, 14)


# ---------- idle 位移 ----------
def shifted(g, dx, dy):
    """整隻角色位移 (dx, dy)（64 格座標），地面影子留在原處。"""
    o = [[0] * 64 for _ in range(64)]
    for y in range(64):
        for x in range(64):
            c = g[y][x]
            if c == 14:
                o[y][x] = 14
    for y in range(64):
        for x in range(64):
            c = g[y][x]
            if c and c != 14 and 0 <= x + dx < 64 and 0 <= y + dy < 64:
                o[y + dy][x + dx] = c
    return o


# ---------- 打呼泡泡 ----------
def bubble(r, dy):
    def f(g):
        cx, cy = 20 + r, 18 + dy - r // 2
        if r == 0:
            return
        if r < 0:  # 破掉：四周噴點
            for ddx, ddy in ((-3, -3), (3, -3), (-3, 3), (3, 3), (0, -4), (4, 0)):
                px(g, 22 + ddx, 16 + dy + ddy, 15)
            px(g, 22, 16 + dy, 6)
            return
        for y in range(32):
            for x in range(32):
                d = ((x + .5 - cx) ** 2 + (y + .5 - cy) ** 2) ** .5
                if r - 1 <= d <= r + .2 or (r == 1 and d <= 1):
                    g[y][x] = 15
        px(g, round(cx - r / 2), round(cy - r / 2), 6)
    return f


def scenes():
    S = {}
    base = girl()
    S["idle"] = [base, shifted(base, 2, -2), base, shifted(base, -2, -2)]
    S["walk"] = [
        side(near=2, far=-2, arm_near=-3, arm_far=3, flow=1),
        side(dy=-1, near=0, far=0, far_lift=1, arm_near=0, arm_far=0, flow=1),
        side(near=-2, far=2, arm_near=3, arm_far=-3, flow=1),
        side(dy=-1, near=0, far=0, near_lift=1, flow=1),
    ]
    S["run"] = [
        side(dy=-1, near=3, far=-3, far_lift=2, arm_near=-4, arm_far=4, lean=1, flow=2, mouth="open",
             fx=lambda g: speed_lines(g, 0)),
        side(dy=0, near=-3, far=3, near_lift=2, arm_near=4, arm_far=-4, lean=1, flow=2, mouth="open",
             fx=lambda g: speed_lines(g, 1)),
    ]
    snore = [(0, 1), (1, 2), (1, 3), (0, 4), (0, -1), (1, 0)]  # (身體浮動, 泡泡半徑；-1 = 破掉)
    S["snore"] = [girl(dy=dy, eyes="closed", arms="front", fx=bubble(r, dy)) for dy, r in snore]
    return S


if __name__ == "__main__":
    mc.PAL[:] = v2.PAL
    mc.scenes = scenes
    mc.DUR.update({"idle": 250, "walk": 160, "run": 110, "snore": 300})
    mc.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_anim")
    os.makedirs(mc.OUT, exist_ok=True)
    mc.main()
    for f in os.listdir(mc.OUT):
        if f.startswith("cat_"):
            os.replace(os.path.join(mc.OUT, f), os.path.join(mc.OUT, "girl_" + f[4:]))
