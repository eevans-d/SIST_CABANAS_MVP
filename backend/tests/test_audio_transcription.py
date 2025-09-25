import pytest
from io import BytesIO

@pytest.mark.asyncio
async def test_low_confidence_audio(test_client):  # type: ignore
    # Simula entorno sin modelo (si modelo no está instalado retornará audio_unclear)
    ogg_dummy = b"OggS"  # encabezado mínimo falso
    files = {"file": ("test.ogg", ogg_dummy, "audio/ogg")}
    resp = await test_client.post("/api/v1/audio/transcribe", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "needs_text"
    assert data["error"] in ("audio_unclear", "processing_failed")
