"""
Transcripcion de notas de voz con Whisper (local, gratis, sin cuota).

Usa faster-whisper. El modelo se carga una sola vez y queda en memoria. Decodifica
el audio de WhatsApp (.ogg/opus) sin necesitar ffmpeg del sistema (faster-whisper
trae su propio decodificador via PyAV).

Config por .env:
  WHISPER_MODEL   -> tiny | base | small | medium  (por defecto: base)
  WHISPER_DEVICE  -> cpu | cuda                     (por defecto: cpu)
"""

from __future__ import annotations

import os
import tempfile

_modelo = None


def _cargar():
    global _modelo
    if _modelo is None:
        from faster_whisper import WhisperModel

        nombre = os.environ.get("WHISPER_MODEL", "base")
        device = os.environ.get("WHISPER_DEVICE", "cpu")
        compute = "int8" if device == "cpu" else "float16"
        _modelo = WhisperModel(nombre, device=device, compute_type=compute)
    return _modelo


def disponible() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def transcribir(audio: bytes, sufijo: str = ".ogg") -> str:
    """Transcribe audio (bytes) a texto en español. Devuelve '' si falla."""
    if not audio:
        return ""
    ruta = None
    try:
        with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as f:
            f.write(audio)
            ruta = f.name
        modelo = _cargar()
        segmentos, _info = modelo.transcribe(ruta, language="es", vad_filter=True)
        return " ".join(s.text.strip() for s in segmentos).strip()
    except Exception as e:
        print(f"[whisper] error transcribiendo: {type(e).__name__}: {e}")
        return ""
    finally:
        if ruta:
            try:
                os.remove(ruta)
            except Exception:
                pass
