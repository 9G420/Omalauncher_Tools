# 上架 Omalauncher 商店：工作計劃

目標：產出可直接投稿到 [SimonSchubert/omarchy-widgets](https://github.com/SimonSchubert/omarchy-widgets) 的版本。
**送出（fork 推送、開 PR 或 issue）前必須先給倉庫擁有者確認。**

協作約定：多個 agent 共用本倉庫。提交只用倉庫的 git 使用者，不加任何 agent 署名。工作分支為 `store-release`。

## 商店的限制

- 每個 widget 一個資料夾 `widgets/weebowiz/<name>/`，只能放 `widget.owl`、`preview.png`、`README.md`、`previews/<theme>.webp`。
- `widget.owl` 上限 256 KB；`meta` 需要 `description`（10–200 字元）、`version`、`license`，`category` 須在固定清單內。
- 命令裡的變數只能以 `${sh(value)}` 帶入；不可含個人路徑或 token；更新必須提高 `version`。
- 背景程式不能另外附檔，所以要內嵌在 `widget.owl`，由使用者按「安裝」寫入 `~/.local`。

## 做法

`widgets/*.owl` 是範本，`tools/build_store.py` 把 `voice/`、`dictation/`、`bin/` 內嵌成安裝腳本後輸出到 `store/widgets/weebowiz/`。
`install.py` 用同一個函式產生 widget，所以 GitHub 安裝與商店安裝得到相同的 widget。

| 商店名稱 | 範本 | 輸出 |
|---|---|---|
| `terminal-voice` | `widgets/46-speak.owl` | `store/widgets/weebowiz/terminal-voice/` |
| `dictation` | `widgets/47-voice-input.owl` | `store/widgets/weebowiz/dictation/` |

兩個 widget 內嵌同一份程式與同一個版本標記（`~/.local/share/oma-voice/store-version`），任一個裝過，另一個就直接可用。

## 進度

- [x] 換行統一為 LF（`.gitattributes`），避免腳本在 Linux 因 CRLF 失敗
- [x] 範本改用 `~` 路徑，補齊 `requires`，加入安裝／更新畫面
- [x] `tools/build_store.py` 產生商店版，`install.py` 共用
- [x] 測試：商店輸出與原始碼同步、無個人路徑、大小在限制內
- [x] 用商店的 `tools/owl.jar review` 檢查
- [ ] 在手機上實測：`owl-check`、按「安裝」、播放、語音輸入送出
- [ ] 用手機實測後的截圖更新 `preview.png`
- [ ] **擁有者確認後**：fork 商店倉庫，複製 `store/widgets/weebowiz/` 並開 PR

## 改了程式之後

1. 修改 `voice/`、`dictation/`、`bin/` 或範本。
2. 提高 `tools/build_store.py` 的 `VERSION`。
3. 執行 `python tools/build_store.py`，再跑 `python -m unittest discover -s tests -v`。
4. 在商店倉庫內檢查：`java -jar tools/owl.jar review . widgets/weebowiz/<name>/widget.owl`。
