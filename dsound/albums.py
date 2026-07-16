from ytmusicapi import YTMusic

_yt = None


def _client() -> YTMusic:
    global _yt
    if _yt is None:
        _yt = YTMusic()
    return _yt


def _best_thumbnail(thumbnails: list) -> str:
    if not thumbnails:
        return ""
    return max(thumbnails, key=lambda t: t.get("width", 0)).get("url", "")


def search_albums(query: str, limit: int = 20) -> list:
    raw = _client().search(query, filter="albums", limit=limit)
    results = []
    for r in raw:
        browse_id = r.get("browseId")
        if not browse_id:
            continue
        results.append(
            {
                "browse_id": browse_id,
                "title": r.get("title") or "",
                "artist": ", ".join(a.get("name", "") for a in (r.get("artists") or []) if a.get("name")),
                "year": r.get("year") or "",
                "thumbnail": _best_thumbnail(r.get("thumbnails")),
                "explicit": bool(r.get("isExplicit")),
            }
        )
    return results


def get_album(browse_id: str) -> dict:
    a = _client().get_album(browse_id)
    artist = ", ".join(x.get("name", "") for x in (a.get("artists") or []) if x.get("name"))
    tracks = []
    for t in a.get("tracks") or []:
        video_id = t.get("videoId")
        if not video_id:
            continue
        tracks.append(
            {
                "video_id": video_id,
                "title": t.get("title") or "",
                "artist": ", ".join(x.get("name", "") for x in (t.get("artists") or []) if x.get("name")) or artist,
                "duration": t.get("duration_seconds") or 0,
            }
        )
    return {
        "browse_id": browse_id,
        "title": a.get("title") or "",
        "artist": artist,
        "year": a.get("year") or "",
        "thumbnail": _best_thumbnail(a.get("thumbnails")),
        "track_count": a.get("trackCount") or len(tracks),
        "tracks": tracks,
    }
