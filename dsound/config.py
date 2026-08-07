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
# 127.0.0.1 = solo esta maquina (default). 0.0.0.0 = accesible desde otros
# dispositivos de tu red (celular, etc.) — dsound no tiene login ni password,
# cualquiera en la misma red podria ver/bajar/borrar tu biblioteca. Opt-in a
# proposito via .env, nunca default.
HOST = os.getenv("DSOUND_HOST", "127.0.0.1")


def require_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def free_space_bytes(path: str) -> int:
    """Espacio libre en el disco que contiene `path` (o el home si `path`
    todavia no existe, ej. la primera vez que se usa una carpeta nueva)."""
    check_path = path if os.path.isdir(path) else os.path.expanduser("~")
    return shutil.disk_usage(check_path).free


def ffmpeg_missing_message() -> str:
    return (
        "ffmpeg no encontrado en PATH. Instalalo: "
        "winget install Gyan.FFmpeg"
    )


def save_output_dir(path: str):
    """Guarda la carpeta de salida en .env para que quede para proximas sesiones."""
    global OUTPUT_DIR
    OUTPUT_DIR = path
    dotenv_path = _DOTENV_PATH or os.path.join(os.getcwd(), ".env")
    set_key(dotenv_path, "OUTPUT_DIR", path)
