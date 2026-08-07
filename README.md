# Dsound

Baja musica de YouTube en MP3 320kbps con tags limpios (titulo/artista + portada del video), desde una interfaz web local.

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

3. (Opcional) Copiar `.env.example` a `.env` si queres cambiar la carpeta de salida o el puerto por default.

## Uso

```
python -m dsound
```

Abre `http://127.0.0.1:5000` en el navegador (se abre solo). Desde ahi:

- Buscar por texto ("artista - cancion") y elegir uno o varios resultados de la grilla (5 columnas x 5 filas, "Mas Resultados..." trae mas de la misma busqueda).
- Pegar un link directo de YouTube para bajarlo sin buscar.
- Pegar un link de track de Spotify (`open.spotify.com/track/...`) — se resuelve a "Artista Titulo" (leyendo la pagina publica, sin login) y busca eso en YouTube.
- "Escuchar" en cada resultado reproduce un preview embebido de YouTube antes de descargar. El link "↗" al lado abre el video en YouTube directamente.
- "editar" en cada resultado deja corregir artista/titulo a mano antes de bajar, por si el parseo automatico del titulo del video no da bien.
- Tildar varios resultados y usar "Descargar seleccionadas" para bajarlos todos (se procesan 2 a la vez, con estado en vivo por item).
- Selector de calidad (128/192/320 kbps) arriba del buscador.
- Si vas a bajar algo que ya tenes (nombre parecido), avisa antes de descargar de nuevo.
- Pestaña "Biblioteca": lista lo que ya bajaste (leyendo los tags), con reproductor y filtro por artista/titulo.
- Cambiar la carpeta de salida con el boton "cambiar" (abre el explorador de archivos nativo).
- Atajos: `/` enfoca el buscador, `Esc` corta el preview activo.

## Desarrollo del frontend

El frontend (`frontend/`) es un proyecto Vite (React + TypeScript + Tailwind v4 + shadcn/ui) separado del paquete Python. Para uso normal de la app **no hace falta Node instalado** — el build ya compilado vive en `dsound/static/` y Flask lo sirve directo.

Solo si vas a tocar la interfaz:

```
cd frontend
npm install
npm run dev
```

Eso levanta Vite en `http://localhost:5173` con hot-reload, proxeando `/api` y `/library` al backend Flask — corre `python -m dsound` en paralelo (puerto 5000) para que el proxy tenga a donde pegarle.

Para dejar los cambios listos para `python -m dsound` (sin Vite corriendo):

```
cd frontend
npm run build
```

Esto compila a `dsound/static/`, pisando el build anterior.

## Notas

- No usa la API de Spotify para busqueda/matching: la API para desarrolladores ahora exige que la cuenta dueña de la app tenga Premium para casi cualquier llamada. El titulo/artista de cada descarga sale del propio titulo del video de YouTube (separando por " - " cuando el video lo trae asi, editable a mano si hace falta) y la portada es el thumbnail del video. Pegar un link de Spotify si funciona (ver arriba), porque solo lee la pagina publica, no pasa por el Web API.
- Default de salida: `~/Music/dsound` (Windows lo muestra como "Musica/dsound", el nombre real de la carpeta es "Music"). Se puede cambiar desde la interfaz o en `.env`.
- El puerto por default es `5000`, configurable con `DSOUND_PORT` en `.env`.
- Por default solo escucha en `127.0.0.1` (esta maquina). Para abrirlo desde otro dispositivo de tu red (celular, etc.), poner `DSOUND_HOST=0.0.0.0` en `.env` — **dsound no tiene login ni password**, con esto activado cualquiera en tu misma red puede ver/bajar/borrar tu biblioteca, activalo solo si confias en tu red. Al arrancar con esto activado, la consola muestra la URL de red para abrir desde el otro dispositivo.
