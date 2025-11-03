#!/bin/bash

# ============================================================================
# FASE 1: SETUP FLY.IO + POSTGRESQL + SECRETS
# ============================================================================
# Este script automatiza:
# 1A: Crear PostgreSQL en región eze (Buenos Aires)
# 1B: Conectar DB a la app
# 1C: Generar 5 secretos críticos
# 1D: Configurar secretos en Fly.io
# ============================================================================

set -e

export PATH="/home/eevan/.fly/bin:$PATH"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                         🔧 FASE 1: SETUP FLY.IO                               ║"
echo "║                     PostgreSQL + Secrets + Configuration                       ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# PRE-REQUISITOS
# ============================================================================

echo "⏳ Verificando pre-requisitos..."

if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl no instalado. Ejecuta FASE 0 primero."
    exit 1
fi

# Verificar autenticación
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ No autenticado con Fly.io. Ejecuta: flyctl auth login"
    exit 1
fi

AUTH_USER=$(flyctl auth whoami 2>&1)
echo "✅ Autenticado como: $AUTH_USER"

# Verificar si la app existe
echo "⏳ Verificando aplicación sist-cabanas-mvp..."
if ! flyctl apps list | grep -q "sist-cabanas-mvp"; then
    echo "❌ App sist-cabanas-mvp no existe en Fly.io"
    echo "⚠️  Debes crear la app primero con: flyctl launch"
    exit 1
fi
echo "✅ App sist-cabanas-mvp encontrada"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1A: CREAR POSTGRESQL (Región EZE - Buenos Aires)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Creando PostgreSQL: sist-cabanas-db en región eze..."
echo "   (Esto puede tomar 3-5 minutos...)"
echo ""

flyctl postgres create \
    --name sist-cabanas-db \
    --region eze \
    --initial-cluster-size 1 \
    --vm-size shared-cpu-1x \
    --volume-size 1 \
    --skip-confirmation

echo ""
echo "✅ PostgreSQL creado exitosamente"
echo ""

# ============================================================================
# 1B: CONECTAR DB A LA APP
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1B: CONECTAR DATABASE A LA APP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Conectando sist-cabanas-db a sist-cabanas-mvp..."
flyctl postgres attach sist-cabanas-db \
    --app sist-cabanas-mvp \
    --skip-confirmation

echo ""
echo "✅ Database conectada"
echo "   Variable de entorno DATABASE_URL creada automáticamente"
echo ""

# ============================================================================
# 1C + 1D: GENERAR Y CONFIGURAR SECRETOS
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1C: GENERAR 5 SECRETOS CRÍTICOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Generando secretos criptográficamente seguros..."
echo ""

JWT_SECRET=$(openssl rand -base64 32)
echo "1️⃣  JWT_SECRET generado (32 bytes, base64)"

REDIS_PASSWORD=$(openssl rand -base64 32)
echo "2️⃣  REDIS_PASSWORD generado (32 bytes, base64)"

ICS_SALT=$(openssl rand -base64 16)
echo "3️⃣  ICS_SALT generado (16 bytes, base64)"

ADMIN_CSRF_SECRET=$(openssl rand -base64 32)
echo "4️⃣  ADMIN_CSRF_SECRET generado (32 bytes, base64)"

GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 12)
echo "5️⃣  GRAFANA_ADMIN_PASSWORD generado (12 bytes, hex)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1D: CONFIGURAR SECRETOS EN FLY.IO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Enviando secretos a Fly.io..."
flyctl secrets set \
    JWT_SECRET="$JWT_SECRET" \
    REDIS_PASSWORD="$REDIS_PASSWORD" \
    ICS_SALT="$ICS_SALT" \
    ADMIN_CSRF_SECRET="$ADMIN_CSRF_SECRET" \
    GRAFANA_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD" \
    --app sist-cabanas-mvp

echo ""
echo "✅ 5 secretos configurados en Fly.io"
echo ""

# ============================================================================
# VERIFICACIÓN FINAL
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "VERIFICACIÓN FINAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 Secretos configurados en sist-cabanas-mvp:"
flyctl secrets list --app sist-cabanas-mvp

echo ""
echo "📊 Apps disponibles:"
flyctl apps list | grep "sist-cabanas"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ FASE 1 COMPLETADA EXITOSAMENTE                          ║"
echo "║                                                                                ║"
echo "║  Next: FASE 2 - Deploy a Producción                                           ║"
echo "║  Comando: bash fase_2_deploy.sh                                               ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
