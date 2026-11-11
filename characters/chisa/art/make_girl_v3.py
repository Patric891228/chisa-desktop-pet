"""v3 外觀：白皙膚色、黑色外套、深藍百褶裙＋腰帶、露膝蓋＋黑襪、髮絲線條。
動畫同 make_girl_anim：idle / walk / run / snore。32x32 繪製後 2 倍放大成 64x64。
用法：python3 make_girl_v3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_cat as mc
from make_girl_8bit import blank, px, rect, ellipse, outline, sprite, up2
from make_girl_anim import arm, speed_lines, shifted, bubble

PAL = [
    (0, 0, 0),        # 0 透明
    (16, 12, 24),     # 1 外框／腰帶／鞋
    (46, 42, 72),     # 2 頭髮
    (100, 96, 146),   # 3 頭髮亮部（髮絲）
    (255, 240, 230),  # 4 皮膚（白皙）
    (246, 186, 190),  # 5 皮膚陰影／腮紅
    (255, 255, 255),  # 6 白（領子、反光）
    (216, 40, 40),    # 7 眼睛紅
    (96, 94, 112),    # 8 外套亮邊
    (240, 52, 60),    # 9 紅（髮帶、領巾）
    (140, 10, 30),    # 10 深紅
    (38, 36, 44),     # 11 黑色外套
    (32, 34, 62),     # 12 深藍裙子／黑襪
    (74, 78, 118),    # 13 百褶亮線
    (80, 64, 96),     # 14 地面影子
    (104, 160, 252),  # 15 藍（泡泡、Z）
]
CLOTH = (11, 8, 12, 13)
SHADOW = 14  # 地面影子顏色（v4 改用 13，14 拿去當金色）


def separate(g):
    """頭髮碰到衣服的地方補一條黑線，避免黑髮和黑衣糊在一起。"""
    o = [r[:] for r in g]
    for y in range(32):
        for x in range(32):
            if g[y][x] in (2, 3):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 32 and 0 <= ny < 32 and g[ny][nx] in CLOTH:
                        o[y][x] = 1
                        break
    return o


def hair_back(g, x0, x1, y0, y1, sway=0, tips_from=None, cx=16):
    """長髮：髮尾鋸齒、幾條亮色髮絲。"""
    tips_from = tips_from if tips_from is not None else y1 - 3
    for y in range(y0, y1 + 1):
        off = sway if y >= tips_from - 2 else 0
        for x in range(x0 + off, x1 + 1 + off):
            if y >= tips_from and (x - cx) % 4 == 0:
                continue
            if y == y1 and (x - cx) % 4 == 2:
                continue
            px(g, x, y, 2)
        for sx, ln in ((x0 + 2, 0), (x0 + 5, 3), (x1 - 4, 2), (x1 - 1, 0)):
            if y0 + 11 + ln <= y <= y1 - 2 - (ln % 2):
                px(g, sx + off, y, 3)


def head_front(g, hx, hy, eyes, mouth, look, blush=False):
    ellipse(g, hx, hy, 12.5, 10.5, 2)
    ellipse(g, hx, hy + 2, 9.5, 7.5, 4, ymin=hy - 1)
    px(g, hx + 1, hy - 11, 2); px(g, hx + 2, hy - 12, 2)  # 呆毛
    # 齊瀏海：鋸齒 + 分束線
    for x in range(hx - 8, hx + 9, 3):
        px(g, x, hy - 1, 2)
    for x in range(hx - 7, hx + 8, 3):
        px(g, x, hy - 3, 1); px(g, x, hy - 2, 1)
    # 光環（天使圈）
    for x in range(hx - 8, hx + 7):
        if (x - hx) % 4 != 3:
            px(g, x, hy - 7 + (1 if abs(x - hx + 1) > 5 else 0), 3)
    # 公主切側髮 + 髮絲
    for s in (-1, 1):
        x0 = hx + s * 9 - (1 if s < 0 else 0)
        rect(g, x0, hy, x0 + 1, hy + 10, 2)
        for y in range(hy + 3, hy + 9):
            px(g, x0 + (1 if s < 0 else 0), y, 3)
        edge = x0 - 1 if s < 0 else x0 + 2
        rect(g, edge, hy + 2, edge, hy + 10, 1)       # 側髮外緣黑線
        rect(g, x0 - (1 if s < 0 else 0), hy + 11, x0 + 1 + (1 if s > 0 else 0), hy + 11, 1)  # 下緣剪齊
    # 紅髮帶
    bow(g, hx - 15, hy - 9)
    # 眼睛
    ey = hy + 2
    for ex in (hx - 6, hx + 3):
        e = ex + look
        if eyes == "open":
            rect(g, e, ey, e + 2, ey, 1)
            rect(g, e, ey + 1, e + 2, ey + 1, 10)
            rect(g, e, ey + 2, e + 2, ey + 4, 9)
            px(g, e, ey + 1, 6); px(g, e + 2, ey + 4, 10)
        elif eyes == "closed":
            rect(g, e, ey + 4, e + 2, ey + 4, 1)
        elif eyes == "glow":  # 解弦之眼（戰鬥調色盤）
            rect(g, e, ey, e + 2, ey, 1)
            rect(g, e, ey + 1, e + 2, ey + 4, 7)
            px(g, e + 1, ey + 2, 14); px(g, e + 1, ey + 3, 14); px(g, e, ey + 1, 15)
        elif eyes == "down":  # 往下看（讀書）
            rect(g, e, ey + 2, e + 2, ey + 2, 1)
            rect(g, e, ey + 3, e + 2, ey + 4, 9)
            px(g, e, ey + 3, 10)
    rect(g, hx - 8, ey + 5, hx - 7, ey + 5, 5); rect(g, hx + 6, ey + 5, hx + 7, ey + 5, 5)
    if blush:  # 臉紅：腮紅加大、加斜線
        rect(g, hx - 9, ey + 5, hx - 6, ey + 6, 5); rect(g, hx + 5, ey + 5, hx + 8, ey + 6, 5)
        for bx in (hx - 8, hx - 6, hx + 6, hx + 8):
            px(g, bx, ey + 5, 9)
    if mouth == "dot":
        px(g, hx, hy + 8, 5)
    elif mouth == "open":
        rect(g, hx - 1, hy + 8, hx, hy + 8, 10)


def bow(g, x, y):
    """紅色蝴蝶結：左右兩個環、中間結、下面兩條垂帶。"""
    sprite(g, x, y, ["##...##", "###.###", "#######", "###.###", "##...##"], 9)
    px(g, x + 3, y + 2, 10)                      # 中間的結
    px(g, x + 1, y + 1, 6)                       # 反光
    px(g, x + 1, y + 3, 10); px(g, x + 5, y + 3, 10)  # 環的陰影
    # 兩條長垂帶，往外斜下，末端剪成深紅
    px(g, x + 3, y + 3, 9)
    left = [(2, 4), (2, 5), (2, 6), (1, 7), (1, 8), (1, 9), (0, 10)]
    right = [(4, 4), (4, 5), (4, 6), (5, 7), (5, 8), (5, 9), (6, 10)]
    for tail in (left, right):
        for i, (dx, dy) in enumerate(tail):
            px(g, x + dx, y + dy, 10 if i == len(tail) - 1 else 9)


def legs_front(g):
    for lx in (13, 17):
        rect(g, lx, 28, lx + 1, 28, 4)      # 膝蓋（露出一格）
        px(g, lx + (1 if lx > 15 else 0), 28, 5)
        rect(g, lx, 29, lx + 1, 29, 12)     # 黑襪
        rect(g, lx, 30, lx + 1, 30, 1)      # 鞋
        px(g, lx + (1 if lx > 15 else 0), 30, 8)


def girl(dy=0, eyes="open", mouth="dot", sway=0, look=0, arms="down", fx=None, raw=False, blush=False, poke=0):
    g = blank()
    hx, hy = 16, 11 + dy
    rect(g, 7, 31, 24, 31, SHADOW)
    hair_back(g, 5, 26, hy, 26, sway=sway, tips_from=24)
    # 外套（黑）：兩側長下擺
    rect(g, 10, 20 + dy, 21, 24 + dy, 11)
    rect(g, 10, 25 + dy, 11, 25 + dy, 11); rect(g, 20, 25 + dy, 21, 25 + dy, 11)
    # 外套前襟亮邊
    rect(g, 12, 21 + dy, 12, 25 + dy, 8); rect(g, 19, 21 + dy, 19, 25 + dy, 8)
    # 腰帶
    rect(g, 13, 24 + dy, 18, 24 + dy, 1); px(g, 15, 24 + dy, 8)
    # 裙子（深藍百褶）
    rect(g, 12, 25 + dy, 19, 25 + dy, 12)
    rect(g, 11, 26, 20, 27, 12)
    for x in (13, 16, 19):
        px(g, x, 26, 13); px(g, x, 27, 13)
    px(g, 14, 25 + dy, 13); px(g, 17, 25 + dy, 13)
    legs_front(g)
    # 袖子
    if arms == "down":
        for x0 in (7, 22):
            rect(g, x0, 21 + dy, x0 + 2, 24 + dy, 11)
            rect(g, x0, 24 + dy, x0 + 2, 24 + dy, 8)
            px(g, x0 + 1, 25 + dy, 4)
    elif arms == "up":  # 雙手舉高伸展
        for x0 in (2, 27):
            rect(g, x0, 6 + dy, x0 + 2, 22 + dy, 11)
            rect(g, x0, 6 + dy, x0 + 2, 6 + dy, 8)
            rect(g, x0, 4 + dy, x0 + 2, 5 + dy, 4)
    elif arms == "grip":  # 雙手垂下握緊裙襬
        for x0 in (8, 21):
            rect(g, x0, 21 + dy, x0 + 2, 24 + dy, 11)
            rect(g, x0, 24 + dy, x0 + 2, 24 + dy, 8)
        rect(g, 10, 25 + dy, 11, 26 + dy, 4); rect(g, 20, 25 + dy, 21, 26 + dy, 4)
        px(g, 12, 26, 13); px(g, 19, 26, 13); px(g, 12, 27, 1); px(g, 19, 27, 1)  # 裙襬被抓皺
    elif arms == "fingers":  # 揪手指：雙手在胸前，指尖碰來碰去
        for x0 in (8, 21):
            rect(g, x0, 21 + dy, x0 + 2, 22 + dy, 11)
        rect(g, 10, 22 + dy, 13, 23 + dy, 11); rect(g, 18, 22 + dy, 21, 23 + dy, 11)
        rect(g, 14 - poke, 22 + dy, 14 - poke, 23 + dy, 4); rect(g, 17 + poke, 22 + dy, 17 + poke, 23 + dy, 4)
        px(g, 15 - poke, 22 + dy, 4); px(g, 16 + poke, 22 + dy, 4)
    elif arms == "hold":  # 雙手捧在胸前
        for x0 in (8, 21):
            rect(g, x0, 21 + dy, x0 + 2, 23 + dy, 11)
        rect(g, 10, 23 + dy, 13, 24 + dy, 11); rect(g, 18, 23 + dy, 21, 24 + dy, 11)
        rect(g, 12, 22 + dy, 13, 23 + dy, 4); rect(g, 18, 22 + dy, 19, 23 + dy, 4)
    elif arms == "behind":  # 手藏到背後：只看到肩膀
        for x0 in (9, 20):
            rect(g, x0, 21 + dy, x0 + 2, 22 + dy, 11)
    elif arms == "front":
        for x0 in (8, 21):
            rect(g, x0, 21 + dy, x0 + 2, 23 + dy, 11)
        rect(g, 10, 23 + dy, 21, 23 + dy, 11)
        rect(g, 10, 22 + dy, 21, 22 + dy, 8)
        rect(g, 15, 24 + dy, 16, 24 + dy, 4)
    # 水手領、紅領巾
    rect(g, 12, 20 + dy, 19, 20 + dy, 6)
    px(g, 13, 21 + dy, 6); px(g, 18, 21 + dy, 6)
    rect(g, 15, 21 + dy, 16, 22 + dy, 9); px(g, 15, 23 + dy, 10); px(g, 16, 23 + dy, 9)
    head_front(g, hx, hy, eyes, mouth, look, blush)
    g = outline(separate(g))
    if fx:
        fx(g)
    return g if raw else up2(g)


# ---------- 側面（朝右） ----------
def leg_side(g, hip, dy, s, lift):
    top, bot = 28 + dy, 29 - lift
    n = bot - top + 1
    x = hip
    for i, y in enumerate(range(top, bot + 1)):
        x = round(hip + s * (i + 1) / n)
        c = 4 if i < 1 else 12
        rect(g, x, y, x + 1, y, c)
    rect(g, x, bot + 1, x + 2, bot + 1, 1)
    px(g, x + 1, bot + 1, 8)


def side(dy=0, near=0, far=0, near_lift=0, far_lift=0, arm_near=0, arm_far=0,
         lean=0, flow=0, eyes="open", mouth="dot", fx=None, behind=None, hold=None, raw=False):
    """behind(g, ctx)：畫在頭後面（例如扛在肩上的武器）；hold(g, ctx)：取代近側手臂（拿武器）。"""
    g = blank()
    hx, hy = 15 + lean, 11 + dy
    ctx = dict(hx=hx, hy=hy, hip=14 + lean, dy=dy, sx=16 + lean, sy=21 + dy)
    hip = 14 + lean
    rect(g, 8, 31, 23, 31, SHADOW)
    # 後髮往後飄
    for y in range(hy, 26 + dy):
        k = (y - hy) / 14
        off = -round(flow * k * 2)
        for x in range(hx - 11 + off, hx + 1 - (3 if y > 20 + dy else 0)):
            if y >= 23 + dy and (x - hx) % 4 == 0:
                continue
            px(g, x, y, 2)
        for sx, ln in ((hx - 9, 0), (hx - 6, 3), (hx - 3, 1)):
            if hy + 10 + ln <= y <= 23 + dy:
                px(g, sx + off, y, 3)
    arm(g, hip + 2, 21 + dy, arm_far)
    leg_side(g, hip, dy, far, far_lift)
    # 外套、後下擺
    rect(g, 11 + lean, 20 + dy, 18 + lean, 23 + dy, 11)
    rect(g, 10 + lean, 24 + dy, 11 + lean, 25 + dy, 11)
    rect(g, 18 + lean, 21 + dy, 18 + lean, 23 + dy, 8)
    # 腰帶與裙子
    rect(g, 12 + lean, 24 + dy, 18 + lean, 24 + dy, 1)
    rect(g, 11 + lean, 25 + dy, 19 + lean, 27 + dy, 12)
    for x in (13, 16, 19):
        px(g, x + lean, 26 + dy, 13); px(g, x + lean, 27 + dy, 13)
    # 領子、領巾
    rect(g, 12 + lean, 20 + dy, 18 + lean, 20 + dy, 6)
    rect(g, 18 + lean, 21 + dy, 19 + lean, 22 + dy, 9)
    px(g, 19 + lean, 23 + dy, 10)
    leg_side(g, hip + 1, dy, near, near_lift)
    if behind:
        behind(g, ctx)
    # 頭
    ellipse(g, hx, hy, 12, 10.5, 2)
    face = blank()
    ellipse(face, hx + 3, hy + 2, 8.5, 7.5, 4, ymin=hy - 1)
    for y in range(32):
        for x in range(32):
            if face[y][x] and x >= hx - 1:
                g[y][x] = 4
    for x in range(hx, hx + 12, 3):
        px(g, x, hy - 1, 2)
    for x in range(hx + 1, hx + 11, 3):
        px(g, x, hy - 2, 1)
    # 公主切側髮：耳前一束 4 格寬、到下巴剪齊，前後都描黑線
    rect(g, hx - 2, hy - 1, hx + 1, hy + 5, 2)
    for y in range(hy + 1, hy + 5):
        px(g, hx, y, 3)
    # 側髮跟頭髮連成一塊（不描後緣），前緣一條垂直線、下緣水平剪齊
    rect(g, hx - 3, hy - 1, hx - 3, hy + 6, 2)
    rect(g, hx + 2, hy - 1, hx + 2, hy + 5, 1)
    rect(g, hx - 1, hy + 6, hx + 2, hy + 6, 1)
    # 側髮下面露出下巴、臉頰下緣
    rect(g, hx - 1, hy + 7, hx + 2, hy + 8, 4)
    px(g, hx - 2, hy + 7, 1); px(g, hx - 2, hy + 8, 1); rect(g, hx - 1, hy + 9, hx + 1, hy + 9, 1)
    px(g, hx + 1, hy - 11, 2); px(g, hx + 2, hy - 12, 2)
    for x in range(hx - 7, hx + 6):
        if (x - hx) % 4 != 3:
            px(g, x, hy - 7 + (1 if x < hx - 5 else 0), 3)
    bow(g, hx - 10, hy - 10)
    e, ey = hx + 6, hy + 2
    if eyes == "open":
        rect(g, e, ey, e + 1, ey, 1)
        rect(g, e, ey + 1, e + 1, ey + 1, 10)
        rect(g, e, ey + 2, e + 1, ey + 4, 9)
        px(g, e, ey + 1, 6)
    elif eyes == "glow":  # 解弦之眼（戰鬥調色盤：7 紫、14 青、15 淡紫）
        rect(g, e, ey, e + 1, ey, 1)
        rect(g, e, ey + 1, e + 1, ey + 4, 7)
        px(g, e, ey + 2, 14); px(g, e + 1, ey + 3, 15)
    elif eyes == "sharp":  # 冷酷瞇眼＋發光
        rect(g, e - 1, ey + 2, e + 1, ey + 2, 1)
        rect(g, e, ey + 3, e + 1, ey + 4, 7)
        px(g, e + 1, ey + 3, 14)
    else:
        rect(g, e - 1, ey + 4, e + 1, ey + 4, 1)
    rect(g, hx + 4, ey + 5, hx + 5, ey + 5, 5)
    if mouth == "dot":
        px(g, hx + 8, hy + 7, 5)
    elif mouth == "open":
        rect(g, hx + 7, hy + 7, hx + 8, hy + 7, 10)
    elif mouth == "smirk":  # 嘴角上揚
        px(g, hx + 7, hy + 7, 1); px(g, hx + 8, hy + 6, 1)
    if hold:
        hold(g, ctx)
    else:
        arm(g, hip + 2, 21 + dy, arm_near, border=True)
    g = outline(separate(g))
    if fx:
        fx(g)
    return g if raw else up2(g)


def scenes():
    S = {}
    base = girl()
    S["idle"] = [base, shifted(base, 2, -2), base, shifted(base, -2, -2)]
    S["walk"] = [
        side(near=2, far=-2, arm_near=-3, arm_far=3, flow=1),
        side(dy=-1, far_lift=1, flow=1),
        side(near=-2, far=2, arm_near=3, arm_far=-3, flow=1),
        side(dy=-1, near_lift=1, flow=1),
    ]
    S["run"] = [
        side(dy=-1, near=3, far=-3, far_lift=2, arm_near=-4, arm_far=4, lean=1, flow=2, mouth="open",
             fx=lambda g: speed_lines(g, 0)),
        side(near=-3, far=3, near_lift=2, arm_near=4, arm_far=-4, lean=1, flow=2, mouth="open",
             fx=lambda g: speed_lines(g, 1)),
    ]
    snore = [(0, 1), (1, 2), (1, 3), (0, 4), (0, -1), (1, 0)]
    S["snore"] = [girl(dy=dy, eyes="closed", arms="front", fx=bubble(r, dy)) for dy, r in snore]
    return S


if __name__ == "__main__":
    mc.PAL[:] = PAL
    mc.scenes = scenes
    mc.DUR.update({"idle": 250, "walk": 160, "run": 110, "snore": 300})
    mc.OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_v3")
    os.makedirs(mc.OUT, exist_ok=True)
    mc.main()
    for f in os.listdir(mc.OUT):
        if f.startswith("cat_"):
            os.replace(os.path.join(mc.OUT, f), os.path.join(mc.OUT, "girl_" + f[4:]))
