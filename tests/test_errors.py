import pytest

from dsound.errors import friendly


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ERROR: [youtube] abc: Sign in to confirm you’re not a bot. Use --cookies", "no eres un bot"),
        ("ERROR: [youtube] abc: Sign in to confirm your age", "restricción de edad"),
        ("ERROR: [youtube] abc: This video is not available", "no está disponible"),
        ("ERROR: [youtube] abc: Video unavailable", "no está disponible"),
        ("ERROR: [youtube] abc: Private video. Sign in", "privado"),
        ("HTTP Error 429: Too Many Requests", "demasiadas solicitudes"),
        ("<urlopen error [Errno 11001] getaddrinfo failed>", "conexión"),
        ("[Errno 28] No space left on device", "espacio"),
        ("ERROR: Could not copy Chrome cookie database", "cookies del navegador"),
        ("ERROR: Postprocessing: ffprobe and ffmpeg not found", "conversión a MP3"),
    ],
)
def test_known_errors(raw, expected):
    assert expected in friendly(raw)


def test_own_messages_pass_through():
    msg = "No se encontró ffmpeg. Instálalo con: winget install Gyan.FFmpeg"
    assert friendly(msg) == msg


def test_unknown_error_is_cleaned():
    assert friendly("ERROR: [youtube] abc123: algo raro pasó") == "algo raro pasó"
    assert friendly("\x1b[0;31mERROR:\x1b[0m boom") == "boom"
    assert friendly("") == "Error desconocido."
    assert len(friendly("x" * 1000)) == 300
