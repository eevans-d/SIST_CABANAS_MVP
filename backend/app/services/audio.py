import io
import uuid
from typing import Any, Dict, Optional

from app.core.config import get_settings
from fastapi import UploadFile

try:  # pragma: no cover - carga perezosa del modelo (puede ser pesado)
    import whisper  # type: ignore

    WHISPER_AVAILABLE = True
except Exception:  # pragma: no cover
    whisper = None  # type: ignore
    WHISPER_AVAILABLE = False

settings = get_settings()

_model_instance = None  # type: ignore


def get_model():  # type: ignore
    global _model_instance
    if not WHISPER_AVAILABLE:
        return None
    if _model_instance is None and whisper is not None:
        # Uso CPU por simplicidad MVP
        _model_instance = whisper.load_model(settings.AUDIO_MODEL)
    return _model_instance


async def transcribe_audio(file: UploadFile) -> Dict[str, Any]:
    """Transcribe audio OGG/OPUS -> texto

    Pipeline mínima MVP:
    - Lee bytes en memoria (evita escribir disco)
    - Intenta transcribir (si modelo no disponible -> devuelve pseudo low confidence)
    - Calcula confidence promedio simple (promedio de segment probabilities si disponible)
    - Si confidence < threshold -> error audio_unclear
    """
    raw = await file.read()
    if not raw:
        return {"error": "empty_file"}

    model = get_model()
    if model is None:
        # Entorno sin modelo instalado -> forzar low confidence (MVP sin audio processing)
        return {"error": "audio_processing_not_available", "confidence": 0.0}

    try:
        # whisper acepta path; para evitar escribir archivo generamos un temp en memoria
        # Sin embargo la librería requiere filename; workaround: escribir temporal si fuese necesario.
        # Para mantener simple y sin IO adicional intentamos usar decode con bytes buffer.
        # Si falla (raise) devolvemos error genérico.
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(raw)
            tmp_path = tmp.name
        result = model.transcribe(tmp_path, language="es")  # type: ignore
        os.unlink(tmp_path)
    except Exception:  # pragma: no cover - errores internos del modelo
        return {"error": "processing_failed"}

    text = result.get("text", "").strip()
    segments = result.get("segments", [])

    confidences = []
    for seg in segments:  # type: ignore
        if "avg_logprob" in seg and seg["avg_logprob"] is not None:
            # Convertir logprob aprox (heurística) a pseudo confidence 0-1
            # logprob suele estar negativo; aplicamos exp limitado
            import math

            conf = max(0.0, min(1.0, math.exp(seg["avg_logprob"])))
            confidences.append(conf)

    confidence = sum(confidences) / len(confidences) if confidences else 0.5

    if confidence < settings.AUDIO_MIN_CONFIDENCE:
        return {"error": "audio_unclear", "confidence": round(confidence, 3)}

    return {
        "text": text.strip(),
        "confidence": round(confidence, 3),
        "id": str(uuid.uuid4()),
    }
