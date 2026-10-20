import threading
import time

import pytest

from dsound import jobs


@pytest.fixture
def fresh_jobs(tmp_path, monkeypatch):
    """Estado de la cola limpio, sin workers reales (los tests corren los jobs a mano)."""
    monkeypatch.setattr(jobs, "_jobs", {})
    monkeypatch.setattr(jobs, "_queue", __import__("queue").Queue())
    monkeypatch.setattr(jobs, "_workers_started", True)
    yield tmp_path / "jobs.sqlite3"
    jobs.close()


def test_progress_is_reported_while_downloading(fresh_jobs, monkeypatch):
    seen = {}

    def fake_download(url, out_dir, on_progress=None, **kwargs):
        on_progress("downloading", 42.123)
        seen["mid"] = jobs.get_job(job_id)
        on_progress("converting", None)
        seen["converting"] = jobs.get_job(job_id)
        return {"filename": "a.mp3", "artist": "", "title": "a", "album": None}

    monkeypatch.setattr(jobs.downloader, "download", fake_download)
    job_id = jobs.enqueue("https://youtu.be/a", title_hint="a")
    jobs._run_job(job_id)

    assert seen["mid"]["status"] == "downloading"
    assert seen["mid"]["phase"] == "downloading" and seen["mid"]["progress"] == 42.1
    assert seen["converting"]["phase"] == "converting"
    done = jobs.get_job(job_id)
    assert done["status"] == "done" and done["progress"] == 100.0 and done["phase"] is None


def test_queue_survives_restart(fresh_jobs, monkeypatch):
    jobs.init(str(fresh_jobs))
    pending = jobs.enqueue("https://youtu.be/pending", title_hint="pendiente", album="Disco", track_number=2)
    finished = jobs.enqueue("https://youtu.be/done", title_hint="listo")
    monkeypatch.setattr(
        jobs.downloader, "download", lambda *a, **k: {"filename": "x.mp3", "artist": "", "title": "x", "album": None}
    )
    jobs._run_job(finished)
    jobs.close()

    # "reinicio": memoria vacia, se vuelve a abrir la misma base
    monkeypatch.setattr(jobs, "_jobs", {})
    new_queue = __import__("queue").Queue()
    monkeypatch.setattr(jobs, "_queue", new_queue)
    resumed = jobs.init(str(fresh_jobs))

    assert resumed == 1
    assert new_queue.get_nowait() == pending
    restored = {j["id"]: j for j in jobs.list_jobs()}
    assert restored[pending]["status"] == "queued"
    assert restored[pending]["album"] == "Disco"
    assert jobs._jobs[pending]["track_number"] == 2
    assert restored[finished]["status"] == "done"
    assert restored[finished]["result"]["filename"] == "x.mp3"


def test_interrupted_download_is_requeued(fresh_jobs, monkeypatch):
    jobs.init(str(fresh_jobs))
    job_id = jobs.enqueue("https://youtu.be/a")
    jobs._jobs[job_id]["status"] = "downloading"
    jobs._save(job_id)
    jobs.close()

    monkeypatch.setattr(jobs, "_jobs", {})
    assert jobs.init(str(fresh_jobs)) == 1
    assert jobs.get_job(job_id)["status"] == "queued"


def test_old_finished_jobs_are_pruned_on_start(fresh_jobs, monkeypatch):
    jobs.init(str(fresh_jobs))
    job_id = jobs.enqueue("https://youtu.be/a")
    jobs._jobs[job_id].update(status="done", finished_at=time.time() - jobs.PRUNE_AFTER_SECONDS - 5)
    jobs._save(job_id)
    jobs.close()

    monkeypatch.setattr(jobs, "_jobs", {})
    jobs.init(str(fresh_jobs))
    assert jobs.get_job(job_id) is None


def test_cancel_queued_job(fresh_jobs, monkeypatch):
    monkeypatch.setattr(jobs.downloader, "download", lambda *a, **k: pytest.fail("no deberia bajar"))
    job_id = jobs.enqueue("https://youtu.be/a")
    assert jobs.cancel_job(job_id)
    jobs._run_job(job_id)
    assert jobs.get_job(job_id)["status"] == "cancelled"
    assert not jobs.cancel_job(job_id)


def test_find_active(fresh_jobs):
    job_id = jobs.enqueue("https://youtu.be/a", title_hint="A - B")
    assert jobs.find_active("https://youtu.be/a")["id"] == job_id
    assert jobs.find_active("https://youtu.be/otro") is None


def test_works_without_database(fresh_jobs):
    jobs.close()
    job_id = jobs.enqueue("https://youtu.be/a")
    assert jobs.get_job(job_id)["status"] == "queued"
