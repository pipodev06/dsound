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

    def fake_download_audio(url, tmp_no_ext, bitrate=None, cancel_event=None):
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

    def fake_download_audio(url, tmp_no_ext, bitrate=None, cancel_event=None):
        names.append(tmp_no_ext)
        raise RuntimeError("boom")

    monkeypatch.setattr(downloader, "download_audio", fake_download_audio)
    monkeypatch.setattr(downloader.config, "require_ffmpeg", lambda: True)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            downloader.download("https://youtu.be/same", str(tmp_path))
    assert names[0] != names[1]
