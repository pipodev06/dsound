# Dsound

Baja musica de YouTube en MP3 320kbps con tags limpios (artista, titulo, album, año, nº de pista y portada), desde una interfaz web local.

Uso personal. Respeta derechos de autor del contenido que descargues.

## Instalacion

### Opcion A: ejecutable listo para usar (recomendado)

1. Bajar el `.zip` de tu sistema desde [Releases](https://github.com/pipodev06/dsound/releases) (`dsound-<version>-windows-x64.zip` o `-linux-x64.zip`).
2. Descomprimirlo donde quieras.
3. Abrir `dsound/dsound.exe` (Windows) o `dsound/dsound` (Linux).

Trae Python y ffmpeg adentro: no hace falta instalar nada. La configuracion opcional va en un `.env` al lado del ejecutable (ver `LEEME.txt` dentro del zip). Windows SmartScreen puede avisar que la app "no es reconocida" porque el ejecutable no esta firmado: "Mas informacion" → "Ejecutar de todas formas".

### Opcion B: desde el codigo

Requisitos: Python 3.10+ y Node.js 18+ (Node solo hace falta si vas a tocar el frontend — para uso normal alcanza con el build ya compilado que trae el repo).

1. Instalar ffmpeg:
   ```
   winget install Gyan.FFmpeg
   ```
   (reiniciar la terminal/sesion despues de instalarlo — Windows tarda en propagar el cambio de PATH a las terminales ya abiertas)

2. Clonar el repo e instalar dsound (instala tambien el comando `dsound`):
   ```
   git clone https://github.com/pipodev06/dsound.git
   cd dsound
   pip install -e .
   ```

3. (Opcional) Copiar `.env.example` a `.env` si queres cambiar la carpeta de salida, el puerto, o el acceso desde otro dispositivo de tu red — ver [Notas](#notas).

## Uso

```
dsound            # o: python -m dsound
```

Si ya hay un dsound abierto, en vez de arrancar otro abre el navegador en el que ya esta corriendo.

Abre `http://127.0.0.1:5000` en el navegador (se abre solo). La interfaz tiene 4 pestañas:

**Buscar**
- Buscar por texto ("artista - cancion") y elegir uno o varios resultados de la grilla (paginado de a 25, "Mas Resultados..." trae mas).
- Pegar uno o varios links de YouTube (separados por espacio o salto de linea) para bajarlos directo, sin buscar.
- Pegar un link de playlist o canal de YouTube (`...&list=...`, `/channel/`, `/@handle`) — trae los primeros 100 videos en la misma grilla, listos para elegir y bajar.
- Pegar un link de track de Spotify (`open.spotify.com/track/...`, incluidos los que traen prefijo de idioma como `intl-es/`) — se resuelve a "Artista Titulo" (leyendo la pagina publica, sin login) y busca eso en YouTube.
- Pegar un link de **playlist o album de Spotify** (`open.spotify.com/playlist/...`, `/album/...`) — lee la lista de temas de la pagina publica (hasta 100), busca cada uno en YouTube (eligiendo el video con duracion parecida) y los deja todos tildados para "Descargar seleccionadas". Los mp3 quedan con el artista/titulo de Spotify, y si es un album, tambien con nombre del album, año, nº de pista y la portada del album.
- "Escuchar" reproduce un preview del video antes de descargar. El link "↗" abre el video en YouTube.
- El icono de lapiz deja corregir artista/titulo a mano antes de bajar. Arranca con el titulo ya limpio (sin "(Official Video)" y similares), igual a como va a quedar el archivo.
- Al bajar un tema suelto, dsound busca su ficha en YouTube Music para usar el artista/titulo oficiales, el album, el año y la portada cuadrada. Solo la usa si coincide de verdad (mismo titulo, artista y duracion parecida); si no, se queda con el titulo del video limpio. Se puede apagar con `DSOUND_MUSIC_METADATA=0`.
- Tildar varios resultados y usar "Descargar seleccionadas" para bajarlos todos en paralelo.
- Si vas a bajar algo que ya tenes (titulo/artista parecido), avisa antes de descargar de nuevo.

**Álbumes**: busca álbumes completos (via YouTube Music) y los baja de una (con año y nº de pista en los tags), con el mismo aviso de duplicados por si ya tenes algunos tracks.

**Biblioteca**: lista lo que ya bajaste (leyendo los tags), con reproductor, filtro por artista/titulo, orden (fecha/artista/titulo/tamaño), y edicion/borrado — de a uno o en lote.

**Descargas**: cola de todo lo que se esta bajando o se bajo, con barra de progreso (porcentaje mientras baja, y "convirtiendo a mp3" al final), opcion de cancelar una descarga en curso o reintentar una que fallo. La cola se guarda en disco (`~/.dsound/`): si cerras dsound con descargas pendientes, se retoman solas al volver a abrirlo.

Calidad de descarga (128/192/320 kbps) y carpeta de salida se configuran arriba a la derecha, en el header.

Atajos: `/` enfoca el buscador, `Esc` cierra el modal/preview activo.

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

## Tests

```
pip install -e ".[dev]"
python -m pytest          # backend

cd frontend
npm test                  # frontend (Vitest)
```

Los tests no bajan nada de internet (YouTube/Spotify se simulan). GitHub Actions corre los tests, el lint y el build del frontend en cada push (`.github/workflows/ci.yml`). Dependabot propone actualizaciones de dependencias (yt-dlp semanal, porque YouTube lo rompe seguido).

## Armar el ejecutable

```
pip install -e ".[build]"
python packaging/build.py
```

Deja `dist/dsound-<version>-<plataforma>.zip` (baja ffmpeg solo; `--no-ffmpeg` para no incluirlo). PyInstaller no cruza plataformas: el `.exe` de Windows se arma en Windows. Para eso esta el workflow `.github/workflows/release.yml`, que arma Windows y Linux, prueba que cada ejecutable arranque y encuentre ffmpeg, y:

- con un tag `v*` (ej. `git tag v0.2.0 && git push origin v0.2.0`) publica un Release con los dos `.zip`;
- si no, los deja como artifacts del run en la pestaña Actions.

## Notas

- No usa la API de Spotify para busqueda/matching: la API para desarrolladores ahora exige que la cuenta dueña de la app tenga Premium para casi cualquier llamada. El titulo/artista de cada descarga sale del propio titulo del video de YouTube (separando por " - " cuando el video lo trae asi, editable a mano si hace falta) y la portada es el thumbnail del video. Pegar un link de Spotify si funciona (ver arriba), porque solo lee la pagina publica, no pasa por el Web API.
- Default de salida: `~/Music/dsound` (Windows lo muestra como "Musica/dsound", el nombre real de la carpeta es "Music"). Se puede cambiar desde la interfaz o en `.env`.
- El puerto por default es `5000`, configurable con `DSOUND_PORT` en `.env`.
- Por default solo escucha en `127.0.0.1` (esta maquina). Para abrirlo desde otro dispositivo de tu red (celular, etc.), poner `DSOUND_HOST=0.0.0.0` en `.env`, **junto con `DSOUND_PASSWORD=<una contraseña>`**: los otros dispositivos van a tener que loguearse (la sesion dura 30 dias; esta PC nunca pide contraseña). Sin `DSOUND_PASSWORD`, cualquiera en tu misma red puede ver/bajar/borrar tu biblioteca, y la consola lo avisa al arrancar. Al arrancar con esto activado, la consola muestra la URL de red para abrir desde el otro dispositivo. La carpeta de salida solo se puede cambiar desde la PC donde corre dsound, y la API de biblioteca solo da acceso a los `.mp3` de esa carpeta. Es HTTP sin cifrar: pensado para tu red de casa, no para exponerlo a internet.
- **dsound es una herramienta personal para uso local/propio**, pensada para correr en tu maquina (no un servicio publico): usa yt-dlp para bajar de YouTube, lo cual esta en tension con los Terminos de Servicio de YouTube. Sos responsable de como la usas y del contenido que descargues.

## Licencia

MIT — ver [LICENSE](LICENSE). El ejecutable incluye ffmpeg (build LGPL de [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds)), con su licencia en `_internal/ffmpeg/LICENSE.txt`.
