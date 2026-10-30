from dsound import youtube_dl
from dsound.clean import channel_artist


def test_progress_percent():
    assert youtube_dl._progress_percent({"downloaded_bytes": 50, "total_bytes": 200}) == 25.0
    assert youtube_dl._progress_percent({"downloaded_bytes": 50, "total_bytes_estimate": 100}) == 50.0
    assert youtube_dl._progress_percent({"downloaded_bytes": 50}) is None
    assert youtube_dl._progress_percent({"downloaded_bytes": 500, "total_bytes": 100}) == 100.0


def test_search_results_include_cleaned_guess():
    results = youtube_dl._map_entries(
        [{"id": "x", "title": "Bad Bunny - Monaco (Official Video)", "channel": "Bad Bunny", "duration": 200}, None]
    )
    assert len(results) == 1
    assert results[0]["artist_guess"] == "Bad Bunny"
    assert results[0]["title_guess"] == "Monaco"
    assert results[0]["webpage_url"] == "https://www.youtube.com/watch?v=x"


def test_channel_artist():
    assert channel_artist("Bad Bunny - Topic") == "Bad Bunny"
    assert channel_artist("RickAstleyVEVO") == "RickAstley"
    assert channel_artist("") == ""


def test_cookies_from_browser_option(monkeypatch):
    monkeypatch.setattr(youtube_dl.config, "COOKIES_BROWSER", "")
    assert "cookiesfrombrowser" not in youtube_dl._with_cookies({})
    monkeypatch.setattr(youtube_dl.config, "COOKIES_BROWSER", "firefox")
    assert youtube_dl._with_cookies({"quiet": True}) == {"quiet": True, "cookiesfrombrowser": ("firefox",)}


def test_download_audio_reports_info_once(monkeypatch):
    calls = {"info": [], "progress": []}

    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download=True):
            hook = self.opts["progress_hooks"][0]
            info = {"title": "Artista - Tema", "thumbnail": "t"}
            hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 4, "info_dict": info})
            hook({"status": "finished", "info_dict": info})
            return info

    monkeypatch.setattr(youtube_dl.yt_dlp, "YoutubeDL", FakeYDL)
    path, info = youtube_dl.download_audio(
        "u",
        "/tmp/x",
        on_info=lambda i: calls["info"].append(i["title"]),
        on_progress=lambda phase, pct: calls["progress"].append((phase, pct)),
    )
    assert path == "/tmp/x.mp3"
    assert calls["info"] == ["Artista - Tema"]
    assert calls["progress"] == [("downloading", 25.0), ("downloading", 100.0)]
