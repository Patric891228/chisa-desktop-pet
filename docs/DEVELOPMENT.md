# 開發說明

## 從原始碼執行

需要 Python 3.9 以上。

```bash
pip install -r requirements.txt
./run.sh            # 或 python desktop_pet.py
```

Linux 若出現 xcb 外掛錯誤，`run.sh` 會提示要安裝的套件。

## 專案結構

```
desktop_pet.py        引擎（所有角色共用）
brain.py              本地小模型（選配）：llama-server 管理、下載、提醒解析、記憶
characters/<id>/      角色包：character.json、assets/（動作圖）、art/（畫圖程式）
characters/_template/ 開新角色用的範本
tools/                動畫審核頁（preview_anims.py）、素材後處理
packaging/            PyInstaller 打包腳本
```

## 切換角色

裝了兩個以上的角色包時，選單 → 設定 → 角色 可以切換（會重新啟動）。也可以用環境變數指定：

```bash
PET_CHARACTER=<角色 id> ./run.sh
```

## 做新角色

1. `cp -r characters/_template characters/<id>`
2. 填 `character.json`（名字、台詞、禮物、專屬動作）
3. 畫動作圖放進 `assets/`，在 `assets/anims.json` 填尺寸和影格時間
4. `python3 tools/preview_anims.py characters/<id>` 產生審核頁，逐個動作確認

完整規格見[新角色指南](CHARACTER_GUIDE.md)。

## 本地小模型

`brain.py` 不依賴 Qt。它在背景跑 llama.cpp 的 `llama-server`，用 OpenAI 相容的 HTTP API（`/v1/chat/completions`）要台詞；
工作在背景執行緒，結果由桌寵每一格呼叫 `Brain.poll()` 交回主執行緒。出錯或逾時一律退回角色包的固定台詞。

- 下載位置：存檔資料夾的 `llm/bin/`（llama-server，固定版本見 `LLAMA_TAG`）和 `llm/models/`（GGUF 模型，清單見 `MODELS`）。
- 記憶：存檔資料夾的 `memory_<角色>.json`（notes：聊天時提到的近況，聊天內容本身不存；days：每天的使用時間和互動次數；fresh：預先產生的新台詞）。
- 開發時不想下載，可以指定自己的檔案：

```bash
PET_LLAMA_SERVER=/path/to/llama-server PET_LLM_MODEL=/path/to/model.gguf ./run.sh
```

- 提醒的時間用規則解析（`parse_reminder`），不交給模型：`python3 -c "from brain import parse_reminder; print(parse_reminder('三點半提醒我開會'))"`。
- 簡轉繁用 `opencc-python-reimplemented`（打包時 `packaging/build.py` 會一起收進去）。

## 打包

```bash
pip install pyinstaller
python packaging/build.py
```

推 `v` 開頭的 tag 會由 GitHub Actions 打包三個系統的版本並建立 Release。
