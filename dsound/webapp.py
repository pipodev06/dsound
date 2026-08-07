import os

from flask import Flask, jsonify, request, send_from_directory

from dsound import albums, config, downloader, jobs, library, native, spotify_link, youtube_dl

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")


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
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502
    if not query:
        return jsonify({"error": "no se pudo leer el link de Spotify."}), 502
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
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502
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
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502
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
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502
    return jsonify({"results": results})


@app.route("/api/albums/<browse_id>")
def albums_detail(browse_id):
    try:
        album = albums.get_album(browse_id)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502
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
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502

    needed = sum(downloader.estimate_mp3_bytes(t.get("duration"), bitrate) for t in album["tracks"])
    free = config.free_space_bytes(config.OUTPUT_DIR)
    if needed > free:
        needed_mb, free_mb = needed / (1024 * 1024), free / (1024 * 1024)
        return (
            jsonify(
                {
                    "error": f"no hay espacio suficiente: el album pesaria ~{needed_mb:.0f}MB "
                    f"y solo tenes ~{free_mb:.0f}MB libres en la carpeta de salida."
                }
            ),
            507,
        )

    duplicates = []
    for t in album["tracks"]:
        existing = downloader.find_duplicate(t["artist"], t["title"], config.OUTPUT_DIR)
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
        )
        tracks.append({"title": t["title"], "artist": t["artist"], "skipped": False, "job_id": job_id})

    return jsonify({"album": album["title"], "artist": album["artist"], "tracks": tracks})


@app.route("/api/preview/<video_id>")
def preview(video_id):
    try:
        data = youtube_dl.get_stream_url(f"https://www.youtube.com/watch?v={video_id}")
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502
    if not data.get("stream_url"):
        return jsonify({"error": "no se encontro stream de audio."}), 502
    return jsonify(data)


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
    )
    return jsonify({"job_id": job_id})


@app.route("/api/jobs/<job_id>")
def job_status(job_id):
    job = jobs.get_job(job_id)
    if job is None:
        return jsonify({"error": "job no encontrado"}), 404
    return jsonify(job)


@app.route("/api/jobs")
def list_jobs():
    return jsonify({"jobs": jobs.list_jobs()})


@app.route("/api/jobs/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id):
    if not jobs.cancel_job(job_id):
        return jsonify({"error": "job no encontrado o ya termino."}), 404
    return jsonify({"ok": True})


@app.route("/api/library")
def get_library():
    return jsonify({"items": library.list_library(config.OUTPUT_DIR)})


@app.route("/library/<path:filename>")
def serve_library_file(filename):
    return send_from_directory(config.OUTPUT_DIR, filename)


@app.route("/api/library/<path:filename>", methods=["DELETE"])
def delete_library_track(filename):
    try:
        library.delete_track(config.OUTPUT_DIR, filename)
    except FileNotFoundError:
        return jsonify({"error": "archivo no encontrado."}), 404
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
        return jsonify({"error": "archivo no encontrado."}), 404
    return jsonify(result)


@app.route("/api/output-dir/pick", methods=["POST"])
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
def set_output_dir():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "falta 'path'"}), 400
    os.makedirs(path, exist_ok=True)
    config.save_output_dir(path)
    return jsonify({"output_dir": path})


def run():
    app.run(host=config.HOST, port=config.PORT, threaded=True)
