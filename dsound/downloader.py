import difflib
import glob
import os

from dsound import config, library
from dsound.clean import build_filename, strip_junk, unique_path
from dsound.tagger import tag_mp3
from dsound.youtube_dl import CancelledError, download_audio, search_youtube

TITLE_DUPLICATE_THRESHOLD = 0.82
ARTIST_DUPLICATE_THRESHOLD = 0.6


class DownloadError(Exception):
    pass


def parse_artist_title(raw_title: str):
    """'Bad Bunny - Titi Me Pregunto (Official Video)' -> ('Bad Bunny', 'Titi Me Pregunto').
    Si no hay separador 'artista - titulo' devuelve artista vacio."""
    cleaned = strip_junk(raw_title)
    if " - " in cleaned:
        artist, title = (p.strip() for p in cleaned.split(" - ", 1))
        if artist and title:
            return artist, title
    return "", (cleaned.strip() or "audio")


def search(query: str, limit: int = 8) -> list:
    return search_youtube(query, limit=limit)


def estimate_mp3_bytes(duration_seconds, bitrate=None) -> int:
    """Estimacion en bytes de como va a pesar el mp3 final, a partir de la
    duracion del video y el bitrate elegido. Sirve para el chequeo de espacio
    en disco antes de bajar un album — no es exacta (el bitrate real puede
    variar un poco), pero alcanza para avisar si claramente no entra."""
    kbps = int(bitrate or config.MP3_BITRATE)
    return int((duration_seconds or 0) * kbps * 1000 / 8)


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_duplicate(artist: str, title: str, out_dir: str):
    """Busca un mp3 ya bajado con titulo (y artista, si se conoce ambos) parecido
    (fuzzy). Compara titulo/artista por separado, no el nombre de archivo entero
    ("artista - titulo") — comparar el string concatenado infla el ratio con
    titulos cortos, porque el prefijo del artista compartido domina la
    comparacion (caso real: "Bad Bunny - EoO" vs "Bad Bunny - Monaco" daba
    0.85 de ratio por el "Bad Bunny - " en comun, no por el titulo). Devuelve
    el nombre del archivo existente si encuentra match, o None."""
    title = (title or "").strip()
    if not os.path.isdir(out_dir) or not title:
        return None

    artist = (artist or "").strip()
    best_name, best_ratio = None, 0.0
    for item in library.list_library(out_dir):
        existing_title = (item["title"] or "").strip()
        if not existing_title:
            continue
        title_ratio = _ratio(title, existing_title)
        if title_ratio < TITLE_DUPLICATE_THRESHOLD:
            continue

        existing_artist = (item["artist"] or "").strip()
        if artist and existing_artist and _ratio(artist, existing_artist) < ARTIST_DUPLICATE_THRESHOLD:
            continue

        if title_ratio > best_ratio:
            best_ratio, best_name = title_ratio, item["filename"]

    return best_name


def download(
    webpage_url: str,
    out_dir: str,
    title_hint: str = "",
    bitrate: str = None,
    artist_override: str = None,
    title_override: str = None,
    album: str = None,
    cover_url_override: str = None,
    cancel_event=None,
) -> dict:
    if not config.require_ffmpeg():
        raise DownloadError(config.ffmpeg_missing_message())

    os.makedirs(out_dir, exist_ok=True)
    tmp_path_no_ext = os.path.join(out_dir, f"._tmp_{abs(hash(webpage_url))}")

    try:
        mp3_path, info = download_audio(
            webpage_url, tmp_path_no_ext, bitrate=bitrate or config.MP3_BITRATE, cancel_event=cancel_event
        )
    except BaseException:
        # limpia archivos parciales (._tmp_*.mp3, .part, etc.) si la descarga se
        # corto a mitad de camino, sea por cancelacion o por cualquier otro error
        for leftover in glob.glob(tmp_path_no_ext + "*"):
            try:
                os.remove(leftover)
            except OSError:
                pass
        raise

    if title_override is not None:
        artist, title = (artist_override or ""), (title_override.strip() or "audio")
    else:
        raw_title = title_hint or info.get("title") or "audio"
        artist, title = parse_artist_title(raw_title)

    filename = build_filename(artist, title).lstrip(" -")
    final_path = unique_path(os.path.join(out_dir, filename))

    meta = {
        "title": title,
        "primary_artist": artist,
        "cover_url": cover_url_override or info.get("thumbnail") or "",
    }
    if album:
        meta["album"] = album
    tag_mp3(mp3_path, meta)
    os.replace(mp3_path, final_path)

    return {
        "filename": os.path.basename(final_path),
        "artist": artist,
        "title": title,
    }
