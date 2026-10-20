"""Ícono de dsound en la bandeja del sistema (junto al reloj), con un menú
para abrir dsound, abrir la carpeta de música y salir.

Es opcional: si no hay entorno gráfico o falta pystray, `run` devuelve False
y dsound sigue funcionando sin ícono."""

import logging
import os
import threading
import webbrowser

from dsound import __version__, config

log = logging.getLogger("dsound.tray")

_icon = None


def icon_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "favicon.png")


def stop():
    """Cierra el ícono (si hay uno). Lo usa el botón "Salir" de la página."""
    if _icon is not None:
        try:
            _icon.stop()
        except Exception:
            pass


def run(url: str, open_folder, on_quit) -> bool:
    """Muestra el ícono y bloquea hasta que se elige "Salir". Devuelve False
    (sin bloquear) si no se pudo mostrar."""
    global _icon
    try:
        import pystray  # falla al importar si no hay entorno gráfico (ej. Linux sin X)
        from PIL import Image

        image = Image.open(icon_path())
    except Exception as e:
        log.info("Sin ícono en la bandeja del sistema: %s", e)
        return False

    def _open(icon=None, item=None):
        webbrowser.open(url)

    def _folder(icon=None, item=None):
        # en otro hilo: abrir el Explorador no tiene que trabar el menú
        threading.Thread(target=open_folder, daemon=True).start()

    def _quit(icon, item=None):
        icon.stop()
        on_quit()

    menu = pystray.Menu(
        pystray.MenuItem("Abrir dsound", _open, default=True),
        pystray.MenuItem("Abrir carpeta de música", _folder),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", _quit),
    )
    try:
        _icon = pystray.Icon("dsound", image, f"dsound {__version__} - {url}", menu)
        _icon.run()
    except Exception as e:
        log.warning("No se pudo mostrar el ícono en la bandeja del sistema: %s", e)
        _icon = None
        return False
    return True


def open_output_folder():
    from dsound.webapp import _open_in_file_manager

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    try:
        _open_in_file_manager(config.OUTPUT_DIR)
    except OSError as e:
        log.warning("No se pudo abrir la carpeta de salida: %s", e)
