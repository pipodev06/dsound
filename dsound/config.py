import os
import shutil
import sys
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "downloads")
MP3_BITRATE = os.getenv("MP3_BITRATE", "320")

# tolerancia de duracion pa matching YT vs Spotify (segundos)
DURATION_TOLERANCE_STRICT = 3
DURATION_TOLERANCE_LOOSE = 8


def require_ffmpeg():
    if shutil.which("ffmpeg") is None:
        sys.exit(
            "ffmpeg no encontrado en PATH. Instalalo: "
            "winget install Gyan.FFmpeg (reiniciar terminal despues)."
        )


def has_spotify_creds():
    return bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)
