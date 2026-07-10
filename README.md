# Dsound

Baja musica en MP3 320kbps con metadata limpia (titulo/artista/album/portada) y sin cortes ni intros de video.

Como funciona: para links de Spotify, usa la API de Spotify solo para sacar metadata exacta (Spotify no permite descargar audio real, solo preview de 30s). Con esa metadata busca el audio en YouTube (prioriza canales "- Topic", que son subida oficial sin intro/outro), descarga el mejor audio disponible y lo convierte a MP3, etiquetado con los datos correctos de Spotify.

Uso personal. Respeta derechos de autor del contenido que descargues.

## Setup

1. Instalar Python 3.10+ y ffmpeg:
   ```
   winget install Gyan.FFmpeg
   ```
   (reiniciar terminal despues)

2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

3. (Opcional pero recomendado) Crear app gratis en https://developer.spotify.com/dashboard para tener metadata exacta de Spotify:
   - Create app -> nombre cualquiera, redirect URI: `http://localhost:8888/callback`
   - Copiar Client ID y Client Secret

4. Copiar `.env.example` a `.env` y completar:
   ```
   SPOTIFY_CLIENT_ID=...
   SPOTIFY_CLIENT_SECRET=...
   ```

## Uso

Modo interactivo (recomendado):
```
python -m dsound
```

Modo directo:
```
python -m dsound "https://open.spotify.com/track/..."
python -m dsound "https://open.spotify.com/playlist/..."
python -m dsound "https://open.spotify.com/album/..."
python -m dsound "https://www.youtube.com/watch?v=..."
python -m dsound "artista - nombre cancion"
```

`-o carpeta` para elegir salida (default `downloads/`).

## Notas

- Sin credenciales de Spotify, el script igual funciona con links/busqueda de YouTube directo (sin matching de duracion contra Spotify).
- El matching prioriza duracion exacta y canales oficiales "- Topic" para evitar versiones live/remix/cover/con charla.
