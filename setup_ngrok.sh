#!/bin/bash

# Setup ngrok for webhook development
# Requiere cuenta gratuita en https://dashboard.ngrok.com/

set -e

echo "🌐 Configurando ngrok para webhooks..."

# Verificar si ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok no está instalado"
    echo "Instala con: snap install ngrok"
    exit 1
fi

echo "✅ ngrok está instalado"

# Verificar si ya hay authtoken configurado
if ngrok config check &> /dev/null; then
    echo "✅ ngrok ya tiene authtoken configurado"
else
    echo "❌ ngrok no tiene authtoken configurado"
    echo ""
    echo "📋 Pasos para configurar:"
    echo "1. Ve a https://dashboard.ngrok.com/"
    echo "2. Regístrate con cuenta gratuita"
    echo "3. Ve a 'Your Authtoken' y copia el token"
    echo "4. Ejecuta: ngrok config add-authtoken <tu-token>"
    echo "5. Vuelve a ejecutar este script"
    echo ""
    exit 1
fi

# Verificar si la API está corriendo
if ! curl -s http://localhost:8000/api/v1/healthz > /dev/null; then
    echo "❌ API no está corriendo en puerto 8000"
    echo "Ejecuta: make up"
    exit 1
fi

echo "✅ API corriendo en puerto 8000"

# Iniciar ngrok en background
echo "🚀 Iniciando ngrok tunnel..."
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# Esperar a que ngrok se inicie
sleep 3

# Obtener URL pública
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo "❌ No se pudo obtener URL de ngrok"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo "✅ ngrok tunnel activo:"
echo "   URL pública: $NGROK_URL"
echo "   Dashboard: http://localhost:4040"
echo "   PID: $NGROK_PID"

# Guardar información
echo "$NGROK_PID" > ngrok.pid
echo "$NGROK_URL" > ngrok.url

echo ""
echo "🔗 URLs para configurar webhooks:"
echo "   WhatsApp: $NGROK_URL/api/v1/webhooks/whatsapp"
echo "   Mercado Pago: $NGROK_URL/api/v1/mercadopago/webhook"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - ngrok se ejecuta en background"
echo "   - Para detener: kill \$(cat ngrok.pid)"
echo "   - La URL cambia cada vez que reinicias ngrok"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Configura webhooks en Meta Developer Console"
echo "   2. Ejecuta: ./test_whatsapp_webhook.sh"
echo "   3. Envía mensajes de prueba a tu número de WhatsApp Business"
