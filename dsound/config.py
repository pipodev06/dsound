import os
import shutil
from dotenv import find_dotenv, load_dotenv, set_key

_DOTENV_PATH = find_dotenv()
load_dotenv(_DOTENV_PATH)

# Carpeta "Music" del usuario (Windows la muestra como "Musica" segun el idioma,
# pero el nombre real de la carpeta es "Music").
_DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Music", "dsound")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", _DEFAULT_OUTPUT_DIR)
MP3_BITRATE = os.getenv("MP3_BITRATE", "320")
PORT = int(os.getenv("DSOUND_PORT", "5000"))


def require_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def ffmpeg_missing_message() -> str:
    return (
        "ffmpeg no encontrado en PATH. Instalalo: "
        "winget install Gyan.FFmpeg (reiniciar terminal despues)."
    )


def save_output_dir(path: str):
    """Guarda la carpeta de salida en .env para que quede para proximas sesiones."""
    global OUTPUT_DIR
    OUTPUT_DIR = path
    dotenv_path = _DOTENV_PATH or os.path.join(os.getcwd(), ".env")
    set_key(dotenv_path, "OUTPUT_DIR", path)
