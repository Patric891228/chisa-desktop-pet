"""睡眼惺忪（sleepy）：睡著時被按鍵叫醒播的動畫。沿用 make_girl_v7.py 的畫法。
流程：閉眼 → 半睜眼 → 眨眼 → 打哈欠（眼角有淚）→ 揉眼睛 → 睜眼。
用法：python3 make_sleepy.py → girl_v7/pet_sleepy.h、girl_v7/sleepy_preview.gif
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_girl_v7 as v7

v4, v3, v6 = v7.v4, v7.v3, v7.v6
px, rect = v7.px, v7.rect
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "girl_v7")
MS = 300

# ---------- 新眼神：sleepy（眼皮很重，只露出下面一條紅）----------
_head_front = v3.head_front


def head_front(g, hx, hy, eyes, mouth, look, blush=False):
    _head_front(g, hx, hy, "none" if eyes == "sleepy" else eyes, mouth, look, blush)
    if eyes == "sleepy":
        ey = hy + 2
        for ex in (hx - 6, hx + 3):
            e = ex + look
            rect(g, e, ey + 3, e + 2, ey + 3, 1)   # 下垂的眼皮
            rect(g, e, ey + 4, e + 2, ey + 4, 9)   # 只露出一條紅眼睛
            px(g, e, ey + 4, 10)


v3.head_front = head_front


def yawn(g):
    rect(g, 15, 19, 16, 20, 10)                    # 打哈欠：嘴巴張大


def tear(g):
    px(g, 22, 16, 6)                               # 眼角的淚


def left_arm_down(g):
    rect(g, 7, 21, 9, 24, 11); rect(g, 7, 24, 9, 24, 8); px(g, 8, 25, 4)


def rub(shift):
    """觀眾右邊的手舉起來揉眼睛，shift 讓拳頭上下動一格。"""
    def f(g):
        left_arm_down(g)
        rect(g, 21, 17, 25, 22, 1); rect(g, 22, 18, 24, 21, 11)          # 袖子
        rect(g, 19, 14 + shift, 22, 17 + shift, 1)                          # 拳頭外框
        rect(g, 20, 15 + shift, 21, 16 + shift, 4)                          # 拳頭
        px(g, 20, 16 + shift, 5)
    return f


def zz(n):
    """頭旁邊殘留的 z，n = 2 兩個、1 一個。"""
    def f(g):
        for x, y in ((27, 0), (23, 4))[:n]:
            rect(g, x, y, x + 3, y, 6); px(g, x + 2, y + 1, 6); px(g, x + 1, y + 2, 6); rect(g, x, y + 3, x + 3, y + 3, 6)
    return f


def both(*fs):
    def f(g):
        for k in fs:
            k(g)
    return f


def sleepy():
    F = v6.front
    return [
        F(dy=1, eyes="closed"),                                     # 還在睡
        F(dy=1, eyes="closed"),                                     # z 散掉
        F(eyes="sleepy"),                                         # 半睜眼
        F(eyes="closed"),                                         # 眨眼
        F(eyes="sleepy", dy=-1, extra=yawn),                      # 打哈欠，身體往上伸
        F(eyes="closed", dy=-1, extra=both(yawn, tear)),
        F(eyes="sleepy", arms="behind", extra=both(rub(0), tear)),  # 揉眼睛
        F(eyes="sleepy", arms="behind", extra=rub(1)),
        F(eyes="open"),                                           # 醒了
    ]


def export():
    frames = [v7.half([[3 if c == 13 else c for c in row] for row in f]) for f in sleepy()]
    L = ["// 由 make_sleepy.py 產生（1 倍，32x32）。格式同 pet_sprites.h：4bpp 索引色，index 0 = 透明", "#pragma once", "#include <stdint.h>", ""]
    names = []
    for i, f in enumerate(frames):
        data = []
        for row in f:
            for x in range(0, 32, 2):
                data.append((row[x] << 4) | row[x + 1])
        nm = f"pet_sleepy_{i}"
        names.append(nm)
        L.append(f"static const uint8_t {nm}[512] = {{")
        for k in range(0, 512, 32):
            L.append("  " + ",".join(f"0x{b:02X}" for b in data[k:k + 32]) + ",")
        L.append("};")
    L += [f"static const uint8_t* const pet_sleepy[] = {{{', '.join(names)}}};",
          "#define PET_SLEEPY_W 32", "#define PET_SLEEPY_H 32", f"#define PET_SLEEPY_FRAMES {len(frames)}", f"#define PET_SLEEPY_MS {MS}", ""]
    open(os.path.join(OUT, "pet_sleepy.h"), "w").write("\n".join(L))
    imgs = []
    for f in frames:
        bg = Image.new("RGBA", (32, 32), (24, 26, 38, 255))
        bg.alpha_composite(v4.to_img(f))
        imgs.append(bg.convert("RGB").resize((32 * 8, 32 * 8), Image.NEAREST))
    imgs[0].save(os.path.join(OUT, "sleepy_preview.gif"), save_all=True, append_images=imgs[1:], duration=MS, loop=0)
    sheet = Image.new("RGB", (len(imgs) * 32 * 4, 32 * 4))
    for i, im in enumerate(imgs):
        sheet.paste(im.resize((128, 128), Image.NEAREST), (i * 128, 0))
    sheet.save(os.path.join(OUT, "sleepy_sheet_x4.png"))


if __name__ == "__main__":
    export()
