import queue
import threading
import uuid

from dsound import config, downloader

WORKER_COUNT = 4

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
        )
        with _lock:
            job["status"] = "done"
            job["result"] = result
    except Exception as e:
        with _lock:
            job["status"] = "error"
            job["error"] = str(e)


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
            "bitrate": bitrate,
            "artist_override": artist_override,
            "title_override": title_override,
            "album": album,
            "cover_url_override": cover_url_override,
            "status": "queued",
        }
    _queue.put(job_id)
    return job_id


def get_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job is not None else None
