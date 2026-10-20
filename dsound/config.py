import os
import shutil
import sys

from dotenv import find_dotenv, load_dotenv, set_key

# Ejecutable armado con PyInstaller (dsound.exe): el .env va al lado del
# ejecutable, no adentro de la carpeta temporal donde PyInstaller extrae el codigo.
FROZEN = bool(getattr(sys, "frozen", False))
APP_DIR = os.path.dirname(sys.executable) if FROZEN else os.getcwd()

_DOTENV_PATH = os.path.join(APP_DIR, ".env") if FROZEN else find_dotenv()
load_dotenv(_DOTENV_PATH)


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


# Carpeta "Music" del usuario (Windows la muestra como "Musica" segun el idioma,
# pero el nombre real de la carpeta es "Music").
_DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Music", "dsound")
OUTPUT_DIR = os.getenv("OUTPUT_DIR") or _DEFAULT_OUTPUT_DIR
MP3_BITRATE = os.getenv("MP3_BITRATE", "320")
PORT = int(os.getenv("DSOUND_PORT", "5000"))
# 127.0.0.1 = solo esta maquina (default). 0.0.0.0 = accesible desde otros
# dispositivos de tu red (celular, etc.). Opt-in a proposito via .env, nunca
# default. Combinarlo con DSOUND_PASSWORD.
HOST = os.getenv("DSOUND_HOST", "127.0.0.1")
# Si esta definida, los dispositivos de la red tienen que loguearse con esta
# contraseña. Esta PC (localhost) nunca la necesita.
PASSWORD = os.getenv("DSOUND_PASSWORD", "")
# Datos internos de dsound (cola de descargas, clave de sesion).
DATA_DIR = os.getenv("DSOUND_DATA_DIR") or os.path.join(os.path.expanduser("~"), ".dsound")
# Buscar artista/titulo/album "oficiales" en YouTube Music al bajar un tema suelto.
MUSIC_METADATA = _env_flag("DSOUND_MUSIC_METADATA", True)
OPEN_BROWSER = not _env_flag("DSOUND_NO_BROWSER", False)


def setup_bundled_ffmpeg():
    """En el ejecutable, ffmpeg viene incluido en la carpeta `ffmpeg/` junto al
    codigo: se pone primero en el PATH para que yt-dlp y el tagger lo usen."""
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return
    bundled = os.path.join(base, "ffmpeg")
    if os.path.isdir(bundled):
        os.environ["PATH"] = bundled + os.pathsep + os.environ.get("PATH", "")


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


def jobs_db_path() -> str:
    return os.path.join(DATA_DIR, "jobs.sqlite3")


def secret_key() -> bytes:
    """Clave para firmar la cookie de sesion. Se guarda en DATA_DIR para que el
    login sobreviva a reinicios de dsound."""
    path = os.path.join(DATA_DIR, "secret_key")
    try:
        with open(path, "rb") as f:
            key = f.read()
        if len(key) >= 32:
            return key
    except OSError:
        pass
    key = os.urandom(32)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "wb") as f:
        f.write(key)
    return key


def save_output_dir(path: str):
    """Guarda la carpeta de salida en .env para que quede para proximas sesiones."""
    global OUTPUT_DIR
    OUTPUT_DIR = path
    dotenv_path = _DOTENV_PATH or os.path.join(os.getcwd(), ".env")
    set_key(dotenv_path, "OUTPUT_DIR", path)
