# dsound

Herramienta personal (uso local, un solo usuario) para bajar audio de YouTube en MP3 320kbps con tags limpios. Backend Flask + frontend HTML/CSS/JS plano servido desde `dsound/static/` (sin build step, sin framework).

## Estilo visual (congelado)

Identidad "terminal": nace del CLI original (banner estilo msfconsole) y se traslada a la web. No cambiar sin pedido explicito del usuario.

**Colores** (custom properties en `static/style.css`, no Tailwind):
- `--bg: #0b0f0d` fondo. `--surface: #121613` tarjetas/paneles. `--surface-2: #171c18` hover/inputs.
- `--border: #232a25` bordes finos (1px), reemplazan sombras para dar elevacion.
- Texto: solo 2 shades — `--text: #e8ece9` (primario) y `--text-muted: #7c8c82` (secundario/labels). Mismo criterio que la regla global de -500/-800: no sumar shades intermedias.
- Acentos semanticos (mismo mapeo que los tags `[+]/[-]/[*]/[!]` del CLI): `--accent: #3ed67a` (ok/verde), `--danger: #ff5c5c` (error/rojo), `--info: #55c2e8` (info/cian), `--warn: #e8c14d` (warning/amarillo).

**Tipografia**: dos familias, sin fuentes externas (system stacks, cero requests).
- `--font-mono` para lo tecnico/dato (wordmark "dsound_", el prompt de busqueda, titulos de resultados, log de estado).
- `--font-sans` para UI/labels (botones, meta info, texto de ayuda).

**Radios/espaciado**: `--radius: 6px` fijo en toda la app (botones, inputs, tarjetas). Escala de espaciado en pasos de 4px (`--space-1` a `--space-6`, de 4px a 32px).

**Sombras**: ninguna. La elevacion se marca con `--border` (1px), no con `box-shadow`.

**Modo**: solo oscuro, deliberado (identidad terminal). No agregar light mode salvo pedido explicito.

**Patrones de componente unicos** (un solo componente reusado, no reimplementar):
- `.btn` con variantes `.btn-accent` / `.btn-ghost` (+ modificador `.btn-sm` para las acciones dentro de una card) — todo boton de la app usa esta clase base.
- `.card` — grid de resultados de busqueda (checkbox de seleccion + thumbnail con preview + titulo + meta + fila de 4 `.icon-btn`: Escuchar / Descargar (`.icon-btn-accent`) / Renombrar (abre el modal de editar compartido con Biblioteca, override local artista/titulo antes de bajar, sin llamar a la API) / Ir al enlace), reusada para cada item. Grid responsive: 2 columnas en mobile hasta 5 en desktop (`min-width: 1100px`), paginado client-side de a 25 (`#load-more`, 5x5). Busqueda inicial trae 25 resultados (`GET /api/search?limit=25`, rapido); al agotar el buffer local, "Mas Resultados" dispara una busqueda nueva con `limit` mas alto (+25 cada vez, tope `SEARCH_LIMIT_CAP=300` en front y back) en vez de traer todo de una — asi el primer render es rapido y el resto es bajo demanda.
- `.lib-row` — fila de la biblioteca local (pestaña "Biblioteca"), reproductor `<audio>` nativo con streaming por range requests. Acciones (editar/eliminar) son `.icon-btn` (SVG inline 15px, sin texto) que abren modales — no toggles inline ni `confirm()`/`prompt()` nativos.
- `.lib-filter` (input de filtro en Biblioteca) — unica excepcion al input con caja completa (`.prompt-input`, `.settings-select`): solo `border-bottom` (`--border` normal, `--accent` en foco), sin fondo ni radio. No aplicar este estilo underline a otros inputs sin pedido explicito.
- `.icon-btn` (+ modificadores `.icon-btn-danger`, `.icon-btn-accent`) — boton cuadrado 30px solo-icono (SVG inline `currentColor`, sin libreria de iconos externa), mismo lenguaje visual que `.btn-ghost` (borde `--border`, radio `--radius`). Usar para acciones repetibles en filas/listas/cards (editar, eliminar, descargar, escuchar, ir al enlace) en vez de texto subrayado o boton de texto — mantiene consistencia visual entre acciones del mismo grupo.
- Álbumes (pestaña "Álbumes") sigue el mismo patron de paginado que Buscar: `GET /api/albums/search?limit=` trae 20 iniciales (`ALBUM_PAGE_STEP=20`), "Mas Resultados" pide mas de a 20 (tope `ALBUM_LIMIT_CAP=100`). Esto es solo para la lista de albumes que matchean la busqueda — el tracklist de un album ya elegido siempre viene completo de una (`get_album`), no se pagina.
- Modales de confirmacion/edicion reusan `.modal-overlay`/`.modal` (mismo componente que el preview de audio). Eliminar destructivo (archivo, no solo dato) siempre pasa por modal propio (nunca `confirm()` nativo), con texto exacto `¿Estás seguro de eliminar {titulo} - {artista}?` y boton de confirmar en `.btn-danger`. Editar campos usa `.modal-form`/`.modal-field` con `<label>` explicito por campo (no placeholder-only). El modal de editar es generico (`openEditModal(artist, title, onSave)`): Biblioteca le pasa un `onSave` que llama `PUT /api/library/<file>` (renombra en disco); las cards de busqueda le pasan un `onSave` que solo guarda un override local en el resultado (`result._override`), sin red, hasta que se le da Descargar.
- Log de estado (`.log-line`) esta separado por pestaña (`#log-search`, `#log-albums`, `#log-library`, uno anidado en cada `<section>` de vista) — las acciones de una pestaña no deben aparecer en el log de otra. Acciones propias de una pestaña (busqueda, descarga, editar/eliminar biblioteca) loguean siempre a su log fijo; solo acciones realmente globales (carpeta de salida, estado del server) usan el log de la pestaña activa en ese momento.
- `.log-line` con modificador `.tag-ok/.tag-err/.tag-info/.tag-warn` — todo mensaje de estado (busqueda, descarga, cambio de carpeta) pasa por este mismo componente, con el mismo vocabulario de tags `[+]/[-]/[*]/[!]` que ya existia en el CLI.

Nota: el preview ("Escuchar") abre un modal (`.modal-overlay`/`.modal`) con un `<video>` nativo (poster = thumbnail) alimentado por `/api/preview/<id>` — el backend saca con yt-dlp la URL directa de un stream mp4 video+audio hasta 480p (sin descargar ni convertir; si no hay muxeado cae a solo audio, `has_video: false`). Esto reemplazo al iframe embebido de YouTube que se usaba antes, porque los videos Vevo/sellos bloquean el embed ("Video no disponible") y el stream directo no tiene esa restriccion. La URL de googlevideo expira (~6h) y esta atada a la IP — sirve para preview inmediato, no guardarla. El link "↗" de cada card sigue abriendo el video en youtube.com.

Atajos de teclado: `/` enfoca el buscador (salvo que ya estes escribiendo en otro input), `Esc` corta el preview activo.

## Arquitectura

- `dsound/downloader.py` — logica de busqueda/descarga/tageo/duplicados, sin dependencias de Flask (reusable). `download()` acepta `bitrate`, y `artist_override`/`title_override` para saltear el parseo automatico cuando el usuario edito la metadata a mano.
- `dsound/jobs.py` — cola de descargas en memoria (`WORKER_COUNT=4` threads daemon) + polling. `/api/download` encola y devuelve `job_id`, el frontend consulta `/api/jobs/<id>` cada ~700ms hasta `done`/`error`. Es lo que permite descargas concurrentes y seleccion multiple sin bloquear el server — subir `WORKER_COUNT` acelera descargas de album/lote a costa de mas carga de red/CPU (ffmpeg) simultanea.
- `dsound/youtube_dl.py` — wrapper de yt-dlp (busqueda + descarga+conversion a mp3, bitrate configurable).
- `dsound/tagger.py` — escribe tags ID3 + portada (usa el thumbnail de YouTube, no hay Spotify).
- `dsound/clean.py` — limpieza de titulos/nombres de archivo.
- `dsound/library.py` — lista lo ya descargado en `OUTPUT_DIR` leyendo tags ID3, para la pestaña Biblioteca.
- `dsound/spotify_link.py` — resuelve un link de `open.spotify.com/track/...` leyendo el `og:title`/`og:description` de la pagina publica (sin login ni API key) y arma "Artista Titulo" para buscarlo en YouTube. Asi se recupera parte de la comodidad de pegar un link de Spotify sin depender del Web API (bloqueado, ver Notas del README).
- `dsound/native.py` — selector de carpeta nativo (tkinter, con fallback si no hay entorno grafico).
- `dsound/webapp.py` — rutas Flask (`/api/search`, `/api/download`, `/api/jobs/<id>`, `/api/library`, `/library/<file>`, `/api/resolve-spotify`, `/api/status`, `/api/output-dir*`) + sirve `static/`.
- `dsound/config.py` — env vars (`OUTPUT_DIR`, `MP3_BITRATE`, `DSOUND_PORT`), persistencia en `.env`.

No usa la API de Spotify para busqueda/matching (ver README, seccion Notas: exige Premium en la cuenta dueña de la app para casi cualquier llamada del Web API, no solo para datos de usuario) — pero si soporta pegar un link de track de Spotify via scraping de la pagina publica (`spotify_link.py`), que no tiene esa restriccion.

**Detector de duplicados**: `downloader.find_duplicate()` compara nombres con fuzzy matching (`difflib`, umbral 0.82) contra lo que ya hay en `OUTPUT_DIR` antes de descargar — por nombre de archivo, no por contenido/ID. Nunca descarga sin preguntar primero, ni para canción individual ni para álbum:
- Canción individual: `/api/download` devuelve 409 con `{duplicate: true, existing: "..."}`; el frontend pregunta con el modal `#duplicate-modal` (nunca `confirm()` nativo) y reintenta con `confirm: true` si el usuario elige "Descargar de todos modos".
- Álbum: `/api/albums/<id>/download` primero hace un chequeo en seco de todos los tracks (sin encolar nada); si hay duplicados y no viene `duplicate_mode`, devuelve 409 con `{duplicate: true, duplicates: [...]}`. El mismo modal muestra la lista completa con 3 opciones: Cancelar (nada), "Omitir y bajar el resto" (`duplicate_mode: "skip"`, reintenta solo con los tracks nuevos) o "Descargar de todos modos" (`duplicate_mode: "force"`, reintenta bajando todo el album igual).
