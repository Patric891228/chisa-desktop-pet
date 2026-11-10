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
from PySide6.QtGui import (QPixmap, QPainter, QTransform, QColor, QFont, QFontMetrics, QCursor,
                           QIcon, QAction, QActionGroup)
from PySide6.QtWidgets import (QApplication, QWidget, QMenu, QSystemTrayIcon, QLabel, QProgressBar,
                               QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout)

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
}

STATUS_TEXT = {"idle": "發呆", "walk": "散步", "run": "跑步", "read": "看書", "snore": "打瞌睡",
               "swing": "練剪刀", "walk_weapon": "扛著剪刀散步", "run_weapon": "扛著剪刀跑步",
               "desk_sleep_r": "趴在桌上午睡", "bed_sleep_r": "睡覺", "headpat": "被摸頭（當機中）",
               "shy_pole": "躲在電線桿後面", "guard": "防備", "shy": "害羞", "gift": "收禮物",
               "sleepy": "睡眼惺忪", "held": "被拎起來", "fall": "往下掉", "land": "落地",
               "peek": "偷看你的螢幕"}
REACTIONS = ("shy_pole", "guard", "shy")
FRONT_ONLY = {"peek", "read", "desk_sleep_r", "bed_sleep_r", "held", "fall", "land"}   # 不水平翻轉的動作      # 摸頭之後隨機接一個


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
        self.settings = {"scale": 4, "on_top": True, "schedule": True, "x": None, "chat": True, "bubble": "paper"}

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


def render_bubble(text, style="paper", max_w=150):
    """在 1 倍畫布上畫像素對話框，回傳 QImage（之後整數倍放大，維持像素感）。"""
    import math
    from PySide6.QtGui import QImage
    _, line, fill, ink, shadow, deco = BUBBLE_STYLES.get(style, BUBBLE_STYLES["paper"])
    font = pixel_font()
    fm = QFontMetrics(font)
    full = fm.horizontalAdvance(text)
    if full > max_w:                                # 換行時讓每行差不多長，不留一個字在第二行
        n = math.ceil(full / max_w)
        max_w = math.ceil(full / n) + fm.horizontalAdvance("。")
    tr = fm.boundingRect(QRect(0, 0, max_w, 400), Qt.TextWordWrap, text)
    tw, th = max(tr.width(), 12), tr.height()
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

    p.setFont(font)
    p.setPen(ink)
    top = pady + (2 if deco == "collar" else 0)
    p.drawText(QRect(mx + padx, my + top - (1 if deco != "collar" else 0), tw, th),
               Qt.TextWordWrap | Qt.AlignHCenter | Qt.AlignVCenter, text)
    p.end()
    return img


class Bubble(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
                         | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)   # macOS：切到別的程式時不要消失
        self.pix = QPixmap()
        self.hide_timer = QTimer(self, singleShot=True, timeout=self.hide)

    def say(self, text, anchor_x, anchor_y, style="paper", zoom=2):
        img = render_bubble(text, style)
        self.pix = QPixmap.fromImage(img.scaled(img.width() * zoom, img.height() * zoom,
                                                Qt.IgnoreAspectRatio, Qt.FastTransformation))
        self.resize(self.pix.size())
        self.place(anchor_x, anchor_y)
        self.show()
        self.raise_()
        self.update()
        self.hide_timer.start(int(2200 + 120 * len(text)))

    def place(self, anchor_x, anchor_y):
        scr = QApplication.screenAt(QPoint(anchor_x, anchor_y)) or QApplication.primaryScreen()
        g = scr.availableGeometry()
        x = max(g.left(), min(g.right() - self.width(), anchor_x - self.width() // 2))
        y = max(g.top(), anchor_y - self.height())
        self.move(x, y)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.transparent)
        p.drawPixmap(0, 0, self.pix)


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
        self.setWindowTitle("她的狀態")
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
        self.gifts = QLabel(); self.neglect = QLabel(); self.pats = QLabel(); self.days = QLabel()
        rows = [("好感度", self.aff), ("精力", self.eng), ("禮物", self.gifts),
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
        self.bubble = Bubble()
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

    def head_point(self):
        m = self.meta()
        return int(self.cx), int(self.bottom - m["h"] * self.scale - 2)

    def say(self, text):
        if text:
            x, y = self.head_point()
            self.bubble.say(text, x, y, self.stats.settings.get("bubble", "paper"), max(1, self.scale // 2))

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
        x = int(round(self.cx - pix.width() / 2))
        y = int(round(self.bottom - pix.height()))
        if self.geometry() != QRect(x, y, pix.width(), pix.height()):
            self.setGeometry(x, y, pix.width(), pix.height())
        self.setMask(mask)
        self.update()
        if self.bubble.isVisible():
            self.bubble.place(*self.head_point())

    def paintEvent(self, _):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.drawPixmap(0, 0, self.pix)

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
        if self.last_action in pool and len(pool) > 1:
            pool.pop(self.last_action)
        a = random.choices(list(pool), weights=list(pool.values()))[0]
        self.last_action = a
        if s.energy < 25 and a in ("snore", "desk_sleep_r") and random.random() < 0.5:
            self.say(pick("tired"))

        g = self.screen_geo()
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
        self.react_clicks = 0
        self.queue = list(steps)
        self.next_in_queue()

    def next_in_queue(self):
        name, loops, line = self.queue.pop(0)
        self.facing_left = False
        self.play(name, loops)
        self.say(line)

    def anim_done(self):
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
    def do_pat(self):
        s = self.stats
        self.input_happened()
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

    def do_gift(self):
        s = self.stats
        self.input_happened()
        pre = self.wake_prefix()
        if s.gift_stock == 0:
            msg = pick("no_gift").format(h=fmt_hours(s.gift_eta() / TIME_SCALE))
            if pre:
                self.react(pre + [("idle", 1, msg)])
            else:
                self.say(msg)
            return
        s.gift_stock -= 1
        s.add_affection(GIFT_GAIN)
        self.react(pre + [("gift", 2, pick("gift"))])
        self.stats.save()

    def show_panel(self):
        self.panel.show(); self.panel.raise_(); self.panel.activateWindow()

    # ---------- 滑鼠 ----------
    def mousePressEvent(self, e):
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
        if abs(self.bottom - floor) > 0.5:     # 工作列或螢幕大小變了
            self.bottom = floor
            self.redraw()

        # 走路
        if self.speed > 0:
            step = self.speed * dt
            if abs(self.target - self.cx) <= step:
                self.cx = self.target
                self.speed = 0
                self.anim_done()
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
    # ---------- 選單、托盤 ----------
    def build_menu(self, menu):
        sleeping = self.mode == "sleep"
        menu.addAction("摸頭" + ("（會吵醒她）" if sleeping else ""), self.do_pat)
        menu.addAction(f"送禮（剩 {self.stats.gift_stock} 個）", self.do_gift)
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
        for label, key, fn in (("永遠在最上層", "on_top", self.apply_on_top),
                               ("照時間作息（午睡、晚上睡覺）", "schedule", self.set_schedule),
                               ("偶爾自言自語", "chat", None)):
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


def main():
    if sys.platform.startswith("linux") and os.environ.get("WAYLAND_DISPLAY") and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"   # Wayland 不准程式自己移動視窗，改走 XWayland
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("desktop-pet")
    pet = Pet(app)
    pet.show()
    app.aboutToQuit.connect(pet.stats.save)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
