"""Vista previa con video. YouTube manda el video y el audio por separado, así
que ffmpeg los une al vuelo sin recodificar (-c copy) y los entrega como un mp4
fragmentado que el <video> del navegador reproduce mientras llega. Como se
genera de corrido, en esta vista previa no se puede adelantar."""

import subprocess
import sys
import threading
import time

# Las URLs de googlevideo duran ~6 h; la vista previa se pide apenas se resuelve.
SOURCE_TTL_SECONDS = 30 * 60
CHUNK_BYTES = 64 * 1024

_lock = threading.Lock()
_sources = {}  # video_id -> (expira, video_url, audio_url, user_agent)
_current = None  # ffmpeg de la vista previa abierta: solo una a la vez


def remember(video_id: str, video_url: str, audio_url: str, user_agent: str = "") -> str:
    """Guarda las URLs y devuelve la ruta local que las reproduce juntas."""
    now = time.time()
    with _lock:
        for key in [k for k, src in _sources.items() if src[0] < now]:
            del _sources[key]
        _sources[video_id] = (now + SOURCE_TTL_SECONDS, video_url, audio_url, user_agent)
    return f"/api/preview/{video_id}/stream"


def _stop(proc) -> None:
    if proc.poll() is None:
        proc.kill()
    proc.stdout.close()
    proc.wait()


def stream(video_id: str):
    """Generador con el mp4 unido, o None si no hay URLs vigentes para ese video."""
    global _current
    with _lock:
        src = _sources.get(video_id)
    if not src or src[0] < time.time():
        return None
    _, video_url, audio_url, user_agent = src

    cmd = ["ffmpeg", "-loglevel", "error"]
    for url in (video_url, audio_url):
        if user_agent:
            cmd += ["-user_agent", user_agent]
        cmd += ["-i", url]
    cmd += [
        "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
        "-f", "mp4", "-movflags", "frag_keyframe+empty_moov+default_base_moof", "pipe:1",
    ]
    # sin esto, en el ejecutable sin consola cada vista previa abriría una ventana negra
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=flags)

    with _lock:
        previous, _current = _current, proc
    if previous is not None and previous.poll() is None:
        # se abrió otra vista previa sin cerrar bien la anterior: su hilo ve el
        # fin del stream y cierra lo suyo
        previous.kill()

    def body():
        global _current
        try:
            while chunk := proc.stdout.read(CHUNK_BYTES):
                yield chunk
        finally:
            _stop(proc)  # el navegador cortó (se cerró el modal) o terminó el video
            with _lock:
                if _current is proc:
                    _current = None

    return body()
