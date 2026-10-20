"""Aviso de versión nueva: consulta el último Release publicado en GitHub.

Se consulta como mucho una vez cada CACHE_SECONDS y cualquier error (sin
internet, límite de la API de GitHub) se ignora: nunca bloquea nada."""

import re
import threading
import time

import requests

from dsound import __version__, config

CACHE_SECONDS = 6 * 60 * 60
_cache = {"at": 0.0, "data": None}
_lock = threading.Lock()


def parse_version(text: str):
    """'v0.3.1' -> (0, 3, 1). None si no tiene forma de versión."""
    match = re.match(r"^v?(\d+)\.(\d+)(?:\.(\d+))?", (text or "").strip())
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def _fetch_latest():
    resp = requests.get(
        f"https://api.github.com/repos/{config.GITHUB_REPO}/releases/latest",
        headers={"Accept": "application/vnd.github+json"},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"tag": data.get("tag_name") or "", "url": data.get("html_url") or ""}


def check(force: bool = False) -> dict:
    current = __version__
    result = {"current": current, "latest": None, "url": None, "update_available": False}
    if not config.UPDATE_CHECK:
        return result

    with _lock:
        fresh = _cache["data"] is not None and time.time() - _cache["at"] < CACHE_SECONDS
        latest = _cache["data"] if fresh and not force else None
    if latest is None:
        try:
            latest = _fetch_latest()
        except Exception:
            return result
        with _lock:
            _cache.update(at=time.time(), data=latest)

    latest_version = parse_version(latest["tag"])
    current_version = parse_version(current)
    result["latest"] = latest["tag"].lstrip("v") or None
    result["url"] = latest["url"] or None
    result["update_available"] = bool(latest_version and current_version and latest_version > current_version)
    return result
