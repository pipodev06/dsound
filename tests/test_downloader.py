import os

import pytest

from dsound import downloader


def _items(*pairs):
    return [{"filename": f"{a} - {t}.mp3", "artist": a, "title": t} for a, t in pairs]


def test_find_duplicate_matches_similar_title(tmp_path):
    items = _items(("Bad Bunny", "Monaco"))
    assert downloader.find_duplicate("Bad Bunny", "Mónaco", str(tmp_path), library_items=items) == "Bad Bunny - Monaco.mp3"


def test_find_duplicate_ignores_shared_artist_prefix(tmp_path):
    items = _items(("Bad Bunny", "Monaco"))
    assert downloader.find_duplicate("Bad Bunny", "EoO", str(tmp_path), library_items=items) is None


def test_find_duplicate_different_artist(tmp_path):
    items = _items(("Queen", "Bohemian Rhapsody"))
    assert downloader.find_duplicate("Panic at the Disco", "Bohemian Rhapsody", str(tmp_path), library_items=items) is None


def test_estimate_mp3_bytes():
    assert downloader.estimate_mp3_bytes(60, "320") == 2_400_000
    assert downloader.estimate_mp3_bytes(None, "320") == 0


def test_failed_download_cleans_only_its_own_temp_files(tmp_path, monkeypatch):
    """Un error en una descarga no tiene que borrar los temporales de otra."""
    other = tmp_path / "._tmp_otra_descarga.webm.part"
    other.write_bytes(b"x")
    seen = {}

    def fake_download_audio(url, tmp_no_ext, **kwargs):
        seen["tmp"] = tmp_no_ext
        open(tmp_no_ext + ".webm.part", "wb").close()
        raise RuntimeError("boom")

    monkeypatch.setattr(downloader, "download_audio", fake_download_audio)
    monkeypatch.setattr(downloader.config, "require_ffmpeg", lambda: True)

    with pytest.raises(RuntimeError):
        downloader.download("https://youtu.be/x", str(tmp_path))

    assert other.exists()
    assert not os.path.exists(seen["tmp"] + ".webm.part")


def test_temp_names_are_unique_per_download(tmp_path, monkeypatch):
    names = []

    def fake_download_audio(url, tmp_no_ext, **kwargs):
        names.append(tmp_no_ext)
        raise RuntimeError("boom")

    monkeypatch.setattr(downloader, "download_audio", fake_download_audio)
    monkeypatch.setattr(downloader.config, "require_ffmpeg", lambda: True)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            downloader.download("https://youtu.be/same", str(tmp_path))
    assert names[0] != names[1]


def _fake_success(tmp_path, monkeypatch, info, lookup_result=None):
    """download() con yt-dlp y el tagger simulados: devuelve lo que se pidio a
    metadata.lookup y los tags que se escribieron."""
    calls = {}

    def fake_download_audio(url, tmp_no_ext, **kwargs):
        if kwargs.get("on_progress"):
            kwargs["on_progress"]("downloading", 50.0)
        open(tmp_no_ext + ".mp3", "wb").close()
        return tmp_no_ext + ".mp3", info

    def fake_lookup(info_, artist, title):
        calls["lookup"] = (artist, title)
        return lookup_result

    monkeypatch.setattr(downloader, "download_audio", fake_download_audio)
    monkeypatch.setattr(downloader.config, "require_ffmpeg", lambda: True)
    monkeypatch.setattr(downloader.metadata, "lookup", fake_lookup)
    monkeypatch.setattr(downloader, "tag_mp3", lambda path, meta: calls.setdefault("meta", meta))
    return calls


def test_download_uses_music_metadata_when_found(tmp_path, monkeypatch):
    info = {"title": "Rick Astley - Never Gonna Give You Up (Official Video)", "thumbnail": "https://i.ytimg.com/x.webp"}
    found = {
        "artist": "Rick Astley",
        "title": "Never Gonna Give You Up",
        "album": "Whenever You Need Somebody",
        "year": "1987",
        "cover_url": "https://lh3.googleusercontent.com/c=w544-h544",
    }
    calls = _fake_success(tmp_path, monkeypatch, info, found)
    result = downloader.download("https://youtu.be/x", str(tmp_path))

    assert calls["lookup"] == ("Rick Astley", "Never Gonna Give You Up")
    assert result["filename"] == "Rick Astley - Never Gonna Give You Up.mp3"
    assert calls["meta"]["album"] == "Whenever You Need Somebody"
    assert calls["meta"]["year"] == "1987"
    assert calls["meta"]["cover_url"].startswith("https://lh3.googleusercontent.com/")


def test_download_falls_back_to_title_parsing(tmp_path, monkeypatch):
    info = {"title": "Artista - Tema (Official Audio)", "thumbnail": "https://i.ytimg.com/x.jpg"}
    calls = _fake_success(tmp_path, monkeypatch, info, None)
    result = downloader.download("https://youtu.be/x", str(tmp_path))
    assert (result["artist"], result["title"]) == ("Artista", "Tema")
    assert calls["meta"]["cover_url"] == "https://i.ytimg.com/x.jpg"
    assert "album" not in calls["meta"]


def test_download_with_override_skips_lookup(tmp_path, monkeypatch):
    calls = _fake_success(tmp_path, monkeypatch, {"title": "x"}, None)
    progress = []
    result = downloader.download(
        "https://youtu.be/x",
        str(tmp_path),
        artist_override="A",
        title_override="B",
        album="Disco",
        year="2020",
        track_number=3,
        on_progress=lambda phase, pct: progress.append((phase, pct)),
    )
    assert "lookup" not in calls
    assert result["filename"] == "A - B.mp3"
    assert calls["meta"]["track_number"] == 3 and calls["meta"]["year"] == "2020"
    assert progress == [("downloading", 50.0)]


@pytest.mark.skipif(__import__("shutil").which("ffmpeg") is None, reason="ffmpeg no instalado")
def test_end_to_end_tags_real_mp3(tmp_path, monkeypatch):
    """Pipeline real (mp3 de verdad + tagger), solo se simula YouTube y la portada."""
    import subprocess

    from mutagen.id3 import ID3

    from dsound import tagger

    def fake_download_audio(url, tmp_no_ext, **kwargs):
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=d=1", "-q:a", "9", tmp_no_ext + ".mp3"],
            check=True,
        )
        return tmp_no_ext + ".mp3", {"title": "x", "thumbnail": "https://i.ytimg.com/x.jpg"}

    cover = tmp_path / "c.png"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=red:s=16x16", "-frames:v", "1", str(cover)], check=True
    )

    class Resp:
        content = cover.read_bytes()

        def raise_for_status(self):
            pass

    monkeypatch.setattr(downloader, "download_audio", fake_download_audio)
    monkeypatch.setattr(tagger.requests, "get", lambda url, timeout=None: Resp())
    out = tmp_path / "music"
    result = downloader.download(
        "https://youtu.be/x",
        str(out),
        artist_override="Pitbull, Christina Aguilera",
        title_override="Feel This Moment",
        album="Global Warming",
        cover_url_override="https://image-cdn-fa.spotifycdn.com/image/x",
        year="2012",
        track_number=3,
    )

    tags = ID3(str(out / result["filename"]))
    assert str(tags["TIT2"]) == "Feel This Moment"
    assert str(tags["TPE1"]) == "Pitbull, Christina Aguilera"
    assert str(tags["TALB"]) == "Global Warming"
    assert str(tags["TDRC"]) == "2012"
    assert str(tags["TRCK"]) == "3"
    assert tags["APIC:Cover"].mime == "image/png"
    assert [p.name for p in out.iterdir()] == [result["filename"]]  # sin temporales
