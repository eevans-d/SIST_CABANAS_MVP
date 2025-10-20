#!/bin/bash

# ============================================================================
# CONTROL MAESTRO: ACTIVACIÓN COMPLETA A PRODUCCIÓN
# ============================================================================
# Orquesta las 4 fases:
# FASE 0: Resolver bloqueante (flyctl)
# FASE 1: Setup Fly.io + PostgreSQL + Secrets
# FASE 2: Deploy a Producción
# FASE 3: Smoke Tests
# ============================================================================

set -e

export PATH="/home/eevan/.fly/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                ║"
echo "║           🚀 MISSION CONTROL: ACTIVACIÓN A PRODUCCIÓN SIST_CABAÑAS 🚀          ║"
echo "║                                                                                ║"
echo "║                      4 FASES → 25 MINUTOS → LIVE                              ║"
echo "║                                                                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# DETERMINAR FASE INICIAL
# ============================================================================

echo "🔍 Analizando estado actual..."
echo ""

# Verificar autenticación
if flyctl auth whoami &> /dev/null; then
    AUTH_STATUS="✅ Autenticado"
    NEXT_PHASE="1"
else
    AUTH_STATUS="❌ NO autenticado"
    NEXT_PHASE="0"
fi

# Verificar app
if flyctl apps list 2>/dev/null | grep -q "sist-cabanas-mvp"; then
    APP_STATUS="✅ App existe"
else
    APP_STATUS="⚠️  App NO existe"
fi

echo "Estado de autenticación: $AUTH_STATUS"
echo "Estado de app:           $APP_STATUS"
echo ""

if [ "$NEXT_PHASE" = "0" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  FASE 0 REQUERIDA: AUTENTICACIÓN"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Ejecuta interactivamente:"
    echo ""
    echo "  export PATH=\"/home/eevan/.fly/bin:\$PATH\""
    echo "  flyctl auth login"
    echo ""
    echo "Luego, vuelve a ejecutar este script:"
    echo ""
    echo "  bash activation_complete.sh"
    echo ""
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                         INICIANDO ACTIVACIÓN COMPLETA                         ║"
echo "║                                                                                ║"
echo "║  FASE 1: Setup Fly.io (PostgreSQL + Secrets) ................. ~10 min         ║"
echo "║  FASE 2: Deploy a Producción ............................. ~5 min         ║"
echo "║  FASE 3: Smoke Tests (5 validaciones críticas) .............. ~5 min         ║"
echo "║                                                                                ║"
echo "║  TOTAL: ~25 minutos → 🎉 LIVE EN PRODUCCIÓN                                   ║"
echo "║                                                                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

read -p "¿Continuar con la activación completa? (s/n): " -r CONFIRM

if [[ ! $CONFIRM =~ ^[sS]$ ]]; then
    echo ""
    echo "Abortado por usuario."
    exit 0
fi

echo ""

# ============================================================================
# FASE 1: SETUP
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                            EJECUTANDO FASE 1                                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ ! -f "$SCRIPT_DIR/fase_1_setup.sh" ]; then
    echo "❌ fase_1_setup.sh no encontrado"
    exit 1
fi

bash "$SCRIPT_DIR/fase_1_setup.sh"
FASE1_RESULT=$?

if [ $FASE1_RESULT -ne 0 ]; then
    echo ""
    echo "❌ FASE 1 FALLIDA - Abortando activación"
    exit 1
fi

echo ""
read -p "FASE 1 completada. ¿Continuar con FASE 2? (s/n): " -r CONFIRM

if [[ ! $CONFIRM =~ ^[sS]$ ]]; then
    echo "Abortado por usuario. Para continuar:"
    echo "  bash fase_2_deploy.sh"
    exit 0
fi

echo ""

# ============================================================================
# FASE 2: DEPLOY
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                            EJECUTANDO FASE 2                                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ ! -f "$SCRIPT_DIR/fase_2_deploy.sh" ]; then
    echo "❌ fase_2_deploy.sh no encontrado"
    exit 1
fi

bash "$SCRIPT_DIR/fase_2_deploy.sh"
FASE2_RESULT=$?

if [ $FASE2_RESULT -ne 0 ]; then
    echo ""
    echo "❌ FASE 2 FALLIDA - Abortando activación"
    echo "Troubleshooting:"
    echo "  flyctl logs -f --app sist-cabanas-mvp"
    exit 1
fi

echo ""
read -p "FASE 2 completada. ¿Continuar con FASE 3 (Smoke Tests)? (s/n): " -r CONFIRM

if [[ ! $CONFIRM =~ ^[sS]$ ]]; then
    echo "Abortado por usuario. Para continuar:"
    echo "  bash fase_3_smoke_tests.sh"
    exit 0
fi

echo ""

# ============================================================================
# FASE 3: SMOKE TESTS
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                            EJECUTANDO FASE 3                                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ ! -f "$SCRIPT_DIR/fase_3_smoke_tests.sh" ]; then
    echo "❌ fase_3_smoke_tests.sh no encontrado"
    exit 1
fi

bash "$SCRIPT_DIR/fase_3_smoke_tests.sh"
FASE3_RESULT=$?

echo ""

# ============================================================================
# RESUMEN FINAL
# ============================================================================

if [ $FASE3_RESULT -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                                ║"
    echo "║                  🎉 ¡ACTIVACIÓN COMPLETADA EXITOSAMENTE! 🎉                  ║"
    echo "║                                                                                ║"
    echo "║  ✅ FASE 1: Setup Fly.io + PostgreSQL + Secrets ..................... ✅      ║"
    echo "║  ✅ FASE 2: Deploy a Producción .................................. ✅      ║"
    echo "║  ✅ FASE 3: Smoke Tests (5/5 tests) .............................. ✅      ║"
    echo "║                                                                                ║"
    echo "║  🌐 APLICACIÓN EN VIVO:                                                       ║"
    echo "║     https://sist-cabanas-mvp.fly.dev                                          ║"
    echo "║                                                                                ║"
    echo "║  📊 DASHBOARD:                                                                ║"
    echo "║     https://fly.io/apps/sist-cabanas-mvp                                      ║"
    echo "║                                                                                ║"
    echo "║  🔗 LINKS ÚTILES:                                                             ║"
    echo "║     • Logs en vivo: flyctl logs -f --app sist-cabanas-mvp                    ║"
    echo "║     • Status: flyctl status --app sist-cabanas-mvp                           ║"
    echo "║     • SSH Console: flyctl ssh console --app sist-cabanas-mvp                 ║"
    echo "║     • Métricas: https://sist-cabanas-mvp.fly.dev/metrics                    ║"
    echo "║                                                                                ║"
    echo "║  📝 PRÓXIMOS PASOS:                                                           ║"
    echo "║     1. Monitorear la aplicación durante la primera hora                     ║"
    echo "║     2. Probar webhooks reales (WhatsApp + Mercado Pago)                     ║"
    echo "║     3. Validar iCal sync con Para Irnos                                     ║"
    echo "║     4. Crear alertas en Grafana para errores críticos                       ║"
    echo "║                                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    exit 0
else
    echo "❌ Algunos tests fallaron. Revisa los logs arriba."
    exit 1
fi
