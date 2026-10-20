"""Cola de descargas: N hilos que bajan en paralelo.

La cola se guarda en SQLite (ver `init`): si dsound se cierra con descargas
pendientes, al volver a abrirlo se retoman solas, y las terminadas siguen
visibles en la pestaña Descargas un rato. Sin `init` (ej. en tests) funciona
igual, solo en memoria."""

import json
import logging
import os
import queue
import sqlite3
import threading
import time
import uuid

from dsound import config, downloader, errors
from dsound.clean import parse_artist_title

log = logging.getLogger("dsound.jobs")

WORKER_COUNT = 4
PRUNE_AFTER_SECONDS = 15 * 60  # cuanto queda visible un job terminado en /api/jobs
FINISHED_STATUSES = ("done", "error", "cancelled")
ACTIVE_STATUSES = ("queued", "downloading")

# datos del pedido que se guardan en disco (lo necesario para re-ejecutarlo)
_PERSISTED_FIELDS = (
    "id",
    "webpage_url",
    "title_hint",
    "display",
    "auto_display",
    "thumbnail",
    "bitrate",
    "artist_override",
    "title_override",
    "album",
    "cover_url_override",
    "year",
    "track_number",
    "status",
    "result",
    "error",
    "enqueued_at",
    "finished_at",
)

_jobs = {}
_lock = threading.Lock()
_queue = queue.Queue()
_workers_started = False
_db = None
_db_lock = threading.Lock()


# --- persistencia -----------------------------------------------------------


def init(db_path: str):
    """Abre (o crea) la base de la cola y retoma lo que quedo pendiente: los jobs
    que estaban en cola o bajando cuando se cerro dsound vuelven a la cola."""
    global _db
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    db = sqlite3.connect(db_path, check_same_thread=False)
    db.execute(
        "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, data TEXT NOT NULL, enqueued_at REAL NOT NULL)"
    )
    db.commit()
    with _db_lock:
        _db = db

    now = time.time()
    to_resume = []
    with _db_lock:
        rows = db.execute("SELECT data FROM jobs ORDER BY enqueued_at").fetchall()
    for (raw,) in rows:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if data.get("status") in FINISHED_STATUSES:
            if data.get("finished_at") and now - data["finished_at"] > PRUNE_AFTER_SECONDS:
                _delete_saved(data["id"])
                continue
        else:
            data["status"] = "queued"
            to_resume.append(data["id"])
        data["cancel_event"] = threading.Event()
        with _lock:
            _jobs[data["id"]] = data
    for job_id in to_resume:
        _save(job_id)
        _queue.put(job_id)
    if to_resume:
        _ensure_workers()
    return len(to_resume)


def close():
    """Cierra la base (para tests)."""
    global _db
    with _db_lock:
        if _db is not None:
            _db.close()
        _db = None


def _save(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        data = {k: job.get(k) for k in _PERSISTED_FIELDS}
    with _db_lock:
        if _db is None:
            return
        _db.execute(
            "INSERT OR REPLACE INTO jobs (id, data, enqueued_at) VALUES (?, ?, ?)",
            (job_id, json.dumps(data), data["enqueued_at"]),
        )
        _db.commit()


def _delete_saved(job_id: str):
    with _db_lock:
        if _db is None:
            return
        _db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        _db.commit()


# --- workers ----------------------------------------------------------------


def _worker():
    while True:
        job_id = _queue.get()
        try:
            _run_job(job_id)
        finally:
            _queue.task_done()


def _ensure_workers():
    global _workers_started
    with _lock:
        if _workers_started:
            return
        _workers_started = True
    for _ in range(WORKER_COUNT):
        threading.Thread(target=_worker, daemon=True).start()


def _finish(job_id: str, **fields):
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        job.update(fields)
        job["finished_at"] = time.time()
    _save(job_id)


def _run_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        if job is None or job["status"] != "queued":
            return
        cancelled = job["cancel_event"].is_set()
        if not cancelled:
            job["status"] = "downloading"
            job["phase"] = "downloading"
            job["progress"] = None
    if cancelled:
        _finish(job_id, status="cancelled")
        return
    _save(job_id)

    def on_progress(phase, percent):
        with _lock:
            job["phase"] = phase
            if percent is not None:
                job["progress"] = round(percent, 1)

    def on_info(info):
        # un link pegado llega sin titulo: apenas yt-dlp lo conoce, se muestra
        with _lock:
            if job.get("auto_display") and info.get("title"):
                artist, title = parse_artist_title(info["title"])
                job["display"] = f"{artist} - {title}" if artist else title
            if not job.get("thumbnail"):
                job["thumbnail"] = info.get("thumbnail") or None
        _save(job_id)

    try:
        result = downloader.download(
            job["webpage_url"],
            config.OUTPUT_DIR,
            title_hint=job["title_hint"],
            bitrate=job.get("bitrate"),
            artist_override=job.get("artist_override"),
            title_override=job.get("title_override"),
            album=job.get("album"),
            cover_url_override=job.get("cover_url_override"),
            cancel_event=job["cancel_event"],
            year=job.get("year"),
            track_number=job.get("track_number"),
            on_progress=on_progress,
            on_info=on_info,
        )
        final_name = f"{result['artist']} - {result['title']}" if result.get("artist") else result["title"]
        _finish(
            job_id,
            status="done",
            result=result,
            progress=100.0,
            display=final_name,
            thumbnail=job.get("thumbnail") or result.get("thumbnail") or None,
        )
    except downloader.CancelledError:
        _finish(job_id, status="cancelled", **({"display": job["webpage_url"]} if job["display"] == PLACEHOLDER_DISPLAY else {}))
    except Exception as e:
        log.warning("descarga fallida %s (%s): %s", job_id, job["webpage_url"], e)
        extra = {}
        if job["display"] == PLACEHOLDER_DISPLAY:
            extra["display"] = job["webpage_url"]  # falló antes de conocer el título
        _finish(job_id, status="error", error=errors.friendly(e), **extra)


# --- API publica --------------------------------------------------------------


PLACEHOLDER_DISPLAY = "Obteniendo datos del video..."


def _display_title(title_hint: str, artist_override, title_override) -> str:
    if title_override is not None:
        return f"{artist_override} - {title_override}" if artist_override else title_override
    if title_hint:
        artist, title = parse_artist_title(title_hint)
        return f"{artist} - {title}" if artist else title
    return PLACEHOLDER_DISPLAY


def enqueue(
    webpage_url: str,
    title_hint: str = "",
    bitrate: str = None,
    artist_override: str = None,
    title_override: str = None,
    album: str = None,
    cover_url_override: str = None,
    year: str = None,
    track_number: int = None,
    thumbnail: str = None,
) -> str:
    _ensure_workers()
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "webpage_url": webpage_url,
            "title_hint": title_hint,
            "display": _display_title(title_hint, artist_override, title_override),
            # True = el nombre visible es provisional y se reemplaza con el real
            "auto_display": title_override is None,
            "thumbnail": thumbnail or cover_url_override or None,
            "bitrate": bitrate,
            "artist_override": artist_override,
            "title_override": title_override,
            "album": album,
            "cover_url_override": cover_url_override,
            "year": year,
            "track_number": track_number,
            "status": "queued",
            "cancel_event": threading.Event(),
            "enqueued_at": time.time(),
            "finished_at": None,
        }
    _save(job_id)
    _queue.put(job_id)
    return job_id


def _public(job: dict) -> dict:
    return {
        "id": job["id"],
        "status": job["status"],
        "display": job["display"],
        "thumbnail": job.get("thumbnail"),
        "album": job.get("album"),
        "result": job.get("result"),
        "error": job.get("error"),
        # avance de la descarga: phase "downloading" (progress 0-100, o None si
        # todavia no se sabe el tamaño) o "converting" (ffmpeg pasando a mp3)
        "phase": job.get("phase") if job["status"] == "downloading" else None,
        "progress": job.get("progress"),
        # datos originales del pedido, para poder reintentar sin tener que
        # volver a buscar (ver POST /api/download desde el frontend)
        "webpage_url": job["webpage_url"],
        "bitrate": job.get("bitrate"),
        "title_hint": job.get("title_hint"),
        "artist_override": job.get("artist_override"),
        "title_override": job.get("title_override"),
    }


def get_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        return _public(job) if job is not None else None


def list_jobs():
    """Todos los jobs activos + los terminados recientemente (se podan despues
    de PRUNE_AFTER_SECONDS para no crecer sin limite), mas nuevos primero."""
    now = time.time()
    with _lock:
        stale = [
            jid
            for jid, job in _jobs.items()
            if job["finished_at"] is not None and now - job["finished_at"] > PRUNE_AFTER_SECONDS
        ]
        for jid in stale:
            del _jobs[jid]
        jobs = sorted(_jobs.values(), key=lambda j: j["enqueued_at"], reverse=True)
        public = [_public(j) for j in jobs]
    for jid in stale:
        _delete_saved(jid)
    return public


def clear_finished() -> int:
    """Quita de la lista (y de disco) las descargas ya terminadas. Devuelve
    cuantas se quitaron."""
    with _lock:
        finished = [jid for jid, job in _jobs.items() if job["status"] in FINISHED_STATUSES]
        for jid in finished:
            del _jobs[jid]
    for jid in finished:
        _delete_saved(jid)
    return len(finished)


def find_active(webpage_url: str):
    """Devuelve el job (version publica) que ya esta en cola o bajando esa
    misma URL, o None. Evita bajar dos veces lo mismo si se pide de nuevo
    antes de que termine la primera descarga."""
    with _lock:
        for job in _jobs.values():
            if job["webpage_url"] == webpage_url and job["status"] in ACTIVE_STATUSES:
                return _public(job)
    return None


def cancel_job(job_id: str) -> bool:
    """Pide cancelar un job. Si todavia esta en cola, lo corta antes de arrancar
    la descarga. Si ya esta descargando, es best-effort (yt-dlp solo chequea
    el flag entre ticks de progreso, ver youtube_dl.download_audio). Devuelve
    False si el job no existe o ya termino (nada que cancelar)."""
    with _lock:
        job = _jobs.get(job_id)
        if job is None or job["status"] in FINISHED_STATUSES:
            return False
        job["cancel_event"].set()
        return True
