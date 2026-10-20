import os
import threading

from mutagen.easyid3 import EasyID3

from dsound.clean import build_filename, unique_path

_cache_lock = threading.Lock()
_tag_cache = {}  # out_dir -> {fname: (mtime, size, item)}


def track_path(out_dir: str, filename: str) -> str:
    """Ruta absoluta de un mp3 de la biblioteca. Solo acepta nombres planos
    terminados en .mp3: la API de biblioteca no tiene que poder leer, editar ni
    borrar otros archivos que haya en la carpeta de salida."""
    safe_name = os.path.basename(filename)
    if safe_name != filename or not safe_name.lower().endswith(".mp3"):
        raise FileNotFoundError(filename)
    path = os.path.join(out_dir, safe_name)
    if not os.path.isfile(path):
        raise FileNotFoundError(safe_name)
    return path


def list_library(out_dir: str) -> list:
    if not os.path.isdir(out_dir):
        return []

    with _cache_lock:
        cached = dict(_tag_cache.get(out_dir, {}))

    current = {}
    items = []
    for fname in os.listdir(out_dir):
        if not fname.lower().endswith(".mp3"):
            continue
        path = os.path.join(out_dir, fname)
        try:
            stat = os.stat(path)
        except OSError:
            continue
        size, mtime = stat.st_size, stat.st_mtime

        entry = cached.get(fname)
        if entry and entry[0] == mtime and entry[1] == size:
            item = entry[2]
        else:
            title, artist = os.path.splitext(fname)[0], ""
            try:
                tags = EasyID3(path)
                title = (tags.get("title") or [title])[0]
                artist = (tags.get("artist") or [""])[0]
            except Exception:
                pass
            item = {
                "filename": fname,
                "title": title,
                "artist": artist,
                "size": size,
                "mtime": mtime,
            }

        current[fname] = (mtime, size, item)
        items.append(item)

    with _cache_lock:
        _tag_cache[out_dir] = current

    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items


def delete_track(out_dir: str, filename: str):
    os.remove(track_path(out_dir, filename))


def update_track(out_dir: str, filename: str, artist: str, title: str) -> dict:
    path = track_path(out_dir, filename)

    title = title.strip() or "audio"
    artist = artist.strip()

    tags = EasyID3(path)
    tags["title"] = title
    if artist:
        tags["artist"] = artist
    elif "artist" in tags:
        del tags["artist"]
    tags.save()

    new_filename = build_filename(artist, title).lstrip(" -")
    if new_filename != filename:
        new_path = unique_path(os.path.join(out_dir, new_filename))
        os.replace(path, new_path)
        new_filename = os.path.basename(new_path)

    return {"filename": new_filename, "title": title, "artist": artist}
