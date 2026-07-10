import yt_dlp

from dsound.config import MP3_BITRATE


def search_youtube(query: str, limit: int = 5) -> list:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "default_search": f"ytsearch{limit}",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)
    entries = info.get("entries", []) if info else []
    results = []
    for e in entries:
        if not e:
            continue
        results.append(
            {
                "id": e.get("id"),
                "title": e.get("title", ""),
                "channel": e.get("channel") or e.get("uploader") or "",
                "duration": e.get("duration") or 0,
                "webpage_url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
            }
        )
    return results


def download_audio(video_url: str, out_path_no_ext: str, bitrate: str = MP3_BITRATE) -> str:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": out_path_no_ext + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }
        ],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([video_url])
    return out_path_no_ext + ".mp3"
