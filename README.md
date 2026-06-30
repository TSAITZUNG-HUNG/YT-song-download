# YT-song-download

讀取歌單 txt，把每個 YouTube 連結的音訊下載成 `.mp3`，自動存到「下載／歌曲」資料夾。下載結束會自動產生失敗清單。

## 功能

- 從 txt 歌單批次下載，逐首顯示進度
- 以「歌名 - 歌手」當作 mp3 檔名，並寫入標題、嵌入封面
- 預設 192kbps（可調整）
- 單首失敗會自動跳過，全部跑完後輸出 `下載失敗清單_日期時間.txt`

## 環境需求

- Python 3
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/)（負責轉檔）

安裝（macOS）：

```bash
pip3 install -U yt-dlp
brew install ffmpeg
```

> Windows 改用 `winget install Gyan.FFmpeg`；Linux 改用 `sudo apt install ffmpeg`。

## 歌單格式

每行一首，放在跟 `download_mp3.py` 相同的資料夾。沒有連結的行（標題、備註、分隔線）會自動略過。

```
1. 開始懂了 - 孫燕姿 | https://www.youtube.com/watch?v=h5eRbbOnPRc
2. 我不難過 - 孫燕姿 | https://www.youtube.com/watch?v=GDsyUtdS1YM
```

預設讀取的檔名為 `華語金曲_YouTube連結.txt`；若找不到，會自動抓同資料夾第一個 `.txt`。

## 使用方式

把 `download_mp3.py` 與歌單 txt 放在同一個資料夾，執行：

```bash
python3 download_mp3.py
```

完成後 mp3 會在使用者家目錄的 `Downloads/歌曲`（即「下載／歌曲」）資料夾裡。

## 常見問題

- **某些歌下載失敗**：多半是該 YouTube 影片已下架或設為私人，可用歌名重新搜尋連結後補上。失敗清單會自動列出。
- **想要更高音質**：把程式裡 `preferredquality` 的 `"192"` 改成 `"320"`。
- **連結帶播放清單參數**：程式已設定 `noplaylist`，只會下載單一首。

## 聲明

請僅下載你擁有版權、已獲授權或屬公眾領域的內容，並遵守 YouTube 及各網站的服務條款。本工具僅供個人合法用途。
