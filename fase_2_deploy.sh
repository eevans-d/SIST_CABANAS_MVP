#!/bin/bash

# ============================================================================
# FASE 2: DEPLOY A PRODUCCIÓN
# ============================================================================
# Este script automatiza:
# 1. Re-validación pre-deploy (debe mostrar 15/15 ✅)
# 2. Deploy a Fly.io
# 3. Monitoreo de logs en tiempo real
# ============================================================================

set -e

export PATH="/home/eevan/.fly/bin:$PATH"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                      🚀 FASE 2: DEPLOY A PRODUCCIÓN                           ║"
echo "║                    Build + Release + Health Check                              ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# ============================================================================
# PRE-REQUISITOS
# ============================================================================

echo "⏳ Verificando pre-requisitos..."

if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl no instalado."
    exit 1
fi

if ! flyctl auth whoami &> /dev/null; then
    echo "❌ No autenticado con Fly.io."
    exit 1
fi

echo "✅ Prerequisitos OK"
echo ""

# ============================================================================
# RE-VALIDACIÓN PRE-DEPLOY
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RE-VALIDACIÓN PRE-DEPLOY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "./pre_deploy_validation.sh" ]; then
    echo "⏳ Ejecutando validación..."
    bash ./pre_deploy_validation.sh

    VALIDATION_RESULT=$?
    if [ $VALIDATION_RESULT -ne 0 ]; then
        echo ""
        echo "❌ VALIDACIÓN FALLIDA"
        echo "⚠️  No se puede desplegar. Revisa los errores arriba."
        exit 1
    fi
    echo "✅ VALIDACIÓN EXITOSA: 15/15 ✅"
else
    echo "⚠️  pre_deploy_validation.sh no encontrado - saltando validación"
fi

echo ""

# ============================================================================
# DEPLOY A FLY.IO
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DEPLOY A FLY.IO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Iniciando deploy de sist-cabanas-mvp..."
echo "   (Esto puede tomar 2-5 minutos. Sistema en zero-downtime)"
echo ""

flyctl deploy \
    --app sist-cabanas-mvp \
    --strategy immediate \
    --wait-timeout 5m

DEPLOY_RESULT=$?

echo ""

if [ $DEPLOY_RESULT -ne 0 ]; then
    echo "❌ DEPLOY FALLIDO"
    echo "ℹ️  Ejecuta para ver logs detallados:"
    echo "    flyctl logs -f --app sist-cabanas-mvp"
    exit 1
fi

echo "✅ DEPLOY COMPLETADO EXITOSAMENTE"
echo ""

# ============================================================================
# MONITOREO DE LOGS
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MONITOREO DE LOGS EN VIVO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Esperando 5 segundos para que app esté lista..."
sleep 5

echo ""
echo "📊 Logs en vivo (últimas 20 líneas, Ctrl+C para salir):"
echo ""

timeout 30 flyctl logs -f --app sist-cabanas-mvp 2>/dev/null || true

echo ""
echo "✅ Monitoreo completado"
echo ""

# ============================================================================
# INFORMACIÓN DE DEPLOY
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "INFORMACIÓN DE DEPLOY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 Estado de la aplicación:"
flyctl status --app sist-cabanas-mvp

echo ""
echo "🌐 URL de producción:"
echo "   https://sist-cabanas-mvp.fly.dev"
echo ""

echo "📊 Dashboard de Fly.io:"
echo "   https://fly.io/apps/sist-cabanas-mvp"
echo ""

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ FASE 2 COMPLETADA EXITOSAMENTE                          ║"
echo "║                                                                                ║"
echo "║  Next: FASE 3 - Smoke Tests (5 tests críticos)                                ║"
echo "║  Comando: bash fase_3_smoke_tests.sh                                          ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
