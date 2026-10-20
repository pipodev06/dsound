import pytest

from dsound import library


def test_track_path_accepts_mp3(tmp_path):
    (tmp_path / "a - b.mp3").write_bytes(b"")
    assert library.track_path(str(tmp_path), "a - b.mp3") == str(tmp_path / "a - b.mp3")


@pytest.mark.parametrize("name", ["secret.txt", "../a - b.mp3", "sub/a - b.mp3", ".env"])
def test_track_path_rejects_non_mp3_or_nested(tmp_path, name):
    (tmp_path / "secret.txt").write_text("x")
    (tmp_path / ".env").write_text("x")
    with pytest.raises(FileNotFoundError):
        library.track_path(str(tmp_path), name)


def test_delete_track_refuses_other_files(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("x")
    with pytest.raises(FileNotFoundError):
        library.delete_track(str(tmp_path), "notes.txt")
    assert f.exists()
