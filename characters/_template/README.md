# 角色包範本

1. 複製這個資料夾：`cp -r characters/_template characters/<id>`（資料夾名稱不要用底線開頭）
2. 改 `character.json` 的 `id`、`name`、`title`、台詞和禮物
3. 把動作圖放進 `assets/`，並在 `assets/anims.json` 填上每個動作的尺寸和影格時間（範例裡的 idle 先換成你的圖）
4. 做審核頁：`python3 tools/preview_anims.py characters/<id>`，打開 `characters/<id>/review.html` 逐個審
5. 試跑：`PET_CHARACTER=<id> ./run.sh`

完整說明：`docs/CHARACTER_GUIDE.md`
