import pytest

from dsound import jobs, webapp

LAN = {"REMOTE_ADDR": "192.168.1.50"}


@pytest.fixture
def client(out_dir):
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


def test_output_dir_change_blocked_from_lan(client, out_dir, tmp_path_factory):
    target = tmp_path_factory.mktemp("elsewhere")
    res = client.post("/api/output-dir", json={"path": str(target)}, environ_base=LAN)
    assert res.status_code == 403
    assert webapp.config.OUTPUT_DIR == str(out_dir)
    assert client.post("/api/output-dir/pick", environ_base=LAN).status_code == 403


def test_output_dir_change_allowed_from_localhost(client, tmp_path_factory):
    target = tmp_path_factory.mktemp("elsewhere")
    res = client.post("/api/output-dir", json={"path": str(target)})
    assert res.status_code == 200
    assert webapp.config.OUTPUT_DIR == str(target)


def test_library_serves_only_mp3(client, out_dir):
    (out_dir / "a - b.mp3").write_bytes(b"ID3")
    (out_dir / "secret.txt").write_text("x")
    assert client.get("/library/a%20-%20b.mp3").status_code == 200
    assert client.get("/library/secret.txt").status_code == 404


def test_library_delete_refuses_non_mp3(client, out_dir):
    f = out_dir / "secret.txt"
    f.write_text("x")
    assert client.delete("/api/library/secret.txt").status_code == 404
    assert f.exists()


def test_cross_origin_writes_rejected(client):
    res = client.post("/api/jobs/x/cancel", headers={"Origin": "https://evil.example"})
    assert res.status_code == 403
    res = client.post("/api/jobs/x/cancel", headers={"Origin": "http://localhost"})
    assert res.status_code == 404  # mismo origen: pasa el filtro, el job no existe
    # `npm run dev`: Vite proxea desde otro puerto de localhost
    res = client.post("/api/jobs/x/cancel", headers={"Origin": "http://localhost:5173"})
    assert res.status_code == 404


def test_download_rejects_url_already_in_queue(client, monkeypatch):
    monkeypatch.setattr(webapp.config, "require_ffmpeg", lambda: True)
    monkeypatch.setattr(
        jobs, "find_active", lambda url: {"display": "Artista - Tema"} if url == "https://youtu.be/q" else None
    )
    res = client.post("/api/download", json={"webpage_url": "https://youtu.be/q", "title": "Artista - Tema"})
    assert res.status_code == 409
    assert "cola" in res.get_json()["existing"]
