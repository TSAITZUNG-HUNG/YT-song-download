#!/usr/bin/env python3
"""
讀取「歌單 txt」，把每首歌下載成純音檔 .mp3，存到「下載 / 歌曲」資料夾。

解決「MV 有講話聲、不是純單曲」的關鍵：
    預設開啟「純音檔模式」(AUDIO_MODE)。程式會為每首歌搜尋 YouTube 上的
    官方純音檔（「- Topic」自動生成頻道 / Art Track），優先下載那個版本，
    而不是 txt 裡的 MV 連結。這種版本就是專輯音檔，沒有 MV 的對白或前奏劇情。
    只有搜尋不到純音檔時，才退回用 txt 裡原本的連結。

其他功能：
    - 響度標準化（loudnorm），各首音量拉齊。
    - 仍支援手動 @時間 剪裁（會停用該首的純音檔搜尋，直接精準剪原連結）。
    - 結束時輸出下載失敗清單。

歌單格式（每行一首，放在跟本程式相同的資料夾）：
    1. 開始懂了 - 孫燕姿 | https://www.youtube.com/watch?v=h5eRbbOnPRc

使用前需安裝：
    pip3 install -U yt-dlp
    ffmpeg：macOS `brew install ffmpeg`；Windows `winget install Gyan.FFmpeg`

執行：
    python3 download_mp3.py

請僅下載你擁有版權、已獲授權或屬公眾領域的內容，並遵守各網站服務條款。
"""

import re
import sys
from datetime import datetime
from pathlib import Path

LIST_FILE = "華語金曲_YouTube連結.txt"
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path.home() / "Downloads" / "歌曲"

# 純音檔模式：優先抓官方音檔而非 MV。想關掉改成 False。
AUDIO_MODE = True
# 搜尋每首歌時取前幾筆結果來挑純音檔版本
SEARCH_N = 8

# 響度標準化目標（EBU R128）。要更大聲可把 I 調高，例如 -12。
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"

URL_RE = re.compile(r"https?://\S+")
TRIM_RE = re.compile(r"@\s*([\d:]+)?\s*(?:-\s*([\d:]+))?")


def sanitize(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return name or "未命名"


def parse_time(t: str):
    if not t:
        return None
    sec = 0
    for p in t.split(":"):
        sec = sec * 60 + int(p)
    return sec


def parse_list(path: Path):
    """回傳 [(歌名, 網址, (start,end)或None), ...]。"""
    songs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = URL_RE.search(line)
        if not m:
            continue
        rest = line[m.end():]
        url = m.group(0).rstrip(".,)")
        trim = None
        tm = TRIM_RE.search(rest)
        if tm and (tm.group(1) or tm.group(2)):
            trim = (parse_time(tm.group(1)) or 0, parse_time(tm.group(2)))
        title = line[: m.start()].split("|")[0]
        title = re.sub(r"^\s*\d+[.\)、]\s*", "", title).strip(" -|\t")
        songs.append((sanitize(title), url, trim))
    return songs


def find_list_file() -> Path:
    preferred = SCRIPT_DIR / LIST_FILE
    if preferred.exists():
        return preferred
    txts = sorted(p for p in SCRIPT_DIR.glob("*.txt") if "下載失敗" not in p.name)
    if txts:
        return txts[0]
    sys.exit(f"找不到歌單 txt，請把它放在：{SCRIPT_DIR}")


def is_audio_track(entry) -> bool:
    """判斷搜尋結果是否為官方純音檔（- Topic / Art Track）。"""
    ch = (entry.get("channel") or entry.get("uploader") or "")
    return ch.strip().endswith("- Topic")


def find_audio_url(search_ydl, title):
    """搜尋官方純音檔，回傳 (url, 來源頻道)；找不到回傳 (None, None)。"""
    query = title.replace(" - ", " ")
    try:
        info = search_ydl.extract_info(f"ytsearch{SEARCH_N}:{query}", download=False)
    except Exception:
        return None, None
    for e in (info.get("entries") or []):
        if is_audio_track(e):
            vid = e.get("id") or e.get("url")
            url = e.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else None)
            if url and not str(url).startswith("http"):
                url = f"https://www.youtube.com/watch?v={url}"
            return url, (e.get("channel") or e.get("uploader"))
    return None, None


def write_failure_list(failures):
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out = OUTPUT_DIR / f"下載失敗清單_{stamp}.txt"
    lines = [
        f"下載失敗清單（{datetime.now().strftime('%Y-%m-%d %H:%M')}）",
        f"共 {len(failures)} 首失敗，格式同原歌單：歌名 | 連結",
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
        from yt_dlp.utils import download_range_func
    except ImportError:
        sys.exit("找不到 yt-dlp，請先執行：pip3 install -U yt-dlp")

    list_path = find_list_file()
    songs = parse_list(list_path)
    if not songs:
        sys.exit(f"在 {list_path.name} 裡找不到任何連結。")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"歌單檔案：{list_path.name}")
    print(f"共 {len(songs)} 首，下載到：{OUTPUT_DIR}")
    print(f"純音檔模式：{'開啟（優先官方音檔）' if AUDIO_MODE else '關閉'}｜已啟用響度標準化\n")

    # 只用來搜尋純音檔的輕量 ydl
    search_ydl = None
    if AUDIO_MODE:
        search_ydl = yt_dlp.YoutubeDL(
            {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True}
        )

    ok = 0
    failures = []
    for i, (title, url, trim) in enumerate(songs, 1):
        dl_url = url
        src = "MV連結(txt)"

        # 純音檔模式：沒有手動剪裁時，優先找官方音檔
        if AUDIO_MODE and not trim:
            audio_url, ch = find_audio_url(search_ydl, title)
            if audio_url:
                dl_url, src = audio_url, f"純音檔：{ch}"

        note = f"（手動剪裁 {trim[0]}s~{trim[1] if trim[1] else '結束'}）" if trim else f"（{src}）"
        print(f"[{i}/{len(songs)}] {title} {note}")

        postprocessors = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ]
        ydl_opts = {
            "outtmpl": str(OUTPUT_DIR / f"{title}.%(ext)s"),
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessor_args": {"extractaudio": ["-af", LOUDNORM]},
            "writethumbnail": True,
            "postprocessors": postprocessors,
        }
        if trim:
            start, end = trim
            end = end if end is not None else float("inf")
            ydl_opts["download_ranges"] = download_range_func(None, [(start, end)])
            ydl_opts["force_keyframes_at_cuts"] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([dl_url])
            ok += 1
        except Exception as e:
            failures.append((title, dl_url, str(e).replace("\n", " ")))
            print(f"    ⚠ 下載失敗：{e}")

    print(f"\n完成！成功 {ok} 首、失敗 {len(failures)} 首。")
    print(f"檔案位置：{OUTPUT_DIR}")
    if failures:
        print(f"失敗清單已存成：{write_failure_list(failures)}")
    else:
        print("沒有任何失敗，太棒了！")


if __name__ == "__main__":
    main()
