import os

from mutagen.easyid3 import EasyID3

from dsound.clean import build_filename, unique_path


def _track_path(out_dir: str, filename: str) -> str:
    safe_name = os.path.basename(filename)
    path = os.path.join(out_dir, safe_name)
    if not os.path.isfile(path):
        raise FileNotFoundError(safe_name)
    return path


def list_library(out_dir: str) -> list:
    if not os.path.isdir(out_dir):
        return []

    items = []
    for fname in os.listdir(out_dir):
        if not fname.lower().endswith(".mp3"):
            continue
        path = os.path.join(out_dir, fname)

        title, artist = os.path.splitext(fname)[0], ""
        try:
            tags = EasyID3(path)
            title = (tags.get("title") or [title])[0]
            artist = (tags.get("artist") or [""])[0]
        except Exception:
            pass

        try:
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
        except OSError:
            size, mtime = 0, 0

        items.append(
            {
                "filename": fname,
                "title": title,
                "artist": artist,
                "size": size,
                "mtime": mtime,
            }
        )

    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items


def delete_track(out_dir: str, filename: str):
    os.remove(_track_path(out_dir, filename))


def update_track(out_dir: str, filename: str, artist: str, title: str) -> dict:
    path = _track_path(out_dir, filename)

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
