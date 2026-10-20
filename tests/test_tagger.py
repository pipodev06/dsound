import shutil
import subprocess

import pytest

from dsound import tagger

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10


def test_prepare_cover_keeps_jpeg_and_png():
    assert tagger.prepare_cover(JPEG) == ("image/jpeg", JPEG)
    assert tagger.prepare_cover(PNG) == ("image/png", PNG)


def test_prepare_cover_rejects_garbage():
    assert tagger.prepare_cover(b"<html>not an image</html>") is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no instalado")
def test_prepare_cover_converts_webp_to_jpeg(tmp_path):
    webp = tmp_path / "c.webp"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=red:s=32x32", "-frames:v", "1", str(webp)],
        check=True,
    )
    mime, data = tagger.prepare_cover(webp.read_bytes())
    assert mime == "image/jpeg"
    assert data.startswith(b"\xff\xd8\xff")
