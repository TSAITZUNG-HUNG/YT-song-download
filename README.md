# YT-song-download

讀取歌單 txt，把每首歌下載成純音檔 `.mp3`，自動存到「下載／歌曲」資料夾。針對「MV 有講話聲、不是純單曲」與「各首大小聲不一」做了處理。

## 功能

- **純音檔模式**：每首歌自動搜尋 YouTube 官方純音檔（「- Topic」自動生成頻道／Art Track），優先下載專輯音檔而非 MV，避免片頭對白與劇情。找不到純音檔才退回 txt 裡的原連結。
- **響度標準化**：以 EBU R128（-14 LUFS）拉齊每首音量。
- **手動剪裁**：可對個別歌曲標時間，精準去掉片頭。
- 以「歌名 - 歌手」當檔名，寫入標題、嵌入封面。
- 全部跑完後輸出 `下載失敗清單_日期時間.txt`。

## 環境需求

- Python 3
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/)

安裝（macOS）：

```bash
pip3 install -U yt-dlp
brew install ffmpeg
```

> Windows：`winget install Gyan.FFmpeg`；Linux：`sudo apt install ffmpeg`

## 歌單格式

每行一首，放在跟 `download_mp3.py` 相同的資料夾。沒有連結的行會自動略過。

```
1. 開始懂了 - 孫燕姿 | https://www.youtube.com/watch?v=h5eRbbOnPRc
2. 我不難過 - 孫燕姿 | https://www.youtube.com/watch?v=GDsyUtdS1YM
```

預設讀取 `華語金曲_YouTube連結.txt`；找不到就抓同資料夾第一個 `.txt`。

### 手動剪裁（選用）

只有需要精準去掉片頭的那幾首，在連結後面空一格加 `@時間`；其他歌不用動。標了時間的會停用純音檔搜尋、直接剪原連結。

```
不該 - 周杰倫 | https://youtu.be/xxx @0:18        # 跳過前 18 秒
珊瑚海 - 周杰倫 | https://youtu.be/xxx @0:15-4:02   # 只取 0:15 到 4:02
某首 | https://youtu.be/xxx @-3:40                  # 從頭到 3:40
```

## 使用方式

把 `download_mp3.py` 與歌單 txt 放同一個資料夾，執行：

```bash
python3 download_mp3.py
```

完成後 mp3 會在 `Downloads/歌曲`。執行時每首會顯示來源，如「(純音檔：孫燕姿 - Topic)」代表抓到乾淨音檔，「(MV連結(txt))」代表退回原連結。

## 可調整項

| 項目 | 位置 | 說明 |
|------|------|------|
| 純音檔模式 | `AUDIO_MODE` | 設 `False` 可關閉、直接抓 txt 連結 |
| 音質 | `preferredquality` | `"192"` 可改 `"320"` |
| 音量 | `LOUDNORM` 的 `I=-14` | 數字越大越大聲，如 `-12` |

## 常見問題

- **某首還是有講話聲**：該歌可能沒有官方純音檔（台語／戲劇曲／冷門歌較常見），程式退回了 MV。可對那首加 `@時間` 手動剪。
- **下載失敗**：多半是 YouTube 影片下架，失敗清單會列出，可用歌名重搜。
- **速度較慢**：純音檔模式要先搜尋再下載，屬正常。

## 聲明

請僅下載你擁有版權、已獲授權或屬公眾領域的內容，並遵守 YouTube 及各網站服務條款。本工具僅供個人合法用途。
