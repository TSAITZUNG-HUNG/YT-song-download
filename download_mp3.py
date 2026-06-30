#!/usr/bin/env python3
"""
讀取「歌單 txt」，把每個連結的影音下載成 .mp3，存到「下載 / 歌曲」資料夾。
結束時會把下載失敗的歌曲輸出成一個 txt 清單。

txt 檔格式（每行一首，放在跟本程式相同的資料夾）：
    1. 開始懂了 - 孫燕姿 | https://www.youtube.com/watch?v=h5eRbbOnPRc
    2. 我不難過 - 孫燕姿 | https://www.youtube.com/watch?v=GDsyUtdS1YM
    ...
沒有連結的行（標題、備註、分隔線等）會自動略過。

使用前需安裝：
    pip3 install -U yt-dlp
    並安裝 ffmpeg（轉檔用）：
        macOS:   brew install ffmpeg
        Windows: winget install Gyan.FFmpeg
        Linux:   sudo apt install ffmpeg

使用方式：
    把歌單 txt 跟本程式放在同一個資料夾，直接執行：
        python3 download_mp3.py

請僅下載你擁有版權、已獲授權或屬公眾領域的內容，並遵守各網站服務條款。
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# 預設歌單檔名（與本程式同資料夾）
LIST_FILE = "華語金曲_YouTube連結.txt"

# 本程式所在資料夾
SCRIPT_DIR = Path(__file__).resolve().parent

# 輸出資料夾：使用者家目錄下的 Downloads/歌曲
OUTPUT_DIR = Path.home() / "Downloads" / "歌曲"

# 解析每行：擷取網址
URL_RE = re.compile(r"https?://\S+")


def sanitize(name: str) -> str:
    """移除檔名不允許的字元。"""
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return name or "未命名"


def parse_list(path: Path):
    """回傳 [(歌名, 網址), ...]。"""
    songs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = URL_RE.search(line)
        if not m:
            continue  # 沒有連結的行直接略過
        url = m.group(0).rstrip(".,)")
        title_part = line[: m.start()].split("|")[0]
        title_part = re.sub(r"^\s*\d+[.\)、]\s*", "", title_part).strip(" -|\t")
        songs.append((sanitize(title_part), url))
    return songs


def find_list_file() -> Path:
    preferred = SCRIPT_DIR / LIST_FILE
    if preferred.exists():
        return preferred
    txts = sorted(p for p in SCRIPT_DIR.glob("*.txt") if "下載失敗" not in p.name)
    if txts:
        return txts[0]
    sys.exit(f"找不到歌單 txt，請把它放在：{SCRIPT_DIR}")


def write_failure_list(failures):
    """把失敗清單寫成 txt，回傳檔案路徑。"""
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out = OUTPUT_DIR / f"下載失敗清單_{stamp}.txt"
    lines = [
        f"下載失敗清單（{datetime.now().strftime('%Y-%m-%d %H:%M')}）",
        f"共 {len(failures)} 首失敗，格式同原歌單：歌名 | 連結",
        "（多半是該 YouTube 影片已下架，可用歌名重新搜尋補上）",
        "=" * 40,
    ]
    for i, (title, url, err) in enumerate(failures, 1):
        lines.append(f"{i}. {title} | {url}")
        lines.append(f"    失敗原因：{err}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main():
    try:
        import yt_dlp
    except ImportError:
        sys.exit("找不到 yt-dlp，請先執行：pip3 install -U yt-dlp")

    list_path = find_list_file()
    songs = parse_list(list_path)
    if not songs:
        sys.exit(f"在 {list_path.name} 裡找不到任何連結。")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"歌單檔案：{list_path.name}")
    print(f"共 {len(songs)} 首，下載到：{OUTPUT_DIR}\n")

    ok = 0
    failures = []  # [(歌名, 網址, 錯誤訊息), ...]
    for i, (title, url) in enumerate(songs, 1):
        print(f"[{i}/{len(songs)}] {title}")
        ydl_opts = {
            "outtmpl": str(OUTPUT_DIR / f"{title}.%(ext)s"),
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",   # 音質 kbps，可改 320
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "writethumbnail": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            ok += 1
        except Exception as e:
            failures.append((title, url, str(e).replace("\n", " ")))
            print(f"    ⚠ 下載失敗：{e}")

    print(f"\n完成！成功 {ok} 首、失敗 {len(failures)} 首。")
    print(f"檔案位置：{OUTPUT_DIR}")

    if failures:
        path = write_failure_list(failures)
        print(f"失敗清單已存成：{path}")
    else:
        print("沒有任何失敗，太棒了！")


if __name__ == "__main__":
    main()
