"""Arma el ejecutable de dsound para el sistema donde se corre.

    pip install -e ".[build]"
    cd frontend && npm ci && npm run build && cd ..   # solo si cambiaste el frontend
    python packaging/build.py

Resultado: dist/dsound-<version>-<plataforma>.zip con la carpeta dsound/
adentro (dsound.exe en Windows, dsound en Linux/macOS) y ffmpeg incluido.

Opciones:
  --ffmpeg-dir DIR   usar un ffmpeg ya bajado (carpeta con ffmpeg[.exe]) en vez de descargarlo
  --no-ffmpeg        no incluir ffmpeg (el usuario lo tiene que tener instalado)
"""

import argparse
import io
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(ROOT, "build")
DIST_DIR = os.path.join(ROOT, "dist")

# Builds estaticas LGPL de ffmpeg (incluyen libmp3lame, que es lo que usa dsound).
FFMPEG_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
FFMPEG_ARCHIVES = {
    ("Windows", "x64"): "ffmpeg-master-latest-win64-lgpl.zip",
    ("Linux", "x64"): "ffmpeg-master-latest-linux64-lgpl.tar.xz",
    ("Linux", "arm64"): "ffmpeg-master-latest-linuxarm64-lgpl.tar.xz",
}


def _arch() -> str:
    machine = platform.machine().lower()
    return "arm64" if machine in ("arm64", "aarch64") else "x64"


def platform_tag() -> str:
    system = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}.get(platform.system(), platform.system().lower())
    return f"{system}-{_arch()}"


def version() -> str:
    sys.path.insert(0, ROOT)
    from dsound import __version__

    return __version__


def download_ffmpeg() -> str:
    """Baja ffmpeg para esta plataforma y devuelve la carpeta con el binario."""
    key = (platform.system(), _arch())
    archive = FFMPEG_ARCHIVES.get(key)
    if not archive:
        sys.exit(f"no hay build de ffmpeg configurada para {key}; usa --ffmpeg-dir o --no-ffmpeg")
    out_dir = os.path.join(BUILD_DIR, "ffmpeg")
    exe_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    if os.path.isfile(os.path.join(out_dir, exe_name)):
        print(f"usando ffmpeg ya descargado en {out_dir}")
        return out_dir

    print(f"descargando {archive}...")
    with urllib.request.urlopen(FFMPEG_BASE + archive, timeout=300) as resp:
        data = resp.read()

    os.makedirs(out_dir, exist_ok=True)
    wanted = {f"bin/{exe_name}": exe_name, "LICENSE.txt": "LICENSE.txt"}
    if archive.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                inner = name.split("/", 1)[-1]
                if inner in wanted:
                    with open(os.path.join(out_dir, wanted[inner]), "wb") as f:
                        f.write(zf.read(name))
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tf:
            for member in tf.getmembers():
                inner = member.name.split("/", 1)[-1]
                if inner in wanted and member.isfile():
                    with open(os.path.join(out_dir, wanted[inner]), "wb") as f:
                        f.write(tf.extractfile(member).read())

    exe_path = os.path.join(out_dir, exe_name)
    if not os.path.isfile(exe_path):
        sys.exit(f"no se encontro {exe_name} dentro de {archive}")
    os.chmod(exe_path, 0o755)
    return out_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ffmpeg-dir")
    parser.add_argument("--no-ffmpeg", action="store_true")
    args = parser.parse_args()

    if not os.path.isfile(os.path.join(ROOT, "dsound", "static", "index.html")):
        sys.exit("falta el frontend compilado (dsound/static). Corre: cd frontend && npm ci && npm run build")

    env = dict(os.environ)
    if not args.no_ffmpeg:
        env["DSOUND_FFMPEG_DIR"] = os.path.abspath(args.ffmpeg_dir) if args.ffmpeg_dir else download_ffmpeg()

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            DIST_DIR,
            "--workpath",
            os.path.join(BUILD_DIR, "pyinstaller"),
            os.path.join(ROOT, "packaging", "dsound.spec"),
        ],
        check=True,
        env=env,
    )

    shutil.copy(os.path.join(ROOT, "packaging", "LEEME.txt"), os.path.join(DIST_DIR, "dsound", "LEEME.txt"))
    archive_base = os.path.join(DIST_DIR, f"dsound-{version()}-{platform_tag()}")
    archive = shutil.make_archive(archive_base, "zip", DIST_DIR, "dsound")
    print(f"\nlisto: {archive}")


if __name__ == "__main__":
    main()
