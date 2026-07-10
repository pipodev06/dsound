import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from dsound.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

_URL_RE = re.compile(r"open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)")


def parse_spotify_url(url: str):
    m = _URL_RE.search(url)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def get_client():
    auth = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
    return spotipy.Spotify(client_credentials_manager=auth)


def _normalize_track(item: dict, album: dict | None = None) -> dict:
    artists = [a["name"] for a in item["artists"]]
    album_data = album or item.get("album", {})
    images = album_data.get("images", [])
    cover_url = images[0]["url"] if images else None
    return {
        "title": item["name"],
        "artists": artists,
        "primary_artist": artists[0] if artists else "",
        "album": album_data.get("name", ""),
        "track_number": item.get("track_number", 1),
        "release_date": album_data.get("release_date", ""),
        "duration_sec": item["duration_ms"] / 1000,
        "cover_url": cover_url,
        "spotify_id": item["id"],
    }


def get_track(sp: spotipy.Spotify, track_id: str) -> dict:
    item = sp.track(track_id)
    return _normalize_track(item)


def get_album_tracks(sp: spotipy.Spotify, album_id: str) -> list:
    album = sp.album(album_id)
    tracks = []
    for item in album["tracks"]["items"]:
        tracks.append(_normalize_track(item, album=album))
    return tracks


def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> list:
    tracks = []
    results = sp.playlist_items(playlist_id)
    while results:
        for entry in results["items"]:
            item = entry.get("track")
            if item and item.get("id"):
                tracks.append(_normalize_track(item))
        results = sp.next(results) if results.get("next") else None
    return tracks


def search_track(sp: spotipy.Spotify, query: str) -> dict | None:
    results = sp.search(q=query, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    if not items:
        return None
    return _normalize_track(items[0])
