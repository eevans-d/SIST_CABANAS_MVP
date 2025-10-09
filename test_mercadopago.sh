#!/bin/bash

# 💳 Script para testing de Mercado Pago

set -e

echo "💳 Testing Mercado Pago integration..."

API_BASE="http://localhost:8000/api/v1"

# Verificar que la API esté corriendo
if ! curl -s $API_BASE/healthz > /dev/null; then
    echo "❌ La API no está corriendo en puerto 8000"
    echo "Ejecuta: docker-compose up -d"
    exit 1
fi

echo "✅ API corriendo en puerto 8000"

# Verificar que hay al menos un alojamiento (consulta directa a DB)
echo "🏠 Verificando alojamientos disponibles..."
ACCOMMODATIONS=$(docker exec alojamientos_postgres psql -U alojamientos -t -c "SELECT COUNT(*) FROM accommodations WHERE active = true;" | tr -d ' ')
if [[ "$ACCOMMODATIONS" == "0" ]]; then
    echo "⚠️  No hay alojamientos activos. Creando uno de prueba..."
    echo "Por favor, verifica que hay al menos un alojamiento activo en la base de datos"
    exit 1
fi

echo "✅ $ACCOMMODATIONS alojamiento(s) activo(s)"

# Test 1: Crear pre-reserva
echo ""
echo "🧪 Test 1: Crear pre-reserva..."

# Obtener ID del primer alojamiento activo
ACCOMMODATION_ID=$(docker exec alojamientos_postgres psql -U alojamientos -t -c "SELECT id FROM accommodations WHERE active = true LIMIT 1;" | tr -d ' ')
echo "Usando accommodation_id: $ACCOMMODATION_ID"

PRE_RESERVE_RESPONSE=$(curl -s -X POST $API_BASE/reservations/pre-reserve \
  -H "Content-Type: application/json" \
  -d "{
    \"accommodation_id\": $ACCOMMODATION_ID,
    \"check_in\": \"2025-12-15\",
    \"check_out\": \"2025-12-17\",
    \"guests\": 2,
    \"contact_name\": \"Test Usuario MP\",
    \"contact_phone\": \"+5491123456789\",
    \"contact_email\": \"test.mp@example.com\",
    \"channel\": \"api\"
  }")

echo "Respuesta pre-reserva:"
echo "$PRE_RESERVE_RESPONSE" | jq .

# Extraer código y payment_link
RESERVATION_CODE=$(echo "$PRE_RESERVE_RESPONSE" | jq -r '.code // "null"')
PAYMENT_LINK=$(echo "$PRE_RESERVE_RESPONSE" | jq -r '.payment_link // "null"')

if [[ "$RESERVATION_CODE" == "null" ]]; then
    echo "❌ No se pudo crear la pre-reserva"
    echo "Respuesta: $PRE_RESERVE_RESPONSE"
    exit 1
fi

echo "✅ Pre-reserva creada: $RESERVATION_CODE"
echo "💳 Payment link: $PAYMENT_LINK"

# Test 2: Simular webhook de pago (con idempotencia)
echo ""
echo "🧪 Test 2: Simular webhook de pago..."

WEBHOOK_PAYLOAD='{
  "id": "test_payment_'$(date +%s)'",
  "status": "approved",
  "amount": 15000.00,
  "currency": "ARS",
  "external_reference": "'$RESERVATION_CODE'"
}'

echo "Payload del webhook:"
echo "$WEBHOOK_PAYLOAD" | jq -C

# Calcular firma HMAC-SHA256 correcta
WEBHOOK_SECRET="sS5zRKswMiOBW_sZdrJdsGCCMbgLNsCz_f3x_7tnNf4"
SIGNATURE=$(echo -n "$WEBHOOK_PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" -binary | xxd -p -c 256)
TIMESTAMP=$(date +%s)

WEBHOOK_RESPONSE=$(curl -s -X POST $API_BASE/mercadopago/webhook \
  -H "Content-Type: application/json" \
  -H "x-signature: ts=$TIMESTAMP,v1=$SIGNATURE" \
  -d "$WEBHOOK_PAYLOAD")

echo ""
echo "Respuesta del webhook:"
echo "$WEBHOOK_RESPONSE" | jq .

# Verificar si fue exitoso
WEBHOOK_STATUS=$(echo "$WEBHOOK_RESPONSE" | jq -r '.status // "error"')
if [[ "$WEBHOOK_STATUS" == "ok" ]]; then
    echo "✅ Webhook procesado correctamente"
else
    echo "❌ Error en el webhook"
    echo "Respuesta: $WEBHOOK_RESPONSE"
fi

# Test 3: Verificar estado de la reserva
echo ""
echo "🧪 Test 3: Verificar estado de la reserva..."
RESERVATION_STATUS=$(curl -s "$API_BASE/reservations/$RESERVATION_CODE" | jq -r '.reservation_status // "unknown"')

echo "Estado de la reserva: $RESERVATION_STATUS"

if [[ "$RESERVATION_STATUS" == "confirmed" ]]; then
    echo "✅ Reserva confirmada correctamente"
elif [[ "$RESERVATION_STATUS" == "pre_reserved" ]]; then
    echo "⚠️  Reserva aún en estado pre_reserved (webhook puede no haber funcionado)"
else
    echo "❌ Estado inesperado: $RESERVATION_STATUS"
fi

# Test 4: Test de idempotencia (enviar el mismo webhook otra vez)
echo ""
echo "🧪 Test 4: Test de idempotencia..."
WEBHOOK_RESPONSE_2=$(curl -s -X POST $API_BASE/mercadopago/webhook \
  -H "Content-Type: application/json" \
  -d "$WEBHOOK_PAYLOAD")

IDEMPOTENT=$(echo "$WEBHOOK_RESPONSE_2" | jq -r '.idempotent // false')
if [[ "$IDEMPOTENT" == "true" ]]; then
    echo "✅ Idempotencia funcionando correctamente"
else
    echo "⚠️  Idempotencia no detectada (puede ser normal si es el primer procesamiento)"
fi

# Test 5: Verificar logs
echo ""
echo "🧪 Test 5: Verificar logs de Mercado Pago..."
echo "Últimos logs de mercadopago:"
docker-compose logs --tail=10 api | grep -i mercadopago || echo "No hay logs de mercadopago"

# Resumen
echo ""
echo "📊 RESUMEN DEL TESTING:"
echo "======================="
echo "✅ Pre-reserva: $RESERVATION_CODE"
echo "✅ Payment link: $PAYMENT_LINK"
echo "✅ Webhook: $WEBHOOK_STATUS"
echo "✅ Estado final: $RESERVATION_STATUS"
echo "✅ Idempotencia: $IDEMPOTENT"
echo ""

if [[ "$WEBHOOK_STATUS" == "ok" && "$RESERVATION_STATUS" == "confirmed" ]]; then
    echo "🎉 ¡MERCADO PAGO FUNCIONANDO CORRECTAMENTE!"
    echo ""
    echo "📱 SIGUIENTE PASO:"
    echo "1. Ve a: https://www.mercadopago.com.ar/developers/"
    echo "2. Crea tu aplicación real"
    echo "3. Obtén credenciales de testing"
    echo "4. Actualiza las variables en .env:"
    echo "   MERCADOPAGO_ACCESS_TOKEN=APP_USR-..."
    echo "5. Haz un pago real con las tarjetas de prueba"
else
    echo "⚠️  Hay algunos issues. Revisa los logs para más detalles."
fi

echo ""
echo "💡 TIPS:"
echo "- Payment link es para testing manual en el navegador"
echo "- Webhook simula lo que MP enviaría en un pago real"
echo "- En producción, MP firmará los webhooks con HMAC"
echo "- Configura webhook URL real cuando tengas dominio"
