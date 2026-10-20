import pytest

from dsound import spotify_link


@pytest.mark.parametrize(
    "url",
    [
        "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "https://open.spotify.com/intl-es/track/4uLU6hMCjMI75M1A2tKUQC?si=abc",
        "open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
    ],
)
def test_track_id_valid(url):
    assert spotify_link.track_id(url) == "4uLU6hMCjMI75M1A2tKUQC"


@pytest.mark.parametrize(
    "url",
    [
        "http://evil.example/?x=open.spotify.com/track/abc",
        "https://open.spotify.com.evil.example/track/abc",
        "https://open.spotify.com/album/abc",
        "file:///etc/passwd",
    ],
)
def test_track_id_rejects_other_urls(url):
    assert spotify_link.track_id(url) is None


def test_resolve_does_not_fetch_untrusted_urls(monkeypatch):
    def fail(*a, **k):
        raise AssertionError("no deberia hacer el pedido")

    monkeypatch.setattr(spotify_link.requests, "get", fail)
    assert spotify_link.resolve("http://127.0.0.1:22/open.spotify.com/track/abc") is None
