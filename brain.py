"""本地小模型（選配）：讓角色偶爾說新台詞、聽懂「三點半提醒我開會」、記得你最近說過的事。

做法：在本機背景跑 llama.cpp 的 llama-server（一個執行檔），載入一個小模型（GGUF 檔），
用 HTTP 跟它要台詞。完全離線；只有第一次啟用、你按下同意時，才會從 GitHub／Hugging Face 下載
llama-server 和模型檔，放在設定資料夾的 llm/ 底下。

這個檔案不依賴 Qt：工作都在背景執行緒做，結果放進佇列，由桌寵每一格呼叫 poll() 在主執行緒處理。
角色的個性寫在角色包 character.json 的 persona（見 docs/CHARACTER_GUIDE.md）；沒有 persona 的角色不會用到這裡。
"""
import json, os, platform, queue, random, re, shutil, socket, subprocess, sys, threading, time, urllib.request, zipfile
from datetime import datetime, date, timedelta

LLAMA_TAG = "b12250"              # llama.cpp 的版本（GitHub Release 標籤）；找不到時改用最新版
LLAMA_REPO = "ggml-org/llama.cpp"
MODELS = {
    "standard": {"label": "Qwen3 1.7B（約 1.1 GB）", "file": "Qwen3-1.7B-Q4_K_M.gguf", "mb": 1100,
                 "url": "https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf"},
}                                 # 固定用這個；開發時可以用 PET_LLM_MODEL 指定別的 GGUF
IDLE_UNLOAD_S = 10 * 60           # 10 分鐘沒用就把模型關掉，平常不佔記憶體
MEMORY_DAYS, MEMORY_MAX = 7, 20   # 短期記憶：最多 7 天、20 條
DAY_CUTOFF_H = 5                  # 凌晨 5 點前還算前一天（熬夜也算同一天）

# 「反應換新」會用到的台詞 key 和情境說明（角色包的 persona.situations 可以覆寫或增加）
SITUATIONS = {
    "pat": "使用者摸了她的頭",
    "drag": "她被滑鼠拎起來懸在半空",
    "land": "她被放開、掉到地上",
    "peek": "她偷偷探頭看使用者的螢幕",
    "chat": "她閒著沒事，隨口自言自語",
    "sleepy": "她在睡覺時被吵醒",
    "climb_top": "她爬到螢幕邊緣的高處往下看",
    "back": "她躲起來一陣子之後回來了",
    "sit_back": "使用者離開座位休息後回來了",
    "tired": "她覺得累了想休息",
}

USER_AGENT = "desktop-pet"


def _s2t():
    """簡體轉台灣繁體（小模型常冒出簡體字）；沒裝 opencc 就原樣輸出。"""
    try:
        from opencc import OpenCC
        cc = OpenCC("s2twp")
        return cc.convert
    except Exception:
        return lambda s: s


TO_TRAD = _s2t()


# ===== 時間解析：「三點半提醒我開會」「20 分鐘後叫我」「明天早上九點交報告」 =====
CN_NUM = {"零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "两": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
NUM = r"[0-9０-９零〇一二兩两三四五六七八九十]+"


def cn_int(s):
    s = s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if s.isdigit():
        return int(s)
    if "十" in s:
        a, _, b = s.partition("十")
        return (CN_NUM.get(a, 1) if a else 1) * 10 + (CN_NUM.get(b, 0) if b else 0)
    n = 0
    for ch in s:
        if ch not in CN_NUM:
            return None
        n = n * 10 + CN_NUM[ch]
    return n


REL_RE = re.compile(rf"(?:(?P<n>{NUM})\s*(?:個)?\s*(?P<half>半)?\s*(?P<unit>分鐘|分|小時|鐘頭)|(?P<halfhr>半)\s*(?:個)?\s*(?:小時|鐘頭))\s*(?:之)?後")
ABS_RE = re.compile(
    rf"(?P<day>今天|今晚|明天|明早|明晚|後天)?\s*(?P<per>早上|上午|中午|下午|傍晚|晚上|凌晨|半夜)?\s*"
    rf"(?:(?P<hh>[0-9０-９]{{1,2}})\s*[:：]\s*(?P<mm>[0-9０-９]{{2}})"
    rf"|(?P<h>{NUM})\s*(?:點|點鐘|時)\s*(?:(?P<half>半)|(?P<q>一刻|三刻)|(?P<m>{NUM})\s*分?)?)")
NOT_FUTURE = ("昨天", "前天", "剛剛", "剛才", "昨晚", "上次")
FILLER = re.compile(r"(請|麻煩|幫我|記得|要|的時候|時候|提醒我|提醒|叫我|通知我|跟我說|告訴我|一下|喔|哦|啊|吧|唷|呢|[，,。.!！~～\s])")


def parse_reminder(text, now=None):
    """找到未來的時間就回傳 (datetime, 要做的事)，否則 None。只用規則，不靠模型（時間不能猜錯）。"""
    now = now or datetime.now()
    if any(w in text for w in NOT_FUTURE):
        return None
    m = REL_RE.search(text)
    if m:
        if m.group("halfhr"):
            mins = 30
        else:
            n = cn_int(m.group("n"))
            if n is None:
                return None
            mins = n * 60 if m.group("unit") in ("小時", "鐘頭") else n
            if m.group("half"):
                mins += 30
        if not 1 <= mins <= 48 * 60:
            return None
        when = now + timedelta(minutes=mins)
        return when.replace(second=0, microsecond=0), _task(text, m)
    m = ABS_RE.search(text)
    if not m:
        return None
    if m.group("hh"):
        h, mi = cn_int(m.group("hh")), cn_int(m.group("mm"))
    else:
        h = cn_int(m.group("h"))
        mi = 30 if m.group("half") else 15 if m.group("q") == "一刻" else 45 if m.group("q") == "三刻" else \
            (cn_int(m.group("m")) if m.group("m") else 0)
    if h is None or mi is None or not (0 <= h <= 24 and 0 <= mi < 60):
        return None
    per, day = m.group("per"), m.group("day")
    if day in ("今晚", "明晚") and not per:
        per = "晚上"
    if day == "明早" and not per:
        per = "早上"
    if per in ("下午", "傍晚", "晚上") and h < 12:
        h += 12
    elif per == "中午" and h < 5:
        h += 12
    elif per in ("凌晨", "半夜") and h == 12:
        h = 0
    h %= 24
    base = now.date() + timedelta(days={"明天": 1, "明早": 1, "明晚": 1, "後天": 2}.get(day, 0))
    when = datetime(base.year, base.month, base.day, h, mi)
    if not per and 1 <= h <= 5:
        when += timedelta(hours=12)              # 沒說早上下午的「三點」：當成下午（很少人半夜三點要提醒）
        h += 12
    if not day and not per:
        if when <= now and h < 12 and when + timedelta(hours=12) > now:
            when += timedelta(hours=12)          # 現在下午兩點說「三點」：是下午三點
        elif when <= now:
            when += timedelta(days=1)            # 今天已經過了：明天
    if when <= now:
        return None
    return when, _task(text, m)


def _task(text, m):
    rest = (text[:m.start()] + " " + text[m.end():])
    rest = re.sub(r"(今天|今晚|明天|後天|早上|上午|中午|下午|傍晚|晚上|凌晨)", "", rest)
    rest = FILLER.sub("", rest)
    return rest[:20] or "時間到了"


def day_key(t=None):
    return (datetime.fromtimestamp(t or time.time()) - timedelta(hours=DAY_CUTOFF_H)).date().isoformat()


# ===== 下載 =====
def _platform_asset_names(tag):
    """llama.cpp Release 裡適合這台電腦的 CPU 版壓縮檔名（見 llama.cpp 的 release.yml／release-publish.yml）：
    Windows：llama-bXXXX-bin-win-cpu-x64.zip；macOS／Linux：llama-bXXXX-bin-macos-arm64.tar.gz、llama-bXXXX-bin-ubuntu-x64.tar.gz。"""
    mach = platform.machine().lower()
    arch = "arm64" if mach in ("arm64", "aarch64") else "x64"
    plat = "win-cpu" if sys.platform == "win32" else "macos" if sys.platform == "darwin" else "ubuntu"
    exts = (".zip",) if sys.platform == "win32" else (".tar.gz", ".zip")
    return [f"llama-{tag}-bin-{plat}-{arch}{e}" for e in exts]


def _fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def server_candidates():
    """可能的下載網址（依序嘗試）：先用固定版本直接組網址（不經 GitHub API，不怕次數限制），
    再問 API 最新版有哪些檔案。"""
    out = [(f"https://github.com/{LLAMA_REPO}/releases/download/{LLAMA_TAG}/{n}", n)
           for n in _platform_asset_names(LLAMA_TAG)]
    try:
        rel = _fetch_json(f"https://api.github.com/repos/{LLAMA_REPO}/releases/latest")
        names = _platform_asset_names(rel.get("tag_name", ""))
        for a in rel.get("assets", []):
            if a.get("name") in names:
                out.append((a["browser_download_url"], a["name"]))
    except Exception:
        pass
    return out


def download(url, dest, progress, cancel):
    """下載到 dest（先寫 .part，可以續傳）。progress(已下載, 總共)；cancel() 回傳 True 就中止。"""
    part = dest + ".part"
    have = os.path.getsize(part) if os.path.exists(part) else 0
    headers = {"User-Agent": USER_AGENT}
    if have:
        headers["Range"] = f"bytes={have}-"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        if have and r.status != 206:            # 伺服器不支援續傳：重新下載
            have = 0
        total = have + int(r.headers.get("Content-Length") or 0)
        with open(part, "ab" if have else "wb") as f:
            done = have
            while True:
                if cancel():
                    raise InterruptedError("取消下載")
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                progress(done, total)
    os.replace(part, dest)


def extract_server(path, bin_dir):
    """解壓縮整包（llama-server 需要同資料夾的 dll／so／dylib）。"""
    shutil.rmtree(bin_dir, ignore_errors=True)
    os.makedirs(bin_dir, exist_ok=True)
    if path.endswith(".tar.gz"):
        import tarfile
        with tarfile.open(path) as t:
            try:
                t.extractall(bin_dir, filter="data")     # 不寫到資料夾外面、保留符號連結和執行權限
            except TypeError:                           # Python 3.11 以前沒有 filter
                root = os.path.realpath(bin_dir) + os.sep
                t.extractall(bin_dir, [m for m in t.getmembers()
                                       if os.path.realpath(os.path.join(bin_dir, m.name)).startswith(root)])
        os.remove(path)
        return
    zip_path = path
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            out = os.path.realpath(os.path.join(bin_dir, info.filename))
            if not out.startswith(os.path.realpath(bin_dir) + os.sep):
                continue                          # 不寫到資料夾外面
            if info.is_dir():
                os.makedirs(out, exist_ok=True); continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            mode = (info.external_attr >> 16) & 0o777
            with z.open(info) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
            if sys.platform != "win32":
                os.chmod(out, 0o755 if (mode & 0o111 or "llama" in os.path.basename(out) or ".so" in out
                                        or out.endswith(".dylib")) else 0o644)
        _fix_symlinks(z, bin_dir)
    os.remove(zip_path)


def _fix_symlinks(z, bin_dir):
    """zip 裡的符號連結（libfoo.so → libfoo.so.0）解出來會是內容為目標檔名的小檔案，換成真的連結或複本。"""
    for info in z.infolist():
        if ((info.external_attr >> 16) & 0o170000) != 0o120000:
            continue
        p = os.path.join(bin_dir, info.filename)
        target = z.read(info).decode("utf-8", "replace")
        tp = os.path.join(os.path.dirname(p), target)
        try:
            os.remove(p)
            if os.path.exists(tp):
                try:
                    os.symlink(target, p)
                except OSError:
                    shutil.copy2(tp, p)
        except OSError:
            pass


# ===== 本體 =====
class Brain:
    def __init__(self, conf_dir, char, settings, char_id):
        self.char, self.settings = char, settings
        self.persona = char.get("persona") or {}
        self.name = char.get("name", "她")
        self.dir = os.path.join(conf_dir, "llm")
        self.bin_dir = os.path.join(self.dir, "bin")
        self.model_dir = os.path.join(self.dir, "models")
        self.mem_path = os.path.join(conf_dir, f"memory_{char_id}.json")
        self.proc, self.port, self.last_use = None, None, 0.0
        self.jobs, self.results = queue.Queue(), queue.Queue()
        self.busy = False                  # 背景正在處理（避免同時排太多）
        self.download_state = None         # 下載中：{"what":..., "done":..., "total":..., "error":...}
        self.cancel_download = False
        self.lock = threading.Lock()
        self.mem = {"notes": [], "days": {}, "fresh": {}, "done": {}}
        self.load()
        self.max_chars = int(self.persona.get("max_chars", 30))
        self.situations = dict(SITUATIONS)
        self.situations.update(self.persona.get("situations", {}))
        threading.Thread(target=self._worker, daemon=True).start()

    # ---------- 設定 ----------
    @property
    def enabled(self):
        return bool(self.persona) and bool(self.settings.get("llm_on", False))

    def model_info(self):
        return MODELS["standard"]

    def model_path(self):
        p = os.environ.get("PET_LLM_MODEL") or self.settings.get("llm_model_path")
        if p and os.path.exists(p):
            return p
        return os.path.join(self.model_dir, self.model_info()["file"])

    def server_path(self):
        p = os.environ.get("PET_LLAMA_SERVER") or self.settings.get("llm_server_path")
        if p and os.path.exists(p):
            return p
        exe = "llama-server.exe" if sys.platform == "win32" else "llama-server"
        for root, _, files in os.walk(self.bin_dir):
            if exe in files:
                return os.path.join(root, exe)
        return shutil.which("llama-server")

    def has_model(self):
        return os.path.exists(self.model_path())

    def installed(self):
        return bool(self.server_path()) and self.has_model()

    def ready(self):
        return self.enabled and self.installed()

    def missing_mb(self):
        """還要下載多少 MB（給確認視窗顯示）。"""
        mb = 0 if self.has_model() else self.model_info()["mb"]
        return mb + (0 if self.server_path() else 30)

    def disk_mb(self):
        total = 0
        for root, _, files in os.walk(self.dir):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        return total // (1 << 20)

    # ---------- 存檔（記憶、預先產生的台詞） ----------
    def load(self):
        try:
            d = json.load(open(self.mem_path, encoding="utf-8"))
            for k in self.mem:
                if isinstance(d.get(k), type(self.mem[k])):
                    self.mem[k] = d[k]
        except (OSError, ValueError):
            pass
        self.prune()

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(self.mem_path), exist_ok=True)
            tmp = self.mem_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.mem, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.mem_path)

    def prune(self):
        cut = (date.today() - timedelta(days=MEMORY_DAYS)).isoformat()
        self.mem["notes"] = [n for n in self.mem["notes"] if n.get("day", "") >= cut][-MEMORY_MAX:]
        self.mem["days"] = {d: v for d, v in self.mem["days"].items() if d >= cut}
        self.mem["done"] = {k: v for k, v in self.mem["done"].items() if v >= cut}

    def forget(self, idx=None):
        if idx is None:
            self.mem["notes"].clear()
            self.mem["days"].clear()
        elif 0 <= idx < len(self.mem["notes"]):
            self.mem["notes"].pop(idx)
        self.save()

    # ---------- 每天的事件紀錄（給「記得昨天的事」用；只記次數和時間，不記內容） ----------
    def log(self, what, value=None):
        if not self.enabled or not self.settings.get("llm_memory", True):
            return
        d = self.mem["days"].setdefault(day_key(), {})
        if what == "active":
            hm = datetime.now().strftime("%H:%M")
            d.setdefault("first", hm)
            d["last"] = hm
        elif what == "gift":
            d.setdefault("gifts", []).append(value)
        else:
            d[what] = d.get(what, 0) + 1

    def day_facts(self, key):
        d = self.mem["days"].get(key)
        if not d:
            return []
        out = []
        if d.get("first"):
            out.append(f"開始用電腦的時間是 {d['first']}")
        if d.get("last"):
            h = int(d["last"][:2])
            out.append(f"最後一次用電腦是 {d['last']}" + ("（熬夜到很晚）" if h < DAY_CUTOFF_H else
                                                    "（很晚）" if h >= 23 else ""))
        if d.get("pats"):
            out.append(f"摸了她的頭 {d['pats']} 次")
        if d.get("gifts"):
            out.append("送了她：" + "、".join(dict.fromkeys(d["gifts"])))
        if d.get("sit"):
            out.append(f"因為坐太久被她提醒了 {d['sit']} 次")
        return out

    # ---------- 台詞換新 ----------
    def tier(self, affection):
        return "high" if affection >= 70 else "low" if affection < 30 else "mid"

    def take_fresh(self, key, affection):
        """從預先產生好的新台詞裡拿一句（沒有就回傳 None，用原本的台詞）。"""
        if not self.ready() or key not in self.situations:
            return None
        chance = float(self.settings.get("llm_fresh", 0.25))
        if chance <= 0 or random.random() >= chance:
            return None
        pool = self.mem["fresh"].get(f"{key}@{self.tier(affection)}") or []
        return pool.pop(0) if pool else None

    def want_refill(self, affection):
        """哪些 key 的新台詞快用完了。"""
        if float(self.settings.get("llm_fresh", 0.25)) <= 0:
            return []
        keys = [k for k in self.situations if self.char.get("lines", {}).get(k)]
        t = self.tier(affection)
        return [k for k in keys if len(self.mem["fresh"].get(f"{k}@{t}", [])) < 2]

    # ---------- 背景工作 ----------
    def submit(self, fn, callback=None):
        """fn 在背景執行緒跑，callback(結果或 None) 回到主執行緒。"""
        self.jobs.put((fn, callback))

    def poll(self):
        """主執行緒每一格呼叫：把背景完成的結果交給 callback。"""
        while True:
            try:
                cb, res = self.results.get_nowait()
            except queue.Empty:
                break
            if cb:
                cb(res)
        if self.proc is not None and time.time() - self.last_use > IDLE_UNLOAD_S and not self.busy:
            self.stop()

    def _worker(self):
        while True:
            fn, cb = self.jobs.get()
            self.busy = True
            try:
                res = fn()
            except Exception as e:           # 模型出錯不要影響桌寵：回 None，呼叫端用固定台詞
                self._log_error(e)
                res = None
            self.busy = not self.jobs.empty()
            self.results.put((cb, res))

    def _log_error(self, e):
        import traceback
        try:
            os.makedirs(self.dir, exist_ok=True)
            with open(os.path.join(self.dir, "error.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {type(e).__name__}: {e}\n")
                f.write("".join(traceback.format_exception(type(e), e, e.__traceback__)))
        except OSError:
            pass

    # ---------- llama-server ----------
    def start(self):
        if self.proc is not None and self.proc.poll() is None:
            return
        exe, model = self.server_path(), self.model_path()
        if not exe or not os.path.exists(model):
            raise RuntimeError("還沒下載模型")
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        threads = max(1, min(4, (os.cpu_count() or 2) // 2))
        args = [exe, "-m", model, "--host", "127.0.0.1", "--port", str(self.port),
                "-c", "2048", "-t", str(threads), "-np", "1"]
        os.makedirs(self.dir, exist_ok=True)
        log = open(os.path.join(self.dir, "server.log"), "w", encoding="utf-8", errors="replace")
        kw = {"creationflags": 0x08000000} if sys.platform == "win32" else {}   # Windows：不要跳出黑色視窗
        self.proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                     cwd=os.path.dirname(exe), **kw)
        t0 = time.time()
        while time.time() - t0 < 120:                # 載入模型：等 /health 回 200
            if self.proc.poll() is not None:
                self.proc = None
                raise RuntimeError("llama-server 啟動失敗，詳見 llm/server.log")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2) as r:
                    if r.status == 200:
                        self.last_use = time.time()
                        return
            except Exception:
                pass
            time.sleep(0.3)
        self.stop()
        raise RuntimeError("llama-server 啟動逾時")

    def stop(self):
        p, self.proc = self.proc, None
        if p is not None and p.poll() is None:
            p.terminate()
            try:
                p.wait(5)
            except subprocess.TimeoutExpired:
                p.kill()

    def complete(self, system, user, max_tokens=120, schema=None, temperature=0.8, history=()):
        """在背景執行緒呼叫。history：之前的對話 [(role, 內容), ...]。回傳模型的文字（已去掉思考段落）。"""
        self.start()
        self.last_use = time.time()
        msgs = [{"role": "system", "content": system}]
        msgs += [{"role": r, "content": c} for r, c in history]
        msgs.append({"role": "user", "content": user})
        body = {"messages": msgs,
                "max_tokens": max_tokens, "temperature": temperature, "top_p": 0.9, "stream": False,
                "chat_template_kwargs": {"enable_thinking": False}}
        if schema:
            body["response_format"] = {"type": "json_schema", "json_schema": {"name": "out", "schema": schema}}
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            out = json.load(r)["choices"][0]["message"].get("content") or ""
        self.last_use = time.time()
        return re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()

    def complete_json(self, system, user, schema, **kw):  # kw 可帶 history
        text = self.complete(system, user, schema=schema, **kw)
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0) if m else text)

    # ---------- 提示詞 ----------
    def system_prompt(self, affection):
        p = self.persona
        tone = p.get("tone", {}).get(self.tier(affection), "")
        rules = [f"只用繁體中文（台灣用語），一次只說一句話，{self.max_chars} 個字以內",
                 "不要用表情符號、不要加引號、不要在句子前面寫名字",
                 "不要提到自己是 AI、模型或程式", "你是待在使用者電腦桌面上的小角色，稱呼使用者為「你」"]
        rules += p.get("rules", [])
        ex = [l for k, v in self.char.get("lines", {}).items() if "@" not in k
              for l in v if "{" not in l and len(l) <= self.max_chars + 5]
        ex = random.sample(ex, min(12, len(ex)))
        s = f"你是「{self.name}」。{p.get('description', '')}\n"
        if p.get("speech"):
            s += f"說話方式：{p['speech']}\n"
        if tone:
            s += f"你現在對使用者的態度：{tone}\n"
        s += "規則：\n" + "\n".join(f"- {r}" for r in rules) + "\n"
        if ex:
            s += "你平常說話的例子（模仿語氣，不要照抄）：\n" + "\n".join(f"- {l}" for l in ex) + "\n"
        return s

    def clean(self, text, limit=None):
        """把模型輸出整理成一句可以放進對話框的台詞；不合格就回傳 None。"""
        if not text:
            return None
        text = TO_TRAD(text.strip().splitlines()[0].strip())
        text = re.sub(rf"^({re.escape(self.name)}|她|我)\s*[:：]\s*", "", text)
        text = text.strip(" \"'「」『』“”‘’")
        text = re.sub(r"[\U0001F000-\U0001FFFF☀-➿]", "", text).strip()
        limit = limit or self.max_chars + 8
        if not text or len(text) > limit or not re.search(r"[\u4e00-\u9fff]", text):
            return None
        if re.search(r"[A-Za-z]{4,}", text) or re.search(r"AI|人工智慧|語言模型|助手|助理", text):
            return None
        return text

    # ---------- 工作（都在背景執行緒跑） ----------
    def job_fresh(self, keys, affection, n=4):
        """幫快用完的台詞 key 各產生幾句新的，存起來慢慢用。"""
        t = self.tier(affection)
        sys_p = self.system_prompt(affection)
        item = {"type": "string", "minLength": 2, "maxLength": self.max_chars + 8}
        schema = {"type": "object", "properties": {"lines": {"type": "array", "items": item,
                                                             "minItems": n, "maxItems": n}},
                  "required": ["lines"]}
        for k in keys[:4]:                         # 一次最多補 4 種，不要佔太久
            own = self.char.get("lines", {}).get(k, [])
            user = (f"情境：{self.situations[k]}。\n她在這個情境原本會說：{'／'.join(own[:5])}\n"
                    f"請另外寫 {n} 句不同的、她在這個情境下可能會說的話。")
            try:
                d = self.complete_json(sys_p, user, schema, max_tokens=60 * n, temperature=0.95)
            except Exception as e:
                self._log_error(e); continue
            good = [c for c in (self.clean(x) for x in d.get("lines", [])) if c and c not in own]
            with self.lock:
                self.mem["fresh"].setdefault(f"{k}@{t}", []).extend(dict.fromkeys(good))
        self.save()
        return True

    def job_reminder(self, when, task, affection):
        sys_p = self.system_prompt(affection)
        day = "今天" if when.date() == date.today() else "明天" if when.date() == date.today() + timedelta(1) else \
            f"{when.month}/{when.day}"
        user = f"使用者請你在{day} {when:%H:%M} 提醒他「{task}」。用一句話答應他。"
        return self.clean(self.complete(sys_p, user, max_tokens=60))

    def job_chat(self, text, history, affection, remember=True):
        """聊天：用角色的語氣回一兩句；使用者提到值得記的近況（考試、生病、出門…）就記下來。
        history 是最近幾輪對話 [(role, 內容), ...]，只存在記憶體裡，不寫進檔案。"""
        sys_p = self.system_prompt(affection) + (
            "\n現在使用者在跟你聊天。用你的語氣自然地回應，一到兩句就好。"
            "遇到你不知道的知識問題，就用角色的方式說不知道，不要編造。")
        if not remember:
            return self.clean(self.complete(sys_p, text, max_tokens=80, history=history), self.max_chars * 2)
        schema = {"type": "object", "properties": {
            "reply": {"type": "string", "minLength": 1, "maxLength": self.max_chars * 2},
            "memory": {"type": "string", "maxLength": 40},
            "ask_later": {"type": "boolean"}}, "required": ["reply", "memory", "ask_later"]}
        user = (f"使用者說：「{text}」\n"
                "請回傳 JSON：reply 是你回他的話；如果他提到自己最近的事，memory 用第三人稱整理成一句短短的紀錄"
                "（例如：使用者明天要考數學），只是閒聊就填空字串；ask_later 表示之後值得主動問他後續"
                "（例如考試、看醫生、出門），是就填 true。")
        d = self.complete_json(sys_p, user, schema, max_tokens=200, temperature=0.7, history=history)
        reply = self.clean(d.get("reply", ""), self.max_chars * 2)
        memo = self.clean(str(d.get("memory", "")), 40)
        if memo:
            self.add_note(memo, bool(d.get("ask_later")))
        return reply

    def add_note(self, memo, ask_later):
        with self.lock:
            self.mem["notes"].append({"day": date.today().isoformat(), "t": time.time(), "text": memo,
                                      "ask": ask_later, "asked": False})
        self.prune()
        self.save()

    def due_note(self):
        """值得主動提起的記憶：至少過了 3 小時、還沒問過。"""
        for n in self.mem["notes"]:
            if n.get("ask") and not n.get("asked") and time.time() - n.get("t", 0) > 3 * 3600:
                return n
        return None

    def job_follow_up(self, note, affection):
        ago = (date.today() - date.fromisoformat(note["day"])).days
        when = "今天稍早" if ago == 0 else "昨天" if ago == 1 else f"{ago} 天前"
        user = f"你記得{when}使用者跟你說過：{note['text']}。現在主動用一句話問他後來怎麼樣了。"
        line = self.clean(self.complete(self.system_prompt(affection), user, max_tokens=60))
        if line:
            note["asked"] = True
            self.save()
        return line

    def job_recap(self, affection):
        """記得昨天的事：把昨天的紀錄講成一句關心的話。"""
        y = (datetime.strptime(day_key(), "%Y-%m-%d") - timedelta(days=1)).date().isoformat()
        facts = self.day_facts(y)
        if not facts:
            return None
        pick = random.sample(facts, min(2, len(facts)))
        user = "你記得昨天：" + "；".join(pick) + "。用一句話跟使用者提起這件事（可以關心、可以小小吐槽）。"
        return self.clean(self.complete(self.system_prompt(affection), user, max_tokens=60))

    def mark_done(self, key):
        self.mem["done"][key] = date.today().isoformat()

    def is_done(self, key):
        return key in self.mem["done"]

    # ---------- 下載 ----------
    def job_install(self):
        """下載還沒有的 llama-server 和模型。進度放在 download_state。"""
        os.makedirs(self.model_dir, exist_ok=True)
        st = self.download_state = {"what": "", "done": 0, "total": 0, "error": None, "finished": False}

        def prog(done, total):
            st["done"], st["total"] = done, total
        try:
            if not self.server_path():
                st["what"] = "llama-server"
                errors = []
                for url, name in server_candidates():
                    zp = os.path.join(self.dir, name)
                    try:
                        download(url, zp, prog, lambda: self.cancel_download)
                        extract_server(zp, self.bin_dir)
                        break
                    except InterruptedError:
                        raise
                    except Exception as e:
                        errors.append(f"{name}：{e}")
                else:
                    raise RuntimeError("下載 llama-server 失敗：\n" + "\n".join(errors[-3:]))
                if not self.server_path():
                    raise RuntimeError("解壓縮後找不到 llama-server")
            if not self.has_model():
                info = self.model_info()
                st["what"] = info["label"]
                st["done"], st["total"] = 0, info["mb"] << 20
                download(info["url"], os.path.join(self.model_dir, info["file"]), prog, lambda: self.cancel_download)
        except Exception as e:
            st["error"] = str(e) or type(e).__name__
            self._log_error(e)
        st["finished"] = True
        return st["error"] is None

    def remove_downloads(self):
        self.stop()
        shutil.rmtree(self.dir, ignore_errors=True)
        self.mem["fresh"].clear()
        self.save()
