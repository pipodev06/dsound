from dsound.clean import build_filename, sanitize_filename, strip_junk, unique_path
from dsound.downloader import parse_artist_title


def test_strip_junk_removes_common_suffixes():
    assert strip_junk("Song (Official Music Video)") == "Song"
    assert strip_junk("Song (Lyrics) | Label") == "Song"
    assert strip_junk("Artist - Song (Official Audio) HD") == "Artist - Song"


def test_parse_artist_title_splits_on_dash():
    assert parse_artist_title("Bad Bunny - Titi Me Pregunto (Official Video)") == ("Bad Bunny", "Titi Me Pregunto")


def test_parse_artist_title_without_separator():
    assert parse_artist_title("Solo un titulo") == ("", "Solo un titulo")
    assert parse_artist_title("(Official Video)") == ("", "audio")


def test_sanitize_filename_removes_windows_invalid_chars():
    assert sanitize_filename('a<b>c:d"e/f\\g|h?i*j.') == "abcdefghij"
    assert len(sanitize_filename("x" * 500)) == 180


def test_build_filename():
    assert build_filename("Artist", "Song: Remix") == "Artist - Song Remix.mp3"


def test_unique_path(tmp_path):
    p = tmp_path / "a.mp3"
    assert unique_path(str(p)) == str(p)
    p.write_bytes(b"")
    assert unique_path(str(p)) == str(tmp_path / "a (2).mp3")


def test_strip_junk_removes_whole_bracket_group():
    title = "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)"
    assert strip_junk(title) == "Rick Astley - Never Gonna Give You Up"
    assert strip_junk("Song [Official HD Video]") == "Song"
    assert strip_junk("Song [Monstercat Release]") == "Song"


def test_strip_junk_keeps_meaningful_groups():
    assert strip_junk("Song (feat. X) [Official Video]") == "Song (feat. X)"
    assert strip_junk("Song (2011 Remaster)") == "Song (2011 Remaster)"


def test_strip_junk_does_not_eat_parts_of_words():
    assert strip_junk("Mvula - Song") == "Mvula - Song"
    assert strip_junk("Lyrical Lemonade - Hold Me") == "Lyrical Lemonade - Hold Me"
    assert strip_junk("Video Killed the Radio Star") == "Video Killed the Radio Star"
