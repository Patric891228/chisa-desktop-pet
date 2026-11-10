"""v6：深綠書皮、正面公主切、仰躺睡姿，新增社恐（電線杆）、初識防備、熟悉後害羞、收禮物。
調色盤 7 改成深綠（眼睛改用 9 紅）。用法：python3 make_girl_v6.py
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_girl_v5 as v5
import make_girl_weapon as v4
import make_girl_v3 as v3
from make_girl_8bit import px as px32, rect as rect32

GREEN = 7
v4.PAL[7] = (34, 92, 60)   # 7 深綠（書皮）
v4.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_v6")
px, rect, blank, paste, finish, ellipse = v5.px, v5.rect, v5.blank, v5.paste, v5.finish, v5.ellipse


# ---------- 讀書：深綠書皮（觀眾看到的是封面） ----------
def read(eyes="down", mouth="dot", dy=0, fx=None):
    W, H, o = 48, 32, 0  # 96x64，右邊留給燈泡
    g = blank(W, H)
    paste(g, v3.girl(eyes=eyes, mouth=mouth, dy=dy, arms="none", raw=True), 0, o)
    for x0 in (7, 22):
        rect(g, x0 - 1, o + 20 + dy, x0 + 3, o + 25 + dy, 1)
        rect(g, x0, o + 21 + dy, x0 + 2, o + 24 + dy, 11)
    bt = o + 20 + dy
    # 攤開的書，從中間書脊往兩邊翹起：外側比中間高 2 格，上下緣都是弧線
    def lift(x):
        d = abs(x - 15.5) / 7.5
        return round(2 * d * d)
    for x in range(8, 24):
        u = lift(x)
        top, bot = bt - u, bt + 5 - u + (1 if x in (8, 23) else 0)
        rect(g, x, top - 1, x, bot + 1, 1)                       # 外框
        if 9 <= x <= 22:
            rect(g, x, top, x, top, 6)                           # 上緣露出的書頁（跟著弧度）
            rect(g, x, top + 1, x, bot, GREEN)                   # 深綠書皮
    rect(g, 15, bt, 16, bt + 6, 1)                               # 書脊（最低點）
    for cx in (12, 19):                                          # 金色燙金標誌（跟著弧度往上）
        yy = bt - lift(cx)
        px(g, cx, yy + 2, 14); px(g, cx - 1, yy + 3, 14); px(g, cx + 1, yy + 3, 14); px(g, cx, yy + 4, 14)
    rect(g, 9, bt, 10, bt + 1, 4); rect(g, 21, bt, 22, bt + 1, 4)  # 雙手扶在翹起來的書邊
    return finish(g, o + 31, fx)


v5.read = read


# ---------- 仰躺：臉朝上的側面 ----------
def bed_sleep(b=0, fx=None, flip=False):
    W, H = 48, 36
    g = blank(W, H)
    rect(g, 1, 35, 46, 35, v4.SHADOW)
    rect(g, 1, 14, 5, 14, v5.WOOD); rect(g, 2, 15, 4, 34, v5.WOOD); rect(g, 3, 16, 3, 32, v5.WOOD_HI)
    rect(g, 42, 20, 46, 20, v5.WOOD); rect(g, 43, 21, 45, 34, v5.WOOD); rect(g, 44, 22, 44, 32, v5.WOOD_HI)
    rect(g, 5, 25, 42, 27, 6); rect(g, 5, 28, 42, 28, 8)
    rect(g, 5, 29, 42, 29, v5.WOOD_HI); rect(g, 5, 30, 42, 31, v5.WOOD)
    rect(g, 6, 32, 7, 34, v5.WOOD); rect(g, 40, 32, 41, 34, v5.WOOD)
    rect(g, 6, 21, 18, 24, 6); rect(g, 6, 24, 18, 24, 8)        # 枕頭
    ellipse(g, 9, 22, 6, 3, 2)                                  # 枕頭上的頭髮
    rect(g, 4, 21, 8, 25, 2)
    # 身體（仰躺，背貼床、胸口朝上）
    rect(g, 22, 20 - b, 31, 24, 11)
    rect(g, 22, 20 - b, 23, 24, 6)                               # 水手領
    rect(g, 24, 19 - b, 25, 19 - b, 9)                           # 領巾
    rect(g, 32, 20, 32, 24, 1)
    rect(g, 33, 20, 36, 24, 12)
    for y in (21, 23):
        rect(g, 33, y, 36, y, 13)
    rect(g, 37, 22, 37, 24, 4)                                   # 膝蓋
    rect(g, 38, 22, 40, 24, 12)
    rect(g, 41, 20, 41, 24, 1); px(g, 42, 20, 1); px(g, 41, 21, 8)  # 鞋尖朝上
    rect(g, 26, 18 - b, 31, 19 - b, 11); rect(g, 31, 18 - b, 31, 19 - b, 8)  # 手放肚子上
    rect(g, 32, 18 - b, 33, 19 - b, 4)
    # 頭：側面頭逆時針轉 90 度（臉朝上），閉眼改畫成橫的
    head = v5.rot_ccw(v5.head_side("none", "dot"))
    rect32(head, 16, 9, 18, 9, 1); px32(head, 15, 8, 1); px32(head, 19, 8, 1)
    paste(head_layer := blank(48, 36), head, 0, 0)
    paste(g, head, 3, -4)
    return finish(g, 35, fx, flip)


# v5.bed_sleep = bed_sleep  # 使用者要求改回 v5 的躺睡（正面臉靠在枕頭上）


# ---------- 小特效 ----------
def bang(x, y):
    """紅色驚嘆號。"""
    def f(g):
        rect(g, x - 1, y - 1, x + 1, y + 6, 1)
        rect(g, x, y, x, y + 3, 9)
        px(g, x, y + 5, 9)
        px(g, x, y + 4, 1)
    return f


def sweat(x, y):
    def f(g):
        px(g, x, y, 6); px(g, x - 1, y + 1, 6); px(g, x, y + 1, 6); px(g, x, y + 2, 13)
        px(g, x + 1, y + 1, 1); px(g, x - 1, y + 2, 1); px(g, x + 1, y + 2, 1)
    return f


def dots(x, y, n=3):
    def f(g):
        for i in range(n):
            px(g, x + i * 2, y, 6)
    return f


def sparkle(x, y):
    def f(g):
        px(g, x, y, 6); px(g, x - 1, y, 14); px(g, x + 1, y, 14); px(g, x, y - 1, 14); px(g, x, y + 1, 14)
    return f


def small_heart(x, y):
    def f(g):
        v5.paste(g, [[9, 0, 9], [9, 9, 9], [0, 9, 0]], x, y)
    return f


both = v5.both


def front(fx=None, extra=None, **kw):
    """正面角色（32x32），可在描邊前加道具（extra）、描邊後加特效（fx）。"""
    g = v3.girl(raw=True, **kw)
    if extra:
        extra(g)
    return finish(g, 31, fx)


# ---------- 社恐：躲在電線杆後面 ----------
def pole_peek(dx, eyes="open", look=0, fx=None, rise=1.0, wire=1.0, dust=False, **kw):
    """rise：電線杆從地板下伸出來的比例（0 = 還在地下，1 = 整根）；wire：電線往兩邊拉出去的比例。"""
    W, H, o = 32, 32, 0
    back, front_ = blank(W, H), blank(W, H)
    n = round(15 * wire)                                         # 電線從杆子往兩邊拉
    if n:
        rect(back, 16 - n, 2, 15 + n, 2, 13); rect(back, 16 - n, 6, 15 + n, 6, 13)
    rect(front_, 4, 3, 27, 4, v5.WOOD)                           # 橫擔
    for x in (6, 25, 10, 21):                                    # 礙子
        px(front_, x, 2, 6)
    rect(front_, 11, 0, 20, 30, 1)                               # 電線杆外框
    rect(front_, 12, 0, 19, 30, 8)
    rect(front_, 13, 0, 13, 30, 6)                               # 亮邊
    rect(front_, 18, 0, 19, 30, 13)                              # 暗邊
    for y in range(22, 27):                                      # 黃黑警示條紋
        for x in range(12, 20):
            px(front_, x, y, 14 if (x + y) % 4 < 2 else 1)
    rect(front_, 14, 8, 17, 11, 6); rect(front_, 15, 9, 16, 10, 13)   # 小告示牌
    off = round((1 - rise) * 31)

    def sunk(layer):                                             # 往下移 off 格，地板（y=30）以下切掉
        out = blank(W, H)
        for y in range(H):
            sy = y - off
            if 0 <= sy < H and y <= 30:
                out[y] = layer[sy][:]
        return out

    g = blank(W, H)
    paste(g, v3.girl(raw=True, eyes=eyes, look=look, **kw), dx, o)   # 角色在最後面
    if rise > 0:
        paste(g, sunk(back), 0, 0)                               # 電線
        paste(g, sunk(front_), 0, 0)                             # 電線杆
    rect(g, 4, 31, 27, 31, v4.SHADOW)
    if 0 < rise < 1 or dust:                                     # 地板裂開、碎屑
        rect(g, 10, 30, 21, 30, 1)
        for x, y in ((8, 29), (9, 28), (23, 29), (22, 28), (7, 27), (24, 27)):
            px(g, x, y, 6)
    return finish(g, 31, fx)


def lean_back(dx):
    """上半身往後（觀眾右邊）縮 dx 格，腳不動：嫌棄地往後退。"""
    def f(g):
        for y in range(0, 25):
            row = g[y]
            g[y] = [0] * dx + row[:-dx]
    return f


def anger(x, y):
    """紅色的青筋符號（生氣／不好意思）。"""
    pts = [(1, 0), (3, 0), (0, 1), (4, 1), (1, 3), (3, 3), (0, 3), (4, 3), (1, 4), (3, 4)]
    pts = [(1, 0), (0, 1), (1, 1), (3, 0), (3, 1), (4, 1), (0, 3), (1, 3), (1, 4), (3, 3), (4, 3), (3, 4)]
    def f(g):
        for dx, dy in pts:
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    px(g, x + dx + ox, y + dy + oy, 1) if g[min(max(y + dy + oy, 0), len(g) - 1)][min(max(x + dx + ox, 0), len(g[0]) - 1)] == 0 else None
        for dx, dy in pts:
            px(g, x + dx, y + dy, 9)
    return f


def tsun_side(eyes="closed", puff=False, fx=None):
    """「哼」地轉頭：側面朝左、臉紅，嘴前面噴一小團氣。"""
    g = v3.side(raw=True, eyes=eyes, lean=-1)
    hx, hy = 15 - 1, 11
    rect(g, hx + 3, hy + 7, hx + 6, hy + 7, 5)
    px(g, hx + 4, hy + 7, 9); px(g, hx + 6, hy + 7, 9)
    if puff:
        for x, y in ((hx + 11, hy + 7), (hx + 12, hy + 6), (hx + 12, hy + 8), (hx + 13, hy + 7), (hx + 14, hy + 6)):
            px(g, x, y, 6)
    g = v5.mirror(g)
    if fx:
        fx(g)
    return v4.up2(g)


def scribble(x, y):
    """頭旁邊一團亂線（嫌棄、不爽）。"""
    pts = [(1, 0), (2, 0), (3, 1), (2, 2), (1, 2), (0, 3), (1, 4), (2, 4), (3, 4), (4, 3), (4, 5), (3, 6), (2, 6), (1, 5)]
    def f(g):
        for dx, dy in pts:
            px(g, x + dx, y + dy, 8)
    return f


def scenes():
    S = _v5_scenes()
    S["shy_pole"] = [
        pole_peek(0, rise=0, fx=bang(28, 2)),                    # 被看到了！
        pole_peek(0, eyes="closed", rise=0.35, wire=0),          # 地板下伸出電線杆
        pole_peek(0, eyes="closed", rise=0.7, wire=0),
        pole_peek(-2, rise=1, wire=0.4, dust=True),
        pole_peek(-7),                                           # 躲好了，偷看
        pole_peek(-7, eyes="closed"),
        pole_peek(-1, look=1),
        pole_peek(4, fx=sweat(30, 6)),
        pole_peek(4, fx=both(sweat(30, 6), bang(29, 1))),
        pole_peek(-7),
        pole_peek(-4, rise=0.6, wire=0.3, blush=True),          # 電線杆收回地板下
        pole_peek(-2, rise=0.25, wire=0, blush=True),
        pole_peek(0, rise=0, blush=True, eyes="down"),
    ]
    # 防備（傲嬌）：臉紅、嘟嘴、冒青筋，然後「哼」地轉頭，偷偷回頭瞄一眼又轉回去
    S["guard"] = [
        front(),
        front(eyes="closed", mouth="wavy", blush=True, arms="front", fx=anger(25, 2)),
        tsun_side(eyes="closed", puff=True),
        tsun_side(eyes="open"),
        tsun_side(eyes="closed", puff=True, fx=anger(3, 2)),
    ]
    S["shy"] = [
        front(dy=-1, mouth="open", fx=bang(28, 2)),
        front(blush=True),
        front(eyes="down", blush=True, arms="fingers", poke=0, dy=1, fx=dots(25, 6)),
        front(eyes="down", blush=True, arms="fingers", poke=1, dy=1, fx=dots(25, 6)),
    ]

    def gear(g):
        cx, cy = 16, 21
        for a in range(0, 360, 45):
            r = math.radians(a)
            px32(g, round(cx + 3 * math.cos(r)), round(cy + 3 * math.sin(r)), 14)
        for y in range(cy - 2, cy + 3):
            for x in range(cx - 2, cx + 3):
                if (x - cx) ** 2 + (y - cy) ** 2 <= 5:
                    px32(g, x, y, 14)
        px32(g, cx, cy, v5.WOOD)

    S["gift"] = [
        front(arms="hold", extra=gear),
        front(arms="hold", extra=gear, fx=both(sparkle(6, 10), sparkle(26, 10))),
        front(arms="behind", dy=-1, fx=both(dots(1, 22, 2), dots(27, 22, 2))),
        front(arms="behind", eyes="down", blush=True, fx=small_heart(26, 8)),
    ]
    return S


_v5_scenes = v5.scenes

# ---------- 打瞌睡泡泡改淺藍色 ----------
# 調色盤沒空位：把 13（百褶亮線、影子、刀光）併進相近的 3（頭髮亮部），13 改成淺藍色只給泡泡用。
# 泡泡先用暫時的 16 號畫，輸出前再換成 13。
v4.PAL[13] = (150, 205, 255)
TMP_BLUE = 16


def bubble(r, dy):
    def f(g):
        cx, cy = 20 + r, 18 + dy - r // 2
        if r == 0:
            return
        if r < 0:
            for ddx, ddy in ((-3, -3), (3, -3), (-3, 3), (3, 3), (0, -4), (4, 0)):
                px32(g, 22 + ddx, 16 + dy + ddy, TMP_BLUE)
            px32(g, 22, 16 + dy, 6)
            return
        for y in range(32):
            for x in range(32):
                d = ((x + .5 - cx) ** 2 + (y + .5 - cy) ** 2) ** .5
                if r - 1 <= d <= r + .2 or (r == 1 and d <= 1):
                    g[y][x] = TMP_BLUE
        px32(g, round(cx - r / 2), round(cy - r / 2), 6)
    return f


v3.bubble = bubble


def scenes_remapped():
    S = scenes()
    remap = {13: 3, TMP_BLUE: 13}
    return {n: [[[remap.get(c, c) for c in row] for row in f] for f in frames] for n, frames in S.items()}


v4.scenes = scenes_remapped
v4.DUR.update({"shy_pole": 280, "guard": 320, "shy": 320, "gift": 380})

if __name__ == "__main__":
    v4.export()
