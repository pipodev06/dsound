"""Arranca el ejecutable armado y comprueba que responde, que encuentra el
ffmpeg incluido, que sirve la interfaz y que "Salir" lo cierra.

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


def get(path, method="GET"):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
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
        status, body = get("/favicon.png")
        assert status == 200 and body[:4] == b"\x89PNG", "falta el ícono"
        assert data.get("version"), "no informa la versión"

        # "Salir" (botón de la página) tiene que cerrar el proceso
        get("/api/shutdown", method="POST")
        proc.wait(timeout=20)
        print("smoke test OK (versión %s)" % data["version"])
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
