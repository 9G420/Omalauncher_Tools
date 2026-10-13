# Omalauncher Tools · Codex Voice & Dictation / 播報與語音輸入

在 Android Omalauncher 首頁閱讀、播放 Codex 回覆，以及用瀏覽器聽寫文字。

## 功能 / Features

- 正式回覆完成後，自動刷新摘要與回覆時間；生成中會標示上次內容。
- 兩個首頁工具及瀏覽器聽寫頁共用中英文介面切換；回覆文字保留原語言。
- 自動跟隨最近活動的 Codex 對話，也可固定對話。
- 播放摘要／全文、停止、手動同步、複製全文。
- 首頁精簡操作；詳情頁固定頂部操作，下方獨立捲動。
- 線上自然中文語音，失敗時退回本機 espeak-ng；可切換純離線播報。
- Chrome 語音輸入、中英切換、編輯、複製，以及明確按鈕送入 Codex 佇列。

## 安裝 / Install

需要 Omalauncher 的 Arch Linux、支援 OWL 5 的版本，以及至少一個本機 Codex 對話。

1. 下載本倉庫 ZIP 並解壓，或 `git clone https://github.com/WeeboWIZ/Omalauncher_Tools.git`。
2. 在解壓後的目錄執行：

```sh
python install.py
```

English: Download this repository, run `python install.py` inside it, then tap EN/中 on either widget to switch both interfaces and the dictation page. The installer preserves your own settings and conversation data.

安裝腳本會安裝 Python、curl、util-linux、espeak-ng、libpulse，以及獨立虛擬環境內的 edge-tts。首頁會出現「Codex 播報」與「語音輸入」。Linux 必須已可透過 PulseAudio 播放聲音。

已有全部依賴時可使用 `python install.py --skip-deps`；這不會建立 TTS 虛擬環境。

## 使用與更新

開啟或恢復一個 Codex 對話，回首頁按「同步」。新正式回覆約半秒內被讀取，切換對話最多約五秒；同步只讀取文字，不會重播歷史回覆。

點「詳情」可播放全文、複製內容、切換聲音、開關自動播報。第一次預設開啟自動播報及線上自然語音。

自動跟隨是依本機會話記錄的最近修改時間判斷，並不是 Android 目前視窗。多個對話同時執行時，可在詳情按「對話：自動跟隨」固定目前對話。重新開啟跟隨即可恢復。

更新：下載新版本，再執行 `python install.py`。保留個人設定、草稿及對話資料，舊程式備份在 `~/.local/share/oma-voice/install-backups/`。更新後若舊播報服務仍在運行，重啟 Linux 一次載入新程式。不要只匯入 `.owl`：它們依賴這個工具的背景程式。

語音輸入需要 Chrome 支援語音辨識及麥克風權限。辨識後停止、編輯並保存，再按「送到目前對話」。送出依賴 Omalauncher 所附 Codex 的 `codex queue`；一般上游 Codex 若無此命令，可改用「複製文字」手動貼上。

## 資料與隱私

本倉庫不包含對話記錄、個人設定、Token、音檔、已下載模型或虛擬環境。安裝後使用者自己的資料位於：

- Codex 來源：`~/.codex/sessions/`（只讀）。
- 播報設定：`~/.config/omalauncher/voice.json`。
- 播報快取與最近回覆：`~/.cache/oma-voice/`。
- 聽寫草稿：瀏覽器 localStorage 及 `~/.cache/oma-speak/`。

**線上自然語音會把需要朗讀的文字傳給 Microsoft Edge TTS 服務**，不需要 API Key，服務可能變更或無法連線。切換「聲音：離線」使用本機 espeak-ng；較大的 Sherpa/Piper 模型不隨分享包分發。瀏覽器聽寫可能使用瀏覽器供應商的線上語音服務。

語音輸入頁只監聽 `127.0.0.1:18763`，保存請求檢查來源與隨機 Token；不對區域網路開放。文字不會在保存時自動送給 Codex。

## 檢查

```sh
python -m unittest discover -s tests -v
```

安裝後也可執行 `owl-check ~/.config/omalauncher/widgets/46-speak.owl` 查看實際首頁及詳情預覽。

## 分享

目前最完整的方式是分享整個倉庫網址或 ZIP，讓對方執行安裝腳本。Omalauncher 小工具商店可作為後續入口，但單獨發布 OWL 檔不足以安裝背景服務。

MIT License。第三方依賴保留各自的授權與服務條款。
