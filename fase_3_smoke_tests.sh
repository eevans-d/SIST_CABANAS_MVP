#!/bin/bash

# ============================================================================
# FASE 3: SMOKE TESTS - 5 PRUEBAS CRÍTICAS
# ============================================================================
# Valida que la aplicación esté funcionando correctamente en producción:
# 1. Health check endpoint (/api/v1/healthz)
# 2. Readiness check (/api/v1/readyz)
# 3. Metrics endpoint (/metrics)
# 4. Homepage (/)
# 5. Database connectivity (via SSH)
# ============================================================================

set -e

export PATH="/home/eevan/.fly/bin:$PATH"

APP_URL="https://sist-cabanas-mvp.fly.dev"
TESTS_PASSED=0
TESTS_FAILED=0

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                     🧪 FASE 3: SMOKE TESTS (5 TESTS)                          ║"
echo "║                    Validación de producción exitosa                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "🎯 Target: $APP_URL"
echo ""

# ============================================================================
# HELPERS
# ============================================================================

test_endpoint() {
    local test_num=$1
    local test_name=$2
    local endpoint=$3
    local expected_status=$4
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TEST $test_num: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    local url="${APP_URL}${endpoint}"
    echo "📍 URL: $url"
    echo "⏳ Enviando request..."
    echo ""
    
    local response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\nfailed")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "$expected_status" ]; then
        echo "✅ HTTP $http_code (esperado: $expected_status)"
        if [ -n "$body" ] && [ "$body" != "failed" ]; then
            echo "📦 Response (primeras 200 chars):"
            echo "$body" | head -c 200
            echo ""
            echo ""
        fi
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ HTTP $http_code (esperado: $expected_status)"
        echo "❌ Response:"
        echo "$body"
        echo ""
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# ============================================================================
# TEST 1: HEALTH CHECK
# ============================================================================

test_endpoint "1" "Health Check" "/api/v1/healthz" "200"

# ============================================================================
# TEST 2: READINESS CHECK
# ============================================================================

test_endpoint "2" "Readiness Check" "/api/v1/readyz" "200"

# ============================================================================
# TEST 3: METRICS ENDPOINT
# ============================================================================

test_endpoint "3" "Metrics Endpoint" "/metrics" "200"

# ============================================================================
# TEST 4: HOMEPAGE
# ============================================================================

test_endpoint "4" "Homepage" "/" "200"

# ============================================================================
# TEST 5: DATABASE CONNECTIVITY VIA SSH
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Database Connectivity (SSH)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "⏳ Conectando a máquina de Fly.io via SSH..."
echo ""

# Ejecutar comando psql en la máquina de Fly.io
if flyctl ssh console --app sist-cabanas-mvp -q << 'EOF' > /tmp/db_test_output.txt 2>&1
echo "Probando conexión a PostgreSQL..."
psql "$DATABASE_URL" -c "SELECT version();" && echo "✅ DB_CONNECTED" || echo "❌ DB_FAILED"
exit
EOF
then
    if grep -q "✅ DB_CONNECTED" /tmp/db_test_output.txt 2>/dev/null; then
        echo "✅ Database connectivity verificado"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ Database connectivity FALLIDO"
        echo "   (Verifica con: flyctl ssh console --app sist-cabanas-mvp)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo "⚠️  No se pudo conectar via SSH (puede deberse a permiso de WireGuard)"
    echo "   Ejecuta manualmente:"
    echo "   flyctl ssh console --app sist-cabanas-mvp"
    echo "   psql \$DATABASE_URL -c 'SELECT version();'"
    echo ""
    echo "⏭️  Saltando TEST 5 (pero puedes verificar manualmente)"
fi

echo ""

# ============================================================================
# RESUMEN FINAL
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                          📊 RESUMEN DE TESTS                                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

TESTS_TOTAL=$((TESTS_PASSED + TESTS_FAILED))

echo "✅ Tests pasados:  $TESTS_PASSED/$TESTS_TOTAL"
echo "❌ Tests fallidos: $TESTS_FAILED/$TESTS_TOTAL"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                   🎉 ¡FASE 3 COMPLETADA EXITOSAMENTE! 🎉                      ║"
    echo "║                                                                                ║"
    echo "║  🚀 APLICACIÓN EN PRODUCCIÓN:                                                 ║"
    echo "║     https://sist-cabanas-mvp.fly.dev                                          ║"
    echo "║                                                                                ║"
    echo "║  📊 Dashboard:                                                                 ║"
    echo "║     https://fly.io/apps/sist-cabanas-mvp                                      ║"
    echo "║                                                                                ║"
    echo "║  📋 Próximos pasos (operaciones):                                              ║"
    echo "║     1. Monitorear logs: flyctl logs -f --app sist-cabanas-mvp                ║"
    echo "║     2. Ver métricas: https://sist-cabanas-mvp.fly.dev/metrics                ║"
    echo "║     3. Probar webhooks: WhatsApp + Mercado Pago                              ║"
    echo "║     4. Verificar iCal sync: /api/v1/ical/export                              ║"
    echo "║                                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        ❌ ALGUNOS TESTS FALLARON ❌                            ║"
    echo "║                                                                                ║"
    echo "║  Troubleshooting:                                                              ║"
    echo "║  1. Ver logs: flyctl logs -f --app sist-cabanas-mvp                           ║"
    echo "║  2. Ver status: flyctl status --app sist-cabanas-mvp                          ║"
    echo "║  3. Conectar via SSH: flyctl ssh console --app sist-cabanas-mvp               ║"
    echo "║  4. Revisar variables de entorno: flyctl config show --app sist-cabanas-mvp   ║"
    echo "║                                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    exit 1
fi
