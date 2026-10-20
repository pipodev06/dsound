import socket

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
def no_side_effects(monkeypatch):
    calls = {"run": 0, "browser": []}
    monkeypatch.setattr(entry, "run", lambda: calls.__setitem__("run", calls["run"] + 1))
    monkeypatch.setattr(entry.webbrowser, "open", lambda url: calls["browser"].append(url))
    monkeypatch.setattr(entry.config, "HOST", "127.0.0.1")
    monkeypatch.setattr(entry.config, "OPEN_BROWSER", True)
    return calls


def test_second_instance_opens_browser_and_does_not_start(busy_port, no_side_effects, monkeypatch):
    monkeypatch.setattr(entry.config, "PORT", busy_port)
    monkeypatch.setattr(entry, "_is_dsound", lambda url: True)
    assert entry.main() == 0
    assert no_side_effects["run"] == 0
    assert no_side_effects["browser"] == [f"http://127.0.0.1:{busy_port}"]


def test_port_taken_by_other_program(busy_port, no_side_effects, monkeypatch):
    monkeypatch.setattr(entry.config, "PORT", busy_port)
    monkeypatch.setattr(entry, "_is_dsound", lambda url: False)
    assert entry.main() == 1
    assert no_side_effects["run"] == 0


def test_free_port_starts_server(no_side_effects, monkeypatch):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    monkeypatch.setattr(entry.config, "PORT", port)
    monkeypatch.setattr(entry.config, "OPEN_BROWSER", False)
    entry.main()
    assert no_side_effects["run"] == 1
