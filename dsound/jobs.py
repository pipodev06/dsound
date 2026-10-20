import queue
import threading
import time
import uuid

from dsound import config, downloader

WORKER_COUNT = 4
PRUNE_AFTER_SECONDS = 15 * 60  # cuanto queda visible un job terminado en /api/jobs

_jobs = {}
_lock = threading.Lock()
_queue = queue.Queue()
_workers_started = False


def _worker():
    while True:
        job_id = _queue.get()
        try:
            _run_job(job_id)
        finally:
            _queue.task_done()


def _ensure_workers():
    global _workers_started
    if _workers_started:
        return
    _workers_started = True
    for _ in range(WORKER_COUNT):
        threading.Thread(target=_worker, daemon=True).start()


def _run_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        if job["cancel_event"].is_set():
            job["status"] = "cancelled"
            job["finished_at"] = time.time()
            return
        job["status"] = "downloading"

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
        )
        with _lock:
            job["status"] = "done"
            job["result"] = result
            job["finished_at"] = time.time()
    except downloader.CancelledError:
        with _lock:
            job["status"] = "cancelled"
            job["finished_at"] = time.time()
    except Exception as e:
        with _lock:
            job["status"] = "error"
            job["error"] = str(e)
            job["finished_at"] = time.time()


def _display_title(title_hint: str, artist_override, title_override) -> str:
    if title_override is not None:
        return f"{artist_override} - {title_override}" if artist_override else title_override
    return title_hint or "descarga"


def enqueue(
    webpage_url: str,
    title_hint: str = "",
    bitrate: str = None,
    artist_override: str = None,
    title_override: str = None,
    album: str = None,
    cover_url_override: str = None,
) -> str:
    _ensure_workers()
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "webpage_url": webpage_url,
            "title_hint": title_hint,
            "display": _display_title(title_hint, artist_override, title_override),
            "bitrate": bitrate,
            "artist_override": artist_override,
            "title_override": title_override,
            "album": album,
            "cover_url_override": cover_url_override,
            "status": "queued",
            "cancel_event": threading.Event(),
            "enqueued_at": time.time(),
            "finished_at": None,
        }
    _queue.put(job_id)
    return job_id


def _public(job: dict) -> dict:
    return {
        "id": job["id"],
        "status": job["status"],
        "display": job["display"],
        "album": job.get("album"),
        "result": job.get("result"),
        "error": job.get("error"),
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
    de PRUNE_AFTER_SECONDS para no crecer sin limite en memoria), mas nuevos
    primero."""
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
        return [_public(j) for j in jobs]


def find_active(webpage_url: str):
    """Devuelve el job (version publica) que ya esta en cola o bajando esa
    misma URL, o None. Evita bajar dos veces lo mismo si se pide de nuevo
    antes de que termine la primera descarga."""
    with _lock:
        for job in _jobs.values():
            if job["webpage_url"] == webpage_url and job["status"] in ("queued", "downloading"):
                return _public(job)
    return None


def cancel_job(job_id: str) -> bool:
    """Pide cancelar un job. Si todavia esta en cola, lo corta antes de arrancar
    la descarga. Si ya esta descargando, es best-effort (yt-dlp solo chequea
    el flag entre ticks de progreso, ver youtube_dl.download_audio). Devuelve
    False si el job no existe o ya termino (nada que cancelar)."""
    with _lock:
        job = _jobs.get(job_id)
        if job is None or job["status"] in ("done", "error", "cancelled"):
            return False
        job["cancel_event"].set()
        return True
