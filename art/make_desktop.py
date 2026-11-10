"""桌面版專用動作：被拎著（held）、掉落（fall）、落地（land）、偷看螢幕（peek）。
沿用 make_girl_v7 / make_sleepy 的畫法，直接輸出 1 倍 32x32。
用法：python3 make_desktop.py <輸出資料夾>   → held.png、fall.png、land.png、peek.png ＋ anims_desktop.json
"""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_sleepy as ms

v7, v4, v3, v6 = ms.v7, ms.v4, ms.v3, ms.v6
v5 = v6.v5
px, rect, blank = v5.px, v5.rect, v5.blank


def base(**kw):
    """正面角色（已描邊的 32x32），把腳和地上影子清掉，之後自己畫。"""
    g = v3.girl(raw=True, **kw)
    for y in range(28, 32):
        for x in range(32):
            g[y][x] = 0
    return g


def dangle_legs(g, kick=0, oy=0):
    """懸空的腳：腳尖朝下，kick=±1 時一腳抬高一格（踢來踢去）。"""
    for i, lx in enumerate((13, 17)):
        up = (kick if i == 0 else -kick)
        up = max(0, up)
        y = 28 + oy - up
        rect(g, lx, y, lx + 1, y, 4); px(g, lx + i, y, 5)        # 膝蓋
        rect(g, lx, y + 1, lx + 1, y + 1, 12)                      # 黑襪
        rect(g, lx, y + 2, lx + 1, y + 2, 1)                       # 鞋（腳尖朝下）
        px(g, lx + (0 if i == 0 else 1), y + 3, 1)


def skirt_flare(g, k):
    """裙襬往兩側飄。"""
    for x, y in ((10 - k, 26), (10 - k, 27), (21 + k, 26), (21 + k, 27)):
        px(g, x, y, 12)
    px(g, 10 - k, 26, 3 if k else 12)


def done(g, fx=None):
    g = v4.outline_any(v5.separate(g), shadow_y=None)
    if fx:
        fx(g)
    return [[3 if c == 13 else c for c in row] for row in g]


def shift(g, oy):
    """整張圖往下移 oy 格（超出畫布的部分切掉），用來做從螢幕下緣冒出來。"""
    out = blank(32, 32)
    for y in range(32):
        sy = y - oy
        if 0 <= sy < 32:
            out[y] = g[sy][:]
    return out


# ---------- 被拎著：後領被抓住，手腳亂晃 ----------
def held():
    F = []
    for k, (kick, arms, sway, eyes, fx) in enumerate((
            (1, "grip", 1, "open", v6.sweat(27, 9)),
            (-1, "down", -1, "open", v6.sweat(27, 10)),
            (1, "grip", 1, "closed", v6.sweat(27, 9)),
            (-1, "down", -1, "open", v6.sweat(27, 10)))):
        g = base(eyes=eyes, mouth="open", arms=arms, sway=sway)
        dangle_legs(g, kick)
        skirt_flare(g, k % 2)

        g = done(g, fx)
        sx = 1 if k % 2 == 0 else -1                   # 整個人左右晃
        g = [(row[1:] + [0]) if sx > 0 else ([0] + row[:-1]) for row in g]
        F.append(g)
    return F


# ---------- 掉落：雙手舉高，頭髮和裙子往上飄，旁邊有速度線 ----------
def fall():
    F = []
    for k in range(2):
        g = base(eyes="closed" if k else "open", mouth="open", arms="up", sway=k)
        dangle_legs(g, 0)
        skirt_flare(g, 1)
        for x in (5, 26):                                # 頭髮被風往上吹
            px(g, x, 8 - k, 2); px(g, x + (1 if x > 16 else -1), 7 - k, 2)

        def lines(gg, k=k):
            for x, y0, n in ((1, 12 + k * 3, 5), (30, 16 - k * 3, 6), (4, 24 - k * 2, 4), (28, 3 + k * 2, 4)):
                rect(gg, x, y0, x, y0 + n - 1, 6)
        F.append(done(g, lines))
    return F


# ---------- 落地：蹲下緩衝、揚起灰塵、站起來整理裙子 ----------
def dust(n):
    def f(g):
        pts = [((5, 30), (6, 29), (26, 30), (25, 29)), ((3, 29), (4, 28), (28, 29), (27, 28)), ((2, 27), (29, 27))]
        for i, puff in enumerate(pts[:n]):
            for x, y in puff:
                px(g, x, y, 6 if i < 2 else 3)
    return f


def land():
    F = v6.front
    return [[[3 if c == 13 else c for c in row] for row in v7.half(f)] for f in (
        F(dy=2, eyes="closed", mouth="open", arms="grip", fx=dust(1)),     # 著地：整個人往下壓
        F(dy=2, eyes="closed", mouth="open", arms="grip", fx=dust(2)),
        F(dy=1, eyes="closed", arms="down", fx=dust(3)),
        F(dy=0, eyes="open", arms="down", fx=v6.sweat(26, 8)),
        F(dy=0, eyes="open", arms="grip", fx=v6.sweat(26, 9)),             # 拍拍裙子
        F(dy=0, eyes="open", arms="down"),
    )]


# ---------- 偷看螢幕：鑽到螢幕下緣，換個地方冒出頭來東張西望 ----------
def hands(g, oy):
    """兩隻手扒在螢幕邊緣（畫布最底下）。"""
    for x in (8, 21):
        rect(g, x - 1, 29, x + 3, 31, 1)
        rect(g, x, 30, x + 2, 31, 4)
        px(g, x + 1, 31, 5)


def peek_frame(oy, look=0, eyes="open", grip=False, fx=None):
    g = v3.girl(raw=True, eyes=eyes, look=look, arms="behind")
    g = shift(g, oy)
    g[31] = [0] * 32 if oy == 0 else g[31]
    if grip:
        hands(g, oy)
    g = v4.outline_any(g, shadow_y=None)
    if fx:
        fx(g)
    return [[3 if c == 13 else c for c in row] for row in g]


PEEK_HIDDEN = 4   # 這一幀整個人不見，程式趁這時把她移到別的位置


def peek():
    return [
        peek_frame(2),                     # 蹲下
        peek_frame(10),                    # 往下鑽
        peek_frame(20),
        peek_frame(28),
        blank(32, 32),                     # 不見了（換位置）
        peek_frame(26, eyes="closed", grip=True),     # 慢慢冒出來
        peek_frame(18, grip=True),
        peek_frame(11, grip=True),
        peek_frame(11, look=-1, grip=True),           # 往左看
        peek_frame(11, look=-1, grip=True),
        peek_frame(11, look=1, grip=True),            # 往右看
        peek_frame(11, look=1, grip=True),
        peek_frame(11, eyes="closed", grip=True),     # 眨眼
        peek_frame(11, grip=True, fx=v6.dots(25, 16)),  # 盯……
        peek_frame(11, grip=True, fx=v6.bang(28, 12)),   # 被發現了！
        peek_frame(24, grip=True),                    # 縮回去
        peek_frame(12),                               # 若無其事地站起來
        peek_frame(4),
        peek_frame(0),
    ]


# ---------- 側面伸手：用 hold／behind 換掉手臂（角度 90 = 正上方） ----------
def reach_arm(ang, L=5):
    def f(g, ctx):
        ex, ey = v4.arm_to(g, ctx["hip"] + 2, ctx["sy"], ang, L)
        rect(g, round(ex) - 1, round(ey) - 1, round(ex), round(ey), 4)   # 手
    return f


def side_raw(**kw):
    g = v3.side(raw=True, **kw)
    g[31] = [0 if c == v4.SHADOW else c for c in g[31]]                # 不要地上的影子
    return g


def finish_raw(g, fx=None):
    g = v4.outline_any(g, shadow_y=None)
    if fx:
        fx(g)
    return [[3 if c == 13 else c for c in row] for row in g]


# ---------- 爬牆：側面朝右，牆在畫布右邊，雙手扶牆、腳踩牆，手腳交替往上 ----------
def wall_arms(near_ang, far_ang):
    """兩隻手往前伸到牆上（畫在頭前面，但位置在下巴下方）。"""
    def f(g, ctx):
        for ang, sy in ((far_ang, ctx["sy"] + 1), (near_ang, ctx["sy"])):
            ex, ey = v4.arm_to(g, ctx["hip"] + 2, sy, ang, 9)
            rect(g, round(ex) - 1, round(ey) - 1, round(ex), round(ey), 4)
    return f


def climb():
    F = []
    for k in range(4):
        a, b = (12, -8) if k < 2 else (-8, 12)
        g = side_raw(lean=2, near=3, far=3, near_lift=2 if k < 2 else 0, far_lift=0 if k < 2 else 2,
                     dy=-1 if k % 2 else 0, hold=wall_arms(a, b))
        F.append(finish_raw(g))
    return F


def hang():
    """掛在牆上休息：雙手扶牆，腳一前一後晃，偶爾流汗往下看。"""
    F = []
    for k in range(4):
        g = side_raw(lean=2, near=2 + (k % 2), far=1 - (k % 2), far_lift=1,
                     hold=wall_arms(5, 5), eyes="closed" if k == 3 else "open")
        F.append(finish_raw(g, v6.sweat(6, 6) if k >= 2 else None))
    return F


# ---------- 雙手往兩旁張開（不往上伸，手才不會變長） ----------
def spread_arms(lift=0, dy=0):
    """從肩膀往兩旁伸直，lift = 手比肩膀高幾格（斜斜往上）。"""
    def f(g):
        for sx, hx in ((9, 1), (22, 30)):
            sy, hy = 21 + dy, 21 + dy - lift
            n = abs(hx - sx)
            for i in range(n + 1):
                x = sx + (hx - sx) * i / n
                y = sy + (hy - sy) * i / n
                rect(g, round(x), round(y) - 1, round(x), round(y) + 1, 11)
                px(g, round(x), round(y) - 1, 8)                  # 袖子上緣亮邊
            rect(g, hx - (1 if hx < 16 else 0), hy - 1, hx + (0 if hx < 16 else 1), hy, 4)   # 手掌
    return f


# ---------- 伸懶腰：雙手往兩旁張開、打哈欠 ----------
def stretch():
    Fr = v6.front
    out = [
        Fr(eyes="open"),
        Fr(eyes="closed", arms="behind", dy=-1, extra=spread_arms(0, -1)),
        Fr(eyes="closed", arms="behind", dy=-1, extra=lambda g: (spread_arms(2, -1)(g), ms.yawn(g))),
        Fr(eyes="closed", arms="behind", dy=-1, extra=lambda g: (spread_arms(2, -1)(g), ms.yawn(g)),
           fx=lambda g: ms.tear(g)),
        Fr(eyes="closed", arms="behind", extra=spread_arms(0)),
        Fr(eyes="sleepy"),
        Fr(eyes="open"),
    ]
    return [[[3 if c == 13 else c for c in row] for row in v7.half(f)] for f in out]


# ---------- 追游標：跳起來，雙手往兩旁斜上張開去撲 ----------
def reach():
    Fr = v6.front
    out = [Fr(eyes="open", arms="behind", dy=-1, extra=spread_arms(4, -1)),
           Fr(eyes="open", arms="behind", mouth="open", dy=-1, extra=spread_arms(5, -1))]
    return [[[3 if c == 13 else c for c in row] for row in v7.half(f)] for f in out]


# ---------- 抓到游標：雙手抓著游標，整個人吊在游標上被拖著走 ----------
CARRY_HAND = {}


def grab_arms(ang, L=11):
    def f(g, ctx):
        for a, sy in ((ang + 6, ctx["sy"] + 1), (ang, ctx["sy"])):
            ex, ey = v4.arm_to(g, ctx["hip"] + 2, sy, a, L)
            rect(g, round(ex) - 1, round(ey) - 1, round(ex), round(ey), 4)
        CARRY_HAND["xy"] = (round(ex), round(ey) - 1)
    return f


def carry():
    F = []
    for k, kw in enumerate((dict(near=2, far=-1, far_lift=1, flow=1, mouth="open"),
                            dict(near=1, far=0, near_lift=1, flow=2),
                            dict(near=-1, far=2, near_lift=1, flow=1, mouth="open"),
                            dict(near=0, far=1, far_lift=1, flow=2, eyes="closed"))):
        g = side_raw(hold=grab_arms(14), **kw)
        F.append(finish_raw(g, v6.sweat(5, 8) if k == 3 else None))
    return F


MS = {"climb": [180] * 4, "hang": [400, 400, 600, 300], "stretch": [300, 400, 500, 500, 400, 400, 300],
      "reach": [120, 120], "carry": [220] * 4,
      "held": [160] * 4, "fall": [90] * 2, "land": [140, 140, 200, 300, 300, 300],
      "peek": [150, 120, 100, 100, 700, 250, 200, 400, 450, 450, 450, 450, 180, 900, 500, 150, 180, 160, 300]}


def to_img(f):
    h, w = len(f), len(f[0])
    im = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            c = f[y][x]
            if c:
                im.putpixel((x, y), (*v4.PAL[c], 255))
    return im


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_v7", "desktop")
    os.makedirs(out, exist_ok=True)
    meta = {}
    for name, fn in (("held", held), ("fall", fall), ("land", land), ("peek", peek),
                     ("climb", climb), ("hang", hang), ("stretch", stretch), ("reach", reach), ("carry", carry)):
        fr = fn()
        strip = Image.new("RGBA", (32 * len(fr), 32))
        for i, f in enumerate(fr):
            strip.alpha_composite(to_img(f), (i * 32, 0))
        strip.save(os.path.join(out, name + ".png"))
        meta[name] = {"w": 32, "h": 32, "frames": len(fr), "ms": MS[name]}
        assert len(MS[name]) == len(fr), name
    meta["peek"]["hidden_frame"] = PEEK_HIDDEN
    meta["carry"]["hand"] = list(CARRY_HAND["xy"])      # 抓游標的手在圖上的位置（1 倍、還沒加上方留白）
    json.dump(meta, open(os.path.join(out, "anims_desktop.json"), "w"), indent=1)
    print("ok", {k: v["frames"] for k, v in meta.items()})
