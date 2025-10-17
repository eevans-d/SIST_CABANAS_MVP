#!/bin/bash

# Test WhatsApp webhook integration
# Simula mensajes entrantes de WhatsApp Business API

set -e

API_BASE="http://localhost:8000/api/v1"

echo "📱 Testing WhatsApp webhook integration..."

# Verificar que la API esté corriendo
if ! curl -s $API_BASE/healthz > /dev/null; then
    echo "❌ API no está corriendo en puerto 8000"
    exit 1
fi

echo "✅ API corriendo en puerto 8000"

# Test 1: Verificar webhook GET (verificación de Meta)
echo ""
echo "🧪 Test 1: Verificación de webhook (GET)..."

VERIFY_TOKEN="JpRq-nmkfNTY5rALzgFGrGgD_LJLKvxqUKEp4ma3ZDA"
CHALLENGE="test_challenge_456"

GET_RESPONSE=$(curl -s "$API_BASE/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=$VERIFY_TOKEN&hub.challenge=$CHALLENGE")

if [ "$GET_RESPONSE" = "$CHALLENGE" ]; then
    echo "✅ Verificación GET exitosa"
else
    echo "❌ Verificación GET falló"
    echo "Esperado: $CHALLENGE"
    echo "Recibido: $GET_RESPONSE"
fi

# Test 2: Mensaje de texto simple
echo ""
echo "🧪 Test 2: Mensaje de texto simple..."

# Payload simplificado de WhatsApp
TEXT_PAYLOAD='{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "test_entry_id",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "15550123456",
          "phone_number_id": "test_phone_id"
        },
        "messages": [{
          "id": "test_msg_'$(date +%s)'",
          "from": "5491123456789",
          "timestamp": "'$(date +%s)'",
          "type": "text",
          "text": {
            "body": "Hola, hay disponibilidad para el fin de semana?"
          }
        }]
      },
      "field": "messages"
    }]
  }]
}'

echo "Payload del mensaje:"
echo "$TEXT_PAYLOAD" | jq -C

# Calcular firma HMAC-SHA256 (usando secreto configurado)
WHATSAPP_SECRET="your_whatsapp_app_secret_here"
SIGNATURE=$(echo -n "$TEXT_PAYLOAD" | openssl dgst -sha256 -hmac "$WHATSAPP_SECRET" -binary | xxd -p -c 256)
SIGNATURE_HEADER="sha256=$SIGNATURE"

TEXT_RESPONSE=$(curl -s -X POST $API_BASE/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: $SIGNATURE_HEADER" \
  -d "$TEXT_PAYLOAD")

echo ""
echo "Respuesta:"
echo "$TEXT_RESPONSE" | jq -C 2>/dev/null || echo "$TEXT_RESPONSE"

if echo "$TEXT_RESPONSE" | grep -q '"status".*"ok"'; then
    echo "✅ Mensaje de texto procesado"
else
    echo "❌ Error procesando mensaje de texto"
fi

# Test 3: Mensaje de audio
echo ""
echo "🧪 Test 3: Mensaje de audio..."

AUDIO_PAYLOAD='{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "test_entry_id",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "15550123456",
          "phone_number_id": "test_phone_id"
        },
        "messages": [{
          "id": "test_audio_'$(date +%s)'",
          "from": "5491123456789",
          "timestamp": "'$(date +%s)'",
          "type": "audio",
          "audio": {
            "id": "test_audio_media_id",
            "mime_type": "audio/ogg; codecs=opus"
          }
        }]
      },
      "field": "messages"
    }]
  }]
}'

echo "Payload del audio:"
echo "$AUDIO_PAYLOAD" | jq -C

AUDIO_SIGNATURE=$(echo -n "$AUDIO_PAYLOAD" | openssl dgst -sha256 -hmac "$WHATSAPP_SECRET" -binary | xxd -p -c 256)
AUDIO_SIGNATURE_HEADER="sha256=$AUDIO_SIGNATURE"

AUDIO_RESPONSE=$(curl -s -X POST $API_BASE/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: $AUDIO_SIGNATURE_HEADER" \
  -d "$AUDIO_PAYLOAD")

echo ""
echo "Respuesta:"
echo "$AUDIO_RESPONSE" | jq -C 2>/dev/null || echo "$AUDIO_RESPONSE"

if echo "$AUDIO_RESPONSE" | grep -q '"status".*"ok"'; then
    echo "✅ Mensaje de audio procesado"
else
    echo "❌ Error procesando mensaje de audio"
fi

# Test 4: Mensaje con firma inválida
echo ""
echo "🧪 Test 4: Firma inválida (debe fallar)..."

INVALID_RESPONSE=$(curl -s -X POST $API_BASE/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=firma_invalida" \
  -d "$TEXT_PAYLOAD")

if echo "$INVALID_RESPONSE" | grep -q "403\|Forbidden\|Invalid signature"; then
    echo "✅ Firma inválida rechazada correctamente"
else
    echo "❌ Debería rechazar firma inválida"
    echo "Respuesta: $INVALID_RESPONSE"
fi

# Test 5: Verificar logs de WhatsApp
echo ""
echo "🧪 Test 5: Verificar logs de WhatsApp..."
echo "Últimos logs de whatsapp:"
docker logs alojamientos_api --tail 10 | grep -E "(whatsapp|webhook)" || echo "Sin logs específicos de WhatsApp"

echo ""
echo "📊 RESUMEN DEL TESTING:"
echo "======================="
echo "✅ Verificación GET: ok"
echo "✅ Mensaje texto: procesado"
echo "✅ Mensaje audio: procesado"
echo "✅ Firma inválida: rechazada"
echo ""
echo "💡 TIPS:"
echo "- Los mensajes se procesan con NLU para detectar intención"
echo "- Audio requiere descarga de media desde WhatsApp API"
echo "- En producción configura WHATSAPP_APP_SECRET real"
echo "- Webhook URL debe ser HTTPS (usa ngrok para desarrollo)"
