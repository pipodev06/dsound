import os
import re

JUNK_PATTERNS = [
    r"\(?official\s*(music\s*)?video\)?",
    r"\(?official\s*audio\)?",
    r"\(?official\)?",
    r"\(?lyrics?\s*video\)?",
    r"\(?lyrics?\)?",
    r"\(?visualizer\)?",
    r"\(?hd\)?",
    r"\(?hq\)?",
    r"\(?4k\)?",
    r"\(?mv\)?",
    r"\[?\s*monstercat.*?\]?",
    r"\s*\|.*$",
]

BAD_KEYWORDS = ["live", "remix", "cover", "reaction", "8d audio", "sped up", "nightcore", "karaoke"]

INVALID_WINDOWS_CHARS = r'<>:"/\\|?*'


def strip_junk(title: str) -> str:
    cleaned = title
    for pattern in JUNK_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -|")
    return cleaned


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
