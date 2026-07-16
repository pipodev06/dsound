import os


def pick_folder(initial_dir: str):
    """Abre el gestor de archivos nativo (Explorador en Windows, el que haya en
    Linux/Mac via Tk) para elegir carpeta. Devuelve (disponible, carpeta_elegida).
    disponible=False si no hay entorno grafico -> el llamador debe pedir la
    carpeta por otro medio."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return False, None

    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(
            initialdir=initial_dir if os.path.isdir(initial_dir) else os.path.expanduser("~"),
            title="dsound - elije carpeta de salida",
        )
        root.destroy()
    except tk.TclError:
        return False, None

    return True, (selected or None)
