import pytest

from dsound import metadata


class FakeYTMusic:
    def __init__(self, results):
        self.results = results
        self.queries = []

    def search(self, query, filter=None, limit=None):
        self.queries.append(query)
        return self.results


SONG = {
    "videoId": "abc",
    "title": "Never Gonna Give You Up",
    "artists": [{"name": "Rick Astley"}],
    "album": {"name": "Whenever You Need Somebody"},
    "year": "1987",
    "duration_seconds": 213,
    "thumbnails": [{"url": "https://lh3.googleusercontent.com/img=w60-h60-l90-rj", "width": 60}],
}


@pytest.fixture
def ytmusic(monkeypatch):
    fake = FakeYTMusic([SONG])
    monkeypatch.setattr(metadata.albums, "client", lambda: fake)
    monkeypatch.setattr(metadata.config, "MUSIC_METADATA", True)
    return fake


def test_uses_ytdlp_music_fields_first(ytmusic):
    info = {"track": "Tema", "artists": ["A", "B"], "album": "Disco", "release_year": 2021}
    assert metadata.lookup(info, "x", "y") == {
        "artist": "A, B",
        "title": "Tema",
        "album": "Disco",
        "year": "2021",
        "cover_url": None,
    }
    assert ytmusic.queries == []


def test_youtube_music_match(ytmusic):
    info = {"id": "dQw4w9WgXcQ", "duration": 212}
    found = metadata.lookup(info, "Rick Astley", "Never Gonna Give You Up")
    assert found["artist"] == "Rick Astley"
    assert found["album"] == "Whenever You Need Somebody"
    assert found["year"] == "1987"
    assert found["cover_url"] == "https://lh3.googleusercontent.com/img=w544-h544-l90-rj"


def test_rejects_different_song(ytmusic):
    assert metadata.lookup({"id": "z", "duration": 212}, "Rick Astley", "Together Forever") is None


def test_rejects_different_artist(ytmusic):
    assert metadata.lookup({"id": "z", "duration": 212}, "Otro Artista", "Never Gonna Give You Up") is None


def test_rejects_very_different_duration(ytmusic):
    # mismo tema pero el video dura 10 minutos (version extendida/en vivo)
    assert metadata.lookup({"id": "z", "duration": 600}, "Rick Astley", "Never Gonna Give You Up") is None


def test_uses_channel_as_artist_hint(ytmusic):
    info = {"id": "z", "duration": 212, "channel": "Rick Astley - Topic"}
    assert metadata.lookup(info, "", "Never Gonna Give You Up")["artist"] == "Rick Astley"
    assert ytmusic.queries == ["Rick Astley Never Gonna Give You Up"]


def test_no_artist_hint_does_not_guess(ytmusic):
    assert metadata.lookup({"id": "z"}, "", "Never Gonna Give You Up") is None
    assert ytmusic.queries == []


def test_errors_never_break_the_download(monkeypatch):
    def boom():
        raise RuntimeError("sin red")

    monkeypatch.setattr(metadata.albums, "client", boom)
    monkeypatch.setattr(metadata.config, "MUSIC_METADATA", True)
    assert metadata.lookup({"id": "z"}, "Rick Astley", "Never Gonna Give You Up") is None


def test_can_be_disabled(ytmusic, monkeypatch):
    monkeypatch.setattr(metadata.config, "MUSIC_METADATA", False)
    assert metadata.lookup({"id": "z", "duration": 212}, "Rick Astley", "Never Gonna Give You Up") is None
    assert ytmusic.queries == []
