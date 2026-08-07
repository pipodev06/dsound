import socket
import threading
import webbrowser

from dsound import config
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


def main():
    url = f"http://127.0.0.1:{config.PORT}"
    print(f"dsound corriendo en {url} (Ctrl+C para cortar)")
    if config.HOST == "0.0.0.0":
        print(f"tambien accesible desde otros dispositivos de tu red en: http://{_lan_ip()}:{config.PORT}")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    run()


if __name__ == "__main__":
    main()
