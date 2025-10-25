"""Tests para envío de fotos de alojamientos por WhatsApp.

Valida:
- Envío de imagen con caption
- Envío de info de alojamiento con foto
- Manejo de alojamientos sin fotos
- Selección de foto primary
"""

from unittest.mock import AsyncMock, patch

import pytest
from app.services.whatsapp import send_accommodation_info_with_photo, send_image_message


@pytest.mark.asyncio
@patch("app.services.whatsapp.settings")
async def test_send_image_message_payload_structure(mock_settings):
    """Payload de imagen debe tener estructura correcta."""
    mock_settings.ENVIRONMENT = "production"
    mock_settings.WHATSAPP_ACCESS_TOKEN = "test_token"
    mock_settings.WHATSAPP_PHONE_ID = "123456"

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        result = await send_image_message(
            to_phone="+5491112345678",
            image_url="https://example.com/cabin.jpg",
            caption="Test Caption",
        )

        assert result["status"] == "sent"

        # Verificar que se llamó con el payload correcto
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        payload = call_args.kwargs["json"]

        assert payload["type"] == "image"
        assert payload["image"]["link"] == "https://example.com/cabin.jpg"
        assert payload["image"]["caption"] == "Test Caption"


@pytest.mark.asyncio
@patch("app.services.whatsapp.settings")
async def test_send_image_without_caption(mock_settings):
    """Imagen puede enviarse sin caption."""
    mock_settings.ENVIRONMENT = "production"
    mock_settings.WHATSAPP_ACCESS_TOKEN = "test_token"
    mock_settings.WHATSAPP_PHONE_ID = "123456"

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        result = await send_image_message(
            to_phone="+5491112345678", image_url="https://example.com/cabin.jpg"
        )

        assert result["status"] == "sent"

        # Verificar payload
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        payload = call_args.kwargs["json"]

        assert "caption" not in payload["image"] or payload["image"].get("caption") is None


@pytest.mark.asyncio
async def test_send_image_skipped_in_non_production():
    """Envío de imagen debe saltearse en desarrollo."""
    result = await send_image_message(
        to_phone="+5491112345678", image_url="https://example.com/test.jpg"
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "non_production"


@pytest.mark.asyncio
@patch("app.services.whatsapp.send_image_message")
@patch("app.services.whatsapp.send_text_message")
async def test_send_accommodation_with_photo(mock_send_text, mock_send_image):
    """Debe enviar foto y luego detalles del alojamiento."""
    mock_send_image.return_value = {"status": "sent"}
    mock_send_text.return_value = {"status": "sent"}

    accommodation = {
        "name": "Cabaña del Bosque",
        "capacity": 6,
        "base_price": 150.00,
        "description": "Hermosa cabaña rodeada de naturaleza",
        "photos": [
            {
                "url": "https://example.com/cabin1.jpg",
                "caption": "Vista exterior",
                "is_primary": True,
                "order": 0,
            },
            {
                "url": "https://example.com/cabin2.jpg",
                "caption": "Interior",
                "is_primary": False,
                "order": 1,
            },
        ],
    }

    result = await send_accommodation_info_with_photo(
        phone="+5491112345678", accommodation=accommodation
    )

    # Verificar que se llamó a enviar imagen
    mock_send_image.assert_called_once()
    call_args = mock_send_image.call_args
    assert call_args.kwargs["image_url"] == "https://example.com/cabin1.jpg"
    assert "Cabaña del Bosque" in call_args.kwargs["caption"]

    # Verificar que se llamó a enviar texto
    mock_send_text.assert_called_once()
    text_args = mock_send_text.call_args
    message = text_args.args[1]

    assert "Cabaña del Bosque" in message
    assert "6 personas" in message
    assert "$150.00" in message
    assert "naturaleza" in message


@pytest.mark.asyncio
@patch("app.services.whatsapp.send_image_message")
@patch("app.services.whatsapp.send_text_message")
async def test_send_accommodation_without_photo_works(mock_send_text, mock_send_image):
    """Debe funcionar aunque el alojamiento no tenga fotos."""
    mock_send_text.return_value = {"status": "sent"}

    accommodation = {
        "name": "Cabaña Sin Foto",
        "capacity": 4,
        "base_price": 100.00,
        "description": "Alojamiento cómodo",
        "photos": [],  # Sin fotos
    }

    result = await send_accommodation_info_with_photo(
        phone="+5491112345678", accommodation=accommodation
    )

    # NO debe intentar enviar imagen
    mock_send_image.assert_not_called()

    # Debe enviar texto normalmente
    mock_send_text.assert_called_once()
    text_args = mock_send_text.call_args
    message = text_args.args[1]

    assert "Cabaña Sin Foto" in message
    assert "4 personas" in message


@pytest.mark.asyncio
@patch("app.services.whatsapp.send_image_message")
@patch("app.services.whatsapp.send_text_message")
async def test_send_accommodation_selects_primary_photo(mock_send_text, mock_send_image):
    """Debe seleccionar la foto marcada como primary."""
    mock_send_image.return_value = {"status": "sent"}
    mock_send_text.return_value = {"status": "sent"}

    accommodation = {
        "name": "Test",
        "capacity": 4,
        "base_price": 100,
        "description": "Test",
        "photos": [
            {"url": "https://example.com/photo1.jpg", "is_primary": False, "order": 0},
            {
                "url": "https://example.com/photo2.jpg",
                "is_primary": True,
                "order": 1,
            },  # Esta es primary
            {"url": "https://example.com/photo3.jpg", "is_primary": False, "order": 2},
        ],
    }

    await send_accommodation_info_with_photo(phone="+5491112345678", accommodation=accommodation)

    # Debe enviar la foto marcada como primary
    call_args = mock_send_image.call_args
    assert call_args.kwargs["image_url"] == "https://example.com/photo2.jpg"


@pytest.mark.asyncio
@patch("app.services.whatsapp.send_image_message")
@patch("app.services.whatsapp.send_text_message")
async def test_send_accommodation_first_photo_if_no_primary(mock_send_text, mock_send_image):
    """Si no hay foto primary, debe usar la primera."""
    mock_send_image.return_value = {"status": "sent"}
    mock_send_text.return_value = {"status": "sent"}

    accommodation = {
        "name": "Test",
        "capacity": 4,
        "base_price": 100,
        "description": "Test",
        "photos": [
            {
                "url": "https://example.com/first.jpg",
                "is_primary": False,
            },  # Esta debería usarse
            {"url": "https://example.com/second.jpg", "is_primary": False},
        ],
    }

    await send_accommodation_info_with_photo(phone="+5491112345678", accommodation=accommodation)

    # Debe enviar la primera foto
    call_args = mock_send_image.call_args
    assert call_args.kwargs["image_url"] == "https://example.com/first.jpg"


@pytest.mark.asyncio
@patch("app.services.whatsapp.send_text_message")
async def test_accommodation_info_has_call_to_action(mock_send_text):
    """Mensaje de info debe incluir call-to-action."""
    mock_send_text.return_value = {"status": "sent"}

    accommodation = {
        "name": "Test Cabin",
        "capacity": 4,
        "base_price": 120,
        "description": "Nice place",
        "photos": [],
    }

    await send_accommodation_info_with_photo(phone="+5491112345678", accommodation=accommodation)

    text_args = mock_send_text.call_args
    message = text_args.args[1]

    # Debe invitar a consultar disponibilidad
    assert "disponibilidad" in message.lower() or "consultar" in message.lower()


@pytest.mark.asyncio
@patch("app.services.whatsapp.send_text_message")
async def test_accommodation_info_formats_price_correctly(mock_send_text):
    """Precio debe formatearse con 2 decimales."""
    mock_send_text.return_value = {"status": "sent"}

    accommodation = {
        "name": "Test",
        "capacity": 4,
        "base_price": 125.5,  # Decimal con 1 lugar
        "description": "Test",
        "photos": [],
    }

    await send_accommodation_info_with_photo(phone="+5491112345678", accommodation=accommodation)

    text_args = mock_send_text.call_args
    message = text_args.args[1]

    # Debe mostrar con 2 decimales
    assert "$125.50" in message


@pytest.mark.asyncio
@patch("app.services.whatsapp.send_image_message")
@patch("app.services.whatsapp.send_text_message")
async def test_photo_with_empty_url_not_sent(mock_send_text, mock_send_image):
    """No debe intentar enviar foto si URL está vacía."""
    mock_send_text.return_value = {"status": "sent"}

    accommodation = {
        "name": "Test",
        "capacity": 4,
        "base_price": 100,
        "description": "Test",
        "photos": [{"url": "", "is_primary": True}],  # URL vacía
    }

    await send_accommodation_info_with_photo(phone="+5491112345678", accommodation=accommodation)

    # No debe intentar enviar imagen
    mock_send_image.assert_not_called()

    # Debe enviar texto
    mock_send_text.assert_called_once()
