#!/usr/bin/env python3
"""Chisa 桌面寵物（純軟體版）
透明、置頂、可拖曳的像素角色，在螢幕下緣走動。素材來自 pixel-assets/girl_v7（1 倍 PNG，執行時放大）。

操作：
  左鍵點她      互動選單：摸頭、送禮、看狀態、設定、離開
  左鍵拖曳      把她拎起來，放開會掉下去、落地
  右鍵          同左鍵選單

數值存在 ~/.config/desktop-pet/save.json。
測試用：PET_TIME_SCALE=60 python3 desktop_pet.py（數值的 1 小時變 1 分鐘）。
"""
import json, os, random, sys, time
from datetime import datetime, date

from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import (QRegion, QPixmap, QPainter, QTransform, QColor, QFont, QFontMetrics, QCursor,
                           QIcon, QAction, QActionGroup)
from PySide6.QtWidgets import (QApplication, QWidget, QMenu, QSystemTrayIcon, QLabel, QProgressBar,
                               QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout)

__version__ = "0.1.1"
FROZEN = getattr(sys, "frozen", False)          # 打包成執行檔（PyInstaller）時為 True
HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(HERE, "assets")
if sys.platform == "win32":
    CONF_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "chisa-desktop-pet")
elif sys.platform == "darwin":
    CONF_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "chisa-desktop-pet")
else:
    CONF_DIR = os.path.join(os.path.expanduser("~"), ".config", "desktop-pet")
SAVE = os.path.join(CONF_DIR, "save.json")
TIME_SCALE = float(os.environ.get("PET_TIME_SCALE", "1"))
HOUR = 3600.0

# ===== 規則（照 ESP32 版，拿掉好感階段，加上精力和摸頭加好感）=====
START_AFFECTION = 10
GIFT_MAX, GIFT_REGEN_H, GIFT_GAIN = 3, 4, 5
NEGLECT_STEP_H = 6                 # 每 6 小時沒理她，好感 -1
PAT_GAIN, PAT_DAILY = 1, 5         # 每天前 5 次摸頭各 +1
WAKE_GRACE_S = 5 * 60              # 睡覺時段被叫醒，5 分鐘沒互動就回去睡

# 每秒精力變化（負的是消耗）
ENERGY_RATE = {"walk": -0.05, "run": -0.15, "walk_weapon": -0.08, "run_weapon": -0.2, "swing": -0.25,
               "climb": -0.2, "hang": -0.05, "reach": -0.2, "carry": -0.1, "stretch": 0.05,
               "idle": 0.03, "read": 0.06, "snore": 0.15, "desk_sleep_r": 0.2, "bed_sleep_r": 0.25}

LINES = {
    "pat": ["……！？", "請、請不要突然這樣。", "摸頭要先提交申請書。", "……申請書呢？", "只准一下下。",
            "下次記得先說一聲。", "……哼，就這次。", "嗯……再一下也可以。"],
    "pat_cap": ["今天的摸頭額度用完了。", "再摸就要收費了。"],
    "pat_spam": ["系統過熱……", "等、等一下……！"],
    "gift": ["……給我的？謝謝。", "我、我會收好的。", "謝謝，我很喜歡。", "又是禮物？……謝謝。", "我會好好珍惜的。"],
    "no_gift": ["禮物送完了，{h} 後會再補一個。"],
    "sleepy": ["嗯……是誰……", "還想睡……", "……現在幾點？"],
    "drag": ["放、放我下來！", "……！？", "我不是行李。"],
    "land": ["……剛剛的事當作沒發生。", "嗚……", "下次先說一聲。"],
    "peek": ["……你在做什麼？", "我只是路過。", "……盯。", "沒、沒有在偷看。"],
    "tired": ["有點累了……", "想休息一下。"],
    "chat": ["……", "今天也要安靜地過。", "（翻書）", "你在忙嗎？", "今天的天氣，還可以。", "剪刀要定期保養。",
             "累了就休息一下吧。"],
    "morning": ["早安。……我還沒完全醒。"],
    "lunch": ["該吃午餐了吧？"],
    "late": ["已經很晚了，你也該睡了。"],
    "neglect": ["……（看了你一眼）", "……你還在嗎？"],
    "sit": ["已經坐 {m} 分鐘了，起來動一動吧。", "坐太久了。站起來，跟我一起伸懶腰。", "休息一下，眼睛看看遠方。"],
    "sit_back": ["歡迎回來。", "休息夠了嗎？"],
    "busy": ["等一下，我在忙。", "現在不行……！"],
    "climb_top": ["這裡視野不錯。", "……好高。", "（往下看）"],
    "climb_jump": ["嘿！", "……跳了。"],
    "climb_down": ["到了。", "下來了。"],
    "chase_start": ["……那個箭頭。", "別動。", "盯——"],
    "chase_high": ["太高了……", "……下來一點。"],
    "chase_miss": ["……沒抓到。", "下次一定。"],
    "chase_got": ["抓到了！", "哼哼，抓到了。"],
    "chase_escape": ["哇——被甩掉了！", "……甩得太用力了。"],
    "chase_return": ["玩夠了，放手。", "好，還給你。"],
}

# 禮物：照《鳴潮》千咲的角色資料（喜歡手工、剪裁、計算、巧克力棒，覺得比草莓口味好吃；討厭辣的食物）
# 名稱、喜好（love/like/normal/dislike）、好感變化、台詞、12x12 像素圖示
GIFTS = {
    "choco":    {"name": "巧克力棒", "pref": "love", "gain": 10,
                 "lines": ["……巧克力棒。你怎麼知道的？", "這個口味最好吃。……謝謝。"]},
    "paper":    {"name": "剪紙用的色紙", "pref": "like", "gain": 6,
                 "lines": ["色紙……我來剪一個最漂亮的給你。", "這個顏色，很適合剪花。"]},
    "sewing":   {"name": "布料和針線", "pref": "like", "gain": 5,
                 "lines": ["布料的紋路很整齊。……可以做點東西。", "針腳要算好間距才漂亮。"]},
    "astrite":  {"name": "星聲", "pref": "normal", "gain": 3,
                 "lines": ["星聲……這是要我拿去抽卡嗎？", "……你自己留著抽吧。"]},
    "strawberry": {"name": "草莓口味巧克力棒", "pref": "normal", "gain": 2,
                   "lines": ["草莓口味的……也可以。", "……原味的比較好吃。"]},
    "spicy":    {"name": "辣味零食", "pref": "dislike", "gain": -2,
                 "lines": ["……這是在挑戰我嗎？", "辣的不行。拿走。"]},
}
PREF_TEXT = {"love": "♥♥♥ 最喜歡", "like": "♥♥ 喜歡", "normal": "♥ 普通", "dislike": "✕ 討厭"}
GIFT_ICONS = {
    "choco": ["............", "........KK..", ".......KBBK.", "......KBCBK.", ".....KBCBK..", "....KWWBK...",
              "...KRWWK....", "..KRRRK.....", ".KRRRK......", ".KRRK.......", "..KK........", "............"],
    "paper": ["............", ".KKKKKKKK...", ".KRRRRRRK...", ".KRRKKKKKKK.", ".KRRKGGGGGK.", ".KRRKGGGGGK.",
              ".KKKKKKKKKKK", "...KNNNNNNNK", "...KNNNNNNNK", "...KNNNNNNNK", "...KKKKKKKKK", "............"],
    "sewing": ["............", "..KKKKKK....", "..KBBBBK..K.", "...KRRK...K.", "...KRRK...K.", "...KRRK..KAK",
               "...KRRK..KAK", "...KRRK..KAK", "..KBBBBK.KAK", "..KKKKKK..K.", "............", "............"],
    "astrite": [".....KK.....", "....KGGK....", "...KGWGGK...", "..KGWGGGGK..", ".KGGGGGGGGK.", "KGGGGWGGGGGK",
                ".KGGGGGGGGK.", "..KGGGGGGK..", "...KGGGGK...", "....KGGK....", ".....KK.....", "............"],
    "strawberry": ["............", "........KK..", ".......KPPK.", "......KPRPK.", ".....KPRPK..", "....KWWPK...",
                   "...KRWWK....", "..KRRRK.....", ".KRRRK......", ".KRRK.......", "..KK........", "............"],
    "spicy": ["............", "..KKKKKKKK..", "..KRRRRRRK..", "..KRRWWRRK..", "..KRWNNWRK..", "..KRWRRWRK..",
              "..KRWRRWRK..", "..KRRWWRRK..", "..KRRRRRRK..", "..KRRRRRRK..", "..KKKKKKKK..", "............"],
}
ICON_COLORS = {"K": (16, 12, 24), "A": (96, 94, 112), "B": (110, 62, 36), "C": (160, 100, 60), "G": (222, 178, 64), "W": (255, 255, 255), "R": (240, 52, 60),
               "D": (140, 10, 30), "N": (34, 92, 60), "L": (90, 170, 80), "P": (246, 186, 190)}


def gift_icon(gid):
    from PySide6.QtGui import QImage
    rows = GIFT_ICONS[gid]
    img = QImage(12, 12, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in ICON_COLORS:
                img.setPixelColor(x, y, QColor(*ICON_COLORS[ch]))
    return img


def chime_line(h):
    period = "凌晨" if h < 6 else "早上" if h < 9 else "上午" if h < 12 else "中午" if h == 12 else \
        "下午" if h < 18 else "晚上"
    h12 = h if h <= 12 else h - 12
    t = f"{period} {h12} 點"
    extra = {7: "……再五分鐘。", 8: "今天也要好好加油。", 12: "吃飯時間到了。", 14: "要不要喝點水？",
             15: "下午茶時間。", 17: "快下班了吧？", 18: "晚餐吃什麼？", 22: "準備休息吧。"}
    if h in extra:
        return f"{t}。{extra[h]}"
    if 9 <= h <= 11:
        return f"{t}了。專心的時間。"
    if 13 <= h <= 16:
        return f"{t}了。眼睛休息一下。"
    return f"{t}了。"

STATUS_TEXT = {"idle": "發呆", "walk": "散步", "run": "跑步", "read": "看書", "snore": "打瞌睡",
               "swing": "練剪刀", "walk_weapon": "扛著剪刀散步", "run_weapon": "扛著剪刀跑步",
               "desk_sleep_r": "趴在桌上午睡", "bed_sleep_r": "睡覺", "headpat": "被摸頭（當機中）",
               "shy_pole": "躲在電線桿後面", "guard": "防備", "shy": "害羞", "gift": "收禮物",
               "sleepy": "睡眼惺忪", "held": "被拎起來", "fall": "往下掉", "land": "落地",
               "peek": "偷看你的螢幕", "climb": "爬螢幕邊緣", "hang": "掛在螢幕邊緣", "stretch": "伸懶腰",
               "reach": "跳起來抓游標", "carry": "吊在你的游標上"}
REACTIONS = ("shy_pole", "guard", "shy")
FRONT_ONLY = {"peek", "read", "desk_sleep_r", "bed_sleep_r", "held", "fall", "land", "stretch", "reach"}   # 不水平翻轉的動作      # 摸頭之後隨機接一個


def pick(key):
    return random.choice(LINES[key])


def minute_of_day():
    t = datetime.now()
    return t.hour * 60 + t.minute


def is_nap(m):   return 12 * 60 + 30 <= m < 13 * 60 + 30
def is_night(m): return m >= 23 * 60 or m < 7 * 60
def is_pre_sleep(m): return 11 * 60 + 30 <= m < 12 * 60 + 30 or 22 * 60 <= m < 23 * 60


def fmt_hours(sec):
    sec = max(0, int(sec))
    h, m = sec // 3600, (sec % 3600) // 60
    return f"{h} 小時 {m} 分" if h else f"{m} 分鐘"


# ===== 數值 =====
class Stats:
    def __init__(self):
        self.affection = START_AFFECTION
        self.gift_stock = GIFT_MAX
        self.gift_timer = 0.0        # 秒（數值時間）
        self.neglect = 0.0           # 秒
        self.neglect_steps = 0
        self.energy = 80.0
        self.pats_today = 0
        self.pats_date = date.today().isoformat()
        self.first_day = date.today().isoformat()
        self.last_seen = time.time()
        self.gift_log = {}           # 每種禮物送過幾次
        self.settings = {"scale": 4, "on_top": True, "schedule": True, "x": None, "chat": True, "bubble": "paper",
                         "sit_min": 50, "chime": True, "climb": True, "chase": True}

    def load(self):
        try:
            d = json.load(open(SAVE, encoding="utf-8"))
        except (OSError, ValueError):
            return
        for k, v in d.items():
            if k == "settings":
                self.settings.update(v)
            elif hasattr(self, k):
                setattr(self, k, v)
        # 關掉期間經過的時間：禮物照常恢復；冷落最多算 24 小時；離開超過 1 小時就睡飽了
        away = max(0.0, time.time() - self.last_seen) * TIME_SCALE
        self.tick(away, awake=False)
        self.tick(min(away, 24 * HOUR), awake=True, gifts=False)
        if away > HOUR:
            self.energy = 100.0

    def save(self):
        self.last_seen = time.time()
        os.makedirs(CONF_DIR, exist_ok=True)
        tmp = SAVE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=1)
        os.replace(tmp, SAVE)

    def add_affection(self, n):
        self.affection = max(0, min(100, self.affection + n))

    def touched(self):
        self.neglect = 0.0
        self.neglect_steps = 0

    def tick(self, dt, awake=True, gifts=True):
        """dt：數值時間（秒）。awake=False 時不算冷落（睡覺時段）。"""
        if gifts:
            if self.gift_stock < GIFT_MAX:
                self.gift_timer += dt
                while self.gift_timer >= GIFT_REGEN_H * HOUR and self.gift_stock < GIFT_MAX:
                    self.gift_timer -= GIFT_REGEN_H * HOUR
                    self.gift_stock += 1
            if self.gift_stock >= GIFT_MAX:
                self.gift_timer = 0.0
        if awake:
            self.neglect += dt
            steps = int(self.neglect // (NEGLECT_STEP_H * HOUR))
            while self.neglect_steps < steps:
                self.neglect_steps += 1
                self.add_affection(-1)
        today = date.today().isoformat()
        if self.pats_date != today:
            self.pats_date, self.pats_today = today, 0

    def gift_eta(self):
        return GIFT_REGEN_H * HOUR - self.gift_timer

    def neglect_eta(self):
        step = NEGLECT_STEP_H * HOUR
        return step - (self.neglect % step)


# ===== 素材 =====
class Sprites:
    def __init__(self):
        self.meta = json.load(open(os.path.join(ASSETS, "anims.json"), encoding="utf-8"))
        self.sheets = {n: QPixmap(os.path.join(ASSETS, n + ".png")) for n in self.meta}
        self.cache = {}

    def frame(self, name, i, scale, flip):
        key = (name, i, scale, flip)
        if key not in self.cache:
            m = self.meta[name]
            p = self.sheets[name].copy(i * m["w"], 0, m["w"], m["h"])
            p = p.scaled(m["w"] * scale, m["h"] * scale, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            if flip:
                p = p.transformed(QTransform().scale(-1, 1))
            self.cache[key] = (p, p.mask())
        return self.cache[key]


# ===== 對話泡泡 =====
# 像素字型：俐方體 11 號（Cubic 11，SIL OFL 1.1，fonts/ 內附授權）
FONT_PATH = os.path.join(HERE, "fonts", "Cubic_11.ttf")
_font_family = None


def pixel_font():
    global _font_family
    if _font_family is None:
        from PySide6.QtGui import QFontDatabase
        fid = QFontDatabase.addApplicationFont(FONT_PATH)
        fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        _font_family = fams[0] if fams else ""
    f = QFont(_font_family) if _font_family else QFont()
    f.setPixelSize(12)
    f.setStyleStrategy(QFont.NoAntialias)
    f.setHintingPreference(QFont.PreferNoHinting)
    return f


C = lambda *rgb: QColor(*rgb)
INK, WHITE, LAV, HAIR = C(16, 12, 24), C(255, 255, 255), C(100, 96, 146), C(46, 42, 72)
RED, DRED, NAVY, COAT = C(240, 52, 60), C(140, 10, 30), C(32, 34, 62), C(38, 36, 44)
CYAN, PURPLE, SKIN = C(80, 220, 230), C(150, 70, 220), C(255, 240, 230)

# 對話框樣式：(名稱, 外框, 底色, 字色, 陰影, 裝飾)
BUBBLE_STYLES = {
    "paper":  ("白紙（黑框白底）", INK, WHITE, INK, LAV, "bow"),
    "coat":   ("制服（深藍底白字）", INK, NAVY, SKIN, C(96, 94, 112), "collar"),
    "system": ("解弦系統（終端機）", PURPLE, C(16, 12, 24, 225), CYAN, None, "bracket"),
}


BOW = [".KK...KK.",
       "KRRK.KRRK",
       "KRDRKRDRK",
       "KRRKDKRRK",
       ".KK.K.KK.",
       "...KRK...",
       "..KR.RK..",
       "..K...K.."]


def render_bubble(text, style="paper", max_w=150, icon=None):
    """在 1 倍畫布上畫像素對話框，回傳 QImage（之後整數倍放大，維持像素感）。"""
    import math
    from PySide6.QtGui import QImage
    _, line, fill, ink, shadow, deco = BUBBLE_STYLES.get(style, BUBBLE_STYLES["paper"])
    font = pixel_font()
    fm = QFontMetrics(font)
    full = fm.horizontalAdvance(text)
    if full > max_w:                                # 換行時讓每行差不多長，不留一個字在第二行
        n = math.ceil(full / max_w)
        max_w = math.ceil(full / n) + fm.horizontalAdvance("。。")
    tr = fm.boundingRect(QRect(0, 0, max_w, 400), Qt.TextWordWrap, text)
    tw, th = max(tr.width(), 12), tr.height()
    iw = icon.width() + 4 if icon is not None else 0
    th = max(th, icon.height() if icon is not None else 0)
    tw += iw
    padx, pady = 7, 5
    bw, bh = tw + padx * 2, th + pady * 2 + (2 if deco == "collar" else 0)
    mx, my = 3, 3                                   # 留邊給蝴蝶結等裝飾
    tail = [5, 4, 3, 2, 1]                          # 尾巴每一列的寬度
    W, H = bw + mx * 2 + 1, bh + my + len(tail) + 2
    img = QImage(W, H, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, False)

    def r(x, y, w, h, c):
        p.fillRect(mx + x, my + y, w, h, c)

    def box(ox, oy, edge, body):
        r(ox + 2, oy, bw - 4, 1, edge); r(ox + 2, oy + bh - 1, bw - 4, 1, edge)
        r(ox, oy + 2, 1, bh - 4, edge); r(ox + bw - 1, oy + 2, 1, bh - 4, edge)
        for x, y in ((1, 1), (bw - 2, 1), (1, bh - 2), (bw - 2, bh - 2)):
            r(ox + x, oy + y, 1, 1, edge)
        r(ox + 2, oy + 1, bw - 4, bh - 2, body); r(ox + 1, oy + 2, bw - 2, bh - 4, body)

    def tail_at(ox, oy, edge, body):
        x0 = bw // 2 - 2                            # 直角三角形尾巴：左邊垂直，往右下收
        for i, w in enumerate(tail):
            r(ox + x0, oy + bh - 1 + i, w, 1, body)
            r(ox + x0 - 1, oy + bh - 1 + i, 1, 1, edge); r(ox + x0 + w, oy + bh - 1 + i, 1, 1, edge)
        r(ox + x0 - 1, oy + bh - 1 + len(tail), 2, 1, edge)

    if shadow is not None:                          # 陰影：右下偏 1 格
        box(1, 1, shadow, shadow); tail_at(1, 1, shadow, shadow)
    p.setCompositionMode(QPainter.CompositionMode_Source)
    box(0, 0, line, fill); tail_at(0, 0, line, fill)
    p.setCompositionMode(QPainter.CompositionMode_SourceOver)

    if deco == "bow":                               # 左上角掛一個紅色蝴蝶結（跟她頭上那個一樣）
        cols = {"K": INK, "R": RED, "D": DRED}
        for y, row in enumerate(BOW):
            for x, ch in enumerate(row):
                if ch in cols:
                    r(x - 3, y - 3, 1, 1, cols[ch])
    elif deco == "collar":                          # 水手領白線＋紅領巾
        r(2, 2, bw - 4, 1, WHITE)
        r(bw // 2 - 3, 1, 6, 1, RED); r(bw // 2 - 2, 2, 4, 1, RED); r(bw // 2 - 1, 3, 2, 1, DRED)
    elif deco == "bracket":                         # 四角青色括號＋右上閃爍點
        for x, y, dx, dy in ((2, 2, 1, 1), (bw - 3, 2, -1, 1), (2, bh - 3, 1, -1), (bw - 3, bh - 3, -1, -1)):
            r(x, y, 1, 1, CYAN); r(x + dx, y, 1, 1, CYAN); r(x, y + dy, 1, 1, CYAN)
        r(bw - 5, -1, 3, 1, CYAN)

    if icon is not None:
        p.drawImage(mx + padx, my + pady + (th - icon.height()) // 2, icon)
    p.setFont(font)
    p.setPen(ink)
    top = pady + (2 if deco == "collar" else 0)
    p.drawText(QRect(mx + padx + iw, my + top - (1 if deco != "collar" else 0), tw - iw, th),
               Qt.TextWordWrap | Qt.AlignHCenter | Qt.AlignVCenter, text)
    p.end()
    return img


class Bubble:
    """對話框：畫在寵物同一個視窗裡（不另開視窗），所以一定跟著她移動。"""
    def __init__(self, on_change):
        self.pix = None
        self.mask = None
        self.on_change = on_change
        self.hide_timer = QTimer(singleShot=True, timeout=self.hide)

    def say(self, text, style="paper", zoom=2, icon=None):
        img = render_bubble(text, style, icon=icon)
        self.pix = QPixmap.fromImage(img.scaled(img.width() * zoom, img.height() * zoom,
                                                Qt.IgnoreAspectRatio, Qt.FastTransformation))
        self.mask = self.pix.mask()
        self.hide_timer.start(int(2200 + 120 * len(text)))
        self.on_change()

    def hide(self):
        self.pix = self.mask = None
        self.on_change()

    def isVisible(self):
        return self.pix is not None


MENU_CSS = """
QMenu { background:#181a26; color:#fff0e6; border:2px solid #100c18; padding:4px; font-family:'%s'; font-size:16px; }
QMenu::item { padding:5px 22px 5px 14px; }
QMenu::item:selected { background:#f0343c; color:#ffffff; }
QMenu::item:disabled { color:#646092; }
QMenu::separator { height:2px; background:#2e2a48; margin:4px 6px; }
QMenu::indicator { width:10px; height:10px; margin-left:4px; }
QMenu::indicator:checked { background:#deb240; border:2px solid #100c18; }
QMenu::indicator:unchecked { background:#26242c; border:2px solid #646092; }
"""


# ===== 狀態面板 =====
BAR_CSS = ("QProgressBar{border:1px solid #646092;border-radius:3px;background:#1a1a26;height:14px;color:#fff;text-align:center}"
           "QProgressBar::chunk{background:%s;border-radius:2px}")


class StatusPanel(QWidget):
    def __init__(self, pet):
        super().__init__(None, Qt.Window | Qt.WindowStaysOnTopHint)
        self.pet = pet
        self.setWindowTitle(f"她的狀態（v{__version__}）")
        self.setStyleSheet("QWidget{background:#181a26;color:#fff0e6;font-size:13px} "
                           "QPushButton{background:#2e2a48;border:1px solid #646092;padding:5px 10px;border-radius:4px}"
                           "QPushButton:hover{background:#464068}")
        L = QVBoxLayout(self)
        self.clock = QLabel(); self.clock.setStyleSheet("font-size:22px;color:#deb240")
        self.doing = QLabel()
        L.addWidget(self.clock); L.addWidget(self.doing)
        grid = QGridLayout()
        self.aff = QProgressBar(maximum=100); self.aff.setStyleSheet(BAR_CSS % "#f0343c")
        self.eng = QProgressBar(maximum=100); self.eng.setStyleSheet(BAR_CSS % "#96cdff")
        self.likes = QLabel(); self.likes.setWordWrap(True)
        self.gifts = QLabel(); self.neglect = QLabel(); self.pats = QLabel(); self.days = QLabel()
        rows = [("好感度", self.aff), ("精力", self.eng), ("禮物", self.gifts), ("喜好", self.likes),
                ("冷落", self.neglect), ("今天摸頭", self.pats), ("相處", self.days)]
        for r, (k, w) in enumerate(rows):
            lab = QLabel(k); lab.setStyleSheet("color:#9a96c0")
            grid.addWidget(lab, r, 0); grid.addWidget(w, r, 1)
        L.addLayout(grid)
        btns = QHBoxLayout()
        for text, fn in (("摸頭", pet.do_pat), ("送禮", pet.do_gift)):
            b = QPushButton(text); b.clicked.connect(fn); btns.addWidget(b)
        L.addLayout(btns)
        self.setFixedWidth(330)
        self.timer = QTimer(self, interval=500, timeout=self.refresh)

    def showEvent(self, e):
        self.refresh(); self.timer.start(); super().showEvent(e)

    def hideEvent(self, e):
        self.timer.stop(); super().hideEvent(e)

    def refresh(self):
        s, pet = self.pet.stats, self.pet
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))
        self.doing.setText("她正在：" + STATUS_TEXT.get(pet.anim_name, pet.anim_name))
        self.aff.setValue(s.affection); self.aff.setFormat(f"{s.affection} / 100")
        self.eng.setValue(int(s.energy)); self.eng.setFormat(f"{int(s.energy)} / 100")
        g = "●" * s.gift_stock + "○" * (GIFT_MAX - s.gift_stock)
        if s.gift_stock < GIFT_MAX:
            g += f"　下一個 {fmt_hours(s.gift_eta() / TIME_SCALE)} 後"
        self.gifts.setText(g)
        known = [f"{GIFTS[g]['name']} {PREF_TEXT[GIFTS[g]['pref']].split()[0]}" for g in GIFTS if s.gift_log.get(g)]
        self.likes.setText("、".join(known) + f"（{len(known)}/{len(GIFTS)}）" if known else f"還不知道（0/{len(GIFTS)}），送禮試試看")
        self.neglect.setText(f"再 {fmt_hours(s.neglect_eta() / TIME_SCALE)} 沒理她，好感 -1")
        self.pats.setText(f"{s.pats_today} 次（前 {PAT_DAILY} 次各 +{PAT_GAIN} 好感）")
        d = (date.today() - date.fromisoformat(s.first_day)).days + 1
        self.days.setText(f"第 {d} 天")


# ===== 寵物本體 =====
class Pet(QWidget):
    TICK_MS = 33

    def __init__(self, app):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        self.app = app
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)   # macOS：切到別的程式時不要消失
        self.setMouseTracking(True)
        self.stats = Stats(); self.stats.load()
        self.sprites = Sprites()
        self.bubble = Bubble(lambda: self.redraw() if hasattr(self, "pix") else None)
        self.sprite_rect = QRect()
        self.bubble_rect = QRect()
        self.panel = StatusPanel(self)
        self.apply_on_top(self.stats.settings["on_top"], init=True)

        g = self.screen_geo()
        x = self.stats.settings.get("x")
        self.cx = float(x) if x is not None and g.left() <= x <= g.right() else float(g.center().x())
        self.bottom = float(g.bottom() + 1)   # 腳底的 y（地面）
        self.vy = 0.0
        self.facing_left = False
        self.mode = "normal"                   # normal / react / sleep / held / fall
        self.queue = []                        # 互動反應佇列：(動畫, 輪數, 說的話)
        self.anim_name, self.frame, self.frame_t = "idle", 0, 0.0
        self.loops_left, self.speed, self.target = 0, 0.0, self.cx
        self.last_action = None
        self.last_input = 0.0                  # 上次互動的 time.time()
        self.woken_at = None                   # 睡覺時段被叫醒的時間
        self.react_clicks = 0
        self.press_pos = None
        self.drag_off = QPoint()
        self.next_chat = time.time() + random.uniform(60, 180)
        self.said_today = set()
        self.last_tick = time.time()
        self.stat_save_t = time.time()
        self.on_arrive = None                  # 走到目標後要做的事（爬牆、追游標）
        self.climb_phase, self.climb_top = None, 0.0
        self.chase_tries, self.caught = 0, False
        self.carry_t, self.carry_until, self.cur_last, self.cur_speed = 0.0, 0.0, None, 0.0
        now = time.time()                      # 久坐提醒：滑鼠一直在動的時間
        self.last_cursor, self.last_move, self.sit_start, self.next_sit = QCursor.pos(), now, now, 0.0
        self.sit_reminded = False
        self.last_chime = minute_of_day() // 60

        if self.stats.settings["schedule"] and self.is_sleep_time():
            self.enter_sleep()
        else:
            self.play("idle", 2)
        self.timer = QTimer(self, interval=self.TICK_MS, timeout=self.tick)
        self.timer.start()
        self.setup_tray()

    # ---------- 小工具 ----------
    @property
    def scale(self):
        return int(self.stats.settings["scale"])

    def screen_geo(self):
        scr = QApplication.screenAt(QPoint(int(getattr(self, "cx", 0)), int(getattr(self, "bottom", 0)) - 5)) \
            or QApplication.primaryScreen()
        return scr.availableGeometry()

    def meta(self, name=None):
        return self.sprites.meta[name or self.anim_name]

    def half_w(self, name=None):
        return self.meta(name)["w"] * self.scale / 2

    def say(self, text, icon=None):
        if text:
            self.bubble.say(text, self.stats.settings.get("bubble", "paper"), max(1, self.scale // 2), icon)

    def is_sleep_time(self):
        m = minute_of_day()
        return is_nap(m) or is_night(m)

    def should_sleep(self):
        if not self.stats.settings["schedule"] or not self.is_sleep_time():
            return False
        return self.woken_at is None or time.time() - max(self.woken_at, self.last_input) >= WAKE_GRACE_S

    def input_happened(self):
        self.last_input = time.time()
        self.stats.touched()

    # ---------- 播放 ----------
    def play(self, name, loops=1, speed=0.0, target=None):
        if name in FRONT_ONLY:
            self.facing_left = False
        self.anim_name, self.frame, self.frame_t = name, 0, 0.0
        self.loops_left, self.speed = loops, speed
        if target is not None:
            self.target = target
            self.facing_left = target < self.cx
        g = self.screen_geo()
        hw = self.half_w(name)
        self.cx = max(g.left() + hw, min(g.right() + 1 - hw, self.cx))
        self.redraw()

    def frame_ms(self):
        return self.meta()["ms"][self.frame]

    def redraw(self):
        flip = self.facing_left
        pix, mask = self.sprites.frame(self.anim_name, self.frame, self.scale, flip)
        self.pix = pix
        sc = self.scale
        S = QRect(int(round(self.cx - pix.width() / 2)), int(round(self.bottom - pix.height())),
                  pix.width(), pix.height())
        if self.bubble.isVisible():
            # 說話時視窗大小固定（只移動、不縮放），避免視窗管理器縮放時殘影變成兩個對話框
            bp = self.bubble.pix
            g = self.screen_geo()
            W = max(56 * sc, bp.width())
            H = (35 - 3) * sc + bp.height()
            wx = max(g.left(), min(g.right() + 1 - W, int(round(self.cx - W / 2))))
            U = QRect(wx, int(round(self.bottom)) - H, W, H)
            bx = max(g.left(), min(g.right() + 1 - bp.width(), int(self.cx) - bp.width() // 2))
            by = S.top() + self.meta().get("pad_top", 0) * sc - bp.height()
            B = QRect(bx, by, bp.width(), bp.height())
            B.moveLeft(max(U.left(), min(U.right() + 1 - B.width(), B.left())))
            B.moveTop(max(U.top(), g.top(), B.top()))
            U = U.united(S).united(B)
        else:
            U = S
        if self.geometry().size() != U.size():
            self.setGeometry(U)
        elif self.pos() != U.topLeft():
            self.move(U.topLeft())
        self.sprite_rect = S.translated(-U.topLeft())
        region = QRegion(mask).translated(self.sprite_rect.topLeft())
        if self.bubble.isVisible():
            self.bubble_rect = B.translated(-U.topLeft())
            region = region.united(QRegion(self.bubble.mask).translated(self.bubble_rect.topLeft()))
        self.setMask(region)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.drawPixmap(self.sprite_rect.topLeft(), self.pix)
        if self.bubble.isVisible():
            p.drawPixmap(self.bubble_rect.topLeft(), self.bubble.pix)

    # ---------- 行為 ----------
    def pick_next(self):
        self.mode = "normal"
        s = self.stats
        m = minute_of_day()
        pool = {"idle": 3, "walk": 3, "run": 2, "read": 2, "walk_weapon": 1, "run_weapon": 1, "swing": 1, "peek": 1}
        if is_pre_sleep(m):
            pool["snore"] = 2
        if s.energy < 25:                        # 累了：多休息，少跑步
            pool = {"idle": 2, "read": 3, "snore": 3, "desk_sleep_r": 2, "walk": 1}
        elif s.energy < 50:
            pool.pop("run", None); pool.pop("run_weapon", None)
        st = s.settings
        if st.get("climb", True) and s.energy >= 40:
            pool["climb"] = 1
        if st.get("chase", True) and s.energy >= 30:
            pool["chase"] = 1
        if self.last_action in pool and len(pool) > 1:
            pool.pop(self.last_action)
        a = random.choices(list(pool), weights=list(pool.values()))[0]
        self.last_action = a
        if s.energy < 25 and a in ("snore", "desk_sleep_r") and random.random() < 0.5:
            self.say(pick("tired"))

        g = self.screen_geo()
        if a == "climb":
            self.start_climb(); return
        if a == "chase":
            self.chase_tries = 0
            self.say(pick("chase_start"))
            self.start_chase(); return
        if a in ("walk", "run", "walk_weapon", "run_weapon"):
            name = a
            hw = self.half_w(name)
            lo, hi = g.left() + hw, g.right() + 1 - hw
            dist = random.uniform(80, 500) * (1.6 if "run" in a else 1)
            tx = self.cx + random.choice((-1, 1)) * dist
            if not lo <= tx <= hi:
                tx = self.cx - (tx - self.cx)
            tx = max(lo, min(hi, tx))
            if abs(tx - self.cx) < 20:
                self.play("idle", random.randint(2, 4)); return
            px_per_s = {"walk": 7, "walk_weapon": 5, "run": 20, "run_weapon": 18}[name] * self.scale
            self.play(name, 0, px_per_s, target=tx)
        else:
            loops = {"idle": (3, 6), "read": (6, 11), "snore": (3, 6), "swing": (2, 4), "desk_sleep_r": (4, 8),
                     "peek": (1, 1)}[a]
            self.facing_left = False if a in ("read", "desk_sleep_r") else self.facing_left
            self.play(a, random.randint(*loops))

    def enter_sleep(self):
        self.mode = "sleep"
        self.woken_at = None
        self.facing_left = False
        self.queue.clear()
        self.play("desk_sleep_r" if is_nap(minute_of_day()) else "bed_sleep_r", 0)

    def react(self, steps):
        """steps：[(動畫, 輪數, 說的話), ...] 依序播。"""
        self.mode = "react"
        self.on_arrive, self.caught, self.speed = None, False, 0
        self.react_clicks = 0
        self.queue = list(steps)
        self.next_in_queue()

    def next_in_queue(self):
        name, loops, line = self.queue.pop(0)
        self.facing_left = False
        self.play(name, loops)
        icon = None
        if name in ("gift", "guard") and getattr(self, "gift_icon_pending", None) is not None and line:
            icon, self.gift_icon_pending = self.gift_icon_pending, None
        self.say(line, icon)

    def anim_done(self):
        if self.mode == "climb":
            self.climb_next(); return
        if self.mode == "react" and self.queue:
            self.next_in_queue(); return
        if self.should_sleep():
            self.enter_sleep()
        else:
            self.pick_next()

    def wake_prefix(self):
        """睡著時被吵醒：先播睡眼惺忪。"""
        if self.mode == "sleep":
            self.woken_at = time.time()
            return [("sleepy", 1, pick("sleepy"))]
        return []

    # ---------- 互動 ----------
    def busy(self):
        if self.mode in ("climb", "jump", "carry", "fall", "held"):
            self.say(pick("busy"))
            return True
        return False

    def do_pat(self):
        s = self.stats
        self.input_happened()
        if self.busy():
            return
        if self.mode == "react" and self.anim_name == "headpat":
            self.react_clicks += 1
            if self.react_clicks == 3:
                self.say(pick("pat_spam"))
            return
        pre = self.wake_prefix()
        if pre:
            self.react(pre); return
        line = pick("pat")
        if s.pats_today < PAT_DAILY:
            s.add_affection(PAT_GAIN)
        elif s.pats_today == PAT_DAILY + 2:
            line = pick("pat_cap")
        s.pats_today += 1
        self.react([("headpat", 1, None), (random.choice(REACTIONS), 1, line)])

    def do_gift(self, gid=None):
        s = self.stats
        self.input_happened()
        if self.busy():
            return
        pre = self.wake_prefix()
        if s.gift_stock == 0:
            msg = pick("no_gift").format(h=fmt_hours(s.gift_eta() / TIME_SCALE))
            if pre:
                self.react(pre + [("idle", 1, msg)])
            else:
                self.say(msg)
            return
        gid = gid or random.choice(list(GIFTS))
        gift = GIFTS[gid]
        s.gift_stock -= 1
        s.add_affection(gift["gain"])
        s.gift_log[gid] = s.gift_log.get(gid, 0) + 1
        line = random.choice(gift["lines"])
        steps = {"love": [("gift", 2, line), ("shy", 1, None)], "like": [("gift", 2, line)],
                 "normal": [("gift", 1, line)], "dislike": [("guard", 1, line)]}[gift["pref"]]
        self.gift_icon_pending = gift_icon(gid)
        self.react(pre + steps)
        self.stats.save()

    def show_panel(self):
        self.panel.show(); self.panel.raise_(); self.panel.activateWindow()

    # ---------- 滑鼠 ----------
    def mousePressEvent(self, e):
        if not self.sprite_rect.contains(e.position().toPoint()):   # 點到對話框：關掉它
            self.bubble.hide()
            return
        if e.button() == Qt.LeftButton:            # 先記下來：放開時沒移動就開選單，有移動就是拎起來
            self.press_pos = e.globalPosition().toPoint()
            self.drag_off = QPoint(int(self.cx), int(self.bottom)) - self.press_pos
        elif e.button() == Qt.RightButton:
            self.menu.popup(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        if self.press_pos is None:
            return
        gp = e.globalPosition().toPoint()
        if self.mode != "held" and (gp - self.press_pos).manhattanLength() > 6:
            self.input_happened()
            was_sleep = self.mode == "sleep"
            self.mode = "held"
            self.on_arrive, self.caught = None, False
            self.queue.clear()
            self.facing_left = False
            self.anim_name, self.frame, self.frame_t, self.loops_left, self.speed = "held", 0, 0.0, 0, 0
            self.say(pick("sleepy") if was_sleep else pick("drag"))
            if was_sleep:
                self.woken_at = time.time()
        if self.mode == "held":
            p = gp + self.drag_off
            self.cx, self.bottom = float(p.x()), float(p.y())
            self.redraw()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or self.press_pos is None:
            return
        self.press_pos = None
        if self.mode == "held":
            self.mode = "fall"
            self.vy = 0.0
            self.anim_name, self.frame, self.frame_t = "fall", 0, 0.0
            self.redraw()
        else:
            self.menu.popup(e.globalPosition().toPoint())   # 左鍵點一下：互動選單

    # ---------- 每一格 ----------
    def tick(self):
        now = time.time()
        dt = min(0.5, now - self.last_tick)
        self.last_tick = now
        s = self.stats

        # 數值
        s.tick(dt * TIME_SCALE, awake=self.mode != "sleep")
        rate = ENERGY_RATE.get(self.anim_name, 0.0)
        s.energy = max(0.0, min(100.0, s.energy + rate * dt * TIME_SCALE ** 0.5))
        if now - self.stat_save_t > 60:
            self.stat_save_t = now
            s.settings["x"] = int(self.cx)
            s.save()

        g = self.screen_geo()
        floor = g.bottom() + 1
        self.check_sitting(now)
        self.check_chime()

        if self.mode == "held":
            self.advance_frame(dt)
            return
        if self.mode == "fall":
            self.vy += 2600 * dt
            self.bottom = min(floor, self.bottom + self.vy * dt)
            if self.bottom >= floor:
                self.bottom = floor
                self.react([("land", 1, pick("land"))])
            else:
                self.advance_frame(dt)
                self.redraw()
            return
        if self.mode == "climb":
            self.tick_climb(dt, g, floor)
            return
        if self.mode == "jump":
            self.tick_jump(dt, floor)
            return
        if self.mode == "carry":
            self.tick_carry(dt, floor)
            return
        if abs(self.bottom - floor) > 0.5:     # 工作列或螢幕大小變了
            self.bottom = floor
            self.redraw()

        # 走路
        if self.speed > 0:
            step = self.speed * dt
            if abs(self.target - self.cx) <= step:
                self.cx = self.target
                self.speed = 0
                cb, self.on_arrive = self.on_arrive, None
                (cb or self.anim_done)()
                return
            self.cx += step if self.target > self.cx else -step
            self.redraw()

        self.advance_frame(dt)
        self.idle_events(now)

    def advance_frame(self, dt):
        self.frame_t += dt * 1000
        changed = False
        while self.frame_t >= self.frame_ms():
            self.frame_t -= self.frame_ms()
            changed = True
            self.frame += 1
            if self.frame >= self.meta()["frames"]:
                self.frame = 0
                if self.loops_left > 0:
                    self.loops_left -= 1
                    if self.loops_left == 0:
                        self.anim_done()
                        return
                elif self.mode == "sleep" and not self.should_sleep():
                    self.react([("sleepy", 1, None)])   # 睡眠時段結束，自己醒來
                    return
            if self.anim_name == "peek" and self.frame == self.meta().get("hidden_frame"):
                self.peek_relocate()
        if changed:
            self.redraw()

    def idle_events(self, now):
        s = self.stats
        if not s.settings.get("chat", True) or self.mode != "normal" or now < self.next_chat:
            return
        self.next_chat = now + random.uniform(180, 420)
        m = minute_of_day()
        today = date.today().isoformat()
        for key, ok in (("morning", 7 * 60 <= m < 9 * 60), ("lunch", 11 * 60 + 50 <= m < 12 * 60 + 30),
                        ("late", is_pre_sleep(m) and m >= 22 * 60)):
            if ok and (key, today) not in self.said_today:
                self.said_today.add((key, today))
                self.say(pick(key)); return
        if s.neglect > 3 * HOUR and random.random() < 0.5:
            self.say(pick("neglect")); return
        if random.random() < 0.6:
            self.say(pick("chat"))

    def peek_relocate(self):
        """偷看：鑽下去之後，在滑鼠下方附近冒出來（看你在做什麼）。"""
        g = self.screen_geo()
        hw = self.half_w("peek")
        tx = QCursor.pos().x() + random.uniform(-1, 1) * self.scale * 24
        self.cx = max(g.left() + hw, min(g.right() + 1 - hw, tx))
        QTimer.singleShot(int(sum(self.meta("peek")["ms"][self.frame:14])), lambda: (
            self.anim_name == "peek" and self.say(pick("peek"))))
    # ---------- 爬螢幕邊緣 ----------
    def start_climb(self):
        """走到比較近的螢幕邊緣，再開始往上爬。"""
        g = self.screen_geo()
        hw = self.half_w("climb")
        left = self.cx - g.left() < g.right() - self.cx
        self.climb_left = left
        tx = g.left() + hw if left else g.right() + 1 - hw
        if abs(tx - self.cx) < 4:
            self.begin_climb(); return
        self.on_arrive = self.begin_climb
        self.play("walk", 0, 7 * self.scale, target=tx)

    def begin_climb(self):
        g = self.screen_geo()
        self.mode, self.climb_phase = "climb", "up"
        self.facing_left = self.climb_left          # 圖是朝右（牆在右邊），左邊的牆就翻轉
        self.climb_top = g.bottom() + 1 - random.uniform(0.3, 0.7) * g.height()
        self.anim_name, self.frame, self.frame_t, self.loops_left, self.speed = "climb", 0, 0.0, 0, 0
        self.redraw()

    def tick_climb(self, dt, g, floor):
        v = 6 * self.scale * dt
        if self.climb_phase == "up":
            self.bottom = max(self.climb_top, self.bottom - v)
            if self.bottom <= self.climb_top:
                self.climb_phase = "hang"
                self.anim_name, self.frame, self.frame_t, self.loops_left = "hang", 0, 0.0, random.randint(3, 6)
                self.say(pick("climb_top"))
        elif self.climb_phase == "down":
            self.bottom = min(floor, self.bottom + v * 1.5)
            if self.bottom >= floor:
                self.bottom = floor
                self.mode = "normal"
                self.say(pick("climb_down"))
                self.pick_next()
                return
        self.advance_frame(dt)
        self.redraw()

    def climb_next(self):
        """掛完了：一半機率直接放手跳下去，一半慢慢爬下來。"""
        if random.random() < 0.5:
            self.mode, self.vy = "fall", 0.0
            self.facing_left = False
            self.anim_name, self.frame, self.frame_t = "fall", 0, 0.0
            self.say(pick("climb_jump"))
        else:
            self.climb_phase = "down"
            self.anim_name, self.frame, self.frame_t, self.loops_left = "climb", 0, 0.0, 0
        self.redraw()

    # ---------- 追游標 ----------
    def start_chase(self):
        c = QCursor.pos()
        g = self.screen_geo()
        if not g.contains(c):
            self.pick_next(); return
        hw = self.half_w("run")
        tx = max(g.left() + hw, min(g.right() + 1 - hw, c.x()))
        self.chase_tries += 1
        if abs(tx - self.cx) < 6 * self.scale:
            self.chase_jump(); return
        self.on_arrive = self.chase_jump
        self.play("run", 0, 30 * self.scale, target=tx)

    def chase_jump(self):
        c = QCursor.pos()
        floor = self.screen_geo().bottom() + 1
        if abs(c.x() - self.cx) > 14 * self.scale and self.chase_tries < 3:   # 游標跑了，再追
            self.start_chase(); return
        reach = 22 * self.scale                           # 雙手張開往上撲時，抓得到的高度（離腳底）
        need = (floor - c.y()) - reach
        if need > 26 * self.scale:                        # 跳不到
            self.mode = "normal"
            self.play("idle", 2)
            self.say(pick("chase_high")); return
        self.mode = "jump"
        self.facing_left = False
        self.vy = -(2 * 2600 * max(need + 3 * self.scale, 6 * self.scale)) ** 0.5
        self.anim_name, self.frame, self.frame_t, self.loops_left, self.speed = "reach", 0, 0.0, 0, 0
        self.caught = False
        self.redraw()

    def tick_jump(self, dt, floor):
        self.vy += 2600 * dt
        self.bottom = min(floor, self.bottom + self.vy * dt)
        c = QCursor.pos()
        sc = self.scale
        if (not self.caught and abs(c.x() - self.cx) < 15 * sc
                and self.bottom - 30 * sc <= c.y() <= self.bottom - 14 * sc):
            self.caught = True
            self.say(pick("chase_got"))
            self.start_carry()
            return
        if self.bottom >= floor:
            self.bottom = floor
            self.mode = "react"
            self.queue = []
            self.play("idle", 2)
            self.say(pick("chase_miss"))
            return
        self.advance_frame(dt)
        self.redraw()

    # ---------- 抓到游標：吊在游標上，游標帶著她走 ----------
    def start_carry(self):
        c = QCursor.pos()
        self.mode = "carry"
        self.facing_left = c.x() < self.cx
        self.anim_name, self.frame, self.frame_t, self.loops_left, self.speed = "carry", 0, 0.0, 0, 0
        self.on_arrive = None
        self.carry_t, self.carry_until = 0.0, random.uniform(4, 9)
        self.cur_last, self.cur_speed = c, 0.0
        self.follow_cursor(c)
        self.redraw()

    def follow_cursor(self, c):
        """把她放到「手剛好抓著游標尖端」的位置。"""
        m, sc = self.meta("carry"), self.scale
        hx, hy = m.get("hand", (28, 17))
        dx = (hx + 0.5 - m["w"] / 2) * sc
        self.cx = c.x() + (dx if self.facing_left else -dx)
        top = c.y() - (hy + m.get("pad_top", 0) + 0.5) * sc
        self.bottom = top + m["h"] * sc

    def tick_carry(self, dt, floor):
        c = QCursor.pos()
        d = ((c.x() - self.cur_last.x()) ** 2 + (c.y() - self.cur_last.y()) ** 2) ** 0.5
        self.cur_last = c
        self.cur_speed = self.cur_speed * 0.6 + (d / max(dt, 1e-3)) * 0.4
        self.carry_t += dt
        self.follow_cursor(c)
        if self.bottom >= floor:                          # 游標帶她碰到地面：自己放手站好
            self.bottom = floor
            self.mode = "react"; self.queue = []
            self.facing_left = False
            self.play("idle", 2)
            self.say(pick("chase_return"))
            self.redraw(); return
        if self.cur_speed > 2500 * self.scale / 4:          # 甩太用力：被甩掉
            self.let_go(pick("chase_escape")); return
        if self.carry_t >= self.carry_until:              # 玩夠了，自己放手
            self.let_go(pick("chase_return")); return
        self.advance_frame(dt)
        self.redraw()

    def let_go(self, line):
        self.mode, self.vy = "fall", 0.0
        self.facing_left = False
        self.anim_name, self.frame, self.frame_t = "fall", 0, 0.0
        self.say(line)
        self.redraw()

    # ---------- 久坐提醒、整點報時 ----------
    def check_sitting(self, now):
        cur = QCursor.pos()
        if cur != self.last_cursor:
            self.last_cursor = cur
            if now - self.last_move > 5 * 60 / TIME_SCALE:     # 離開超過 5 分鐘：算有休息
                self.sit_start = now
                if self.sit_reminded and self.mode == "normal":
                    self.say(pick("sit_back"))
                self.sit_reminded = False
            self.last_move = now
        limit = int(self.stats.settings.get("sit_min", 50))
        if limit <= 0 or now < self.next_sit or now - self.last_move > 60:
            return
        if now - self.sit_start >= limit * 60 / TIME_SCALE and self.mode == "normal":
            self.next_sit = now + 10 * 60 / TIME_SCALE                # 沒休息的話，10 分鐘後再提醒
            self.sit_reminded = True
            mins = int((now - self.sit_start) * TIME_SCALE // 60)
            self.react([("stretch", 2, pick("sit").format(m=mins))])

    def check_chime(self):
        h = minute_of_day() // 60
        if minute_of_day() % 60 != 0 or h == self.last_chime:
            return
        self.last_chime = h
        if not self.stats.settings.get("chime", True) or self.mode == "sleep":
            return
        self.say(chime_line(h))

    # ---------- 選單、托盤 ----------
    def build_menu(self, menu):
        sleeping = self.mode == "sleep"
        menu.addAction("摸頭" + ("（會吵醒她）" if sleeping else ""), self.do_pat)
        gm = menu.addMenu(f"送禮（剩 {self.stats.gift_stock} 個）")
        if self.stats.gift_stock == 0:
            info = gm.addAction(f"禮物送完了，{fmt_hours(self.stats.gift_eta() / TIME_SCALE)} 後補一個")
            info.setEnabled(False)
        for gid, gift in GIFTS.items():
            known = self.stats.gift_log.get(gid, 0) > 0
            label = f"{gift['name']}　{PREF_TEXT[gift['pref']] if known else '？'}"
            a = gm.addAction(QIcon(QPixmap.fromImage(gift_icon(gid).scaled(24, 24))), label)
            a.triggered.connect(lambda _=False, gid=gid: self.do_gift(gid))
            a.setEnabled(self.stats.gift_stock > 0)
        menu.addAction("看她的狀態", self.show_panel)
        menu.addSeparator()
        st = menu.addMenu("設定")
        size = st.addMenu("大小")
        grp = QActionGroup(size)
        for k in (2, 3, 4, 5, 6, 8):
            a = QAction(f"{k} 倍（{32 * k} 像素高）", size, checkable=True, checked=self.scale == k)
            a.triggered.connect(lambda _=False, k=k: self.set_scale(k))
            grp.addAction(a); size.addAction(a)
        bub = st.addMenu("對話框樣式")
        bgrp = QActionGroup(bub)
        for key, (label, *_) in BUBBLE_STYLES.items():
            a = QAction(label, bub, checkable=True, checked=self.stats.settings.get("bubble") == key)
            a.triggered.connect(lambda _=False, key=key: (self.stats.settings.__setitem__("bubble", key),
                                                          self.say(pick("chat"))))
            bgrp.addAction(a); bub.addAction(a)
        sit = st.addMenu("久坐提醒")
        sgrp = QActionGroup(sit)
        for m in (0, 30, 45, 50, 60, 90):
            a = QAction("關閉" if m == 0 else f"連續用電腦 {m} 分鐘", sit, checkable=True,
                        checked=int(self.stats.settings.get("sit_min", 50)) == m)
            a.triggered.connect(lambda _=False, m=m: self.stats.settings.__setitem__("sit_min", m))
            sgrp.addAction(a); sit.addAction(a)
        for label, key, fn in (("永遠在最上層", "on_top", self.apply_on_top),
                               ("照時間作息（午睡、晚上睡覺）", "schedule", self.set_schedule),
                               ("偶爾自言自語", "chat", None),
                               ("整點報時", "chime", None),
                               ("會爬螢幕邊緣", "climb", None),
                               ("會追滑鼠游標", "chase", None)):
            a = QAction(label, st, checkable=True, checked=bool(self.stats.settings.get(key, True)))
            a.triggered.connect(lambda on, key=key, fn=fn: (self.stats.settings.__setitem__(key, on), fn and fn(on)))
            st.addAction(a)
        a = QAction("開機自動啟動", st, checkable=True, checked=autostart_enabled())
        a.triggered.connect(set_autostart)
        st.addAction(a)
        menu.addSeparator()
        menu.addAction("離開", self.quit)

    def setup_tray(self):
        self.app.setStyleSheet(MENU_CSS % pixel_font().family())
        self.menu = QMenu()
        self.menu.aboutToShow.connect(lambda: (self.menu.clear(), self.build_menu(self.menu)))
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            pix, _ = self.sprites.frame("idle", 0, 2, False)
            self.app.setWindowIcon(QIcon(pix))
            self.tray = QSystemTrayIcon(QIcon(pix), self)
            self.tray_menu = QMenu()
            self.tray_menu.aboutToShow.connect(lambda: (self.tray_menu.clear(), self.build_menu(self.tray_menu)))
            self.tray.setContextMenu(self.tray_menu)
            self.tray.setToolTip("Chisa 桌面寵物")
            self.tray.activated.connect(lambda r: self.show_panel() if r == QSystemTrayIcon.Trigger else None)
            self.tray.show()

    def set_scale(self, k):
        self.scale_was = self.scale
        self.stats.settings["scale"] = k
        self.sprites.cache.clear()
        if self.speed:
            self.speed = self.speed / self.scale_was * k
        self.scale_was = k
        self.redraw()

    def set_schedule(self, on):
        if not on and self.mode == "sleep":
            self.react([("sleepy", 1, pick("sleepy"))])
        elif on and self.should_sleep() and self.mode == "normal":
            self.enter_sleep()

    def apply_on_top(self, on, init=False):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(on))
        if not init:
            self.show()

    def quit(self):
        self.stats.settings["x"] = int(self.cx)
        self.stats.save()
        self.app.quit()


# ===== 開機自動啟動（Linux：autostart .desktop；Windows：登錄檔 Run；macOS：LaunchAgent）=====
APP_ID = "chisa-desktop-pet"


def launch_cmd():
    return [sys.executable] if FROZEN else [sys.executable, os.path.abspath(__file__)]


def _autostart_path():
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents", f"com.{APP_ID}.plist")
    return os.path.join(os.path.expanduser("~"), ".config", "autostart", f"{APP_ID}.desktop")


def autostart_enabled():
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
                winreg.QueryValueEx(k, APP_ID)
            return True
        except OSError:
            return False
    return os.path.exists(_autostart_path())


def set_autostart(on):
    cmd = launch_cmd()
    if sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE) as k:
            if on:
                winreg.SetValueEx(k, APP_ID, 0, winreg.REG_SZ, " ".join(f'"{c}"' for c in cmd))
            else:
                try:
                    winreg.DeleteValue(k, APP_ID)
                except OSError:
                    pass
        return
    path = _autostart_path()
    if not on:
        if os.path.exists(path):
            os.remove(path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if sys.platform == "darwin":
            args = "".join(f"<string>{c}</string>" for c in cmd)
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                    f'<plist version="1.0"><dict><key>Label</key><string>com.{APP_ID}</string>'
                    f'<key>ProgramArguments</key><array>{args}</array>'
                    '<key>RunAtLoad</key><true/></dict></plist>\n')
        else:
            exe = " ".join(f'"{c}"' for c in cmd)
            f.write("[Desktop Entry]\nType=Application\nName=Chisa 桌面寵物\n"
                    f"Exec=env QT_QPA_PLATFORM=xcb {exe}\n"
                    "X-GNOME-Autostart-enabled=true\n")


# ===== 同時只跑一隻：新開的會把舊的關掉（避免開機自動啟動＋手動再開，出現兩隻、兩個對話框）=====
SERVER_NAME = "chisa-desktop-pet-" + (os.environ.get("USER") or os.environ.get("USERNAME") or "me")


def take_over_instance():
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if sock.waitForConnected(300):              # 已經有一隻在跑：請她離開，等她關掉
        sock.write(b"quit\n"); sock.flush()
        sock.waitForBytesWritten(300)
        sock.waitForDisconnected(3000)
    sock.abort()
    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer()
    server.listen(SERVER_NAME)
    return server


def _on_other_instance(server, app):
    c = server.nextPendingConnection()
    if c is None:
        return
    def read():
        if b"quit" in bytes(c.readAll()):
            app.quit()
    c.readyRead.connect(read)
    if c.bytesAvailable():
        read()


def main():
    if sys.platform.startswith("linux") and os.environ.get("WAYLAND_DISPLAY") and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"   # Wayland 不准程式自己移動視窗，改走 XWayland
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("desktop-pet")
    server = take_over_instance()
    pet = Pet(app)
    pet.show()
    server.newConnection.connect(lambda: _on_other_instance(server, app))
    app.aboutToQuit.connect(pet.stats.save)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
