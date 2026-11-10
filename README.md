# Chisa 桌面寵物

住在你桌面下緣的像素 Chisa：會散步、看書、午睡、扛著剪刀到處跑、偷看你的螢幕，摸頭前請先提交申請書。

*A tiny pixel-art Chisa who lives on your desktop. Windows / macOS / Linux.*

> **非官方同人作品。** Chisa 角色版權屬於原作，本專案與原作官方無關，請勿用於商業用途。

![新動作預覽](docs/new_actions.gif)

## 下載

到 [Releases](../../releases) 下載自己系統的檔案，解壓縮後點兩下就能開，不用另外安裝 Python。

| 系統 | 檔案 | 第一次開啟 |
| --- | --- | --- |
| Windows 10/11 | `ChisaDesktopPet-windows.zip` → `ChisaDesktopPet.exe` | 若出現 SmartScreen「未知的發行者」，按「其他資訊 → 仍要執行」 |
| macOS（Apple 晶片） | `ChisaDesktopPet-macos.zip` → `ChisaDesktopPet.app` | 程式沒有簽章，第一次請在程式上按右鍵 →「打開」 |
| Linux（x86_64） | `ChisaDesktopPet-linux.tar.gz` → `ChisaDesktopPet` | `chmod +x ChisaDesktopPet && ./ChisaDesktopPet` |

## 操作

| 操作 | 反應 |
| --- | --- |
| 左鍵點她 | 互動選單：摸頭、送禮、看她的狀態、設定、離開 |
| 摸頭 | 當機動畫，再隨機接 社恐／防備／害羞。每天前 5 次各 +1 好感；當機中再摸三下會過熱 |
| 送禮 | 有庫存就收禮物，好感 +5 |
| 左鍵拖曳 | 把她拎起來（手腳亂晃），放開會往下掉，落地時蹲一下、揚起灰塵 |
| 右鍵 | 同左鍵選單 |
| 系統匣圖示 | 點一下開狀態面板（桌面有系統匣才會出現） |

「設定」裡有：大小（2–8 倍）、對話框樣式、永遠在最上層、照時間作息、偶爾自言自語、開機自動啟動。

![選單](docs/menu_preview.png)

## 她自己會做的事

- 沿著螢幕下緣走路、跑步、看書、發呆、扛剪刀走、扛剪刀跑、練剪刀。
- **偷看螢幕**：鑽進螢幕下緣，從滑鼠下方附近冒出頭左看右看，被發現就縮回去，再若無其事地站起來。
- **精力**：跑跳會消耗，看書、發呆、睡覺會恢復。累了會常常打瞌睡、趴桌午睡。
- **作息**（依電腦的時間）：12:30–13:30 趴桌午睡、23:00–07:00 睡床，睡前一小時會打瞌睡。睡著時互動會先播睡眼惺忪，5 分鐘沒理又回去睡。
- **自言自語**：每幾分鐘可能說一句（早安、午餐、該睡了），很久沒理她會偷看你。

## 數值

| 項目 | 規則 |
| --- | --- |
| 好感度 | 0–100，開始是 10 |
| 禮物 | 庫存最多 3 個，每 4 小時補 1 個；送一個 +5 好感 |
| 摸頭 | 每天前 5 次各 +1 |
| 冷落 | 醒著時每 6 小時沒互動 −1，任何互動都會重新計時 |
| 關掉程式時 | 禮物照常補；冷落最多算 24 小時；離開超過 1 小時精力回滿 |

存檔位置：Linux `~/.config/desktop-pet/`、Windows `%APPDATA%\chisa-desktop-pet\`、macOS `~/Library/Application Support/chisa-desktop-pet/`。刪掉 `save.json` 就從頭開始。

## 對話框

像素風，三種樣式可在設定切換。字型是內附的[俐方體 11 號（Cubic 11）](https://github.com/ACh-K/Cubic-11)，SIL OFL 1.1 授權（見 `fonts/`）。

![對話框樣式](docs/bubble_styles.png)

## 從原始碼執行

需要 Python 3.9 以上。

```bash
pip install -r requirements.txt
python desktop_pet.py
```

Linux 也可以直接 `bash run.sh`（會在資料夾裡建立 `.venv`）。Ubuntu／Debian 第一次要先 `sudo apt install python3-venv libxcb-cursor0`。

測試用：`PET_TIME_SCALE=60 python desktop_pet.py`，數值的 1 小時變 1 分鐘。

## 打包

```bash
pip install -r requirements.txt pyinstaller
python packaging/build.py      # 產生在 dist/
```

在哪個系統執行就產生哪個系統的版本。推到 GitHub 後，Actions 會自動打包三個系統；推 `v` 開頭的標籤（例如 `git tag v0.1.0 && git push --tags`）會建立 Release 並附上下載檔。

## 改內容

- 台詞：`desktop_pet.py` 開頭的 `LINES`。
- 規則數字：同一檔開頭的 `GIFT_*`、`NEGLECT_STEP_H`、`PAT_*`、`ENERGY_RATE`。
- 動作圖：`assets/` 是 1 倍 PNG，由 `art/` 裡的 Python 程式畫出來（畫風說明見 `art/STYLE.md`，桌面版專用動作在 `art/make_desktop.py`）。改完執行 `bash tools/rebuild_assets.sh`（需要 Pillow）。

## 遇到問題

- **Linux 拖不動、位置怪怪的（Wayland）**：程式會自動改走 XWayland。如果還是不行，登入畫面改選「Ubuntu on Xorg」。
- **背景是黑色不是透明**：桌面沒開合成器（compositor）。GNOME、KDE、Windows、macOS 預設都有；輕量 Linux 桌面要另外開 picom。
- **Linux 出現 `Could not load the Qt platform plugin "xcb"`**：`sudo apt install libxcb-cursor0`。
