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


def test_pasted_link_gets_real_name_while_and_after_downloading(fresh_jobs, monkeypatch):
    """Un link pegado llega sin título: antes quedaba como "descarga" para siempre."""
    seen = {}

    def fake_download(url, out_dir, on_info=None, **kwargs):
        seen["before"] = jobs.get_job(job_id)["display"]
        on_info({"title": "Rick Astley - Never Gonna Give You Up (Official Video)", "thumbnail": "https://i.ytimg.com/t.jpg"})
        seen["during"] = jobs.get_job(job_id)
        return {"filename": "x.mp3", "artist": "Rick Astley", "title": "Never Gonna Give You Up", "album": "Whenever"}

    monkeypatch.setattr(jobs.downloader, "download", fake_download)
    job_id = jobs.enqueue("https://youtu.be/dQw4w9WgXcQ", title_hint="")
    jobs._run_job(job_id)

    assert seen["before"] == jobs.PLACEHOLDER_DISPLAY
    assert seen["during"]["display"] == "Rick Astley - Never Gonna Give You Up"
    assert seen["during"]["thumbnail"] == "https://i.ytimg.com/t.jpg"
    done = jobs.get_job(job_id)
    assert done["display"] == "Rick Astley - Never Gonna Give You Up"
    assert done["thumbnail"] == "https://i.ytimg.com/t.jpg"


def test_title_hint_is_cleaned_for_display(fresh_jobs):
    job_id = jobs.enqueue("https://youtu.be/a", title_hint="Bad Bunny - Monaco (Official Video)")
    assert jobs.get_job(job_id)["display"] == "Bad Bunny - Monaco"


def test_override_name_is_kept(fresh_jobs, monkeypatch):
    def fake_download(url, out_dir, on_info=None, **kwargs):
        on_info({"title": "Otro - Nombre"})
        return {"filename": "x.mp3", "artist": "Pitbull", "title": "Global Warming", "album": None}

    monkeypatch.setattr(jobs.downloader, "download", fake_download)
    job_id = jobs.enqueue("https://youtu.be/a", artist_override="Pitbull", title_override="Global Warming", thumbnail="https://i.ytimg.com/a.jpg")
    jobs._run_job(job_id)
    job = jobs.get_job(job_id)
    assert job["display"] == "Pitbull - Global Warming"
    assert job["thumbnail"] == "https://i.ytimg.com/a.jpg"


def test_errors_are_friendly(fresh_jobs, monkeypatch):
    def fake_download(*a, **k):
        raise RuntimeError("ERROR: [youtube] abc: Sign in to confirm you’re not a bot.")

    monkeypatch.setattr(jobs.downloader, "download", fake_download)
    job_id = jobs.enqueue("https://youtu.be/a")
    jobs._run_job(job_id)
    assert "no eres un bot" in jobs.get_job(job_id)["error"]


def test_clear_finished(fresh_jobs, monkeypatch):
    jobs.init(str(fresh_jobs))
    monkeypatch.setattr(jobs.downloader, "download", lambda *a, **k: {"filename": "x.mp3", "artist": "", "title": "x"})
    done = jobs.enqueue("https://youtu.be/done")
    jobs._run_job(done)
    pending = jobs.enqueue("https://youtu.be/pending")

    assert jobs.clear_finished() == 1
    assert [j["id"] for j in jobs.list_jobs()] == [pending]
    jobs.close()
    monkeypatch.setattr(jobs, "_jobs", {})
    jobs.init(str(fresh_jobs))
    assert jobs.get_job(done) is None  # también se borró de disco


def test_failed_before_title_shows_link(fresh_jobs, monkeypatch):
    def fake_download(*a, **k):
        raise RuntimeError("ERROR: [youtube] x: Video unavailable")

    monkeypatch.setattr(jobs.downloader, "download", fake_download)
    job_id = jobs.enqueue("https://youtu.be/xyz")
    jobs._run_job(job_id)
    job = jobs.get_job(job_id)
    assert job["display"] == "https://youtu.be/xyz"
    assert "no está disponible" in job["error"]
