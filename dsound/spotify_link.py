import html as html_module
import re

import requests

TRACK_RE = re.compile(r"open\.spotify\.com/track/([a-zA-Z0-9]+)")
_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]*)"')
_DESC_RE = re.compile(r'<meta property="og:description" content="([^"]*)"')
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def is_track_url(text: str) -> bool:
    return bool(TRACK_RE.search(text or ""))


def resolve(url: str):
    """Lee la pagina publica de un track de Spotify (sin login/API, solo el
    og:title/og:description que cualquiera puede ver) y arma 'Artista Titulo'
    para buscar en YouTube. Devuelve None si no pudo leerlo."""
    if not TRACK_RE.search(url):
        return None

    resp = requests.get(url, headers=_HEADERS, timeout=10)
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
