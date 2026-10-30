import pytest

from dsound import updates


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    monkeypatch.setattr(updates, "_cache", {"at": 0.0, "data": None})
    monkeypatch.setattr(updates.config, "UPDATE_CHECK", True)


def test_parse_version():
    assert updates.parse_version("v0.3.1") == (0, 3, 1)
    assert updates.parse_version("0.10") == (0, 10, 0)
    assert updates.parse_version("latest") is None
    assert updates.parse_version("v1.0.0") > updates.parse_version("v0.10.9")


def test_update_available(monkeypatch):
    monkeypatch.setattr(updates, "__version__", "0.3.0")
    monkeypatch.setattr(updates, "_fetch_latest", lambda: {"tag": "v0.3.1", "url": "https://github.com/x/releases/v0.3.1"})
    info = updates.check()
    assert info == {
        "current": "0.3.0",
        "latest": "0.3.1",
        "url": "https://github.com/x/releases/v0.3.1",
        "update_available": True,
    }


def test_same_or_older_version(monkeypatch):
    monkeypatch.setattr(updates, "__version__", "0.3.0")
    monkeypatch.setattr(updates, "_fetch_latest", lambda: {"tag": "v0.3.0", "url": "u"})
    assert updates.check()["update_available"] is False


def test_result_is_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(updates, "_fetch_latest", lambda: calls.append(1) or {"tag": "v9.0.0", "url": "u"})
    updates.check()
    updates.check()
    assert len(calls) == 1
    updates.check(force=True)
    assert len(calls) == 2


def test_errors_are_ignored(monkeypatch):
    def boom():
        raise OSError("sin internet")

    monkeypatch.setattr(updates, "_fetch_latest", boom)
    assert updates.check()["update_available"] is False


def test_can_be_disabled(monkeypatch):
    monkeypatch.setattr(updates.config, "UPDATE_CHECK", False)
    monkeypatch.setattr(updates, "_fetch_latest", lambda: pytest.fail("no debería consultar"))
    assert updates.check()["latest"] is None
