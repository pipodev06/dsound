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


def _embed_html(entity):
    import json

    data = {"props": {"pageProps": {"state": {"data": {"entity": entity}}}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></html>'


ALBUM_ENTITY = {
    "name": "Global Warming",
    "subtitle": "Pitbull",
    "releaseDate": {"isoString": "2012-11-16T00:00:00Z"},
    "visualIdentity": {
        "image": [
            {"url": "https://image-cdn-fa.spotifycdn.com/image/small", "maxWidth": 64},
            {"url": "https://image-cdn-fa.spotifycdn.com/image/big", "maxWidth": 640},
        ]
    },
    "trackList": [
        {"title": "Global Warming (feat. Sensato)", "subtitle": "Pitbull,\xa0Sensato", "duration": 85400},
        {"title": "Don't Stop the Party", "subtitle": "Pitbull", "duration": 206120},
        {"title": "", "subtitle": "x", "duration": 1},
    ],
}


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=x", ("playlist", "37i9dQZF1DXcBWIGoYBM5M")),
        ("https://open.spotify.com/intl-es/album/4aawyAB9vmqN3uQ7FjRGTy", ("album", "4aawyAB9vmqN3uQ7FjRGTy")),
        ("https://open.spotify.com/artist/abc", None),
    ],
)
def test_parse_link(url, expected):
    assert spotify_link.parse_link(url) == expected


def test_parse_embed_page_album():
    c = spotify_link.parse_embed_page("album", _embed_html(ALBUM_ENTITY))
    assert c["name"] == "Global Warming" and c["artist"] == "Pitbull" and c["year"] == "2012"
    assert c["cover"] == "https://image-cdn-fa.spotifycdn.com/image/big"
    assert c["tracks"] == [
        {"title": "Global Warming (feat. Sensato)", "artist": "Pitbull, Sensato", "duration": 85},
        {"title": "Don't Stop the Party", "artist": "Pitbull", "duration": 206},
    ]


def test_parse_embed_page_invalid():
    assert spotify_link.parse_embed_page("album", "<html>sin datos</html>") is None


def test_match_on_youtube_presets_tags(monkeypatch):
    collection = spotify_link.parse_embed_page("album", _embed_html(ALBUM_ENTITY))
    queries = []

    def fake_search(query, limit=3):
        queries.append(query)
        if "Global Warming" in query:
            return [
                {"id": "long", "title": "GW (1 hour)", "duration": 3600, "webpage_url": "u1"},
                {"id": "gw", "title": "Pitbull - Global Warming", "duration": 87, "webpage_url": "u2"},
            ]
        return []

    monkeypatch.setattr(spotify_link.youtube_dl, "search_youtube", fake_search)
    results, missing = spotify_link.match_on_youtube(collection)

    assert [r["id"] for r in results] == ["gw"]  # descarta la version de 1 hora
    assert results[0]["preset"] == {
        "artist": "Pitbull, Sensato",
        "title": "Global Warming (feat. Sensato)",
        "album": "Global Warming",
        "cover_url": "https://image-cdn-fa.spotifycdn.com/image/big",
        "year": "2012",
        "track_number": 1,
    }
    assert results[0]["title_guess"] == "Global Warming (feat. Sensato)"
    assert missing == ["Pitbull - Don't Stop the Party"]
    assert "Pitbull, Sensato - Global Warming (feat. Sensato)" in queries


def test_playlist_does_not_force_album_tags(monkeypatch):
    collection = spotify_link.parse_embed_page("playlist", _embed_html(dict(ALBUM_ENTITY, name="Mix")))
    monkeypatch.setattr(
        spotify_link.youtube_dl,
        "search_youtube",
        lambda q, limit=3: [{"id": q, "title": q, "duration": 0, "webpage_url": q}],
    )
    results, _ = spotify_link.match_on_youtube(collection)
    assert results[0]["preset"]["album"] is None and results[0]["preset"]["track_number"] is None


def test_resolve_does_not_fetch_untrusted_urls(monkeypatch):
    def fail(*a, **k):
        raise AssertionError("no deberia hacer el pedido")

    monkeypatch.setattr(spotify_link.requests, "get", fail)
    assert spotify_link.resolve("http://127.0.0.1:22/open.spotify.com/track/abc") is None


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_get_collection_album_reads_year_from_album_page(monkeypatch):
    entity = dict(ALBUM_ENTITY, releaseDate=None)
    pages = {
        "https://open.spotify.com/embed/album/4aaw": _embed_html(entity),
        "https://open.spotify.com/album/4aaw": '<meta name="music:release_date" content="2012-11-16">',
    }
    monkeypatch.setattr(spotify_link.requests, "get", lambda url, **kw: FakeResponse(pages[url]))
    c = spotify_link.get_collection("https://open.spotify.com/album/4aaw")
    assert c["year"] == "2012" and len(c["tracks"]) == 2


def test_get_collection_rejects_track_links(monkeypatch):
    monkeypatch.setattr(spotify_link.requests, "get", lambda *a, **k: pytest.fail("no deberia pedir nada"))
    assert spotify_link.get_collection("https://open.spotify.com/track/abc") is None
