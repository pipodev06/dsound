import subprocess

import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, ID3NoHeaderError
from mutagen.mp3 import MP3


def _image_mime(data: bytes):
    """Tipo real de la imagen segun sus primeros bytes (no confiamos en la URL
    ni en el Content-Type). Solo JPEG y PNG son portadas ID3 que leen todos
    los reproductores."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def _to_jpeg(data: bytes):
    """Convierte una imagen (ej. el .webp que suele dar YouTube) a JPEG con
    ffmpeg, que dsound ya necesita para el mp3. None si no se pudo."""
    try:
        proc = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-frames:v", "1", "-f", "image2pipe", "-c:v", "mjpeg", "pipe:1"],
            input=data,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or _image_mime(proc.stdout) != "image/jpeg":
        return None
    return proc.stdout


def prepare_cover(data: bytes):
    """Devuelve (mime, bytes) listos para el frame APIC, o None si la imagen
    no se puede usar como portada."""
    mime = _image_mime(data)
    if mime:
        return mime, data
    jpeg = _to_jpeg(data)
    return ("image/jpeg", jpeg) if jpeg else None


def tag_mp3(filepath: str, meta: dict):
    try:
        tags = EasyID3(filepath)
    except ID3NoHeaderError:
        tags = EasyID3()
        tags.save(filepath)
        tags = EasyID3(filepath)

    tags["title"] = meta["title"]
    artists = meta.get("artists") or ([meta["primary_artist"]] if meta.get("primary_artist") else [])
    if artists:
        tags["artist"] = artists
    if meta.get("album"):
        tags["album"] = meta["album"]
    if meta.get("release_date"):
        tags["date"] = meta["release_date"][:4]
    tags.save(filepath)

    cover_url = meta.get("cover_url")
    if cover_url:
        try:
            resp = requests.get(cover_url, timeout=10)
            resp.raise_for_status()
            cover = prepare_cover(resp.content)
            if cover is None:
                return
            mime, image = cover
            audio = MP3(filepath, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime=mime,
                    type=3,
                    desc="Cover",
                    data=image,
                )
            )
            audio.save()
        except requests.RequestException:
            pass
