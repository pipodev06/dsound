import datetime
import functools
import hmac
import logging
import os
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

from flask import Flask, Response, abort, jsonify, redirect, request, send_from_directory, session

from dsound import __version__, albums, config, downloader, errors, jobs, library, native, spotify_link, updates, youtube_dl
from dsound import preview as preview_stream

log = logging.getLogger("dsound.web")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

LOOPBACK_ADDRS = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}


@app.before_request
def reject_cross_site_writes():
    """Bloquea POST/PUT/DELETE que vienen de otra pagina abierta en el navegador
    (CSRF): el navegador manda el header Origin en esos pedidos, y tiene que
    ser el host de dsound o localhost (el proxy de `npm run dev` reescribe el
    Host, asi que se acepta cualquier puerto de localhost). Pedidos sin Origin
    (curl, scripts) pasan."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    origin = request.headers.get("Origin")
    if not origin:
        return None
    parsed = urlparse(origin)
    if parsed.netloc == request.host or parsed.hostname in LOCAL_HOSTNAMES:
        return None
    return jsonify({"error": "pedido de otro origen rechazado."}), 403


def _api_error(e, status=502):
    """Respuesta de error con un mensaje entendible; el detalle técnico va al log."""
    log.warning("%s %s: %s", request.method, request.path, e)
    return jsonify({"error": errors.friendly(e)}), status


def _is_local_request() -> bool:
    return request.remote_addr in LOOPBACK_ADDRS


AUTH_EXEMPT_PATHS = {"/login"}


@app.before_request
def require_login():
    """Con DSOUND_PASSWORD definida, los dispositivos de la red tienen que
    loguearse. Esta PC (localhost) entra siempre sin contraseña."""
    if not config.PASSWORD or _is_local_request() or request.path in AUTH_EXEMPT_PATHS:
        return None
    if session.get("auth") == _password_fingerprint():
        return None
    if request.path.startswith("/api/") or request.path.startswith("/library/"):
        return jsonify({"error": "Necesitas iniciar sesión.", "login": True}), 401
    return redirect("/login")


def _password_fingerprint() -> str:
    """Se guarda en la sesion en vez de un simple True: si cambias la contraseña
    en .env, las sesiones viejas dejan de valer."""
    return hmac.new(app.secret_key, config.PASSWORD.encode(), "sha256").hexdigest()


_LOGIN_PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dsound - iniciar sesión</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #0d0f12;
         color: #e6e6e6; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
  form {{ width: min(320px, calc(100vw - 32px)); display: flex; flex-direction: column; gap: 12px;
         padding: 24px; border: 1px solid #2a2f37; border-radius: 8px; background: #14171c; }}
  h1 {{ margin: 0 0 4px; font-size: 1.1rem; color: #3ddc84; }}
  input {{ padding: 10px; border-radius: 6px; border: 1px solid #2a2f37; background: #0d0f12; color: inherit;
          font: inherit; }}
  button {{ padding: 10px; border: 0; border-radius: 6px; background: #3ddc84; color: #06210f; font: inherit;
           font-weight: 700; cursor: pointer; }}
  .err {{ color: #ff6b6b; font-size: 0.85rem; margin: 0; }}
</style></head>
<body><form method="post" action="/login">
  <h1>dsound &gt;</h1>
  <label for="password">contraseña</label>
  <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
  {error}
  <button type="submit">Entrar</button>
</form></body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if not config.PASSWORD or _is_local_request():
        return redirect("/")
    error = ""
    if request.method == "POST":
        given = request.form.get("password", "")
        if hmac.compare_digest(given.encode(), config.PASSWORD.encode()):
            session.clear()
            session.permanent = True
            session["auth"] = _password_fingerprint()
            return redirect("/")
        time.sleep(1)  # frena intentos de adivinar la contraseña por fuerza bruta
        error = '<p class="err">contraseña incorrecta.</p>'
    return _LOGIN_PAGE.format(error=error), (401 if error else 200)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


def local_only(view):
    """Restringe un endpoint a pedidos hechos desde esta misma máquina: cambiar
    la carpeta de salida o los ajustes, abrir la carpeta, cerrar dsound. Con
    DSOUND_HOST=0.0.0.0, alguien en la red podría, por ejemplo, apuntar la
    carpeta a ~/.ssh y después leer o borrar archivos de ahí vía /library."""

    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if request.remote_addr not in LOOPBACK_ADDRS:
            return jsonify({"error": "Esto solo se puede hacer desde la PC donde se ejecuta dsound."}), 403
        return view(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/status")
def status():
    return jsonify(
        {
            "ffmpeg": config.require_ffmpeg(),
            "ffmpeg_message": config.ffmpeg_missing_message(),
            "output_dir": config.OUTPUT_DIR,
            "version": __version__,
            # los botones de Ajustes/Salir/Abrir carpeta solo sirven en esta PC
            "local": _is_local_request(),
        }
    )


@app.route("/api/spotify-collection")
def spotify_collection():
    url = (request.args.get("url") or "").strip()
    if not url:
        return jsonify({"error": "falta 'url'"}), 400
    try:
        collection = spotify_link.get_collection(url)
    except Exception as e:
        return _api_error(e)
    if not collection:
        return jsonify({"error": "No se pudo leer la playlist o el álbum de Spotify."}), 502
    if not collection["tracks"]:
        return jsonify({"error": "La playlist o el álbum de Spotify está vacío."}), 404
    results, missing = spotify_link.match_on_youtube(collection)
    return jsonify(
        {
            "kind": collection["kind"],
            "name": collection["name"],
            "total": len(collection["tracks"]),
            "results": results,
            "missing": missing,
        }
    )


@app.route("/api/resolve-spotify")
def resolve_spotify():
    url = (request.args.get("url") or "").strip()
    if not url:
        return jsonify({"error": "falta 'url'"}), 400
    try:
        query = spotify_link.resolve(url)
    except Exception as e:
        return _api_error(e)
    if not query:
        return jsonify({"error": "No se pudo leer el enlace de Spotify."}), 502
    return jsonify({"query": query})


SEARCH_LIMIT_CAP = 300


@app.route("/api/search")
def search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "falta 'q'"}), 400

    try:
        limit = int(request.args.get("limit") or 25)
    except ValueError:
        limit = 25
    limit = max(1, min(limit, SEARCH_LIMIT_CAP))

    try:
        results = downloader.search(query, limit=limit)
    except Exception as e:
        return _api_error(e)
    return jsonify({"results": results})


PLAYLIST_LIMIT_CAP = 100


@app.route("/api/playlist")
def playlist():
    url = (request.args.get("url") or "").strip()
    if not url:
        return jsonify({"error": "falta 'url'"}), 400

    try:
        limit = int(request.args.get("limit") or 50)
    except ValueError:
        limit = 50
    limit = max(1, min(limit, PLAYLIST_LIMIT_CAP))

    try:
        results = youtube_dl.get_playlist_videos(url, limit=limit)
    except Exception as e:
        return _api_error(e)
    return jsonify({"results": results})


ALBUM_SEARCH_LIMIT_CAP = 100


@app.route("/api/albums/search")
def albums_search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "falta 'q'"}), 400

    try:
        limit = int(request.args.get("limit") or 20)
    except ValueError:
        limit = 20
    limit = max(1, min(limit, ALBUM_SEARCH_LIMIT_CAP))

    try:
        results = albums.search_albums(query, limit=limit)
    except Exception as e:
        return _api_error(e)
    return jsonify({"results": results})


@app.route("/api/albums/<browse_id>")
def albums_detail(browse_id):
    try:
        album = albums.get_album(browse_id)
    except Exception as e:
        return _api_error(e)
    return jsonify(album)


@app.route("/api/albums/<browse_id>/download", methods=["POST"])
def albums_download(browse_id):
    data = request.get_json(silent=True) or {}
    bitrate = data.get("bitrate") or None
    duplicate_mode = data.get("duplicate_mode")  # None | "skip" | "force"

    if not config.require_ffmpeg():
        return jsonify({"error": config.ffmpeg_missing_message()}), 409

    try:
        album = albums.get_album(browse_id)
    except Exception as e:
        return _api_error(e)

    needed = sum(downloader.estimate_mp3_bytes(t.get("duration"), bitrate) for t in album["tracks"])
    free = config.free_space_bytes(config.OUTPUT_DIR)
    if needed > free:
        needed_mb, free_mb = needed / (1024 * 1024), free / (1024 * 1024)
        return (
            jsonify(
                {
                    "error": f"No hay espacio suficiente: el álbum pesaría unos {needed_mb:.0f} MB "
                    f"y solo quedan {free_mb:.0f} MB libres en la carpeta de salida."
                }
            ),
            507,
        )

    # se lee la biblioteca una sola vez para todo el album, no una vez por track
    library_items = library.list_library(config.OUTPUT_DIR)
    duplicates = []
    for t in album["tracks"]:
        existing = downloader.find_duplicate(t["artist"], t["title"], config.OUTPUT_DIR, library_items=library_items)
        if existing:
            duplicates.append({"title": t["title"], "artist": t["artist"], "existing": existing})

    if duplicates and duplicate_mode is None:
        return jsonify({"duplicate": True, "album": album["title"], "duplicates": duplicates}), 409

    tracks = []
    for t in album["tracks"]:
        existing = next(
            (d["existing"] for d in duplicates if d["title"] == t["title"] and d["artist"] == t["artist"]), None
        )
        if existing and duplicate_mode == "skip":
            tracks.append({"title": t["title"], "artist": t["artist"], "skipped": True, "existing": existing})
            continue
        job_id = jobs.enqueue(
            f"https://www.youtube.com/watch?v={t['video_id']}",
            title_hint=t["title"],
            bitrate=bitrate,
            artist_override=t["artist"],
            title_override=t["title"],
            album=album["title"],
            cover_url_override=album["thumbnail"],
            year=str(album["year"]) if album.get("year") else None,
            track_number=t.get("track_number"),
        )
        tracks.append({"title": t["title"], "artist": t["artist"], "skipped": False, "job_id": job_id})

    return jsonify({"album": album["title"], "artist": album["artist"], "tracks": tracks})


@app.route("/api/preview/<video_id>")
def preview(video_id):
    try:
        data = youtube_dl.get_stream_url(f"https://www.youtube.com/watch?v={video_id}")
    except Exception as e:
        return _api_error(e)
    if not data.get("stream_url"):
        return jsonify({"error": "No se encontró audio para este video."}), 502
    video_url, audio_url = data.pop("video_url", ""), data.pop("audio_url", "")
    user_agent = data.pop("user_agent", "")
    if video_url and audio_url and config.require_ffmpeg():
        data["stream_url"] = preview_stream.remember(video_id, video_url, audio_url, user_agent)
        data["has_video"] = True
    return jsonify(data)


@app.route("/api/preview/<video_id>/stream")
def preview_video(video_id):
    body = preview_stream.stream(video_id)
    if body is None:
        return jsonify({"error": "La vista previa expiró. Vuelve a abrirla."}), 404
    return Response(body, mimetype="video/mp4", direct_passthrough=True)


# Hosts de los que se aceptan portadas que manda el cliente (Spotify, YouTube,
# YouTube Music). El servidor descarga esa imagen: no puede ser cualquier URL.
COVER_HOST_SUFFIXES = (".scdn.co", ".spotifycdn.com", ".ytimg.com", ".googleusercontent.com", ".ggpht.com")


def _valid_cover_url(url):
    if not url:
        return None
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme == "https" and any(host.endswith(sfx) for sfx in COVER_HOST_SUFFIXES):
        return url
    return None


def _clean_track_number(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 0 < number < 1000 else None


@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json(silent=True) or {}
    webpage_url = (data.get("webpage_url") or "").strip()
    title_hint = data.get("title") or ""
    confirm = bool(data.get("confirm"))
    bitrate = data.get("bitrate") or None
    artist_override = data.get("artist_override")
    title_override = data.get("title_override")
    if not webpage_url:
        return jsonify({"error": "falta 'webpage_url'"}), 400

    if not config.require_ffmpeg():
        return jsonify({"error": config.ffmpeg_missing_message()}), 409

    if not confirm:
        active = jobs.find_active(webpage_url)
        if active:
            return jsonify({"duplicate": True, "existing": f"{active['display']} (ya esta en la cola de descargas)"}), 409
        if title_override is not None:
            artist_guess, title_guess = (artist_override or ""), title_override
        elif title_hint:
            artist_guess, title_guess = downloader.parse_artist_title(title_hint)
        else:
            artist_guess = title_guess = None
        if title_guess:
            existing = downloader.find_duplicate(artist_guess, title_guess, config.OUTPUT_DIR)
            if existing:
                return jsonify({"duplicate": True, "existing": existing}), 409

    job_id = jobs.enqueue(
        webpage_url,
        title_hint=title_hint,
        bitrate=bitrate,
        artist_override=artist_override,
        title_override=title_override,
        album=(data.get("album") or None),
        cover_url_override=_valid_cover_url(data.get("cover_url")),
        year=(str(data["year"])[:4] if data.get("year") else None),
        track_number=_clean_track_number(data.get("track_number")),
        thumbnail=_valid_cover_url(data.get("thumbnail")),
    )
    return jsonify({"job_id": job_id})


@app.route("/api/jobs/<job_id>")
def job_status(job_id):
    job = jobs.get_job(job_id)
    if job is None:
        return jsonify({"error": "Descarga no encontrada."}), 404
    return jsonify(job)


@app.route("/api/jobs")
def list_jobs():
    return jsonify({"jobs": jobs.list_jobs()})


@app.route("/api/jobs/clear", methods=["POST"])
def clear_jobs():
    return jsonify({"cleared": jobs.clear_finished()})


@app.route("/api/jobs/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id):
    if not jobs.cancel_job(job_id):
        return jsonify({"error": "La descarga no existe o ya terminó."}), 404
    return jsonify({"ok": True})


@app.route("/api/library")
def get_library():
    return jsonify({"items": library.list_library(config.OUTPUT_DIR)})


@app.route("/library/<path:filename>")
def serve_library_file(filename):
    try:
        library.track_path(config.OUTPUT_DIR, filename)
    except FileNotFoundError:
        abort(404)
    return send_from_directory(config.OUTPUT_DIR, filename)


@app.route("/api/library/<path:filename>", methods=["DELETE"])
def delete_library_track(filename):
    try:
        library.delete_track(config.OUTPUT_DIR, filename)
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado."}), 404
    return jsonify({"ok": True})


@app.route("/api/library/<path:filename>", methods=["PUT"])
def update_library_track(filename):
    data = request.get_json(silent=True) or {}
    artist = data.get("artist") or ""
    title = data.get("title") or ""
    if not title.strip():
        return jsonify({"error": "falta 'title'"}), 400
    try:
        result = library.update_track(config.OUTPUT_DIR, filename, artist, title)
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado."}), 404
    return jsonify(result)


@app.route("/api/output-dir/pick", methods=["POST"])
@local_only
def pick_output_dir():
    available, picked = native.pick_folder(config.OUTPUT_DIR)
    if not available:
        return jsonify({"available": False})
    if not picked:
        return jsonify({"available": True, "cancelled": True})
    os.makedirs(picked, exist_ok=True)
    config.save_output_dir(picked)
    return jsonify({"available": True, "output_dir": picked})


@app.route("/api/output-dir", methods=["POST"])
@local_only
def set_output_dir():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "falta 'path'"}), 400
    os.makedirs(path, exist_ok=True)
    config.save_output_dir(path)
    return jsonify({"output_dir": path})


@app.route("/api/settings")
def get_settings():
    return jsonify(
        {
            "cookies_browser": config.COOKIES_BROWSER,
            "cookie_browsers": list(config.COOKIE_BROWSERS),
            "music_metadata": config.MUSIC_METADATA,
        }
    )


@app.route("/api/settings", methods=["POST"])
@local_only
def update_settings():
    data = request.get_json(silent=True) or {}
    try:
        config.save_settings(
            cookies_browser=data.get("cookies_browser"),
            music_metadata=data.get("music_metadata"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return get_settings()


@app.route("/api/update-check")
def update_check():
    return jsonify(updates.check())


def _open_in_file_manager(path: str):
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 - abre el Explorador en esa carpeta
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


@app.route("/api/output-dir/open", methods=["POST"])
@local_only
def open_output_dir():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    try:
        _open_in_file_manager(config.OUTPUT_DIR)
    except OSError as e:
        return _api_error(e, 500)
    return jsonify({"ok": True})


# Lo reemplaza __main__ para cerrar también el ícono de la bandeja.
def _default_shutdown():
    os._exit(0)


shutdown_handler = _default_shutdown


@app.route("/api/shutdown", methods=["POST"])
@local_only
def shutdown():
    # se responde primero y se cierra un instante después
    threading.Timer(0.5, lambda: shutdown_handler()).start()
    return jsonify({"ok": True})


def configure():
    """Lo que necesita disco (clave de sesion, base de la cola). Separado de la
    importacion del modulo para que los tests no toquen ~/.dsound."""
    app.secret_key = config.secret_key()
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=30)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    return jobs.init(config.jobs_db_path())


def run():
    """Servidor de producción (waitress): sin el aviso de "development server"
    de Flask y sin una línea en la consola por cada pedido."""
    from waitress import serve

    resumed = configure()
    if resumed:
        log.info("Retomando %d descarga(s) pendiente(s) de la sesión anterior.", resumed)
    serve(app, host=config.HOST, port=config.PORT, threads=16, ident="dsound")
