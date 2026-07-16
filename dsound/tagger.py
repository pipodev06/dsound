import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, ID3NoHeaderError
from mutagen.mp3 import MP3


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
            audio = MP3(filepath, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=resp.content,
                )
            )
            audio.save()
        except requests.RequestException:
            pass
