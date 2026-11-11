#!/usr/bin/env python3
"""Build a single-file HTML page to review every animation of a character pack.

Usage:  python3 tools/preview_anims.py characters/<id> [out.html]

The page shows each animation playing (per-frame timing from anims.json) plus
its frame strip, groups them by role (required / recommended / transition /
extra), lists required animations that are still missing, and lets you mark
each card OK / 需修改 with a note.  Marks are kept in the browser
(localStorage, keyed by character + animation + image hash), so a redrawn
sprite comes back as "unreviewed".  "匯出審核結果" copies a text summary.
"""
import base64, hashlib, html, json, sys
from pathlib import Path

# Animations the engine knows about.  (name, 中文, what it should show)
REQUIRED = [
    ("idle", "待機", "正面站立，呼吸/眨眼循環"),
    ("walk", "走路", "側面朝右，循環"),
    ("held", "被拎起", "被滑鼠抓著懸空"),
    ("fall", "掉落", "放開後往下掉"),
    ("land", "落地", "著地緩衝，播一次"),
    ("headpat", "摸頭", "被摸頭的反應"),
    ("gift", "收禮", "收到禮物的開心反應"),
    ("sleepy", "想睡", "打瞌睡/揉眼睛"),
]
RECOMMENDED = [
    ("run", "跑步", "側面朝右，循環"),
    ("read", "看書", "坐著看書（寬圖要設 ax）"),
    ("snore", "睡覺", "原地睡著"),
    ("desk_sleep_r", "趴桌睡", "趴在桌上睡（寬圖要設 ax）"),
    ("bed_sleep_r", "床上睡", "躺床睡"),
    ("peek", "探頭", "從螢幕邊偷看，需 hidden_frame"),
    ("stretch", "伸懶腰", "手往兩側張開"),
    ("peace", "比耶", "暫時屏蔽前比耶"),
    ("climb", "爬牆", "貼牆往上爬（側面）"),
    ("hang", "掛著", "抓在螢幕上緣"),
]
TRANSITIONS = [
    ("turn", "轉身", "正面 → 側面"),
    ("turn_back", "轉回", "側面 → 正面（可用 turn 倒放）"),
    ("book_open", "翻開書", "站 → 看書"),
    ("book_close", "闔上書", "看書 → 站"),
    ("desk_in", "趴下", "站 → 趴桌"),
    ("desk_out", "起身", "趴桌 → 站"),
    ("bed_in", "躺下", "站 → 床"),
    ("bed_out", "起床", "床 → 站"),
    ("wall_jump", "跳上牆", "地面 → 爬牆"),
    ("wall_land", "跳下牆", "牆 → 地面"),
    ("jolt", "驚醒", "睡 → 醒"),
    ("relax", "放鬆", "反應結束回待機"),
    ("draw_weapon", "拔武器", "空手 → 武器姿勢（有武器的角色才需要）"),
    ("sheath", "收武器", "武器 → 空手"),
]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cdir = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else cdir / "review.html"
    char = json.loads((cdir / "character.json").read_text(encoding="utf-8"))
    anims = json.loads((cdir / "assets" / "anims.json").read_text(encoding="utf-8"))
    cid = char.get("id", cdir.name)
    extra = char.get("extra_anims", {})
    known = {n for n, *_ in REQUIRED + RECOMMENDED + TRANSITIONS}
    groups = [("必要", REQUIRED), ("建議", RECOMMENDED), ("轉場（可省略）", TRANSITIONS),
              ("專屬動作 extra_anims", [(n, n, json.dumps(v, ensure_ascii=False)) for n, v in extra.items()])]
    others = [n for n in anims if n not in known and n not in extra]
    if others:
        groups.append(("未宣告（引擎不會用到）", [(n, n, "anims.json 有，但不在規格或 extra_anims") for n in others]))

    data, missing = [], []
    for gname, items in groups:
        cards = []
        for name, zh, desc in items:
            png = cdir / "assets" / f"{name}.png"
            meta = anims.get(name)
            if not meta or not png.exists():
                if gname in ("必要",) or name in extra:
                    missing.append(name)
                cards.append({"id": name, "zh": zh, "desc": desc, "missing": True})
                continue
            raw = png.read_bytes()
            cards.append({"id": name, "zh": zh, "desc": desc, "w": meta["w"], "h": meta["h"],
                          "n": meta["frames"], "ms": meta["ms"], "hash": hashlib.sha1(raw).hexdigest()[:10],
                          "info": {k: v for k, v in meta.items() if k not in ("w", "h", "frames", "ms")},
                          "src": "data:image/png;base64," + base64.b64encode(raw).decode()})
        data.append({"g": gname, "cards": cards})

    page = TEMPLATE.replace("__TITLE__", html.escape(char.get("name", cid))) \
        .replace("__CID__", json.dumps(cid)).replace("__MISSING__", json.dumps(missing, ensure_ascii=False)) \
        .replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}  ({sum(len(g['cards']) for g in data)} cards, missing required: {missing or 'none'})")


TEMPLATE = r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__ 動畫審核</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#222;--mute:#777;--line:#ddd;--ok:#2e7d32;--fix:#c62828;--chk:#e9e7e1}
@media (prefers-color-scheme:dark){:root{--bg:#1b1b1d;--card:#26262a;--ink:#eee;--mute:#999;--line:#3a3a40;--ok:#66bb6a;--fix:#ef5350;--chk:#303036}}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;z-index:2}
h1{font-size:18px;margin:0}h2{font-size:16px;margin:24px 16px 8px}
.wrap{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;padding:0 16px}
.c{background:var(--card);border:2px solid var(--line);border-radius:10px;padding:10px}
.c.ok{border-color:var(--ok)}.c.fix{border-color:var(--fix)}.c.miss{opacity:.55;border-style:dashed}
.stage{background:repeating-conic-gradient(var(--chk) 0 25%,transparent 0 50%) 0 0/16px 16px;display:flex;justify-content:center;align-items:flex-end;min-height:150px;border-radius:6px}
canvas{image-rendering:pixelated}.strip{overflow-x:auto;margin-top:6px}.strip img{image-rendering:pixelated;height:70px}
.meta{color:var(--mute);font-size:12px}.btns{display:flex;gap:6px;margin-top:6px}
button{font:inherit;padding:4px 10px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
button.on.okb{background:var(--ok);color:#fff}button.on.fixb{background:var(--fix);color:#fff}
textarea{width:100%;box-sizing:border-box;margin-top:6px;font:inherit;background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:6px}
.warn{color:var(--fix);font-weight:600}pre{white-space:pre-wrap;margin:16px;padding:12px;background:var(--card);border-radius:8px}
</style></head><body>
<header><h1>__TITLE__ 動畫審核</h1><span id="sum"></span>
<label>速度 <select id="spd"><option value="1">1x</option><option value="0.5">0.5x</option><option value="0.25">0.25x</option></select></label>
<button id="exp">匯出審核結果</button></header>
<div id="miss"></div><div id="root"></div><pre id="out" hidden></pre>
<script>
const CID=__CID__, MISSING=__MISSING__, DATA=__DATA__, S=4;
const KEY=c=>`review:${CID}:${c.id}:${c.hash}`;
function load(c){try{return JSON.parse(localStorage.getItem(KEY(c)))||{}}catch(e){return {}}}
function save(c,v){try{localStorage.setItem(KEY(c),JSON.stringify(v))}catch(e){}}
let speed=1;document.getElementById('spd').onchange=e=>speed=+e.target.value;
if(MISSING.length)document.getElementById('miss').innerHTML=`<p class="warn" style="margin:12px 16px">缺少必要動畫：${MISSING.join('、')}</p>`;
const root=document.getElementById('root'),all=[];
for(const g of DATA){
  const h=document.createElement('h2');h.textContent=g.g;root.appendChild(h);
  const w=document.createElement('div');w.className='wrap';root.appendChild(w);
  for(const c of g.cards){
    const el=document.createElement('div');el.className='c';w.appendChild(el);
    if(c.missing){el.classList.add('miss');el.innerHTML=`<b>${c.zh}</b> <code>${c.id}</code><div class="meta">${c.desc}</div><div class="meta">（尚未繪製）</div>`;continue}
    all.push(c);
    el.innerHTML=`<b>${c.zh}</b> <code>${c.id}</code><div class="meta">${c.desc}</div>
<div class="stage"><canvas width="${c.w*S}" height="${c.h*S}"></canvas></div>
<div class="strip"><img src="${c.src}"></div>
<div class="meta">${c.w}×${c.h} · ${c.n} 格 · ${c.ms.join('/')} ms ${Object.keys(c.info).length?'· '+JSON.stringify(c.info):''}</div>
<div class="btns"><button class="okb">OK</button><button class="fixb">需修改</button></div>
<textarea rows="2" placeholder="修改意見"></textarea>`;
    const st=load(c),ok=el.querySelector('.okb'),fx=el.querySelector('.fixb'),ta=el.querySelector('textarea');
    ta.value=st.note||'';
    const paint=()=>{const s=load(c).s;el.classList.toggle('ok',s==='ok');el.classList.toggle('fix',s==='fix');ok.classList.toggle('on',s==='ok');fx.classList.toggle('on',s==='fix');summary()};
    const set=s=>{const v=load(c);v.s=v.s===s?null:s;v.note=ta.value;save(c,v);paint()};
    ok.onclick=()=>set('ok');fx.onclick=()=>set('fix');ta.oninput=()=>{const v=load(c);v.note=ta.value;if(ta.value&&!v.s)v.s='fix';save(c,v);paint()};
    const img=new Image();img.src=c.src;const cv=el.querySelector('canvas'),x=cv.getContext('2d');x.imageSmoothingEnabled=false;
    let f=0;const tick=()=>{x.clearRect(0,0,cv.width,cv.height);x.drawImage(img,f*c.w,0,c.w,c.h,0,0,c.w*S,c.h*S);const d=c.ms[f]/speed;f=(f+1)%c.n;setTimeout(tick,d)};
    img.onload=tick;paint();
  }
}
function summary(){let o=0,fx=0;for(const c of all){const s=load(c).s;if(s==='ok')o++;else if(s==='fix')fx++}
  document.getElementById('sum').textContent=`OK ${o} · 需修改 ${fx} · 未審 ${all.length-o-fx} / ${all.length}`}
document.getElementById('exp').onclick=()=>{
  const L=[`# ${CID} 動畫審核`];if(MISSING.length)L.push('缺少：'+MISSING.join(', '));
  for(const c of all){const v=load(c);L.push(`- ${c.id} (${c.zh}): ${v.s==='ok'?'OK':v.s==='fix'?'需修改':'未審'}${v.note?' — '+v.note.replace(/\n/g,' '):''}`)}
  const t=L.join('\n'),p=document.getElementById('out');p.hidden=false;p.textContent=t;
  try{navigator.clipboard.writeText(t)}catch(e){}p.scrollIntoView()};
summary();
</script></body></html>"""

if __name__ == "__main__":
    main()
