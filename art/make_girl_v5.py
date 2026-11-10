"""v5：在 v4 的基礎上新增趴睡（木桌椅）、躺睡（床）、讀書（燈泡靈光一閃）。
調色盤 15 改成木頭色；泡泡、刀光改用 13，Z 改用白色。
趴睡、躺睡各有朝右（_r）和朝左（_l）兩個方向。用法：python3 make_girl_v5.py
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_girl_weapon as v4
import make_girl_v3 as v3
from make_girl_8bit import blank as blank32, px as px32, rect as rect32, ellipse as ellipse32

WOOD, WOOD_HI = 15, 14
v4.PAL[15] = (150, 92, 52)    # 15 木頭
v4.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_v5")
px, blank = v4.px, v4.blank


def rect(g, x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            px(g, x, y, c)


def ellipse(g, cx, cy, rx, ry, c):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if ((x - cx + .5) / rx) ** 2 + ((y - cy + .5) / ry) ** 2 <= 1:
                g[y][x] = c


def thick(g, x0, y0, x1, y1, r, c):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        cx, cy = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    px(g, x, y, c)


def paste(g, layer, ox, oy):
    for y, row in enumerate(layer):
        for x, c in enumerate(row):
            if c:
                px(g, x + ox, y + oy, c)


def mirror(g):
    return [row[::-1] for row in g]


def separate(g):
    """黑髮碰到黑衣服的地方補一條黑線（任意大小畫布版）。"""
    h, w = len(g), len(g[0])
    o = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] in (2, 3):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and g[ny][nx] in v3.CLOTH:
                        o[y][x] = 1
                        break
    return o


def finish(g, shadow_y, fx=None, flip=False):
    g = v4.outline_any(separate(g), shadow_y=shadow_y)
    if flip:
        g = mirror(g)
    if fx:
        fx(g)
    return v4.up2(g)


# ---------- 特效 ----------
def zz(x, y, n=4):
    def f(g):
        for i in range(n):
            px(g, x + i, y, 6); px(g, x + i, y + n - 1, 6); px(g, x + n - 1 - i, y + i, 6)
    return f


def both(*fs):
    def f(g):
        for h in fs:
            if h:
                h(g)
    return f


def bubble(r, dy):
    """打呼鼻涕泡（灰藍色圈＋白色反光），r = -1 時破掉。"""
    def f(g):
        cx, cy = 20 + r, 18 + dy - r // 2
        if r == 0:
            return
        if r < 0:
            for ddx, ddy in ((-3, -3), (3, -3), (-3, 3), (3, 3), (0, -4), (4, 0)):
                px32(g, 22 + ddx, 16 + dy + ddy, 13)
            px32(g, 22, 16 + dy, 6)
            return
        for y in range(32):
            for x in range(32):
                d = ((x + .5 - cx) ** 2 + (y + .5 - cy) ** 2) ** .5
                if r - 1 <= d <= r + .2 or (r == 1 and d <= 1):
                    g[y][x] = 13
        px32(g, round(cx - r / 2), round(cy - r / 2), 6)
    return f


v3.bubble = bubble


# ---------- 側面頭部（獨立一層，方便旋轉、貼上） ----------
def head_side(eyes="closed", mouth="dot"):
    g = blank32()
    hx, hy = 15, 12
    ellipse32(g, hx, hy, 12, 10.5, 2)
    face = blank32()
    ellipse32(face, hx + 3, hy + 2, 8.5, 7.5, 4, ymin=hy - 1)
    for y in range(32):
        for x in range(32):
            if face[y][x] and x >= hx - 1:
                g[y][x] = 4
    for x in range(hx, hx + 12, 3):
        px32(g, x, hy - 1, 2)
    for x in range(hx + 1, hx + 11, 3):
        px32(g, x, hy - 2, 1)
    # 公主切側髮：耳前一束 4 格寬、到下巴剪齊，前後都描黑線
    rect32(g, hx - 2, hy - 1, hx + 1, hy + 5, 2)
    for y in range(hy + 1, hy + 5):
        px32(g, hx, y, 3)
    # 側髮跟頭髮連成一塊（不描後緣），前緣一條垂直線、下緣水平剪齊
    rect32(g, hx - 3, hy - 1, hx - 3, hy + 6, 2)
    rect32(g, hx + 2, hy - 1, hx + 2, hy + 5, 1)
    rect32(g, hx - 1, hy + 6, hx + 2, hy + 6, 1)
    # 側髮下面露出下巴、臉頰下緣
    rect32(g, hx - 1, hy + 7, hx + 2, hy + 8, 4)
    px32(g, hx - 2, hy + 7, 1); px32(g, hx - 2, hy + 8, 1); rect32(g, hx - 1, hy + 9, hx + 1, hy + 9, 1)
    px32(g, hx + 1, hy - 11, 2); px32(g, hx + 2, hy - 12, 2)
    for x in range(hx - 7, hx + 6):
        if (x - hx) % 4 != 3:
            px32(g, x, hy - 7 + (1 if x < hx - 5 else 0), 3)
    v3.bow(g, hx - 10, hy - 10)
    e, ey = hx + 6, hy + 2
    if eyes == "open":
        rect32(g, e, ey, e + 1, ey, 1)
        rect32(g, e, ey + 1, e + 1, ey + 1, 10)
        rect32(g, e, ey + 2, e + 1, ey + 4, 9)
        px32(g, e, ey + 1, 6)
    elif eyes == "closed":
        rect32(g, e - 1, ey + 4, e + 1, ey + 4, 1)
    rect32(g, hx + 4, ey + 5, hx + 5, ey + 5, 5)
    if mouth == "dot":
        px32(g, hx + 8, hy + 7, 5)
    return g  # 頭中心在 (15, 12)


def rot_ccw(g):
    """逆時針轉 90 度：臉（朝右）變成朝上。(x, y) -> (y, 31 - x)"""
    n = len(g)
    o = [[0] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            o[n - 1 - x][y] = g[y][x]
    return o


# ---------- 趴睡：坐在木椅上趴桌子（朝右） ----------
def desk_sleep(b=0, fx=None, flip=False):
    W, H, o = 48, 36, 4
    g = blank(W, H)
    Y = lambda y: y + o
    rect(g, 3, Y(31), 46, Y(31), v4.SHADOW)
    # 椅子
    rect(g, 5, Y(9), 8, Y(9), WOOD)
    rect(g, 6, Y(10), 7, Y(22), WOOD); rect(g, 7, Y(11), 7, Y(21), WOOD_HI)
    rect(g, 6, Y(22), 17, Y(22), WOOD_HI); rect(g, 6, Y(23), 17, Y(23), WOOD)
    rect(g, 7, Y(24), 7, Y(30), WOOD); rect(g, 16, Y(24), 16, Y(30), WOOD)
    rect(g, 8, Y(27), 15, Y(27), WOOD)
    # 桌子
    rect(g, 23, Y(19), 46, Y(19), WOOD_HI); rect(g, 23, Y(20), 46, Y(21), WOOD)
    rect(g, 25, Y(22), 26, Y(30), WOOD); rect(g, 43, Y(22), 44, Y(30), WOOD)
    rect(g, 30, Y(22), 39, Y(24), WOOD); px(g, 34, Y(23), WOOD_HI); px(g, 35, Y(23), WOOD_HI)
    rect(g, 30, Y(25), 39, Y(25), 1)
    # 坐姿的腿：大腿在椅面上（裙子蓋住），膝蓋露一格，小腿垂下
    rect(g, 10, Y(19), 18, Y(21), 12)
    for x in (12, 15, 18):
        px(g, x, Y(21), 13)
    rect(g, 19, Y(20), 20, Y(20), 4)
    rect(g, 19, Y(21), 20, Y(28), 12)
    rect(g, 19, Y(29), 21, Y(30), 1); px(g, 20, Y(30), 8)
    # 上半身往前趴
    thick(g, 13, Y(17) + b, 21, Y(13) + b, 3, 11)
    rect(g, 11, Y(18), 17, Y(18), 1)  # 腰帶
    # 披在背上的長髮
    thick(g, 19, Y(6) + b, 11, Y(18) + b, 2.5, 2)
    for i in range(5):
        px(g, 17 - i * 1.4, Y(9) + b + i * 2, 3)
    # 雙手交疊在桌上
    rect(g, 18, Y(17), 40, Y(18), 11)
    rect(g, 39, Y(17), 40, Y(18), 8)
    rect(g, 41, Y(17), 42, Y(18), 4)
    # 頭靠在手臂上
    paste(g, head_side("closed"), 30 - 15, Y(8) + b - 12)
    g = [row for i, row in enumerate(g) if i not in (28, 29, 30, 31)]  # 收進 64px 高：縮短桌腳、椅腳
    return finish(g, 31, fx, flip)


# ---------- 躺睡：仰躺在床上（朝右＝頭在左） ----------
def bed_sleep(b=0, fx=None, flip=False):
    W, H = 48, 36
    g = blank(W, H)
    rect(g, 1, 35, 46, 35, v4.SHADOW)
    # 床頭板、床尾板
    rect(g, 1, 14, 5, 14, WOOD); rect(g, 2, 15, 4, 34, WOOD); rect(g, 3, 16, 3, 32, WOOD_HI)
    rect(g, 42, 20, 46, 20, WOOD); rect(g, 43, 21, 45, 34, WOOD); rect(g, 44, 22, 44, 32, WOOD_HI)
    # 床墊、床框、床腳
    rect(g, 5, 25, 42, 27, 6); rect(g, 5, 28, 42, 28, 8)
    rect(g, 5, 29, 42, 29, WOOD_HI); rect(g, 5, 30, 42, 31, WOOD)
    rect(g, 6, 32, 7, 34, WOOD); rect(g, 40, 32, 41, 34, WOOD)
    # 枕頭
    rect(g, 6, 21, 17, 24, 6); rect(g, 6, 24, 17, 24, 8); rect(g, 17, 22, 17, 24, 8)
    # 散在枕頭上的長髮
    ellipse(g, 16, 19, 14, 5, 2)
    for x in (3, 6, 22, 25):
        rect(g, x, 17, x, 22, 3)
    # 身體（仰躺，胸口朝上）
    rect(g, 25, 20 - b, 32, 24, 11)          # 外套
    rect(g, 33, 20, 33, 24, 1)               # 腰帶
    rect(g, 34, 20, 36, 24, 12)              # 裙子
    for y in (21, 23):
        rect(g, 34, y, 36, y, 13)
    rect(g, 37, 21, 37, 24, 4)               # 膝蓋
    rect(g, 38, 21, 39, 24, 12)              # 黑襪
    rect(g, 40, 19, 41, 24, 1); px(g, 41, 19, 8)  # 鞋（腳尖朝上）
    # 手放在肚子上
    rect(g, 27, 18 - b, 32, 19 - b, 11); rect(g, 32, 18 - b, 32, 19 - b, 8)
    rect(g, 33, 18 - b, 34, 19 - b, 4)
    # 頭：正面朝向畫面（Q 版常見的睡姿畫法），靠在枕頭上
    head = blank32()
    v3.head_front(head, 16, 11, "closed", "dot", 0)
    paste(g, head, 16 - 16, 13 - 11)
    g = [row for i, row in enumerate(g) if i not in (0, 1, 32, 33)]  # 收進 64px 高
    return finish(g, 31, fx, flip)


# ---------- 讀書：正面站著，燈泡亮起 ----------
def bulb(state, big=False, oy=0):
    """state: 'off' 灰色燈泡、'on' 亮黃色加光芒。"""
    def f(g):
        cx, cy = 39, 6 + oy  # 燈泡放在頭的右邊（畫面高只有 64px）
        for y in range(len(g)):
            for x in range(len(g[0])):
                d = ((x + .5 - cx) ** 2 + (y + .5 - cy) ** 2) ** .5
                if d <= 2.6:
                    g[y][x] = 14 if state == "on" else 8
                elif d <= 3.4 and y < cy + 2:
                    g[y][x] = 1
        rect(g, 24, cy + 2, 26, cy + 2, 1)
        rect(g, 24, cy + 3, 26, cy + 3, 8)
        rect(g, 24, cy + 4, 26, cy + 4, 1)
        px(g, cx - 1, cy - 1, 6)
        if state == "on":
            r0, r1 = (5, 6) if not big else (5, 7)
            for a in (0, 40, 90, 140, 180, 220, 320):
                ra = math.radians(a)
                for r in range(r0, r1 + 1):
                    px(g, cx + r * math.cos(ra), cy - r * math.sin(ra), 6 if big and r == r1 else 14)
    return f


def read(eyes="down", mouth="dot", dy=0, fx=None):
    W, H, o = 32, 40, 8
    g = blank(W, H)
    paste(g, v3.girl(eyes=eyes, mouth=mouth, dy=dy, arms="none", raw=True), 0, o)
    # 袖子（從肩膀往前拿書）
    for x0 in (7, 22):
        rect(g, x0 - 1, o + 20 + dy, x0 + 3, o + 25 + dy, 1)
        rect(g, x0, o + 21 + dy, x0 + 2, o + 24 + dy, 11)
    # 打開的書：白色書頁、灰色書脊、紅色封面
    bt = o + 21 + dy
    rect(g, 8, bt - 1, 23, bt + 5, 1)
    rect(g, 9, bt + 4, 22, bt + 4, 9)
    rect(g, 9, bt, 22, bt + 3, 6)
    rect(g, 15, bt, 16, bt + 3, 8)
    for y in (bt + 1, bt + 2):
        rect(g, 10, y, 13, y, 13); rect(g, 18, y, 21, y, 13)
    rect(g, 9, bt + 1, 10, bt + 2, 4); rect(g, 21, bt + 1, 22, bt + 2, 4)  # 雙手
    return finish(g, o + 31, fx)


_v4_scenes = v4.scenes


def scenes():
    S = _v4_scenes()
    # 趴睡、躺睡：呼吸起伏＋Z 往上飄；朝左版本先翻轉再畫 Z，字才不會反過來
    def zs(frames, flip):
        out = []
        for i, zlist in enumerate(frames):
            fs = [zz(47 - x - (n - 1) if flip else x, y, n) for x, y, n in zlist]
            out.append(both(*fs))
        return out

    desk_z = [[(41, 6, 4)], [(42, 4, 4)], [(43, 1, 4), (40, 8, 3)], [(41, 6, 3)]]
    bed_z = [[(29, 6, 4)], [(30, 4, 4)], [(31, 1, 4), (28, 8, 3)], [(29, 6, 3)]]
    breath = [0, 1, 1, 0]
    for flip, tag in ((False, "r"), (True, "l")):
        S[f"desk_sleep_{tag}"] = [desk_sleep(b, f, flip) for b, f in zip(breath, zs(desk_z, flip))]
    for flip, tag in ((False, "r"), (True, "l")):
        S[f"bed_sleep_{tag}"] = [bed_sleep(b, f, flip) for b, f in zip(breath, zs(bed_z, flip))]
    S["read"] = [
        read(),
        read(dy=1),
        read(eyes="open", fx=bulb("off")),
        read(eyes="open", mouth="open", fx=bulb("on")),
        read(eyes="open", mouth="open", fx=bulb("on", big=True)),
    ]
    return S


v4.scenes = scenes
v4.DUR.update({"desk_sleep_r": 400, "desk_sleep_l": 400, "bed_sleep_r": 400, "bed_sleep_l": 400, "read": 300})

if __name__ == "__main__":
    v4.export()
