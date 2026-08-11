# Dsound

Baja musica de YouTube en MP3 320kbps con tags limpios (titulo/artista + portada del video), desde una interfaz web local.

Uso personal. Respeta derechos de autor del contenido que descargues.

## Instalacion

Requisitos: Python 3.10+ y Node.js 18+ (Node solo hace falta si vas a tocar el frontend — para uso normal alcanza con el build ya compilado que trae el repo).

1. Instalar ffmpeg:
   ```
   winget install Gyan.FFmpeg
   ```
   (reiniciar la terminal/sesion despues de instalarlo — Windows tarda en propagar el cambio de PATH a las terminales ya abiertas)

2. Clonar el repo e instalar las dependencias de Python:
   ```
   git clone https://github.com/pipodev06/dsound.git
   cd dsound
   pip install -r requirements.txt
   ```

3. (Opcional) Copiar `.env.example` a `.env` si queres cambiar la carpeta de salida, el puerto, o el acceso desde otro dispositivo de tu red — ver [Notas](#notas).

## Uso

```
python -m dsound
```

Abre `http://127.0.0.1:5000` en el navegador (se abre solo). La interfaz tiene 4 pestañas:

**Buscar**
- Buscar por texto ("artista - cancion") y elegir uno o varios resultados de la grilla (paginado de a 25, "Mas Resultados..." trae mas).
- Pegar uno o varios links de YouTube (separados por espacio o salto de linea) para bajarlos directo, sin buscar.
- Pegar un link de playlist o canal de YouTube (`...&list=...`, `/channel/`, `/@handle`) — trae los primeros 100 videos en la misma grilla, listos para elegir y bajar.
- Pegar un link de track de Spotify (`open.spotify.com/track/...`, incluidos los que traen prefijo de idioma como `intl-es/`) — se resuelve a "Artista Titulo" (leyendo la pagina publica, sin login) y busca eso en YouTube.
- "Escuchar" reproduce un preview del video antes de descargar. El link "↗" abre el video en YouTube.
- El icono de lapiz deja corregir artista/titulo a mano antes de bajar, por si el parseo automatico del titulo no da bien.
- Tildar varios resultados y usar "Descargar seleccionadas" para bajarlos todos en paralelo.
- Si vas a bajar algo que ya tenes (titulo/artista parecido), avisa antes de descargar de nuevo.

**Álbumes**: busca álbumes completos (via YouTube Music) y los baja de una, con el mismo aviso de duplicados por si ya tenes algunos tracks.

**Biblioteca**: lista lo que ya bajaste (leyendo los tags), con reproductor, filtro por artista/titulo, orden (fecha/artista/titulo/tamaño), y edicion/borrado — de a uno o en lote.

**Descargas**: cola de todo lo que se esta bajando o se bajo, con opcion de cancelar una descarga en curso o reintentar una que fallo.

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

## Notas

- No usa la API de Spotify para busqueda/matching: la API para desarrolladores ahora exige que la cuenta dueña de la app tenga Premium para casi cualquier llamada. El titulo/artista de cada descarga sale del propio titulo del video de YouTube (separando por " - " cuando el video lo trae asi, editable a mano si hace falta) y la portada es el thumbnail del video. Pegar un link de Spotify si funciona (ver arriba), porque solo lee la pagina publica, no pasa por el Web API.
- Default de salida: `~/Music/dsound` (Windows lo muestra como "Musica/dsound", el nombre real de la carpeta es "Music"). Se puede cambiar desde la interfaz o en `.env`.
- El puerto por default es `5000`, configurable con `DSOUND_PORT` en `.env`.
- Por default solo escucha en `127.0.0.1` (esta maquina). Para abrirlo desde otro dispositivo de tu red (celular, etc.), poner `DSOUND_HOST=0.0.0.0` en `.env` — **dsound no tiene login ni password**, con esto activado cualquiera en tu misma red puede ver/bajar/borrar tu biblioteca, activalo solo si confias en tu red. Al arrancar con esto activado, la consola muestra la URL de red para abrir desde el otro dispositivo.
- **dsound es una herramienta personal para uso local/propio**, pensada para correr en tu maquina (no un servicio publico): usa yt-dlp para bajar de YouTube, lo cual esta en tension con los Terminos de Servicio de YouTube. Sos responsable de como la usas y del contenido que descargues.

## Licencia

MIT — ver [LICENSE](LICENSE).
