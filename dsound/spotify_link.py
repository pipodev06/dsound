import html as html_module
import re
from urllib.parse import urlparse

import requests

TRACK_PATH_RE = re.compile(r"^/(?:[\w-]+/)?track/([a-zA-Z0-9]+)/?$")
_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]*)"')
_DESC_RE = re.compile(r'<meta property="og:description" content="([^"]*)"')
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def track_id(url: str):
    """ID del track si `url` es de verdad un link de track de open.spotify.com
    (ej. https://open.spotify.com/intl-es/track/<id>?si=...), si no None.
    Se valida el host para no terminar pidiendo una URL cualquiera."""
    url = url.strip()
    if "://" not in url:
        url = "https://" + url  # links pegados sin esquema: open.spotify.com/track/...
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname != "open.spotify.com":
        return None
    match = TRACK_PATH_RE.match(parsed.path)
    return match.group(1) if match else None


def resolve(url: str):
    """Lee la pagina publica de un track de Spotify (sin login/API, solo el
    og:title/og:description que cualquiera puede ver) y arma 'Artista Titulo'
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
