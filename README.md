# dsound

Descarga música de YouTube en MP3 (hasta 320 kbps) con los datos bien puestos: artista, título, álbum, año, número de pista y portada. Todo desde una interfaz web que se abre en tu navegador y funciona en tu PC.

Uso personal. Respeta los derechos de autor del contenido que descargues.

## Instalación

### Opción A: instalador para Windows (recomendado)

1. Descarga `dsound-<versión>-windows-x64-setup.exe` desde [Releases](https://github.com/pipodev06/dsound/releases/latest).
2. Ábrelo y sigue los pasos. No pide permisos de administrador: se instala para tu usuario y crea un acceso directo en el menú Inicio (y, si quieres, en el escritorio y al iniciar Windows).

Trae todo incluido (Python, ffmpeg y yt-dlp): no hace falta instalar nada más.

Si Windows SmartScreen muestra «Windows protegió su PC», es porque el ejecutable no está firmado digitalmente: haz clic en «Más información» → «Ejecutar de todas formas».

### Opción B: versión portable

Descarga el `.zip` de tu sistema desde [Releases](https://github.com/pipodev06/dsound/releases/latest) (`windows-x64.zip` o `linux-x64.zip`), descomprímelo y abre `dsound.exe` (Windows) o `./dsound` (Linux).

### Opción C: desde el código fuente

Requisitos: Python 3.10 o superior y ffmpeg (`winget install Gyan.FFmpeg` en Windows; después de instalarlo, abre una terminal nueva para que tome el cambio).

```
git clone https://github.com/pipodev06/dsound.git
cd dsound
pip install -e .
dsound
```

## Uso

Al abrir dsound se abre el navegador en `http://127.0.0.1:5000` y aparece un ícono junto al reloj de Windows (bandeja del sistema) con las opciones «Abrir dsound», «Abrir carpeta de música» y «Salir». No queda ninguna ventana negra abierta. También puedes cerrarlo con el botón de apagado de la parte superior de la página.

Si dsound ya está abierto y lo vuelves a abrir, no se inicia otra copia: solo se abre el navegador.

La interfaz tiene 4 pestañas:

**Buscar**
- Busca por texto («artista canción») y elige uno o varios resultados (se muestran de 25 en 25; «Más resultados...» trae más).
- Pega uno o varios enlaces de YouTube (separados por espacios o saltos de línea) para descargarlos directamente.
- Pega el enlace de una playlist o de un canal de YouTube para ver sus primeros 100 videos y elegir cuáles descargar.
- Pega el enlace de una **canción de Spotify**: dsound lee la página pública (sin iniciar sesión) y busca esa canción en YouTube.
- Pega el enlace de una **playlist o álbum de Spotify**: dsound lee la lista de canciones (hasta 100), busca cada una en YouTube (eligiendo el video con duración parecida) y las deja todas seleccionadas para «Descargar seleccionadas». Los MP3 quedan con el artista y el título de Spotify y, si es un álbum, también con el nombre del álbum, el año, el número de pista y la portada.
- El botón de reproducir muestra una vista previa (solo audio, con la portada de imagen).
- El lápiz permite corregir el artista y el título antes de descargar. Empieza con el título ya limpio (sin «(Official Video)» y similares), tal como quedará el archivo.
- Al descargar una canción suelta, dsound busca su ficha en YouTube Music para usar el artista, el título, el álbum, el año y la portada oficiales. Solo la usa si coincide de verdad (mismo título, artista y duración parecida); si no, se queda con el título del video limpio. Se puede desactivar en Ajustes.
- Si ya tienes algo parecido en tu biblioteca, o si ya está en la cola, avisa antes de descargarlo otra vez.

**Álbumes**: busca álbumes completos (con YouTube Music) y los descarga de una vez, con año y número de pista en los datos del MP3.

**Biblioteca**: lista lo que ya descargaste, con reproductor, filtro, orden (fecha, artista, título, tamaño) y opciones para editar o eliminar, de una en una o varias a la vez.

**Descargas**: la cola con el nombre y la miniatura de cada canción, una barra de progreso (porcentaje mientras descarga y «convirtiendo a mp3» al final), y botones para cancelar, reintentar, «Limpiar terminadas» y «Abrir carpeta». La cola se guarda en disco: si cierras dsound con descargas pendientes, continúan solas la próxima vez que lo abras.

En la parte superior de la página se eligen la calidad (128, 192 o 320 kbps) y la carpeta de salida, y están los botones de Ajustes y para cerrar dsound.

**Ajustes**
- **Usar cookies del navegador**: soluciona el error «YouTube pidió confirmar que no eres un bot» y permite descargar videos con restricción de edad. Debes haber iniciado sesión en YouTube con ese navegador. En Windows, Firefox es el que mejor funciona: Chrome y Edge cifran sus cookies y a veces hay que cerrarlos por completo.
- **Buscar los datos oficiales en YouTube Music** (activado por defecto).

Cuando sale una versión nueva de dsound, aparece un aviso en la parte superior con el enlace para descargarla.

Atajos: `/` va al buscador y `Esc` cierra la ventana abierta.

## Configuración (opcional)

Se hace en un archivo `.env` (copia `.env.example`). Con el instalador o la versión portable, el `.env` va en la misma carpeta que `dsound.exe`.

| Variable | Para qué sirve |
|---|---|
| `OUTPUT_DIR` | Carpeta de salida (por defecto `~/Music/dsound`). También se cambia desde la página. |
| `MP3_BITRATE` | Calidad por defecto (`320`). |
| `DSOUND_PORT` | Puerto (por defecto `5000`). |
| `DSOUND_HOST` | `0.0.0.0` para abrir dsound desde otros dispositivos de tu red (celular, etc.). |
| `DSOUND_PASSWORD` | Contraseña para esos otros dispositivos (esta PC nunca la pide). |
| `DSOUND_COOKIES_BROWSER` | Navegador para las cookies de YouTube (`firefox`, `chrome`, `edge`...). También desde Ajustes. |
| `DSOUND_MUSIC_METADATA` | `0` para no buscar datos en YouTube Music. También desde Ajustes. |
| `DSOUND_UPDATE_CHECK` | `0` para no avisar de versiones nuevas. |
| `DSOUND_NO_BROWSER` | `1` para no abrir el navegador al iniciar. |
| `DSOUND_NO_TRAY` | `1` para no mostrar el ícono junto al reloj. |
| `DSOUND_DATA_DIR` | Dónde se guardan la cola, la sesión y el log (por defecto `~/.dsound`). |

### Abrir dsound desde el celular

Pon `DSOUND_HOST=0.0.0.0` **y** `DSOUND_PASSWORD=<una contraseña>` en el `.env`. Los otros dispositivos de tu red tendrán que iniciar sesión (la sesión dura 30 días). Sin contraseña, cualquier persona en tu red podría ver, descargar y borrar tu biblioteca. Desde otros dispositivos no se puede cambiar la carpeta de salida ni los ajustes, ni cerrar dsound. Es HTTP sin cifrar: está pensado para la red de tu casa, no para exponerlo a internet.

## Si algo falla

- El registro de lo que hace dsound está en `~/.dsound/dsound.log` (en Windows: `C:\Users\<tu usuario>\.dsound\dsound.log`).
- «YouTube pidió confirmar que no eres un bot»: activa «Usar cookies del navegador» en Ajustes.
- Si YouTube cambió algo y las descargas dejan de funcionar, normalmente se arregla con una versión nueva de yt-dlp: dsound publica una versión nueva automáticamente cada vez que sale una (revisa el aviso de la página o [Releases](https://github.com/pipodev06/dsound/releases)).

## Desarrollo

### Frontend

El frontend (`frontend/`) es un proyecto Vite (React + TypeScript + Tailwind v4 + shadcn/ui). Para usar dsound **no hace falta Node**: el build compilado está en `dsound/static/` y lo sirve el backend.

Para modificar la interfaz:

```
cd frontend
npm install
npm run dev
```

Eso levanta Vite en `http://localhost:5173` con recarga automática y redirige `/api` y `/library` al backend: ejecuta `dsound` al mismo tiempo (puerto 5000). Para dejar los cambios listos en `dsound/static/`:

```
cd frontend
npm run build
```

### Pruebas

```
pip install -e ".[dev]"
python -m pytest          # backend

cd frontend
npm test                  # frontend (Vitest)
```

Las pruebas no descargan nada de internet (YouTube y Spotify se simulan). GitHub Actions ejecuta las pruebas, el lint y el build en cada push (`.github/workflows/ci.yml`). Dependabot propone actualizaciones de dependencias.

### Armar el ejecutable

```
pip install -e ".[build]"
python packaging/build.py
```

Deja `dist/dsound-<versión>-<plataforma>.zip` (descarga ffmpeg solo; con `--no-ffmpeg` no lo incluye). PyInstaller no genera ejecutables para otros sistemas: el `.exe` de Windows se arma en Windows. Para eso está el workflow `.github/workflows/release.yml`, que arma Windows (zip + instalador con Inno Setup) y Linux, prueba que cada ejecutable inicie, encuentre ffmpeg y se cierre bien, y:

- con un tag `v*` (por ejemplo `git tag v0.3.0 && git push origin v0.3.0`), o ejecutándolo a mano con una versión, publica un Release;
- si no, deja los archivos como artifacts en la pestaña Actions.

El workflow `.github/workflows/auto-release.yml` revisa cada lunes si salió una versión nueva de yt-dlp y, si el último Release no la incluye, publica uno nuevo automáticamente.

El ícono se genera con `python packaging/make_icon.py`.

## Notas

- No usa la API de Spotify (exige que la cuenta dueña de la app tenga Premium): solo lee las páginas públicas.
- dsound es una herramienta personal para usar en tu propia PC, no un servicio público. Usa yt-dlp para descargar de YouTube, lo que puede ir en contra de los Términos de Servicio de YouTube. Eres responsable de cómo lo usas y del contenido que descargas.

## Licencia

MIT; consulta [LICENSE](LICENSE). El ejecutable incluye ffmpeg (build LGPL de [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds)), con su licencia en `_internal/ffmpeg/LICENSE.txt`.
