import pytest

from dsound import jobs, webapp

LAN = {"REMOTE_ADDR": "192.168.1.50"}


@pytest.fixture
def client(out_dir, monkeypatch):
    webapp.app.config["TESTING"] = True
    webapp.app.secret_key = b"k" * 32
    monkeypatch.setattr(webapp.config, "PASSWORD", "")
    return webapp.app.test_client()


@pytest.fixture
def enqueued(monkeypatch):
    """Captura lo que se manda a la cola sin bajar nada."""
    calls = []
    monkeypatch.setattr(webapp.config, "require_ffmpeg", lambda: True)
    monkeypatch.setattr(jobs, "find_active", lambda url: None)
    monkeypatch.setattr(jobs, "enqueue", lambda url, **kw: calls.append((url, kw)) or f"job{len(calls)}")
    return calls


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


# --- contraseña (DSOUND_PASSWORD) ---------------------------------------------


@pytest.fixture
def with_password(client, monkeypatch):
    monkeypatch.setattr(webapp.config, "PASSWORD", "clave123")
    return client


def test_localhost_never_needs_password(with_password):
    assert with_password.get("/api/library").status_code == 200


def test_lan_needs_login(with_password):
    res = with_password.get("/api/library", environ_base=LAN)
    assert res.status_code == 401 and res.get_json()["login"] is True
    assert with_password.get("/library/a.mp3", environ_base=LAN).status_code == 401
    res = with_password.get("/", environ_base=LAN)
    assert res.status_code == 302 and res.headers["Location"].endswith("/login")


def test_lan_login_flow(with_password, monkeypatch):
    monkeypatch.setattr(webapp.time, "sleep", lambda s: None)
    bad = with_password.post("/login", data={"password": "nope"}, environ_base=LAN)
    assert bad.status_code == 401
    assert with_password.get("/api/library", environ_base=LAN).status_code == 401

    ok = with_password.post("/login", data={"password": "clave123"}, environ_base=LAN)
    assert ok.status_code == 302
    assert with_password.get("/api/library", environ_base=LAN).status_code == 200

    # cambiar la contraseña invalida las sesiones existentes
    monkeypatch.setattr(webapp.config, "PASSWORD", "otra")
    assert with_password.get("/api/library", environ_base=LAN).status_code == 401


def test_login_page_renders(with_password):
    res = with_password.get("/login", environ_base=LAN)
    assert res.status_code == 200 and b'type="password"' in res.data


def test_no_password_means_open_lan(client):
    assert client.get("/api/library", environ_base=LAN).status_code == 200


# --- descargas con datos fijados (Spotify / albumes) -----------------------------


def test_download_passes_preset_tags(client, enqueued):
    res = client.post(
        "/api/download",
        json={
            "webpage_url": "https://youtu.be/q",
            "title": "x",
            "artist_override": "Pitbull",
            "title_override": "Global Warming",
            "album": "Global Warming",
            "cover_url": "https://image-cdn-fa.spotifycdn.com/image/big",
            "year": "2012-11-16",
            "track_number": "1",
            "confirm": True,
        },
    )
    assert res.status_code == 200
    _, kw = enqueued[0]
    assert kw["album"] == "Global Warming"
    assert kw["cover_url_override"] == "https://image-cdn-fa.spotifycdn.com/image/big"
    assert kw["year"] == "2012" and kw["track_number"] == 1


@pytest.mark.parametrize(
    "cover",
    ["http://i.ytimg.com/a.jpg", "https://evil.example/a.jpg", "https://i.ytimg.com.evil.example/a.jpg", "file:///etc/passwd"],
)
def test_download_ignores_untrusted_cover_urls(client, enqueued, cover):
    client.post("/api/download", json={"webpage_url": "https://youtu.be/q", "cover_url": cover, "confirm": True})
    assert enqueued[0][1]["cover_url_override"] is None


def test_spotify_collection_endpoint(client, monkeypatch):
    collection = {"kind": "playlist", "name": "Mix", "tracks": [{"title": "a", "artist": "b", "duration": 1}]}
    monkeypatch.setattr(webapp.spotify_link, "get_collection", lambda url: collection)
    monkeypatch.setattr(webapp.spotify_link, "match_on_youtube", lambda c: ([{"id": "x"}], ["b - c"]))
    data = client.get("/api/spotify-collection?url=https://open.spotify.com/playlist/abc").get_json()
    assert data == {"kind": "playlist", "name": "Mix", "total": 1, "results": [{"id": "x"}], "missing": ["b - c"]}


def test_spotify_collection_bad_link(client):
    res = client.get("/api/spotify-collection?url=https://evil.example/playlist/abc")
    assert res.status_code == 502


def test_album_download_sends_year_and_track_numbers(client, enqueued, monkeypatch):
    album = {
        "title": "Disco",
        "artist": "A",
        "year": "1999",
        "thumbnail": "https://lh3.googleusercontent.com/c",
        "tracks": [
            {"video_id": "v1", "title": "Uno", "artist": "A", "duration": 100, "track_number": 1},
            {"video_id": "v2", "title": "Dos", "artist": "A", "duration": 100, "track_number": 2},
        ],
    }
    monkeypatch.setattr(webapp.albums, "get_album", lambda browse_id: album)
    res = client.post("/api/albums/xyz/download", json={})
    assert res.status_code == 200
    assert [(kw["track_number"], kw["year"], kw["album"]) for _, kw in enqueued] == [(1, "1999", "Disco"), (2, "1999", "Disco")]


# --- ajustes, versión, abrir carpeta, cerrar -----------------------------------


@pytest.fixture
def saved_env(monkeypatch):
    saved = {}
    monkeypatch.setattr(webapp.config, "_save_env", lambda k, v: saved.__setitem__(k, v))
    monkeypatch.setattr(webapp.config, "COOKIES_BROWSER", "")
    monkeypatch.setattr(webapp.config, "MUSIC_METADATA", True)
    return saved


def test_status_reports_version_and_local(client):
    assert client.get("/api/status").get_json()["local"] is True
    data = client.get("/api/status", environ_base=LAN).get_json()
    assert data["local"] is False and data["version"] == webapp.__version__


def test_settings_roundtrip(client, saved_env):
    assert client.get("/api/settings").get_json()["cookies_browser"] == ""
    res = client.post("/api/settings", json={"cookies_browser": "Firefox", "music_metadata": False})
    assert res.status_code == 200
    assert res.get_json()["cookies_browser"] == "firefox"
    assert res.get_json()["music_metadata"] is False
    assert saved_env == {"DSOUND_COOKIES_BROWSER": "firefox", "DSOUND_MUSIC_METADATA": "0"}


def test_settings_rejects_unknown_browser(client, saved_env):
    assert client.post("/api/settings", json={"cookies_browser": "netscape"}).status_code == 400
    assert saved_env == {}


def test_settings_only_from_this_pc(client, saved_env):
    assert client.post("/api/settings", json={"cookies_browser": "firefox"}, environ_base=LAN).status_code == 403
    assert client.get("/api/settings", environ_base=LAN).status_code == 200


def test_update_check_endpoint(client, monkeypatch):
    monkeypatch.setattr(webapp.updates, "check", lambda: {"current": "0.3.0", "latest": "0.3.1", "url": "u", "update_available": True})
    assert client.get("/api/update-check").get_json()["update_available"] is True


def test_open_output_dir(client, out_dir, monkeypatch):
    opened = []
    monkeypatch.setattr(webapp, "_open_in_file_manager", opened.append)
    assert client.post("/api/output-dir/open").status_code == 200
    assert opened == [str(out_dir)]
    assert client.post("/api/output-dir/open", environ_base=LAN).status_code == 403
    assert len(opened) == 1


def test_shutdown(client, monkeypatch):
    calls = []
    monkeypatch.setattr(webapp, "shutdown_handler", lambda: calls.append(1))

    class InstantTimer:
        def __init__(self, delay, fn):
            self.fn = fn

        def start(self):
            self.fn()

    monkeypatch.setattr(webapp.threading, "Timer", InstantTimer)
    assert client.post("/api/shutdown", environ_base=LAN).status_code == 403
    assert calls == []
    assert client.post("/api/shutdown").status_code == 200
    assert calls == [1]


def test_shutdown_blocked_from_other_sites(client, monkeypatch):
    monkeypatch.setattr(webapp, "shutdown_handler", lambda: pytest.fail("no debería cerrar"))
    assert client.post("/api/shutdown", headers={"Origin": "https://evil.example"}).status_code == 403


def test_clear_jobs_endpoint(client, monkeypatch):
    monkeypatch.setattr(jobs, "clear_finished", lambda: 3)
    assert client.post("/api/jobs/clear").get_json() == {"cleared": 3}


def test_download_passes_thumbnail(client, enqueued):
    client.post("/api/download", json={"webpage_url": "https://youtu.be/q", "thumbnail": "https://i.ytimg.com/vi/q/hq.jpg", "confirm": True})
    client.post("/api/download", json={"webpage_url": "https://youtu.be/r", "thumbnail": "https://evil.example/x.jpg", "confirm": True})
    assert enqueued[0][1]["thumbnail"] == "https://i.ytimg.com/vi/q/hq.jpg"
    assert enqueued[1][1]["thumbnail"] is None


def test_api_errors_are_friendly(client, monkeypatch):
    def boom(q, limit=25):
        raise RuntimeError("ERROR: [youtube] x: HTTP Error 429: Too Many Requests")

    monkeypatch.setattr(webapp.downloader, "search", boom)
    res = client.get("/api/search?q=algo")
    assert res.status_code == 502
    assert "demasiadas solicitudes" in res.get_json()["error"]
