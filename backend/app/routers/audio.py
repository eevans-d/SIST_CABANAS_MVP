from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.audio import transcribe_audio
from app.services import nlu

router = APIRouter(prefix="/audio", tags=["audio"])

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if file.content_type not in ("audio/ogg", "audio/opus", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Formato no soportado")
    result = await transcribe_audio(file)
    if "error" in result:
        # Caso low confidence u otro error
        return {"status": "needs_text", **result}
    analysis = nlu.analyze(result["text"]) if result.get("text") else {"intents": ["desconocido"], "dates": []}
    return {
        "status": "ok",
        "text": result["text"],
        "confidence": result["confidence"],
        "nlu": analysis,
    }
