import os
import re

# Palabras que delatan un parentesis/corchete de "relleno" del video:
# "(Official Video)", "[4K Remaster]", "(Lyrics)", "[Monstercat Release]"...
# Si un grupo entre () o [] contiene alguna, se borra el grupo entero.
_JUNK_GROUP_WORDS = re.compile(
    r"\b(official|video|audio|lyrics?|letra|visualizer|hd|hq|4k|mv|monstercat)\b",
    re.IGNORECASE,
)
_BRACKET_GROUP = re.compile(r"[(\[]([^()\[\]]*)[)\]]")

# Relleno suelto (fuera de parentesis). Siempre con limites de palabra, para no
# comerse pedazos de nombres reales ("Mvula", "Lyrical Lemonade").
JUNK_PATTERNS = [
    r"\bofficial\s+(music\s+)?video\b",
    r"\bofficial\s+audio\b",
    r"\blyrics?\s+video\b",
    r"\blyrics\b",
    r"\bvisualizer\b",
    r"\b(hd|hq|4k|mv)\b",
    r"\s*\|.*$",
]

BAD_KEYWORDS = ["live", "remix", "cover", "reaction", "8d audio", "sped up", "nightcore", "karaoke"]

INVALID_WINDOWS_CHARS = r'<>:"/\\|?*'


def strip_junk(title: str) -> str:
    cleaned = _BRACKET_GROUP.sub(
        lambda m: "" if _JUNK_GROUP_WORDS.search(m.group(1)) else m.group(0), title
    )
    for pattern in JUNK_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[(\[]\s*[)\]]", "", cleaned)  # parentesis que quedaron vacios
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -|")
    return cleaned


def parse_artist_title(raw_title: str):
    """'Bad Bunny - Titi Me Pregunto (Official Video)' -> ('Bad Bunny', 'Titi Me Pregunto').
    Si no hay separador 'artista - titulo' devuelve artista vacio."""
    cleaned = strip_junk(raw_title or "")
    if " - " in cleaned:
        artist, title = (p.strip() for p in cleaned.split(" - ", 1))
        if artist and title:
            return artist, title
    return "", (cleaned.strip() or "audio")


_CHANNEL_SUFFIX = re.compile(r"(\s*-\s*topic|vevo|\s+official)$", re.IGNORECASE)


def channel_artist(channel: str) -> str:
    """Nombre de canal -> posible artista: 'Bad Bunny - Topic' -> 'Bad Bunny',
    'RickAstleyVEVO' -> 'RickAstley'. Solo se usa como pista para validar
    metadata, nunca como artista final directo."""
    return _CHANNEL_SUFFIX.sub("", (channel or "").strip()).strip()


def sanitize_filename(name: str) -> str:
    for ch in INVALID_WINDOWS_CHARS:
        name = name.replace(ch, "")
    name = name.strip().rstrip(".")
    return name[:180]


def build_filename(artist: str, title: str) -> str:
    return sanitize_filename(f"{artist} - {title}") + ".mp3"


def unique_path(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 2
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"
