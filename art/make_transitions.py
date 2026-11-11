"""動作之間的轉換格：轉身、抽剪刀、拿書、家具從地板冒出來、跳上牆、蹲低、驚醒……
沿用 make_desktop / make_sleepy 的畫法，直接輸出 1 倍。
用法：python3 make_transitions.py <輸出資料夾>   → turn.png、draw_weapon.png …… ＋ anims_trans.json

程式（desktop_pet.py）會依「前一個動作的姿勢 → 下一個動作的姿勢」自動插入這些轉換格。
"ax" 是角色中心在圖上的 x（寬圖裡角色不在正中央時，程式用它對齊，切換時才不會跳一下）。
"""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_desktop as md

ms, v7, v4, v3, v6, v5 = md.ms, md.v7, md.v4, md.v3, md.v6, md.v5
px, rect, blank, paste = v5.px, v5.rect, v5.blank, v5.paste
WOOD, WOOD_HI = v5.WOOD, v5.WOOD_HI


def remap(f):
    return [[3 if c == 13 else c for c in row] for row in f]


def fr(f64, re=True):
    """64 格（2 倍）的圖縮回 1 倍；re=True 時把 13 換成 3（正面角色的百褶亮線）。"""
    return v7.half(remap(f64) if re else f64)


def pad_right(f, n):
    return [row + [0] * n for row in f]


def sink(layer, rise, floor):
    """整層往下移，地板（floor 那一列）以下切掉：rise=1 整個露出，0 完全在地下。"""
    off = round((1 - rise) * floor)
    h, w = len(layer), len(layer[0])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        sy = y - off
        if 0 <= sy < h and y <= floor:
            out[y] = layer[sy][:]
    return out


def debris(g, x0, x1, y):
    rect(g, x0, y, x1, y, 1)
    for x, yy in ((x0 - 2, y - 1), (x0 - 1, y - 2), (x1 + 2, y - 1), (x1 + 1, y - 2), (x0 - 3, y - 3), (x1 + 3, y - 3)):
        px(g, x, yy, 6)


# ---------- 1. 轉身：正面 → 斜看 → 側面 ----------
def turn():
    a = fr(v6.front(look=1, sway=1))
    b = fr(v3.side())
    return [a, b]


# ---------- 2. 從背後抽出剪刀扛上肩（收回就倒著播） ----------
def draw_weapon():
    W = v4.with_weapon
    return [fr(f) for f in (
        W(160, 265, behind=True, arm_far=2),                 # 手伸到背後握住
        W(-170, 230, behind=True, dy=-1),                    # 往上抽出來
        W(-120, 185, behind=True, flow=1),                   # 甩到身後
        W(-110, 165, near=1, far=-1, arm_far=2, flow=1),     # 扛好（接扛著剪刀走）
    )]


# ---------- 3. 拿出書、翻開（收書就倒著播） ----------
def closed_book(g):
    rect(g, 12, 20, 19, 25, 1)
    rect(g, 13, 21, 18, 24, v6.GREEN)
    rect(g, 13, 21, 13, 24, 6)                               # 書頁的邊
    px(g, 16, 22, 14); px(g, 15, 23, 14); px(g, 17, 23, 14)  # 燙金標誌


def book_open():
    a = fr(v6.front(arms="behind", look=1))                          # 手伸到背後拿書
    b = fr(v6.front(arms="hold", eyes="down", extra=closed_book))    # 書拿在胸前
    return [pad_right(a, 16), pad_right(b, 16)]


# ---------- 4／6. 桌椅從地板冒出來（48 寬，角色站在 x 0–31） ----------
def desk_layer():
    """make_girl_v5.desk_sleep 的桌椅（不含人），同樣砍掉 28–31 列收成 32 高。"""
    o = 4
    g = blank(48, 36)
    Y = lambda y: y + o
    rect(g, 5, Y(9), 8, Y(9), WOOD)
    rect(g, 6, Y(10), 7, Y(22), WOOD); rect(g, 7, Y(11), 7, Y(21), WOOD_HI)
    rect(g, 6, Y(22), 17, Y(22), WOOD_HI); rect(g, 6, Y(23), 17, Y(23), WOOD)
    rect(g, 7, Y(24), 7, Y(30), WOOD); rect(g, 16, Y(24), 16, Y(30), WOOD)
    rect(g, 8, Y(27), 15, Y(27), WOOD)
    rect(g, 23, Y(19), 46, Y(19), WOOD_HI); rect(g, 23, Y(20), 46, Y(21), WOOD)
    rect(g, 25, Y(22), 26, Y(30), WOOD); rect(g, 43, Y(22), 44, Y(30), WOOD)
    rect(g, 30, Y(22), 39, Y(24), WOOD); px(g, 34, Y(23), WOOD_HI); px(g, 35, Y(23), WOOD_HI)
    rect(g, 30, Y(25), 39, Y(25), 1)
    return [row for i, row in enumerate(g) if i not in (28, 29, 30, 31)]


def bed_layer():
    """make_girl_v5.bed_sleep 的床（不含人），同樣砍掉 0、1、32、33 列。"""
    g = blank(48, 36)
    rect(g, 1, 14, 5, 14, WOOD); rect(g, 2, 15, 4, 34, WOOD); rect(g, 3, 16, 3, 32, WOOD_HI)
    rect(g, 42, 20, 46, 20, WOOD); rect(g, 43, 21, 45, 34, WOOD); rect(g, 44, 22, 44, 32, WOOD_HI)
    rect(g, 5, 25, 42, 27, 6); rect(g, 5, 28, 42, 28, 8)
    rect(g, 5, 29, 42, 29, WOOD_HI); rect(g, 5, 30, 42, 31, WOOD)
    rect(g, 6, 32, 7, 34, WOOD); rect(g, 40, 32, 41, 34, WOOD)
    rect(g, 6, 21, 17, 24, 6); rect(g, 6, 24, 17, 24, 8); rect(g, 17, 22, 17, 24, 8)
    return [row for i, row in enumerate(g) if i not in (0, 1, 32, 33)]


def with_furniture(layer, rise, girl_dx, girl_kw, extra=None):
    g = blank(48, 32)
    if rise > 0:
        paste(g, sink(layer, rise, 30), 0, 0)
    girl = v3.girl(raw=True, **girl_kw)
    if extra:
        extra(girl)
    girl[31] = [0] * 32                                  # 人的影子不要，最後統一畫
    paste(g, girl, girl_dx, 0)
    rect(g, 3, 31, 46, 31, v4.SHADOW)
    if 0 < rise < 1:
        debris(g, 4, 45, 30)
    return fr(v5.finish(g, 31))


def desk_in():
    return [with_furniture(desk_layer(), r, 0, kw, ex) for r, kw, ex in (
        (0, dict(eyes="sleepy"), ms.yawn),
        (0.5, dict(eyes="sleepy", arms="behind"), ms.rub(0)),
        (1, dict(eyes="closed", dy=1), None),
    )]


def desk_out():
    return [with_furniture(desk_layer(), r, 0, kw) for r, kw in (
        (1, dict(eyes="closed", dy=1)),
        (0.5, dict(eyes="sleepy")),
        (0, dict(eyes="sleepy")),
    )]


def bed_in():
    return [with_furniture(bed_layer(), r, 8, kw, ex) for r, kw, ex in (
        (0, dict(eyes="sleepy"), ms.yawn),
        (0.5, dict(eyes="closed", dy=-1), ms.yawn),
        (1, dict(eyes="closed", dy=1), None),
    )]


def bed_out():
    return [with_furniture(bed_layer(), r, 8, kw) for r, kw in (
        (1, dict(eyes="closed", dy=1)),
        (0.5, dict(eyes="sleepy")),
        (0, dict(eyes="sleepy")),
    )]


# ---------- 7／8. 跳上牆、爬下來落地 ----------
def wall_jump():
    a = md.side_raw(dy=1, near=1, far=-1, lean=1)                             # 面對牆蹲低
    b = md.side_raw(dy=-2, lean=2, near_lift=2, far_lift=1, hold=md.wall_arms(25, 10))   # 往上跳、伸手抓牆
    return [md.finish_raw(a), md.finish_raw(b)]


def wall_land():
    return [md.finish_raw(md.side_raw(dy=1, near=1, far=-1))]                # 腳踩地、膝蓋彎一下


# ---------- 9. 撲游標前：轉正、蹲低蓄力 ----------
def crouch():
    return [fr(v6.front(dy=1, look=0, arms="grip")), fr(v6.front(dy=2, mouth="open", arms="grip"))]


# ---------- 10. 打瞌睡驚醒 ----------
def jolt():
    return [fr(v6.front(eyes="blank", dy=-1, fx=v6.bang(28, 2))), fr(v6.front(eyes="open", fx=v6.sweat(27, 9)))]


# ---------- 11. 當機後表情鬆開（眨眼） ----------
def relax():
    return [fr(v6.front(eyes="closed", blush=True))]


CLIPS = {
    "turn": (turn, [80, 90], None),
    "draw_weapon": (draw_weapon, [110, 110, 120, 140], None),
    "book_open": (book_open, [170, 220], 16),
    "desk_in": (desk_in, [450, 260, 300], 16),
    "desk_out": (desk_out, [300, 260, 300], 16),
    "bed_in": (bed_in, [450, 300, 300], None),
    "bed_out": (bed_out, [300, 260, 300], None),
    "wall_jump": (wall_jump, [140, 160], None),
    "wall_land": (wall_land, [180], None),
    "crouch": (crouch, [90, 200], None),
    "jolt": (jolt, [260, 300], None),
    "relax": (relax, [260], None),
}
REVERSED = {"turn_back": "turn", "sheath": "draw_weapon", "book_close": "book_open"}


def to_img(f):
    h, w = len(f), len(f[0])
    im = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            c = f[y][x]
            if c:
                im.putpixel((x, y), (*v4.PAL[c], 255))
    return im


def save(out, name, frames, ms_list, ax):
    w, h = len(frames[0][0]), len(frames[0])
    strip = Image.new("RGBA", (w * len(frames), h))
    for i, f in enumerate(frames):
        assert len(f[0]) == w and len(f) == h, (name, i)
        strip.alpha_composite(to_img(f), (i * w, 0))
    strip.save(os.path.join(out, name + ".png"))
    m = {"w": w, "h": h, "frames": len(frames), "ms": ms_list}
    if ax is not None:
        m["ax"] = ax
    return m


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "girl_v7", "trans")
    os.makedirs(out, exist_ok=True)
    meta, made = {}, {}
    for name, (fn, ms_list, ax) in CLIPS.items():
        frames = fn()
        assert len(frames) == len(ms_list), name
        made[name] = frames
        meta[name] = save(out, name, frames, ms_list, ax)
    for name, src in REVERSED.items():
        m = CLIPS[src]
        meta[name] = save(out, name, made[src][::-1], m[1][::-1], m[2])
    # 寬圖裡角色不在正中央的既有動作也標上 ax
    meta["_ax"] = {"read": 16, "desk_sleep_r": 16}
    json.dump(meta, open(os.path.join(out, "anims_trans.json"), "w"), indent=1)
    print("ok", {k: v["frames"] for k, v in meta.items() if not k.startswith("_")})
