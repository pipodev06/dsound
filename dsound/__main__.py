import threading
import webbrowser

from dsound import config
from dsound.webapp import run


def main():
    url = f"http://127.0.0.1:{config.PORT}"
    print(f"dsound corriendo en {url} (Ctrl+C para cortar)")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    run()


if __name__ == "__main__":
    main()
