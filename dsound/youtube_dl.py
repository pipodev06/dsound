import yt_dlp

from dsound.config import MP3_BITRATE


class CancelledError(Exception):
    """El usuario cancelo el job antes de que terminara."""


def _best_thumbnail(entry: dict) -> str:
    thumbs = entry.get("thumbnails") or []
    if thumbs:
        return thumbs[-1].get("url", "")
    return entry.get("thumbnail", "") or ""


def _map_entries(entries: list) -> list:
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
    return _map_entries(entries)


def get_playlist_videos(url: str, limit: int = 50) -> list:
    """Lista los videos de una playlist o canal de YouTube (metadata liviana,
    sin bajar nada) — mismo shape que search_youtube, para poder reusar
    la misma grilla/seleccion/descarga de Buscar."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "playlistend": limit,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries", []) if info else []
    return _map_entries(entries)[:limit]


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


def download_audio(video_url: str, out_path_no_ext: str, bitrate: str = MP3_BITRATE, cancel_event=None):
    """Descarga y convierte a mp3. Devuelve (ruta_mp3, info_dict del video).
    Si se pasa cancel_event (threading.Event) y se activa mientras yt-dlp esta
    bajando el archivo, corta tirando CancelledError — best-effort, con 3 huecos
    conocidos donde NO se puede cortar (yt-dlp solo nos avisa entre ticks, no da
    forma de abortar a mitad de esas fases):
    1. Mientras resuelve/extrae info del video, antes de que arranque la
       descarga en si (puede tardar unos segundos en videos largos).
    2. Una vez que ffmpeg (postprocesador) ya arranco a convertir a mp3 — se
       chequea el flag antes de lanzar ffmpeg (hook 'started'), pero mientras el
       proceso de ffmpeg esta corriendo no hay forma de interrumpirlo desde aca.
    Para canciones sueltas (algunos minutos) esto no se nota — el hueco importa
    sobre todo en videos muy largos, donde la conversion tarda de verdad. El
    caso mas util y 100% confiable sigue siendo cancelar un job que todavia
    esta en cola (jobs.py corta ahi antes de llamar a esta funcion)."""

    def _check_cancel(_status=None):
        if cancel_event is not None and cancel_event.is_set():
            raise CancelledError()

    def _check_cancel_pp(status):
        if status.get("status") == "started":
            _check_cancel()

    opts = {
        "format": "bestaudio/best",
        "outtmpl": out_path_no_ext + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [_check_cancel],
        "postprocessor_hooks": [_check_cancel_pp],
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
