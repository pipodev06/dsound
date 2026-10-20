import json
import socket
import sys
import threading
import urllib.request
import webbrowser

from dsound import __version__, config
from dsound.webapp import run


def _lan_ip() -> str:
    """IP de este equipo en la red local, para mostrarla cuando HOST=0.0.0.0
    (no abre conexion real, es el truco estandar de UDP connect sin enviar nada)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
        except OSError:
            return False
    return True


def _is_dsound(url: str) -> bool:
    """Si lo que ocupa el puerto es otro dsound (ej. doble click dos veces al .exe)."""
    try:
        with urllib.request.urlopen(f"{url}/api/status", timeout=3) as resp:
            return "output_dir" in json.loads(resp.read())
    except (OSError, ValueError):
        return False


def main():
    config.setup_bundled_ffmpeg()
    url = f"http://127.0.0.1:{config.PORT}"

    # chequear el puerto ANTES de abrir la cola: un segundo dsound no tiene que
    # retomar (y bajar dos veces) las descargas pendientes del primero
    if not _port_free(config.HOST, config.PORT):
        if _is_dsound(url):
            print(f"dsound ya esta abierto en {url}: abriendo el navegador.")
            if config.OPEN_BROWSER:
                webbrowser.open(url)
            return 0
        print(f"el puerto {config.PORT} esta ocupado por otro programa. Cambialo con DSOUND_PORT en el .env.")
        return 1

    print(f"dsound {__version__} corriendo en {url} (Ctrl+C para cortar)")
    if config.HOST == "0.0.0.0":
        print(f"tambien accesible desde otros dispositivos de tu red en: http://{_lan_ip()}:{config.PORT}")
        if not config.PASSWORD:
            print(
                "OJO: sin DSOUND_PASSWORD, cualquiera en tu red puede ver, bajar y borrar tu "
                "biblioteca. Defini DSOUND_PASSWORD en el .env para pedir contraseña."
            )
    if not config.require_ffmpeg():
        print(config.ffmpeg_missing_message())
    if config.OPEN_BROWSER:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    run()


if __name__ == "__main__":
    sys.exit(main())
