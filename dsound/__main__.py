import json
import logging
import logging.handlers
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

from dsound import __version__, config, tray, webapp

log = logging.getLogger("dsound")


def _lan_ip() -> str:
    """IP de este equipo en la red local, para mostrarla cuando HOST=0.0.0.0
    (no abre conexión real: es el truco estándar de UDP connect sin enviar nada)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def setup_logging():
    """Log en ~/.dsound/dsound.log (rota a 1 MB) y, si hay consola, también en
    pantalla. El .exe de Windows no tiene consola: sys.stdout es None."""
    root = logging.getLogger()
    if getattr(setup_logging, "done", False):
        return
    setup_logging.done = True
    if sys.stdout is None or sys.stderr is None:
        devnull = open(os.devnull, "w", encoding="utf-8")
        sys.stdout = sys.stdout or devnull
        sys.stderr = sys.stderr or devnull

    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            config.log_path(), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError:
        pass
    if not config.FROZEN or sys.platform != "win32":
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(console)
    for noisy in ("urllib3", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # igual que waitress: sin esto, justo después de cerrar dsound el puerto
        # queda unos segundos en TIME_WAIT (Linux/macOS) y parece "ocupado".
        # En Windows SO_REUSEADDR significa otra cosa (permite robar el puerto).
        if sys.platform != "win32":
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except OSError:
            return False
    return True


def _is_dsound(url: str) -> bool:
    """Si lo que ocupa el puerto es otro dsound (ej. doble clic dos veces al .exe)."""
    try:
        with urllib.request.urlopen(f"{url}/api/status", timeout=3) as resp:
            return "output_dir" in json.loads(resp.read())
    except (OSError, ValueError):
        return False


def _wait_until_up(url: str, server: threading.Thread, timeout: float = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline and server.is_alive():
        if _is_dsound(url):
            return True
        time.sleep(0.2)
    return False


def _quit():
    log.info("Cerrando dsound.")
    logging.shutdown()
    os._exit(0)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # --background: arranca sin abrir el navegador (inicio con Windows); queda el ícono
    open_browser = config.OPEN_BROWSER and "--background" not in argv
    setup_logging()
    config.setup_bundled_ffmpeg()
    url = f"http://127.0.0.1:{config.PORT}"

    # chequear el puerto ANTES de abrir la cola: un segundo dsound no tiene que
    # retomar (y descargar dos veces) las descargas pendientes del primero
    if not _port_free(config.HOST, config.PORT):
        if _is_dsound(url):
            log.info("dsound ya está abierto en %s: abriendo el navegador.", url)
            if open_browser:
                webbrowser.open(url)
            return 0
        log.error("El puerto %s está ocupado por otro programa. Cámbialo con DSOUND_PORT en el archivo .env.", config.PORT)
        return 1

    log.info("dsound %s se está ejecutando en %s", __version__, url)
    if config.HOST == "0.0.0.0":
        log.info("También puedes abrirlo desde otros dispositivos de tu red en: http://%s:%s", _lan_ip(), config.PORT)
        if not config.PASSWORD:
            log.warning(
                "ATENCIÓN: sin DSOUND_PASSWORD, cualquier persona en tu red puede ver, descargar y borrar "
                "tu biblioteca. Define DSOUND_PASSWORD en el archivo .env para pedir contraseña."
            )
    if not config.require_ffmpeg():
        log.warning(config.ffmpeg_missing_message())

    server = threading.Thread(target=webapp.run, name="dsound-server", daemon=True)
    server.start()
    if not _wait_until_up(url, server):
        log.error("El servidor no pudo arrancar. Revisa el log: %s", config.log_path())
        return 1
    if open_browser:
        webbrowser.open(url)

    def quit_all():
        tray.stop()
        _quit()

    webapp.shutdown_handler = quit_all

    if config.TRAY and tray.run(url, tray.open_output_folder, _quit):
        return 0  # se eligió "Salir" en el ícono

    log.info("Para cerrar dsound presiona Ctrl+C (o usa el botón Salir de la página).")
    try:
        while server.is_alive():
            server.join(timeout=1)
    except KeyboardInterrupt:
        pass
    _quit()


if __name__ == "__main__":
    sys.exit(main())
