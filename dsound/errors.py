"""Traduce los errores tecnicos (yt-dlp, red, disco) a mensajes que se
entienden. El detalle original queda en el log (~/.dsound/dsound.log)."""

import re

# (patron del error original, mensaje para el usuario). Gana el primero que
# coincide. Mensaje None = el error ya es claro (mensajes propios de dsound).
_RULES = [
    (r"ffmpeg no encontrado|no se encontr", None),
    (
        r"confirm you.?re not a bot",
        "YouTube pidió confirmar que no eres un bot. Activa «Usar cookies del navegador» en Ajustes "
        "(con la sesión de YouTube iniciada en ese navegador) o vuelve a intentarlo más tarde.",
    ),
    (
        r"confirm your age|age.restricted|inappropriate for some users",
        "Este video tiene restricción de edad. Activa «Usar cookies del navegador» en Ajustes, "
        "con una cuenta mayor de edad iniciada en YouTube.",
    ),
    (
        r"could not (copy|find).*cookie|failed to decrypt|cookie database|app.bound encryption",
        "No se pudieron leer las cookies del navegador. Cierra el navegador por completo y vuelve a "
        "intentarlo. En Windows, Chrome y Edge cifran sus cookies: Firefox suele funcionar mejor.",
    ),
    (r"private video", "Este video es privado."),
    (
        r"video (is )?(not available|unavailable)|this video has been removed|not available in your country",
        "Este video no está disponible: fue eliminado, es privado o está bloqueado en tu país.",
    ),
    (r"members.only|join this channel", "Este video es solo para miembros del canal."),
    (r"premieres? in|live event will begin", "Este video todavía no se ha estrenado."),
    (r"http error 429|too many requests", "YouTube está recibiendo demasiadas solicitudes. Espera unos minutos."),
    (r"http error 403", "YouTube rechazó la descarga (error 403). Vuelve a intentarlo en unos minutos."),
    (
        r"getaddrinfo|name or service not known|temporary failure in name resolution|"
        r"connection (refused|reset|aborted)|timed? ?out|network is unreachable|unable to download webpage",
        "No hay conexión con YouTube. Revisa tu conexión a internet.",
    ),
    (r"no space left|disk full|errno 28", "No hay espacio suficiente en el disco."),
    (r"permission denied|errno 13|access is denied", "No hay permiso para escribir en la carpeta de salida."),
    (r"ffmpeg|ffprobe|postprocessing", "Falló la conversión a MP3 (ffmpeg)."),
]

_COMPILED = [(re.compile(pattern, re.IGNORECASE), message) for pattern, message in _RULES]
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def friendly(error) -> str:
    """Mensaje claro para mostrar en la interfaz."""
    text = _ANSI.sub("", str(error) or "")
    for pattern, message in _COMPILED:
        if pattern.search(text):
            if message is None:
                break
            return message
    text = re.sub(r"^ERROR:\s*", "", text.strip())
    text = re.sub(r"^\[[\w:]+\]\s*[\w-]+:\s*", "", text)  # "[youtube] abc123: " de yt-dlp
    return text[:300] or "Error desconocido."
