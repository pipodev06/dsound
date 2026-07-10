from difflib import SequenceMatcher

from dsound.clean import BAD_KEYWORDS
from dsound.config import DURATION_TOLERANCE_LOOSE, DURATION_TOLERANCE_STRICT


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def score_candidate(spotify_track: dict, yt_result: dict) -> float:
    score = 0.0

    dur_diff = abs(yt_result.get("duration", 0) - spotify_track["duration_sec"])
    if dur_diff <= DURATION_TOLERANCE_STRICT:
        score += 5.0
    elif dur_diff <= DURATION_TOLERANCE_LOOSE:
        score += 2.0
    else:
        score -= dur_diff * 0.3

    channel = (yt_result.get("channel") or "").lower()
    if "topic" in channel:
        score += 4.0
    if spotify_track["primary_artist"].lower() in channel:
        score += 2.0

    title_query = f"{spotify_track['primary_artist']} {spotify_track['title']}"
    score += _similarity(title_query, yt_result.get("title", "")) * 3.0

    yt_title_lower = (yt_result.get("title") or "").lower()
    spotify_title_lower = spotify_track["title"].lower()
    for bad in BAD_KEYWORDS:
        if bad in yt_title_lower and bad not in spotify_title_lower:
            score -= 6.0

    return score


def pick_best(spotify_track: dict, yt_results: list) -> dict | None:
    if not yt_results:
        return None
    scored = [(score_candidate(spotify_track, r), r) for r in yt_results]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]
