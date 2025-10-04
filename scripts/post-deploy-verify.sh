#!/bin/bash
#
# Post-Deploy Verification Script
#
# Verifica que todos los componentes del sistema estén funcionando
# correctamente después del deploy.
#
# Uso:
#   bash post-deploy-verify.sh [DOMAIN]
#
# Ejemplo:
#   bash post-deploy-verify.sh staging.alojamientos.com
#

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
DOMAIN="${1:-localhost}"
PROTOCOL="https"
BASE_URL="${PROTOCOL}://${DOMAIN}"
API_URL="${BASE_URL}/api/v1"

# Si es localhost, usar http
if [[ "$DOMAIN" == "localhost" ]]; then
    PROTOCOL="http"
    BASE_URL="${PROTOCOL}://${DOMAIN}:8000"
    API_URL="${BASE_URL}/api/v1"
fi

# Contadores
PASSED=0
FAILED=0
WARNINGS=0

# Funciones de output
print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_test() {
    echo -n -e "${YELLOW}[TEST]${NC} $1 ... "
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}"
    if [[ -n "${1:-}" ]]; then
        echo -e "${RED}       $1${NC}"
    fi
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}"
    if [[ -n "${1:-}" ]]; then
        echo -e "${YELLOW}       $1${NC}"
    fi
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Tests de infraestructura
test_docker_running() {
    print_test "Docker daemon está corriendo"

    if docker info &>/dev/null; then
        print_pass
    else
        print_fail "Docker no está corriendo o no tienes permisos"
        return 1
    fi
}

test_containers_running() {
    print_test "Contenedores están corriendo"

    local containers=(
        "alojamientos_api"
        "alojamientos_postgres"
        "alojamientos_redis"
    )

    local all_running=true
    for container in "${containers[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            print_fail "Contenedor $container no está corriendo"
            all_running=false
        fi
    done

    if $all_running; then
        print_pass
    else
        return 1
    fi
}

test_containers_healthy() {
    print_test "Contenedores están healthy"

    local containers=(
        "alojamientos_postgres"
        "alojamientos_redis"
    )

    local all_healthy=true
    for container in "${containers[@]}"; do
        local health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
        if [[ "$health" != "healthy" ]] && [[ "$health" != "no-healthcheck" ]]; then
            print_fail "Contenedor $container no está healthy: $health"
            all_healthy=false
        fi
    done

    if $all_healthy; then
        print_pass
    else
        return 1
    fi
}

# Tests de conectividad
test_domain_resolution() {
    if [[ "$DOMAIN" == "localhost" ]]; then
        print_test "Domain resolution (localhost)"
        print_pass
        return
    fi

    print_test "Dominio resuelve correctamente"

    if host "$DOMAIN" &>/dev/null; then
        local ip=$(host "$DOMAIN" | grep "has address" | awk '{print $4}' | head -1)
        print_pass
        print_info "IP: $ip"
    else
        print_fail "Dominio $DOMAIN no resuelve"
        return 1
    fi
}

test_http_accessible() {
    print_test "HTTP/HTTPS accesible"

    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -k --connect-timeout 10 "$BASE_URL" 2>/dev/null || echo "000")

    if [[ "$status_code" == "200" ]] || [[ "$status_code" == "301" ]] || [[ "$status_code" == "302" ]]; then
        print_pass
        print_info "Status code: $status_code"
    else
        print_fail "No se puede acceder a $BASE_URL (status: $status_code)"
        return 1
    fi
}

# Tests de API
test_health_endpoint() {
    print_test "Health endpoint responde"

    local response=$(curl -s -k --connect-timeout 10 "$API_URL/healthz" 2>/dev/null || echo '{}')
    local status=$(echo "$response" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")

    if [[ "$status" == "healthy" ]]; then
        print_pass

        # Verificar sub-checks
        local db_status=$(echo "$response" | jq -r '.checks.database // "unknown"')
        local redis_status=$(echo "$response" | jq -r '.checks.redis // "unknown"')

        print_info "Database: $db_status, Redis: $redis_status"
    elif [[ "$status" == "degraded" ]]; then
        print_warn "API está degradada"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        print_fail "Health check falló o retornó status: $status"
        echo "$response"
        return 1
    fi
}

test_database_connection() {
    print_test "Conexión a base de datos"

    if docker exec alojamientos_api python -c "
from app.core.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('ok')
except Exception as e:
    print(f'error: {e}')
    exit(1)
" 2>/dev/null | grep -q "ok"; then
        print_pass
    else
        print_fail "No se puede conectar a la base de datos"
        return 1
    fi
}

test_redis_connection() {
    print_test "Conexión a Redis"

    if docker exec alojamientos_redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        print_pass
    else
        print_fail "No se puede conectar a Redis"
        return 1
    fi
}

test_database_migrations() {
    print_test "Migraciones de DB ejecutadas"

    local current_revision=$(docker exec alojamientos_api alembic current 2>/dev/null | grep -oP '[a-f0-9]{12}' | head -1 || echo "none")

    if [[ "$current_revision" != "none" ]] && [[ -n "$current_revision" ]]; then
        print_pass
        print_info "Current revision: $current_revision"
    else
        print_fail "No se encontró revisión de Alembic"
        return 1
    fi
}

test_database_tables() {
    print_test "Tablas de DB creadas"

    local tables=$(docker exec alojamientos_postgres psql -U alojamientos -d alojamientos -t -c "\dt" 2>/dev/null | wc -l)

    if [[ "$tables" -gt 3 ]]; then
        print_pass
        print_info "Tablas encontradas: $tables"
    else
        print_fail "No se encontraron tablas en la base de datos"
        return 1
    fi
}

# Tests de seguridad
test_ssl_certificate() {
    if [[ "$DOMAIN" == "localhost" ]]; then
        print_test "SSL certificate (skipped for localhost)"
        print_pass
        return
    fi

    print_test "Certificado SSL válido"

    local ssl_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)

    if [[ -n "$ssl_info" ]]; then
        local expiry=$(echo "$ssl_info" | grep "notAfter" | cut -d= -f2)
        print_pass
        print_info "Expira: $expiry"
    else
        print_fail "No se pudo verificar certificado SSL"
        return 1
    fi
}

test_security_headers() {
    if [[ "$DOMAIN" == "localhost" ]]; then
        print_test "Security headers (skipped for localhost)"
        print_pass
        return
    fi

    print_test "Headers de seguridad presentes"

    local headers=$(curl -s -I -k "$BASE_URL" 2>/dev/null)

    local has_hsts=$(echo "$headers" | grep -i "Strict-Transport-Security" || echo "")
    local has_xframe=$(echo "$headers" | grep -i "X-Frame-Options" || echo "")
    local has_xcontent=$(echo "$headers" | grep -i "X-Content-Type-Options" || echo "")

    if [[ -n "$has_hsts" ]] && [[ -n "$has_xframe" ]] && [[ -n "$has_xcontent" ]]; then
        print_pass
    else
        print_warn "Algunos headers de seguridad faltan"
        [[ -z "$has_hsts" ]] && print_info "Falta: Strict-Transport-Security"
        [[ -z "$has_xframe" ]] && print_info "Falta: X-Frame-Options"
        [[ -z "$has_xcontent" ]] && print_info "Falta: X-Content-Type-Options"
    fi
}

test_ports_not_exposed() {
    print_test "Puertos DB/Redis no expuestos públicamente"

    # Verificar que postgres y redis NO estén escuchando en 0.0.0.0
    local postgres_bind=$(docker port alojamientos_postgres 5432 2>/dev/null | grep "0.0.0.0" || echo "")
    local redis_bind=$(docker port alojamientos_redis 6379 2>/dev/null | grep "0.0.0.0" || echo "")

    if [[ -z "$postgres_bind" ]] && [[ -z "$redis_bind" ]]; then
        print_pass
    else
        print_warn "Puertos de DB/Redis expuestos públicamente"
        [[ -n "$postgres_bind" ]] && print_info "Postgres expuesto en: $postgres_bind"
        [[ -n "$redis_bind" ]] && print_info "Redis expuesto en: $redis_bind"
    fi
}

# Tests de métricas y observabilidad
test_metrics_endpoint() {
    print_test "Endpoint de métricas accesible"

    local metrics=$(curl -s -k --connect-timeout 10 "$BASE_URL/metrics" 2>/dev/null || echo "")

    if echo "$metrics" | grep -q "reservation_creations_total"; then
        print_pass
    else
        print_warn "Métricas no accesibles o incompletas"
    fi
}

test_logs_present() {
    print_test "Logs de API generándose"

    local log_lines=$(docker logs alojamientos_api --tail 10 2>/dev/null | wc -l)

    if [[ "$log_lines" -gt 0 ]]; then
        print_pass
    else
        print_fail "No se encontraron logs de API"
        return 1
    fi
}

test_no_errors_in_logs() {
    print_test "No hay errores críticos en logs recientes"

    local errors=$(docker logs alojamientos_api --tail 100 2>&1 | grep -i "error\|critical\|exception" | grep -v "No such" | wc -l)

    if [[ "$errors" -eq 0 ]]; then
        print_pass
    else
        print_warn "Se encontraron $errors líneas con errores en logs"
    fi
}

# Tests funcionales
test_webhook_verification() {
    print_test "Webhook WhatsApp verifica correctamente"

    # Test de verificación de webhook (GET)
    local verify_token="test_token_12345"
    local response=$(curl -s -k --connect-timeout 10 \
        "$API_URL/webhooks/whatsapp?hub.mode=subscribe&hub.challenge=test_challenge&hub.verify_token=$verify_token" \
        2>/dev/null || echo "")

    if [[ "$response" == "test_challenge" ]] || echo "$response" | grep -q "verify_token"; then
        print_pass
    else
        print_warn "Verificación de webhook no funcionó como esperado"
        print_info "Response: $response"
    fi
}

test_prereservation_endpoint() {
    print_test "Endpoint de pre-reserva responde"

    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -k --connect-timeout 10 \
        -X POST "$API_URL/reservations/prereserve" \
        -H "Content-Type: application/json" \
        -d '{"accommodation_id":1}' \
        2>/dev/null || echo "000")

    # 422 es esperado (validación), 404 también es aceptable (no existe accommodation)
    if [[ "$status_code" == "422" ]] || [[ "$status_code" == "404" ]] || [[ "$status_code" == "400" ]]; then
        print_pass
        print_info "Endpoint responde correctamente (status: $status_code)"
    elif [[ "$status_code" == "000" ]]; then
        print_fail "No se pudo conectar al endpoint"
        return 1
    else
        print_warn "Status code inesperado: $status_code"
    fi
}

# Resumen final
print_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  RESUMEN DE VERIFICACIÓN${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}✓ Tests pasados:${NC}     $PASSED"
    echo -e "  ${RED}✗ Tests fallados:${NC}    $FAILED"
    echo -e "  ${YELLOW}⚠ Warnings:${NC}          $WARNINGS"
    echo ""

    local total=$((PASSED + FAILED))
    local percentage=$((PASSED * 100 / total))

    echo -e "  Éxito: ${percentage}%"
    echo ""

    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}  ✅ DEPLOY EXITOSO - Todos los tests críticos pasaron${NC}"
        echo ""
        return 0
    elif [[ $FAILED -le 2 ]]; then
        echo -e "${YELLOW}  ⚠️  DEPLOY PARCIAL - Revisar fallos menores${NC}"
        echo ""
        return 1
    else
        echo -e "${RED}  ❌ DEPLOY FALLIDO - Se requiere corrección${NC}"
        echo ""
        return 2
    fi
}

# Main
main() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🔍 Verificación Post-Deploy${NC}"
    echo -e "${BLUE}  Sistema MVP Alojamientos v0.9.9${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    print_info "Target: $DOMAIN"
    print_info "API URL: $API_URL"
    echo ""

    # Infraestructura
    print_header "1. INFRAESTRUCTURA"
    test_docker_running || true
    test_containers_running || true
    test_containers_healthy || true

    # Conectividad
    print_header "2. CONECTIVIDAD"
    test_domain_resolution || true
    test_http_accessible || true

    # API
    print_header "3. API Y SERVICIOS"
    test_health_endpoint || true
    test_database_connection || true
    test_redis_connection || true
    test_database_migrations || true
    test_database_tables || true

    # Seguridad
    print_header "4. SEGURIDAD"
    test_ssl_certificate || true
    test_security_headers || true
    test_ports_not_exposed || true

    # Observabilidad
    print_header "5. OBSERVABILIDAD"
    test_metrics_endpoint || true
    test_logs_present || true
    test_no_errors_in_logs || true

    # Funcional
    print_header "6. TESTS FUNCIONALES"
    test_webhook_verification || true
    test_prereservation_endpoint || true

    # Resumen
    print_summary

    return $?
}

# Ejecutar
main "$@"
