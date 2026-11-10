"""程式產生 64x64、16 色的像素貓範例，並輸出 sprite sheet、預覽 GIF 與 ESP32 用 C 標頭檔。
用法：python3 make_cat.py   （需要 Pillow）
"""
from PIL import Image
import math, os

W = H = 64
OUT = os.path.dirname(os.path.abspath(__file__))

# 16 色調色盤（index 0 = 透明）
PAL = [
    (0, 0, 0),        # 0 透明
    (34, 28, 40),     # 1 外框
    (240, 150, 70),   # 2 身體主色
    (196, 104, 52),   # 3 身體陰影
    (255, 196, 120),  # 4 身體亮部
    (255, 236, 205),  # 5 肚子/口鼻
    (255, 255, 255),  # 6 眼白/反光
    (40, 36, 60),     # 7 瞳孔
    (255, 140, 160),  # 8 粉紅（鼻、耳內、腮紅）
    (230, 60, 80),    # 9 愛心紅
    (120, 170, 255),  # 10 Z 藍
    (70, 60, 90),     # 11 地面影子
    (160, 90, 50),    # 12 條紋
    (255, 230, 90),   # 13 星星黃
    (180, 210, 255),  # 14 淡藍
    (90, 200, 140),   # 15 綠（備用）
]


def blank():
    return [[0] * W for _ in range(H)]


def ellipse(g, cx, cy, rx, ry, c):
    for y in range(H):
        for x in range(W):
            if ((x - cx + .5) / rx) ** 2 + ((y - cy + .5) / ry) ** 2 <= 1:
                g[y][x] = c


def shade_ellipse(g, cx, cy, rx, ry, base, dark, light):
    for y in range(H):
        for x in range(W):
            dx, dy = (x - cx + .5) / rx, (y - cy + .5) / ry
            d = dx * dx + dy * dy
            if d <= 1 and g[y][x] == base:
                if dx * .5 + dy * .8 > .55:
                    g[y][x] = dark
                elif dx * -.6 + dy * -.8 > .62 and d > .35:
                    g[y][x] = light


def tri(g, pts, c):
    (x0, y0), (x1, y1), (x2, y2) = pts
    for y in range(H):
        for x in range(W):
            px, py = x + .5, y + .5
            d1 = (px - x1) * (y0 - y1) - (x0 - x1) * (py - y1)
            d2 = (px - x2) * (y1 - y2) - (x1 - x2) * (py - y2)
            d3 = (px - x0) * (y2 - y0) - (x2 - x0) * (py - y0)
            neg = d1 < 0 or d2 < 0 or d3 < 0
            pos = d1 > 0 or d2 > 0 or d3 > 0
            if not (neg and pos):
                g[y][x] = c


def px(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c


def outline(g):
    o = [r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and g[ny][nx] not in (0, 1, 11, 10, 13, 9):
                        o[y][x] = 1
                        break
    return o


def heart(g, x, y):
    for dy, row in enumerate(["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]):
        for dx, ch in enumerate(row):
            if ch == "1":
                px(g, x + dx, y + dy, 9)
    px(g, x + 1, y + 1, 6)


def zz(g, x, y, s):
    for i in range(s):
        px(g, x + i, y, 10); px(g, x + i, y + s - 1, 10); px(g, x + s - 1 - i, y + i, 10)


def star(g, x, y):
    for d in range(-2, 3):
        px(g, x + d, y, 13); px(g, x, y + d, 13)


def cat(dy=0, eyes="open", mouth="w", tail=0.0, ears=0, look=0, lying=False,
        stretch=0, fx=None):
    g = blank()
    by = 46 + (4 if lying else 0)
    # 地面影子
    ellipse(g, 32, 58, 18 + stretch, 3, 11)
    # 尾巴（一串圓形）
    for i in range(9):
        a = math.radians(-40 + tail * 25 + i * 9)
        tx = 46 + stretch + i * 1.6 * math.cos(a) - (2 if lying else 0)
        ty = by + 6 - i * 2.2 * (0.4 if lying else 1) + i * 0.3 * math.sin(a * 2)
        ellipse(g, tx, ty, 3, 3, 2)
    # 身體
    rx, ry = 16 + stretch, (8 if lying else 11)
    ellipse(g, 32 - stretch // 2, by + dy * .5, rx, ry, 2)
    shade_ellipse(g, 32 - stretch // 2, by + dy * .5, rx, ry, 2, 3, 4)
    ellipse(g, 30 - stretch // 2, by + 3 + dy * .5, 8, 6 if not lying else 4, 5)
    # 腳
    if not lying:
        for fxp in (22 - stretch, 38 - stretch):
            ellipse(g, fxp, 56, 4, 3, 2)
            px(g, fxp - 1, 57, 3); px(g, fxp + 1, 57, 3)
    hx = 30 - stretch + look
    hy = (36 if lying else 27) + dy + (4 if stretch else 0)
    # 耳朵
    e = ears
    tri(g, [(hx - 14, hy - 4), (hx - 11 - e, hy - 16 + abs(e) * 2), (hx - 3, hy - 9)], 2)
    tri(g, [(hx + 14, hy - 4), (hx + 11 + e, hy - 16 + abs(e) * 2), (hx + 3, hy - 9)], 2)
    tri(g, [(hx - 12, hy - 6), (hx - 10 - e, hy - 13 + abs(e) * 2), (hx - 6, hy - 9)], 8)
    tri(g, [(hx + 12, hy - 6), (hx + 10 + e, hy - 13 + abs(e) * 2), (hx + 6, hy - 9)], 8)
    # 頭
    ellipse(g, hx, hy, 15, 12, 2)
    shade_ellipse(g, hx, hy, 15, 12, 2, 3, 4)
    # 額頭條紋
    for sx in (-3, 0, 3):
        for k in range(3 - abs(sx) // 3):
            px(g, hx + sx, hy - 11 + k, 12)
    # 口鼻
    ellipse(g, hx, hy + 5, 6, 3.5, 5)
    # 眼睛
    for ex in (hx - 7, hx + 6):
        ey = hy - 1
        if eyes == "open":
            for yy in range(ey - 2, ey + 3):
                for xx in range(ex - 1, ex + 2):
                    px(g, xx, yy, 7)
            px(g, ex - 1 + (1 if look > 0 else 0), ey - 2, 6)
            px(g, ex - 1 + (1 if look > 0 else 0), ey - 1, 6)
        elif eyes == "closed":
            for xx in range(ex - 2, ex + 3):
                px(g, xx, ey + 1, 7)
            px(g, ex - 2, ey, 7); px(g, ex + 2, ey, 7)
        elif eyes == "happy":
            for xx in range(ex - 2, ex + 3):
                px(g, xx, ey - (1 if abs(xx - ex) < 2 else 0), 7)
            px(g, ex - 2, ey + 1, 7); px(g, ex + 2, ey + 1, 7)
        elif eyes == "half":
            for xx in range(ex - 1, ex + 2):
                px(g, xx, ey, 7); px(g, xx, ey + 1, 7)
    # 腮紅
    for bx in (hx - 10, hx + 9):
        px(g, bx, hy + 3, 8); px(g, bx + 1, hy + 3, 8)
    # 鼻子
    px(g, hx - 1, hy + 3, 8); px(g, hx, hy + 3, 8)
    # 嘴
    my = hy + 5
    if mouth == "w":
        for xx, yy in ((-3, 0), (-2, 1), (-1, 0), (0, 0), (1, 1), (2, 0)):
            px(g, hx + xx, my + yy, 1)
    elif mouth == "open":
        for yy in range(my, my + 3):
            for xx in range(hx - 2, hx + 2):
                px(g, xx, yy, 1)
        px(g, hx - 1, my + 2, 8); px(g, hx, my + 2, 8)
    elif mouth == "yawn":
        ellipse(g, hx, my + 2, 3, 3, 1)
        px(g, hx - 1, my + 3, 8); px(g, hx, my + 3, 8)
    g = outline(g)
    if fx:
        fx(g)
    return g


def scenes():
    S = {}
    S["idle"] = [cat(dy=0), cat(dy=1), cat(dy=1, tail=.6), cat(dy=0, tail=.6)]
    S["blink"] = [cat(), cat(eyes="half"), cat(eyes="closed"), cat(eyes="half")]
    S["happy"] = [
        cat(dy=0, eyes="happy", mouth="open", ears=1, fx=lambda g: heart(g, 50, 6)),
        cat(dy=-3, eyes="happy", mouth="open", ears=-1, tail=1, fx=lambda g: heart(g, 51, 3)),
        cat(dy=-5, eyes="happy", mouth="open", ears=1, tail=-1, fx=lambda g: (heart(g, 52, 1), star(g, 8, 8))),
        cat(dy=-2, eyes="happy", mouth="open", ears=0, fx=lambda g: star(g, 10, 6)),
    ]
    S["sleep"] = [
        cat(eyes="closed", mouth="w", lying=True, fx=lambda g: zz(g, 46, 18, 4)),
        cat(dy=1, eyes="closed", mouth="w", lying=True, fx=lambda g: (zz(g, 46, 16, 4), zz(g, 52, 9, 5))),
        cat(dy=1, eyes="closed", mouth="w", lying=True, fx=lambda g: (zz(g, 47, 13, 4), zz(g, 53, 5, 6))),
        cat(eyes="closed", mouth="w", lying=True, fx=lambda g: zz(g, 52, 3, 5)),
    ]
    S["stretch"] = [cat(), cat(stretch=2, eyes="half"), cat(stretch=4, eyes="closed", mouth="yawn"),
                    cat(stretch=2, eyes="half", mouth="yawn")]
    S["look"] = [cat(look=-2), cat(look=-3), cat(look=2), cat(look=3)]
    return S


def to_img(g, scale=1):
    im = Image.new("RGBA", (W, H))
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            im.putpixel((x, y), (*PAL[c], 0 if c == 0 else 255))
    return im.resize((W * scale, H * scale), Image.NEAREST) if scale > 1 else im


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


DUR = {}  # 每個情境每幀毫秒數，沒設定就用 180


def main():
    S = scenes()
    names = list(S)
    # sprite sheet：每列一個情境、每欄一格
    sheet = Image.new("RGBA", (W * max(len(v) for v in S.values()), H * len(names)))
    for r, n in enumerate(names):
        for c, f in enumerate(S[n]):
            sheet.paste(to_img(f), (c * W, r * H))
    sheet.save(os.path.join(OUT, "cat_sheet_64.png"))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(OUT, "cat_sheet_x4.png"))
    # 預覽 GIF（深色背景模擬螢幕）
    frames, durs = [], []
    for n in names:
        reps = max(2, 8 // len(S[n]))
        for _ in range(reps):
            for f in S[n]:
                durs.append(DUR.get(n, 180))
                bg = Image.new("RGBA", (W, H), (24, 26, 38, 255))
                bg.alpha_composite(to_img(f))
                frames.append(bg.convert("RGB").resize((W * 4, H * 4), Image.NEAREST))
    frames[0].save(os.path.join(OUT, "cat_preview.gif"), save_all=True, append_images=frames[1:], duration=durs, loop=0)
    # C 標頭：4-bit 索引（一 byte 兩像素）+ RGB565 調色盤，index 0 視為透明
    lines = ["// 由 make_cat.py 產生。64x64、4bpp 索引色，index 0 = 透明", "#pragma once", "#include <stdint.h>", "",
             "#define PET_W 64", "#define PET_H 64", "",
             "static const uint16_t pet_palette[16] = {" + ", ".join(f"0x{rgb565(*c):04X}" for c in PAL) + "};", ""]
    table = []
    for n in names:
        for i, f in enumerate(S[n]):
            data = []
            for y in range(H):
                for x in range(0, W, 2):
                    data.append((f[y][x] << 4) | f[y][x + 1])
            lines.append(f"static const uint8_t pet_{n}_{i}[{len(data)}] = {{")
            for k in range(0, len(data), 32):
                lines.append("  " + ",".join(f"0x{b:02X}" for b in data[k:k + 32]) + ",")
            lines.append("};")
        table.append(f"static const uint8_t* const pet_{n}[] = {{" + ", ".join(f"pet_{n}_{i}" for i in range(len(S[n]))) + "};")
        table.append(f"#define PET_{n.upper()}_FRAMES {len(S[n])}")
        table.append(f"#define PET_{n.upper()}_MS {DUR.get(n, 180)}")
    lines += [""] + table
    with open(os.path.join(OUT, "pet_sprites.h"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("ok", names)


if __name__ == "__main__":
    main()
