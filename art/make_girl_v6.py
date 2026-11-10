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
    rect(g, 8, bt - 1, 23, bt + 6, 1)           # 外框
    rect(g, 9, bt, 22, bt, 6)                   # 上緣露出的書頁
    rect(g, 9, bt + 1, 22, bt + 5, GREEN)       # 深綠書皮
    rect(g, 15, bt + 1, 16, bt + 5, 1)          # 書背（中間摺線）
    for cx in (12, 19):                         # 金色燙金標誌
        px(g, cx, bt + 2, 14); px(g, cx - 1, bt + 3, 14); px(g, cx + 1, bt + 3, 14); px(g, cx, bt + 4, 14)
    rect(g, 9, bt + 2, 10, bt + 3, 4); rect(g, 21, bt + 2, 22, bt + 3, 4)  # 雙手
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
def pole_peek(dx, eyes="open", look=0, fx=None):
    W, H, o = 32, 32, 0
    g = blank(W, H)
    rect(g, 0, 2, 31, 2, 13); rect(g, 0, 6, 31, 6, 13)          # 電線
    paste(g, v3.girl(raw=True, eyes=eyes, look=look), dx, o)
    rect(g, 4, 3, 27, 4, v5.WOOD)                                # 橫擔
    px(g, 6, 2, 6); px(g, 25, 2, 6); px(g, 10, 2, 6); px(g, 21, 2, 6)  # 礙子
    rect(g, 11, 0, 20, 30, 1)                                    # 電線杆外框
    rect(g, 12, 0, 19, 30, 8)
    rect(g, 13, 0, 13, 30, 6)                                    # 亮邊
    rect(g, 18, 0, 19, 30, 13)                                   # 暗邊
    for y in range(22, 27):                                      # 黃黑警示條紋
        for x in range(12, 20):
            px(g, x, y, 14 if (x + y) % 4 < 2 else 1)
    rect(g, 14, 8, 17, 11, 6); rect(g, 15, 9, 16, 10, 13)      # 小告示牌
    rect(g, 4, 31, 27, 31, v4.SHADOW)
    return finish(g, 31, fx)


def scenes():
    S = _v5_scenes()
    S["shy_pole"] = [
        pole_peek(-7),
        pole_peek(-7, eyes="closed"),
        pole_peek(-1, look=1),
        pole_peek(4, fx=sweat(30, 6)),
        pole_peek(4, fx=both(sweat(30, 6), bang(29, 1))),
        pole_peek(-7),
    ]
    S["guard"] = [
        front(),
        front(arms="grip", look=-1),
        v5.mirror(v3.side(eyes="open")),
        front(arms="grip", look=-1, dy=1, fx=sweat(4, 12)),
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
