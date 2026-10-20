"""Arranca el ejecutable armado y chequea que responde y que encuentra ffmpeg.

    python packaging/smoke_test.py dist/dsound/dsound[.exe]
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

PORT = 5077


def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=5) as resp:
        return resp.status, resp.read()


def main():
    exe = os.path.abspath(sys.argv[1])
    tmp = tempfile.mkdtemp(prefix="dsound-smoke-")
    env = dict(os.environ)
    env.update(
        DSOUND_PORT=str(PORT),
        DSOUND_NO_BROWSER="1",
        DSOUND_DATA_DIR=os.path.join(tmp, "data"),
        OUTPUT_DIR=os.path.join(tmp, "music"),
    )
    # sin ffmpeg del sistema en el PATH: tiene que usar el que viene incluido
    env["PATH"] = os.path.dirname(exe)
    proc = subprocess.Popen([exe], env=env, cwd=tmp)
    try:
        deadline = time.time() + 60
        while True:
            try:
                status, body = get("/api/status")
                break
            except OSError:
                if proc.poll() is not None:
                    sys.exit(f"el ejecutable termino con codigo {proc.returncode}")
                if time.time() > deadline:
                    sys.exit("el ejecutable no respondio en 60s")
                time.sleep(1)

        data = json.loads(body)
        print("status:", data)
        assert data["ffmpeg"] is True, "no encontro el ffmpeg incluido"
        status, body = get("/")
        assert status == 200 and b"<div id=\"root\">" in body, "no sirve el frontend"
        status, body = get("/api/jobs")
        assert json.loads(body) == {"jobs": []}
        print("smoke test OK")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
