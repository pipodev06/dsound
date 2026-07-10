import argparse
import os
import sys

from tqdm import tqdm

from dsound import spotify_client as sp_client
from dsound.clean import build_filename, strip_junk
from dsound.config import OUTPUT_DIR, has_spotify_creds, require_ffmpeg
from dsound.matcher import pick_best
from dsound.tagger import tag_mp3
from dsound.youtube_dl import download_audio, search_youtube

YOUTUBE_HOST_RE = ("youtube.com", "youtu.be")


class DownloadError(Exception):
    pass


def download_spotify_track(sp, track: dict, out_dir: str):
    query = f"{track['primary_artist']} {track['title']} audio"
    results = search_youtube(query, limit=5)
    best = pick_best(track, results)
    if not best:
        print(f"  [SKIP] sin match en YouTube: {track['primary_artist']} - {track['title']}")
        return

    filename = build_filename(track["primary_artist"], track["title"])
    final_path = os.path.join(out_dir, filename)
    tmp_path_no_ext = os.path.join(out_dir, "._tmp_" + os.path.splitext(filename)[0])

    mp3_path = download_audio(best["webpage_url"], tmp_path_no_ext)
    tag_mp3(mp3_path, track)
    os.replace(mp3_path, final_path)
    print(f"  [OK] {filename}")


def download_youtube_direct(url: str, out_dir: str):
    tmp_path_no_ext = os.path.join(out_dir, "._tmp_direct")
    mp3_path = download_audio(url, tmp_path_no_ext)

    raw_title = os.path.splitext(os.path.basename(mp3_path))[0].replace("._tmp_direct", "")
    cleaned = strip_junk(raw_title) or "audio"
    filename = build_filename("", cleaned).lstrip(" -")
    final_path = os.path.join(out_dir, filename)
    os.replace(mp3_path, final_path)
    print(f"  [OK] {filename}")


def run(url_or_query: str, out_dir: str):
    require_ffmpeg()
    os.makedirs(out_dir, exist_ok=True)

    if "open.spotify.com" in url_or_query:
        if not has_spotify_creds():
            raise DownloadError(
                "Falta SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET en .env. "
                "Crealas gratis en https://developer.spotify.com/dashboard"
            )
        kind, sid = sp_client.parse_spotify_url(url_or_query)
        if not kind:
            raise DownloadError("Link de Spotify invalido.")
        sp = sp_client.get_client()

        if kind == "track":
            tracks = [sp_client.get_track(sp, sid)]
        elif kind == "album":
            tracks = sp_client.get_album_tracks(sp, sid)
        else:
            tracks = sp_client.get_playlist_tracks(sp, sid)

        print(f"{len(tracks)} track(s) encontrado(s). Descargando...")
        for track in tqdm(tracks, desc="Progreso"):
            download_spotify_track(sp, track, out_dir)

    elif any(h in url_or_query for h in YOUTUBE_HOST_RE):
        download_youtube_direct(url_or_query, out_dir)

    else:
        if has_spotify_creds():
            sp = sp_client.get_client()
            track = sp_client.search_track(sp, url_or_query)
            if track:
                download_spotify_track(sp, track, out_dir)
                return
        results = search_youtube(url_or_query, limit=1)
        if not results:
            raise DownloadError("Sin resultados.")
        download_youtube_direct(results[0]["webpage_url"], out_dir)


def interactive(out_dir: str):
    print("=== Dsound (modo interactivo) ===")
    print(f"Carpeta de salida: {out_dir}")
    print("Pegá link de Spotify/YouTube o texto de busqueda. 'salir' pa terminar, 'carpeta' pa cambiar salida.\n")

    while True:
        try:
            entry = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nChau.")
            break

        if not entry:
            continue
        if entry.lower() in ("salir", "exit", "quit", "q"):
            print("Chau.")
            break
        if entry.lower() == "carpeta":
            new_dir = input(f"Nueva carpeta (actual: {out_dir}): ").strip()
            if new_dir:
                out_dir = new_dir
                os.makedirs(out_dir, exist_ok=True)
                print(f"Carpeta cambiada a: {out_dir}")
            continue

        try:
            run(entry, out_dir)
        except DownloadError as e:
            print(f"  [ERROR] {e}")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
        print()


def main():
    require_ffmpeg()
    parser = argparse.ArgumentParser(description="Descarga musica en MP3 320kbps con metadata limpia")
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="link Spotify (track/album/playlist), link YouTube, o texto de busqueda. Si se omite, entra en modo interactivo.",
    )
    parser.add_argument("-o", "--output", default=OUTPUT_DIR, help="carpeta de salida")
    args = parser.parse_args()

    if args.input is None:
        interactive(args.output)
        return

    try:
        run(args.input, args.output)
    except DownloadError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
