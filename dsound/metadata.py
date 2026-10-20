"""Metadata "oficial" para temas sueltos (artista, titulo, album, año, portada
cuadrada), en vez de adivinarla solo desde el titulo del video.

Orden de prioridad:
1. Lo que ya trae yt-dlp para videos musicales ("track", "artists", "album").
   No cuesta nada: viene en la misma info de la descarga.
2. Una busqueda en YouTube Music por "artista titulo". Solo se acepta un
   resultado que coincida de verdad (mismo video, o titulo + artista + duracion
   parecidos); si no, se descarta.
3. Si nada de eso da, el llamador se queda con el parseo del titulo de siempre.

Cualquier error (sin red, YouTube Music bloqueado, timeout) devuelve None:
la metadata es una mejora, nunca puede hacer fallar una descarga."""

import concurrent.futures
import difflib
import re

from dsound import albums, config
from dsound.clean import channel_artist, strip_junk

LOOKUP_TIMEOUT_SECONDS = 10
TITLE_MATCH_THRESHOLD = 0.85
ARTIST_MATCH_THRESHOLD = 0.6
DURATION_TOLERANCE_SECONDS = 10

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="dsound-meta")
_THUMB_SIZE_RE = re.compile(r"=w\d+-h\d+")


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


def _artist_matches(candidate: str, wanted: str) -> bool:
    candidate, wanted = (candidate or "").lower(), (wanted or "").lower()
    if not candidate or not wanted:
        return False
    return wanted in candidate or candidate in wanted or _ratio(candidate, wanted) >= ARTIST_MATCH_THRESHOLD


def _big_thumbnail(thumbnails: list) -> str:
    """Portada cuadrada de YouTube Music en alta resolucion (las URLs de
    googleusercontent aceptan el tamaño como parametro: =w544-h544)."""
    if not thumbnails:
        return ""
    url = max(thumbnails, key=lambda t: t.get("width", 0)).get("url", "")
    return _THUMB_SIZE_RE.sub("=w544-h544", url)


def _from_info(info: dict):
    track = (info.get("track") or "").strip()
    artists = info.get("artists") or ([info["artist"]] if info.get("artist") else [])
    if not track or not artists:
        return None
    year = info.get("release_year") or (info.get("release_date") or "")[:4]
    return {
        "artist": ", ".join(artists),
        "title": track,
        "album": info.get("album") or None,
        "year": str(year) if year else None,
        "cover_url": None,
    }


def _pick_song(results: list, info: dict, artist_hint: str, title_hint: str):
    duration = info.get("duration") or 0
    for r in results:
        title = r.get("title") or ""
        artist = ", ".join(a.get("name", "") for a in (r.get("artists") or []) if a.get("name"))
        if not title or not artist:
            continue
        if r.get("videoId") and r.get("videoId") == info.get("id"):
            return r, title, artist
        if _ratio(strip_junk(title), title_hint) < TITLE_MATCH_THRESHOLD:
            continue
        if not _artist_matches(artist, artist_hint):
            continue
        song_duration = r.get("duration_seconds") or 0
        if duration and song_duration and abs(song_duration - duration) > DURATION_TOLERANCE_SECONDS:
            continue
        return r, title, artist
    return None


def _from_youtube_music(info: dict, artist_hint: str, title_hint: str):
    if not title_hint:
        return None
    # sin artista en el titulo, el canal ("Bad Bunny - Topic") sirve de pista;
    # sin ninguna pista no se arriesga: "Hello" a secas podria ser cualquiera
    artist_hint = artist_hint or channel_artist(info.get("channel") or info.get("uploader") or "")
    if not artist_hint:
        return None
    results = albums.client().search(f"{artist_hint} {title_hint}", filter="songs", limit=5)
    picked = _pick_song(results or [], info, artist_hint, title_hint)
    if not picked:
        return None
    song, title, artist = picked
    album = (song.get("album") or {}).get("name") if isinstance(song.get("album"), dict) else None
    return {
        "artist": artist,
        "title": title,
        "album": album,
        "year": str(song["year"]) if song.get("year") else None,
        "cover_url": _big_thumbnail(song.get("thumbnails")) or None,
    }


def lookup(info: dict, artist_hint: str, title_hint: str):
    """Devuelve {artist, title, album, year, cover_url} o None."""
    found = _from_info(info)
    if found or not config.MUSIC_METADATA:
        return found
    future = _executor.submit(_from_youtube_music, info, artist_hint, title_hint)
    try:
        return future.result(timeout=LOOKUP_TIMEOUT_SECONDS)
    except Exception:
        return None
