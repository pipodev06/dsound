"""Links de Spotify, sin login ni Web API (que hoy exige Premium):

- track: se lee el og:title/og:description de la pagina publica y se arma
  "Artista Titulo" para buscar en YouTube.
- playlist / album: se lee la pagina "embed" publica (la que usan los
  reproductores embebidos), que trae la lista de temas con artista y duracion.
  Despues cada tema se busca en YouTube (ver `match_on_youtube`)."""

import concurrent.futures
import html as html_module
import json
import re
from urllib.parse import urlparse

import requests

from dsound import youtube_dl

LINK_PATH_RE = re.compile(r"^/(?:[\w-]+/)?(track|playlist|album)/([a-zA-Z0-9]+)/?$")
_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]*)"')
_DESC_RE = re.compile(r'<meta property="og:description" content="([^"]*)"')
_RELEASE_DATE_RE = re.compile(r'<meta name="music:release_date" content="(\d{4})')
_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
COLLECTION_TRACK_CAP = 100
MATCH_WORKERS = 8
DURATION_TOLERANCE_SECONDS = 15


def parse_link(url: str):
    """(tipo, id) si `url` es un link de open.spotify.com de track, playlist o
    album (ej. https://open.spotify.com/intl-es/playlist/<id>?si=...), si no
    None. Se valida el host para no terminar pidiendo una URL cualquiera."""
    url = (url or "").strip()
    if "://" not in url:
        url = "https://" + url  # links pegados sin esquema: open.spotify.com/track/...
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname != "open.spotify.com":
        return None
    match = LINK_PATH_RE.match(parsed.path)
    return (match.group(1), match.group(2)) if match else None


def track_id(url: str):
    """ID del track si `url` es un link de track de Spotify, si no None."""
    link = parse_link(url)
    return link[1] if link and link[0] == "track" else None


def resolve(url: str):
    """Lee la pagina publica de un track de Spotify y arma 'Artista Titulo'
    para buscar en YouTube. Devuelve None si no pudo leerlo."""
    tid = track_id(url)
    if not tid:
        return None

    resp = requests.get(f"https://open.spotify.com/track/{tid}", headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    html_body = resp.text

    title_match = _TITLE_RE.search(html_body)
    if not title_match:
        return None
    title = html_module.unescape(title_match.group(1))

    artist = ""
    desc_match = _DESC_RE.search(html_body)
    if desc_match:
        desc = html_module.unescape(desc_match.group(1))
        artist = desc.split(" · ")[0].strip()

    return f"{artist} {title}".strip()


def _biggest_image(images: list) -> str:
    if not images:
        return ""
    return max(images, key=lambda i: i.get("maxWidth") or i.get("width") or 0).get("url", "")


def parse_embed_page(kind: str, html_body: str):
    """Saca nombre, portada y temas del JSON que trae la pagina embed."""
    match = _NEXT_DATA_RE.search(html_body)
    if not match:
        return None
    try:
        entity = json.loads(match.group(1))["props"]["pageProps"]["state"]["data"]["entity"]
    except (ValueError, KeyError, TypeError):
        return None

    cover = _biggest_image((entity.get("visualIdentity") or {}).get("image"))
    if not cover:
        cover = _biggest_image((entity.get("coverArt") or {}).get("sources"))
    release = entity.get("releaseDate") or {}
    year = (release.get("isoString") or "")[:4] if isinstance(release, dict) else ""

    tracks = []
    for t in entity.get("trackList") or []:
        title = (t.get("title") or "").strip()
        if not title:
            continue
        artist = ", ".join(a.strip() for a in (t.get("subtitle") or "").replace("\xa0", " ").split(",") if a.strip())
        tracks.append({"title": title, "artist": artist, "duration": round((t.get("duration") or 0) / 1000)})

    return {
        "kind": kind,
        "name": entity.get("name") or entity.get("title") or "",
        "artist": (entity.get("subtitle") or "") if kind == "album" else "",
        "cover": cover,
        "year": year or None,
        "tracks": tracks[:COLLECTION_TRACK_CAP],
    }


def get_collection(url: str):
    """Playlist o album de Spotify -> dict de `parse_embed_page`, o None si el
    link no es de playlist/album o no se pudo leer."""
    link = parse_link(url)
    if not link or link[0] not in ("playlist", "album"):
        return None
    kind, cid = link
    resp = requests.get(f"https://open.spotify.com/embed/{kind}/{cid}", headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    collection = parse_embed_page(kind, resp.text)
    if collection and kind == "album" and not collection["year"]:
        collection["year"] = _album_year(cid)
    return collection


def _album_year(album_id: str):
    """La pagina embed de un album no trae la fecha; la pagina normal si, en
    <meta name="music:release_date">. Si falla, el album queda sin año."""
    try:
        resp = requests.get(f"https://open.spotify.com/album/{album_id}", headers=_HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    match = _RELEASE_DATE_RE.search(resp.text)
    return match.group(1) if match else None


def _best_match(candidates: list, duration: int):
    """De los resultados de YouTube, el primero con duracion parecida al tema de
    Spotify (descarta versiones extendidas, en vivo de 10 min, etc.)."""
    for c in candidates:
        if not duration or not c.get("duration") or abs(c["duration"] - duration) <= DURATION_TOLERANCE_SECONDS:
            return c
    return None


def _match_one(track: dict):
    query = f"{track['artist']} - {track['title']}" if track["artist"] else track["title"]
    try:
        candidates = youtube_dl.search_youtube(query, limit=3)
    except Exception:
        return None
    return _best_match(candidates, track["duration"])


def match_on_youtube(collection: dict):
    """Busca cada tema en YouTube (en paralelo). Devuelve (resultados, faltantes):
    resultados con el mismo formato que /api/search, pero con el artista/titulo
    de Spotify ya fijados para que el mp3 quede con esos tags."""
    tracks = collection["tracks"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=MATCH_WORKERS) as pool:
        matches = list(pool.map(_match_one, tracks))

    results, missing = [], []
    seen = set()
    for index, (track, match) in enumerate(zip(tracks, matches), start=1):
        if not match or match["id"] in seen:
            missing.append(f"{track['artist']} - {track['title']}" if track["artist"] else track["title"])
            continue
        seen.add(match["id"])
        item = dict(match)
        item["artist_guess"] = track["artist"]
        item["title_guess"] = track["title"]
        item["preset"] = {
            "artist": track["artist"],
            "title": track["title"],
            "album": collection["name"] if collection["kind"] == "album" else None,
            "cover_url": collection["cover"] if collection["kind"] == "album" else None,
            "year": collection["year"] if collection["kind"] == "album" else None,
            "track_number": index if collection["kind"] == "album" else None,
        }
        results.append(item)
    return results, missing
