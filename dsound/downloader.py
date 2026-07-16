import difflib
import os

from dsound import config
from dsound.clean import build_filename, strip_junk, unique_path
from dsound.tagger import tag_mp3
from dsound.youtube_dl import download_audio, search_youtube

DUPLICATE_THRESHOLD = 0.82


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


def find_duplicate(artist: str, title: str, out_dir: str):
    """Busca un mp3 ya bajado con nombre parecido (fuzzy). Devuelve el nombre
    del archivo existente si encuentra match, o None."""
    if not os.path.isdir(out_dir):
        return None
    candidate = build_filename(artist, title).lstrip(" -")[:-4].lower()  # sin ".mp3"
    best_name, best_ratio = None, 0.0
    for fname in os.listdir(out_dir):
        if not fname.lower().endswith(".mp3"):
            continue
        existing = os.path.splitext(fname)[0].lower()
        ratio = difflib.SequenceMatcher(None, candidate, existing).ratio()
        if ratio > best_ratio:
            best_ratio, best_name = ratio, fname
    return best_name if best_ratio >= DUPLICATE_THRESHOLD else None


def download(
    webpage_url: str,
    out_dir: str,
    title_hint: str = "",
    bitrate: str = None,
    artist_override: str = None,
    title_override: str = None,
    album: str = None,
    cover_url_override: str = None,
) -> dict:
    if not config.require_ffmpeg():
        raise DownloadError(config.ffmpeg_missing_message())

    os.makedirs(out_dir, exist_ok=True)
    tmp_path_no_ext = os.path.join(out_dir, f"._tmp_{abs(hash(webpage_url))}")

    mp3_path, info = download_audio(webpage_url, tmp_path_no_ext, bitrate=bitrate or config.MP3_BITRATE)

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
