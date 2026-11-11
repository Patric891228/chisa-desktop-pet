# 新角色指南

桌寵分成兩層：

- **引擎** `desktop_pet.py`：走路、拖曳、掉落、爬牆、睡覺作息、對話框、送禮、摸頭、固定位置、暫時躲起來、滑鼠穿透、今日行事曆、整點報時、久坐提醒、轉場動畫。所有角色共用，不用改。
- **角色包** `characters/<id>/`：這個角色的圖、台詞、禮物和專屬動作。新角色只要做一個角色包。

## 資料夾

```
characters/
  chisa/                 千咲（完整範例）
  _template/             空白範本（底線開頭的資料夾不會被當成角色）
  <id>/
    character.json       名字、台詞、禮物、專屬動作
    assets/              <動作>.png（橫向一排的影格）＋ anims.json
    art/                 畫圖程式或原始檔（可選）
    build_assets.sh      重新產生 assets/ 的指令（可選）
```

## 開新角色的流程

1. `cp -r characters/_template characters/<id>`，改 `character.json` 的 `id`、`name`、`title`。
2. 先畫**必要**動作（見下表），放進 `assets/`，在 `anims.json` 記下尺寸、格數和每格毫秒數。
3. 做審核頁：`python3 tools/preview_anims.py characters/<id>`，用瀏覽器打開 `characters/<id>/review.html`。
   每個動作會循環播放並列出全部影格，逐個按 **OK** 或 **需修改** 並寫意見；「匯出審核結果」會複製一份文字清單。
   審核紀錄存在瀏覽器裡，和圖的內容綁在一起，所以重畫過的動作會自動變回「未審」。
4. 改到全部 OK 後，再補建議動作、轉場、專屬動作，每加一批就重新產生審核頁。
5. 試跑：`PET_CHARACTER=<id> ./run.sh`。裝了兩個以上角色包時，右鍵 → 設定 → 角色 也可以切換（會重新啟動）。

缺少的動作引擎會自動跳過：沒有 `run` 就只用走的，沒有轉場就直接切換，沒有 `climb` 就不爬牆。只有必要動作缺了會不自然。

## 畫圖規則

- 1 倍大小的像素圖，程式會用整數倍放大（2～8 倍），不要先放大。
- 角色約 32 像素高，寬 32（單張寬圖可以更寬，例如看書、趴桌）。
- **腳踩在最下面一列**，引擎用圖的底部對齊地面。
- 上方要留 3 像素左右的空間給頭髮起伏，`anims.json` 的 `pad_top` 填留了幾格，對話框會貼著頭頂出現。
- 側面的動作（walk、run、climb…）一律**畫成面向右**，往左走時程式會自動左右翻轉。
- 同一個動作的每格大小相同，從左到右排成一張 PNG（寬 = w × 格數）。
- 寬圖裡角色中心不在正中央時，設 `ax`（角色中心的 x），引擎才不會在切換時跳一下。
- 不要用半透明，邊緣用深色描邊在任何桌布上都看得清楚。

## anims.json

```json
{
 "idle": {"w": 32, "h": 35, "frames": 4, "ms": [300, 300, 300, 300], "pad_top": 3},
 "read": {"w": 44, "h": 35, "frames": 6, "ms": [400, 400, 400, 400, 400, 900], "pad_top": 3, "ax": 16},
 "peek": {"w": 32, "h": 35, "frames": 8, "ms": [...], "pad_top": 3, "hidden_frame": 0}
}
```

| 欄位 | 意思 |
|---|---|
| `w`, `h` | 一格的寬高（像素） |
| `frames` | 格數 |
| `ms` | 每格停留的毫秒數（長度 = frames） |
| `pad_top` | 圖上方留白幾格 |
| `ax` | 寬圖裡角色中心的 x（可省略，預設正中央） |
| `hidden_frame` | 只給 `peek`：完全躲起來的那一格 |

## 動作規格

### 必要

| 名稱 | 內容 |
|---|---|
| `idle` | 正面站著發呆，呼吸／眨眼循環 |
| `walk` | 側面朝右走路，循環 |
| `held` | 被滑鼠拎起來懸空 |
| `fall` | 放開後往下掉 |
| `land` | 落地緩衝，播一次 |
| `headpat` | 被摸頭 |
| `gift` | 收到禮物 |
| `sleepy` | 被吵醒、睡眼惺忪 |

### 建議

| 名稱 | 內容 |
|---|---|
| `run` | 側面朝右跑步 |
| `read` | 坐著看書 |
| `snore` | 站著打瞌睡（沒有床和桌子時的睡覺） |
| `desk_sleep_r` | 趴在桌上午睡 |
| `bed_sleep_r` | 躺床睡覺 |
| `peek` | 從畫面邊緣探頭偷看，要設 `hidden_frame` |
| `stretch` | 伸懶腰（手往兩側張開，往上伸手看起來會變長） |
| `peace` | 比耶，「暫時躲起來」前會播 |
| `climb` | 貼著螢幕邊緣往上爬（側面朝右） |
| `hang` | 掛在螢幕上緣 |
| `jolt` | 嚇一跳（行事曆提醒、被吵醒） |

### 轉場（可省略）

| 名稱 | 什麼時候播 |
|---|---|
| `turn` / `turn_back` | 正面 → 側面 / 側面 → 正面 |
| `book_open` / `book_close` | 站 → 看書 / 看書 → 站 |
| `desk_in` / `desk_out` | 站 → 趴桌 / 趴桌 → 站 |
| `bed_in` / `bed_out` | 站 → 躺床 / 躺床 → 站 |
| `wall_jump` / `wall_land` | 地面 → 爬牆 / 牆 → 地面 |
| `relax` | 反應結束回到待機 |
| `draw_weapon` / `sheath` | 空手 → 武器姿勢 / 收回（有 `posture: weapon` 的專屬動作才需要） |

倒過來的轉場（turn_back、book_close、sheath）可以直接用正向的影格倒序。

### 專屬動作

寫在 `character.json` 的 `extra_anims`，見下面。

## character.json

| 欄位 | 意思 |
|---|---|
| `id` | 跟資料夾同名，英數小寫 |
| `name` | 角色名字（選單、狀態視窗） |
| `title` | 通知欄提示、開機自動啟動的名字 |
| `about` | 一句介紹 |
| `lines` | 台詞，每個 key 是一串句子，隨機挑一句；缺的 key 就不說話 |
| `chime_extra` | 整點報時後面接的話，`{"12": "吃飯時間到了。"}` |
| `gifts` | 禮物，見下面 |
| `status_text` | 狀態視窗裡每個動作的中文（引擎有預設值，只需寫專屬動作或想改的） |
| `energy_rate` | 每個動作每秒增減的體力（同上，有預設值） |
| `pat_reactions` | 摸頭後隨機接的反應動作，例如 `["shy", "guard"]` |
| `gift_reactions` | 依喜好（love / like / normal / dislike）播的動作，`[["gift", 2], ["shy", 1]]` 是 [動作, 播幾次] |
| `extra_anims` | 專屬動作 |

### 台詞 key

| key | 什麼時候說 |
|---|---|
| `pat` | 摸頭 |
| `pat_cap` | 今天摸頭次數滿了 |
| `pat_spam` | 連續狂點 |
| `gift` | 收禮（禮物自己沒寫台詞時用） |
| `no_gift` | 禮物送完了，`{h}` = 還要多久補一個 |
| `sleepy` | 睡覺時被吵醒 |
| `drag` | 被拎起來 |
| `land` | 落地 |
| `peek` | 偷看螢幕 |
| `tired` | 體力低 |
| `chat` | 隨口自言自語 |
| `morning` / `lunch` / `late` | 早上／中午／深夜第一次見面 |
| `neglect` | 很久沒理她 |
| `sit` | 久坐提醒，`{m}` = 已經連續幾分鐘 |
| `sit_back` | 起來休息後回來 |
| `busy` | 正在忙，不理你 |
| `climb_top` / `climb_jump` / `climb_down` | 爬到頂、跳上牆、爬下來 |
| `hide` / `back` | 暫時躲起來／回來 |
| `pin_go` | 走去固定位置 |
| `passthrough_on` / `passthrough_off` | 開／關滑鼠穿透 |

### 禮物

```json
"gifts": {
  "choco": {"name": "巧克力棒", "pref": "love", "gain": 10,
            "lines": ["……巧克力棒。你怎麼知道的？"],
            "icon": ["............", "...12 個字元 × 12 行..."]}
}
```

`pref` 是 love / like / normal / dislike，`gain` 是加多少好感。`icon` 是 12×12 的字元圖，`.` 是透明，可用的顏色：
K 黑、A 灰、B 深棕、C 棕、G 金、W 白、R 紅、D 暗紅、N 深綠、L 綠、P 粉紅。

### 專屬動作（extra_anims）

```json
"extra_anims": {
  "swing":       {"posture": "weapon", "loops": [2, 4], "pool": 1, "stay_pool": 1},
  "walk_weapon": {"posture": "weapon", "move": 5, "pool": 1, "tiring": true},
  "shy":         {}
}
```

| 欄位 | 意思 |
|---|---|
| `posture` | 姿勢群組；同群組之間不用轉場，從 front 進出會播 `draw_weapon` / `sheath`（weapon）或 `turn` |
| `front_only` | 只能從正面姿勢接（例如面向你的動作） |
| `move` | 會移動，數字是速度（walk 是 7、run 是 20） |
| `loops` | 一次播幾輪，`[最少, 最多]` |
| `pool` | 自由活動時被抽中的權重（0 或省略 = 不會自己出現，只用在反應） |
| `stay_pool` | 「待在原地」或固定位置時的權重 |
| `tiring` | 體力低時不做 |

只用在摸頭或收禮反應的動作寫 `{}` 就好。

## 千咲的做法（參考）

千咲的圖全部用 Python 畫（`characters/chisa/art/`），`build_assets.sh` 依序跑畫圖程式，最後用 `tools/finish_assets.py` 合併各程式輸出的 `anims_*.json`。
新角色也可以用 Aseprite 之類的工具畫，只要輸出橫排 PNG 並手寫 `anims.json`，不一定要寫程式。
