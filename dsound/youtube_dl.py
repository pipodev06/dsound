import yt_dlp

from dsound.config import MP3_BITRATE


def _best_thumbnail(entry: dict) -> str:
    thumbs = entry.get("thumbnails") or []
    if thumbs:
        return thumbs[-1].get("url", "")
    return entry.get("thumbnail", "") or ""


def search_youtube(query: str, limit: int = 8) -> list:
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
                "thumbnail": _best_thumbnail(e),
                "webpage_url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
            }
        )
    return results


def get_stream_url(video_url: str) -> dict:
    """Saca la URL directa de un stream video+audio (sin descargar nada), para
    preview en el navegador con <video> nativo. Preferimos mp4 muxeado hasta
    480p (alcanza para identificar el video y pesa poco); si no hay, cae a solo
    audio. Funciona tambien con videos que bloquean el embed (Vevo/sellos)."""
    opts = {
        "format": (
            "best[ext=mp4][vcodec!=none][acodec!=none][height<=480]"
            "/best[vcodec!=none][acodec!=none][height<=480]"
            "/best[vcodec!=none][acodec!=none]"
            "/bestaudio[ext=m4a]/bestaudio"
        ),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    return {
        "stream_url": info.get("url", ""),
        "has_video": info.get("vcodec") not in (None, "none"),
        "title": info.get("title", ""),
        "duration": info.get("duration") or 0,
        "thumbnail": _best_thumbnail(info),
    }


def download_audio(video_url: str, out_path_no_ext: str, bitrate: str = MP3_BITRATE):
    """Descarga y convierte a mp3. Devuelve (ruta_mp3, info_dict del video)."""
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
        info = ydl.extract_info(video_url, download=True)
    return out_path_no_ext + ".mp3", info
