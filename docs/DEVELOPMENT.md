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

## 打包

```bash
pip install pyinstaller
python packaging/build.py
```

推 `v` 開頭的 tag 會由 GitHub Actions 打包三個系統的版本並建立 Release。
