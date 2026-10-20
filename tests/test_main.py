import socket
import threading

import pytest

from dsound import __main__ as entry


@pytest.fixture
def busy_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    yield s.getsockname()[1]
    s.close()


@pytest.fixture
def no_side_effects(monkeypatch, tmp_path):
    calls = {"run": 0, "browser": [], "tray": 0, "quit": 0}

    def fake_run():
        calls["run"] += 1

    monkeypatch.setattr(entry.webapp, "run", fake_run)
    monkeypatch.setattr(entry.webbrowser, "open", lambda url: calls["browser"].append(url))
    monkeypatch.setattr(entry, "_quit", lambda: calls.__setitem__("quit", calls["quit"] + 1))
    monkeypatch.setattr(entry, "setup_logging", lambda: None)
    monkeypatch.setattr(entry.config, "HOST", "127.0.0.1")
    monkeypatch.setattr(entry.config, "OPEN_BROWSER", True)
    monkeypatch.setattr(entry.config, "TRAY", True)
    return calls


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_second_instance_opens_browser_and_does_not_start(busy_port, no_side_effects, monkeypatch):
    monkeypatch.setattr(entry.config, "PORT", busy_port)
    monkeypatch.setattr(entry, "_is_dsound", lambda url: True)
    assert entry.main([]) == 0
    assert no_side_effects["run"] == 0
    assert no_side_effects["browser"] == [f"http://127.0.0.1:{busy_port}"]


def test_port_taken_by_other_program(busy_port, no_side_effects, monkeypatch):
    monkeypatch.setattr(entry.config, "PORT", busy_port)
    monkeypatch.setattr(entry, "_is_dsound", lambda url: False)
    assert entry.main([]) == 1
    assert no_side_effects["run"] == 0


def test_starts_server_opens_browser_and_shows_tray(no_side_effects, monkeypatch):
    port = _free_port()
    monkeypatch.setattr(entry.config, "PORT", port)
    monkeypatch.setattr(entry, "_wait_until_up", lambda url, server, timeout=30: True)
    tray_args = {}

    def fake_tray(url, open_folder, on_quit):
        tray_args["url"] = url
        return True  # el usuario eligió "Salir"

    monkeypatch.setattr(entry.tray, "run", fake_tray)
    assert entry.main([]) == 0
    assert no_side_effects["run"] == 1
    assert no_side_effects["browser"] == [f"http://127.0.0.1:{port}"]
    assert tray_args["url"] == f"http://127.0.0.1:{port}"
    # el botón "Salir" de la página cierra todo
    assert entry.webapp.shutdown_handler is not entry.webapp._default_shutdown


def test_without_tray_waits_for_server(no_side_effects, monkeypatch):
    """Sin entorno gráfico (tray.run devuelve False) sigue funcionando como antes."""
    port = _free_port()
    monkeypatch.setattr(entry.config, "PORT", port)
    monkeypatch.setattr(entry.config, "OPEN_BROWSER", False)
    monkeypatch.setattr(entry, "_wait_until_up", lambda url, server, timeout=30: True)
    monkeypatch.setattr(entry.tray, "run", lambda *a: False)
    entry.main([])
    assert no_side_effects["run"] == 1
    assert no_side_effects["quit"] == 1  # el servidor terminó -> se cierra


def test_server_that_never_starts(no_side_effects, monkeypatch):
    monkeypatch.setattr(entry.config, "PORT", _free_port())
    monkeypatch.setattr(entry, "_wait_until_up", lambda url, server, timeout=30: False)
    assert entry.main([]) == 1
    assert no_side_effects["browser"] == []


def test_wait_until_up_stops_when_server_dies():
    dead = threading.Thread(target=lambda: None)
    dead.start()
    dead.join()
    assert entry._wait_until_up("http://127.0.0.1:1", dead, timeout=5) is False


def test_tray_falls_back_when_unavailable(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_pystray(name, *args, **kwargs):
        if name == "pystray":
            raise ImportError("sin entorno gráfico")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_pystray)
    assert entry.tray.run("http://x", lambda: None, lambda: None) is False


def test_tray_icon_file_exists():
    """El ícono de la bandeja sale del build del frontend (frontend/public/favicon.png)."""
    import os

    assert os.path.isfile(entry.tray.icon_path())


def test_background_flag_does_not_open_browser(no_side_effects, monkeypatch):
    monkeypatch.setattr(entry.config, "PORT", _free_port())
    monkeypatch.setattr(entry, "_wait_until_up", lambda url, server, timeout=30: True)
    monkeypatch.setattr(entry.tray, "run", lambda *a: True)
    assert entry.main(["--background"]) == 0
    assert no_side_effects["browser"] == []
