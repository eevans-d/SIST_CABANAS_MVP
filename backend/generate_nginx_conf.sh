#!/usr/bin/env bash
set -euo pipefail

# Script para generar nginx.conf desde template con variables de entorno
# Uso: ./generate_nginx_conf.sh [.env file path]

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Archivo $ENV_FILE no encontrado"
    echo "Uso: $0 [path/to/.env]"
    exit 1
fi

# Cargar variables de entorno
set -a
source "$ENV_FILE"
set +a

# Validar que DOMAIN esté definido
if [ -z "${DOMAIN:-}" ]; then
    echo "❌ Error: Variable DOMAIN no definida en $ENV_FILE"
    echo "Ejemplo: DOMAIN=alojamientos.tuempresa.com"
    exit 1
fi

TEMPLATE="nginx.conf.template"
OUTPUT="nginx.conf"

if [ ! -f "$TEMPLATE" ]; then
    echo "❌ Error: Template $TEMPLATE no encontrado"
    exit 1
fi

echo "🔧 Generando nginx.conf desde template..."
echo "   DOMAIN: $DOMAIN"

# Reemplazar variables usando envsubst
envsubst '${DOMAIN}' < "$TEMPLATE" > "$OUTPUT"

echo "✅ Generado: $OUTPUT"
echo ""
echo "Próximos pasos:"
echo "1. Revisar: cat $OUTPUT"
echo "2. Copiar al contenedor o volumen de Nginx"
echo "3. Reiniciar Nginx: docker-compose restart nginx"
