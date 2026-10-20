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
