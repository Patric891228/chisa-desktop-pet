"""v4：武器動作（剪刀大刃，跟角色差不多高）＋全身伸展 idle。
一般動作 64x64；武器動作 112x96（角色大小不變，只是畫布變大放得下武器）。
32 格繪製後 2 倍放大。用法：python3 make_girl_weapon.py
"""
import math, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_cat as mc
import make_girl_v3 as v3
from make_girl_8bit import rect as rect32
from make_girl_anim import bubble

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_v4")

PAL = list(v3.PAL)
PAL[14] = (222, 178, 64)   # 14 改成金色（武器轉軸、飾線）
SHADOW = 13                # 影子改用 13
GOLD = 14


# ---------- 任意大小畫布的工具 ----------
def blank(w, h):
    return [[0] * w for _ in range(h)]


def px(g, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = c


def outline_any(g, shadow_y=None):
    """在透明格外圍描黑框；最底下影子那一列不描。"""
    h, w = len(g), len(g[0])
    o = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        c = g[ny][nx]
                        if c in (0, 1) or ny == shadow_y:
                            continue
                        o[y][x] = 1
                        break
    return o


def up2(g):
    return [[g[y // 2][x // 2] for x in range(len(g[0]) * 2)] for y in range(len(g) * 2)]


# v3 改用新的描邊（影子不描邊、金色要描邊）與影子顏色
v3.SHADOW = SHADOW
v3.outline = lambda g: outline_any(g, shadow_y=31)


def speed_lines(g, k):
    for y, x0, n in ((13, 0 + k, 3), (19, 1 - k, 4), (25, 0 + k, 3)):
        rect32(g, x0, y, x0 + n - 1, y, SHADOW)


v3.speed_lines = speed_lines


# ---------- 剪刀大刃 ----------
def weapon(g, x0, y0, ang, L=22):
    """以手 (x0, y0) 為原點，沿 ang 方向畫。t：沿刀方向，w：垂直方向（+ 為刃背那側）。"""
    c, s = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    nx, ny = -s, c

    def P(t, w, col):
        px(g, x0 + c * t + nx * w, y0 + s * t + ny * w, col)

    def T(a, b, w, col):
        t = a
        while t <= b:
            P(t, w, col)
            t += 0.5

    # 紅色握環（剪刀把手）：手後方一個空心環
    for i in range(36):
        a = 2 * math.pi * i / 36
        P(-4 + 2.6 * math.cos(a), 0.6 + 1.7 * math.sin(a), 9)
    # 握柄
    T(-1.5, 0.5, 0, 11)
    # 刀身：紅色主體、黑色內刃、金色細線
    T(2, L - 3, -1, 9)
    T(2, L - 1, 0, 9)
    T(2, L - 6, 1, 11)
    T(4, 14, -2, 9)
    T(3, 15, 0, 11)   # 中線改黑色
    T(L - 1, L, 0, 9)
    # 黑色尖刺（剪刀另一片的叉）
    for t, w in ((3, 2), (4, 2.5), (5, 3), (6, 3.5), (7, 4), (6, 2), (7, 2.5), (8, 3), (9, 3.5)):
        P(t, w, 11)
    # 金色轉軸
    for dt in (-1, 0, 1):
        for dw in (-1, 0, 1):
            if abs(dt) + abs(dw) < 2:
                P(1.5 + dt, dw, GOLD)
    P(1.5, 0, 10)


# ---------- 合成：角色＋武器放到大畫布 ----------
CW, CH, OX, OY = 56, 32, 12, 0  # 生活空間高 64px：畫布 112x64


def with_weapon(arm_ang, blade_ang, behind=False, fx=None, arm_len=4, **side_kw):
    hand = {}

    def hold(g, ctx):
        hx, hy = arm_to(g, ctx["sx"], ctx["sy"], arm_ang, arm_len)
        hand["xy"] = (hx, hy)

    ch = side(hold=hold, raw=True, **side_kw)
    g = blank(CW, CH)
    hx, hy = hand["xy"]
    hx, hy = hx + OX, hy + OY
    if behind:
        weapon(g, hx, hy, blade_ang)
    for y in range(32):
        for x in range(32):
            if ch[y][x]:
                g[y + OY][x + OX] = ch[y][x]
    if not behind:
        weapon(g, hx, hy, blade_ang)
    px(g, hx, hy, 4)  # 手握在柄上
    g = outline_any(g, shadow_y=OY + 31)
    if fx:
        fx(g)
    return up2(g)


def arm_to(g, sx, sy, ang, L=4):
    c, s = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    pts = [(round(sx + c * t), round(sy + s * t)) for t in (0, 1, 2, 3, L)]
    for x, y in pts:
        rect32(g, x - 2, y - 1, x + 2, y + 1, 1)
    for x, y in pts:
        rect32(g, x - 1, y, x + 1, y, 11)
    return sx + c * (L + 1), sy + s * (L + 1)


def arc(a0, a1, r, c=6, cx=OX + 16, cy=OY + 21):
    def f(g):
        n = int(abs(a1 - a0) / 3)
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            px(g, cx + r * math.cos(a), cy - r * math.sin(a), c if i % 3 else 13)
            if c == 6:
                px(g, cx + (r - 1) * math.cos(a), cy - (r - 1) * math.sin(a), 13)
    return f


side = v3.side


# ---------- idle：全身伸展（腳不動） ----------
def stretch(g, dx):
    """64 格座標：腰以上整個往上拉 2px 並往 dx 方向傾，腳與影子不動。"""
    WAIST = 50
    o = [[0] * 64 for _ in range(64)]
    for y in range(WAIST - 2, 64):
        o[y] = g[y][:]
    for y in range(WAIST - 2):
        for x in range(64):
            c = g[y + 2][x]
            if c and 0 <= x + dx < 64:
                o[y][x + dx] = c
    return o


def scenes():
    S = {}
    base = v3.girl()
    st_pose = v3.girl(eyes="closed")  # 不舉手，閉眼伸展
    S["idle"] = [base, stretch(st_pose, 2), base, stretch(st_pose, -2)]
    old = v3.scenes()
    S["walk"], S["run"], S["snore"] = old["walk"], old["run"], old["snore"]
    st = dict(near=2, far=-2)
    S["swing"] = [
        with_weapon(-30, 12, **st),
        with_weapon(130, 150, dy=-1, arm_far=3, **st),
        with_weapon(20, -5, lean=1, mouth="open", arm_far=-3, fx=arc(100, -5, 23), **st),
        with_weapon(-50, -15, dy=1, lean=1, arm_far=-3, fx=arc(15, -20, 23, c=13), **st),
    ]

    def lines(k):
        def f(g):
            for y, x0, n in ((10, 2 + k, 4), (16, 3 - k, 5)):
                for x in range(x0, x0 + n):
                    px(g, x, y, SHADOW)
        return f

    S["run_weapon"] = [
        with_weapon(210, 190, dy=-1, near=3, far=-3, far_lift=2, arm_far=4, lean=1, flow=2, mouth="open",
                    fx=lines(0)),
        with_weapon(215, 197, near=-3, far=3, near_lift=2, arm_far=-4, lean=1, flow=2, mouth="open",
                    fx=lines(1)),
    ]
    S["walk_weapon"] = [
        with_weapon(-110, 165, near=2, far=-2, arm_far=3, flow=1),
        with_weapon(-95, 175, dy=-1, far_lift=1, flow=1),
        with_weapon(-80, 185, near=-2, far=2, arm_far=-3, flow=1),
        with_weapon(-95, 175, dy=-1, near_lift=1, flow=1),
    ]
    return S


DUR = {"idle": 300, "walk": 160, "run": 110, "snore": 300,
       "swing": 140, "run_weapon": 110, "walk_weapon": 230}


def to_img(f):
    h, w = len(f), len(f[0])
    im = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            c = f[y][x]
            im.putpixel((x, y), (*PAL[c], 0 if c == 0 else 255))
    return im


def export():
    os.makedirs(OUT, exist_ok=True)
    S = scenes()
    names = list(S)
    cw = max(len(fr[0][0]) for fr in S.values())
    chh = max(len(fr[0]) for fr in S.values())
    ncol = max(len(v) for v in S.values())
    sheet = Image.new("RGBA", (cw * ncol, chh * len(names)))
    for r, n in enumerate(names):
        for c, f in enumerate(S[n]):
            sheet.paste(to_img(f), (c * cw, r * chh))
    sheet.save(os.path.join(OUT, "girl_sheet.png"))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(OUT, "girl_sheet_x3.png"))
    # 預覽 GIF：統一放在 112x96 的深色畫面中，角色腳底對齊
    frames, durs = [], []
    for n in names:
        reps = max(2, 8 // len(S[n]))
        for _ in range(reps):
            for f in S[n]:
                bg = Image.new("RGBA", (cw, chh), (24, 26, 38, 255))
                im = to_img(f)
                bg.alpha_composite(im, ((cw - im.width) // 2 if im.width < cw else 0, chh - im.height))
                frames.append(bg.convert("RGB").resize((cw * 3, chh * 3), Image.NEAREST))
                durs.append(DUR[n])
    frames[0].save(os.path.join(OUT, "girl_preview.gif"), save_all=True, append_images=frames[1:], duration=durs, loop=0)
    # C 標頭：每組動作自己的寬高
    L = ["// 由 make_girl_weapon.py 產生。4bpp 索引色（一 byte 兩像素，高 4 位元在左），index 0 = 透明",
         "// 角色腳底在每張圖的最下方；武器動作的圖比較大，畫的時候以底部中央對齊。",
         "#pragma once", "#include <stdint.h>", "",
         "static const uint16_t pet_palette[16] = {" + ", ".join(f"0x{mc.rgb565(*c):04X}" for c in PAL) + "};", ""]
    table = []
    for n in names:
        h, w = len(S[n][0]), len(S[n][0][0])
        for i, f in enumerate(S[n]):
            data = [(f[y][x] << 4) | f[y][x + 1] for y in range(h) for x in range(0, w, 2)]
            L.append(f"static const uint8_t pet_{n}_{i}[{len(data)}] = {{")
            for k in range(0, len(data), 32):
                L.append("  " + ",".join(f"0x{b:02X}" for b in data[k:k + 32]) + ",")
            L.append("};")
        U = n.upper()
        table += [f"static const uint8_t* const pet_{n}[] = {{" + ", ".join(f"pet_{n}_{i}" for i in range(len(S[n]))) + "};",
                  f"#define PET_{U}_W {w}", f"#define PET_{U}_H {h}",
                  f"#define PET_{U}_FRAMES {len(S[n])}", f"#define PET_{U}_MS {DUR[n]}", ""]
    with open(os.path.join(OUT, "pet_sprites.h"), "w") as fh:
        fh.write("\n".join(L + [""] + table) + "\n")
    total = sum(len(f) * len(f[0]) // 2 for v in S.values() for f in v)
    print("ok", names, f"{total / 1024:.1f} KB")


if __name__ == "__main__":
    export()
