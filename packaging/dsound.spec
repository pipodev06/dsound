# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller. No se usa directo: correr `python packaging/build.py`,
# que baja ffmpeg y le pasa la carpeta via DSOUND_FFMPEG_DIR.
import os
import sys

from PyInstaller.utils.hooks import collect_data_files

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
FFMPEG_DIR = os.environ.get("DSOUND_FFMPEG_DIR", "")
FFMPEG_NAME = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"

datas = [(os.path.join(ROOT, "dsound", "static"), os.path.join("dsound", "static"))]
datas += collect_data_files("ytmusicapi")  # traducciones/locales que ytmusicapi lee en runtime

binaries = []
if FFMPEG_DIR:
    binaries.append((os.path.join(FFMPEG_DIR, FFMPEG_NAME), "ffmpeg"))
    license_file = os.path.join(FFMPEG_DIR, "LICENSE.txt")
    if os.path.isfile(license_file):
        datas.append((license_file, "ffmpeg"))

a = Analysis(
    [os.path.join(ROOT, "packaging", "launcher.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="dsound",
    console=True,  # la consola muestra la URL y se cierra con Ctrl+C
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="dsound", upx=False)
