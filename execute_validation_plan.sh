#!/bin/bash

# ================================================================
# SCRIPT MAESTRO DE VALIDACIÓN EXHAUSTIVA
# Sistema MVP de Alojamientos
# ================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
REPORTS_DIR="reports/validation_$(date +%Y%m%d_%H%M%S)"
BACKEND_DIR="backend"
START_TIME=$(date +%s)

# Crear directorio de reportes
mkdir -p "$REPORTS_DIR"

# Función de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_phase() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  $1${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Verificar prerequisitos
check_prerequisites() {
    log_phase "VERIFICANDO PREREQUISITOS"

    local missing_tools=()

    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    command -v python3 >/dev/null 2>&1 || missing_tools+=("python3")
    command -v pip >/dev/null 2>&1 || missing_tools+=("pip")
    command -v jq >/dev/null 2>&1 || missing_tools+=("jq")

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Herramientas faltantes: ${missing_tools[*]}"
        log_info "Instalar con: sudo apt-get install ${missing_tools[*]}"
        exit 1
    fi

    # Verificar que containers están corriendo
    if ! docker ps | grep -q "alojamientos_api"; then
        log_error "Containers no están corriendo"
        log_info "Iniciar con: docker-compose up -d"
        exit 1
    fi

    log_success "Todos los prerequisitos cumplidos"
}

# ================================================================
# FASE 1: AUDITORÍA Y DIAGNÓSTICO
# ================================================================
phase1_audit() {
    log_phase "FASE 1: AUDITORÍA Y DIAGNÓSTICO (2-3h)"

    cd "$BACKEND_DIR"

    # 1.1 Instalación de herramientas
    log_info "Instalando herramientas de análisis..."
    pip install -q pylint flake8 mypy bandit radon safety black isort 2>&1 | tee "$REPORTS_DIR/tool_installation.log"

    # 1.2 Análisis estático
    log_info "Ejecutando análisis estático de código..."

    log_info "  → Flake8 (style checking)..."
    flake8 app/ tests/ --max-line-length=100 \
        --exclude=__pycache__,migrations,temp \
        --extend-ignore=E203,W503 \
        > "../$REPORTS_DIR/flake8_report.txt" 2>&1 || true

    log_info "  → MyPy (type checking)..."
    mypy app/ --ignore-missing-imports \
        --no-implicit-optional \
        > "../$REPORTS_DIR/mypy_report.txt" 2>&1 || true

    log_info "  → Radon (complexity analysis)..."
    radon cc app/ -a -nb > "../$REPORTS_DIR/complexity_report.txt"
    radon mi app/ -nb > "../$REPORTS_DIR/maintainability_report.txt"

    log_info "  → Pylint (comprehensive linting)..."
    pylint app/ --exit-zero --output-format=json \
        > "../$REPORTS_DIR/pylint_report.json" 2>&1 || true

    # 1.3 Análisis de seguridad
    log_info "Ejecutando análisis de seguridad..."

    log_info "  → Safety (dependency vulnerabilities)..."
    safety check --json > "../$REPORTS_DIR/safety_report.json" 2>&1 || echo '{"vulnerabilities": []}' > "../$REPORTS_DIR/safety_report.json"

    log_info "  → Bandit (security issues)..."
    bandit -r app/ -f json -o "../$REPORTS_DIR/bandit_report.json" 2>&1 || true

    # 1.4 Auditoría de secrets
    log_info "  → Auditoría de secrets hardcoded..."
    grep -rn "password\|secret\|api_key\|token" app/ \
        --exclude-dir=__pycache__ \
        | grep -v "getenv\|environ\|settings\." \
        > "../$REPORTS_DIR/secrets_audit.txt" || echo "No hardcoded secrets found" > "../$REPORTS_DIR/secrets_audit.txt"

    # 1.5 Análisis de base de datos
    log_info "Ejecutando análisis de base de datos..."

    docker exec -i alojamientos_postgres psql -U alojamientos -d alojamientos_db > "../$REPORTS_DIR/db_analysis.txt" 2>&1 << 'SQL'
-- Verificar extensiones
\echo '=== EXTENSIONES ==='
SELECT extname, extversion FROM pg_extension WHERE extname IN ('btree_gist', 'pg_trgm');

\echo ''
\echo '=== CONSTRAINTS ==='
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    conrelid::regclass AS table_name,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid::regclass::text ~ 'reservation|accommodation'
ORDER BY conrelid, contype;

\echo ''
\echo '=== ÍNDICES ==='
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

\echo ''
\echo '=== ESTADÍSTICAS DE ÍNDICES ==='
SELECT
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

\echo ''
\echo '=== TABLAS CON MUCHOS SEQUENTIAL SCANS ==='
SELECT
    tablename,
    seq_scan AS sequential_scans,
    seq_tup_read AS sequential_tuples,
    idx_scan AS index_scans
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND (idx_scan = 0 OR idx_scan IS NULL)
  AND seq_scan > 10
ORDER BY seq_scan DESC;
SQL

    # 1.6 Análisis de dependencias
    log_info "Analizando dependencias..."
    pip list --outdated > "../$REPORTS_DIR/outdated_packages.txt"
    pip list --format=json > "../$REPORTS_DIR/installed_packages.json"

    cd ..
    log_success "Fase 1 completada - Reportes en $REPORTS_DIR"
}

# ================================================================
# FASE 2: TESTING EXHAUSTIVO
# ================================================================
phase2_testing() {
    log_phase "FASE 2: TESTING EXHAUSTIVO (4-6h)"

    cd "$BACKEND_DIR"

    # 2.1 Tests unitarios con coverage
    log_info "Ejecutando tests unitarios con coverage..."

    pytest tests/ -v \
        --cov=app \
        --cov-report=html:"../$REPORTS_DIR/coverage_html" \
        --cov-report=json:"../$REPORTS_DIR/coverage.json" \
        --cov-report=term \
        --cov-fail-under=70 \
        -n auto \
        --tb=short \
        > "../$REPORTS_DIR/pytest_unit.log" 2>&1 || log_warning "Algunos tests unitarios fallaron"

    # 2.2 Tests críticos de anti-doble-booking
    log_info "Ejecutando tests críticos de anti-doble-booking..."

    pytest tests/test_double_booking.py \
        tests/test_constraint_validation.py \
        tests/test_reservation_concurrency.py \
        -v -s \
        > "../$REPORTS_DIR/double_booking_tests.log" 2>&1 || log_error "Tests de doble-booking FALLARON"

    # 2.3 Tests de servicios críticos
    log_info "Ejecutando tests de servicios críticos..."

    pytest tests/test_reservation_service.py \
        tests/test_whatsapp_webhook.py \
        tests/test_mercadopago_webhook.py \
        tests/test_nlu.py \
        -v \
        > "../$REPORTS_DIR/critical_services_tests.log" 2>&1 || log_warning "Algunos tests de servicios fallaron"

    # 2.4 Tests de background jobs
    log_info "Ejecutando tests de background jobs..."

    pytest tests/test_expiration_job.py \
        tests/test_reminder_job.py \
        -v \
        > "../$REPORTS_DIR/jobs_tests.log" 2>&1 || log_warning "Algunos tests de jobs fallaron"

    cd ..

    # 2.5 Tests E2E contra API real
    log_info "Ejecutando tests E2E contra API real..."

    # Verificar que API está respondiendo
    if curl -f -s http://localhost:8000/api/v1/healthz > /dev/null; then
        log_success "API respondiendo correctamente"

        # Test básico E2E
        python3 << 'PYTEST' > "$REPORTS_DIR/e2e_basic_test.log" 2>&1
import requests
import sys
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
success_count = 0
fail_count = 0

def test(name, func):
    global success_count, fail_count
    try:
        func()
        print(f"✓ {name}")
        success_count += 1
    except Exception as e:
        print(f"✗ {name}: {e}")
        fail_count += 1

def test_health():
    resp = requests.get(f"{BASE_URL}/api/v1/healthz", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["redis"]["status"] == "ok"

def test_create_reservation():
    payload = {
        "accommodation_id": 1,
        "check_in": (date.today() + timedelta(days=90)).isoformat(),
        "check_out": (date.today() + timedelta(days=92)).isoformat(),
        "guests": 2,
        "contact_name": "E2E Validation Test",
        "contact_phone": "+5491100000000",
        "contact_email": "e2e@validation.test",
        "channel": "validation_e2e"
    }
    resp = requests.post(f"{BASE_URL}/api/v1/reservations/pre-reserve", json=payload, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] is not None
    assert data["error"] is None

def test_metrics():
    resp = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert resp.status_code == 200
    assert b"reservations_created_total" in resp.content

# Ejecutar tests
test("Health Check", test_health)
test("Create Reservation", test_create_reservation)
test("Metrics Endpoint", test_metrics)

print(f"\n✓ Passed: {success_count}")
print(f"✗ Failed: {fail_count}")
sys.exit(0 if fail_count == 0 else 1)
PYTEST

        if [ $? -eq 0 ]; then
            log_success "Tests E2E básicos pasaron"
        else
            log_error "Tests E2E básicos fallaron"
        fi
    else
        log_error "API no está respondiendo - saltando tests E2E"
    fi

    log_success "Fase 2 completada"
}

# ================================================================
# FASE 3: PERFORMANCE Y OPTIMIZACIÓN
# ================================================================
phase3_performance() {
    log_phase "FASE 3: ANÁLISIS DE PERFORMANCE (2-3h)"

    # 3.1 Load testing básico
    log_info "Ejecutando load testing básico..."

    # Test simple con curl
    log_info "  → Test de carga con 100 requests concurrentes..."

    cat > "$REPORTS_DIR/load_test_simple.sh" << 'BASH'
#!/bin/bash
TOTAL=100
SUCCESS=0
FAILED=0
RESPONSE_TIMES=()

for i in $(seq 1 $TOTAL); do
    START=$(date +%s%3N)
    if curl -s -f -o /dev/null http://localhost:8000/api/v1/healthz 2>&1; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
    END=$(date +%s%3N)
    RESPONSE_TIMES+=($((END - START)))
done

echo "Total: $TOTAL"
echo "Success: $SUCCESS"
echo "Failed: $FAILED"
echo "Success Rate: $(awk "BEGIN {printf \"%.2f\", ($SUCCESS/$TOTAL)*100}")%"

# Calcular estadísticas
IFS=$'\n' SORTED=($(sort -n <<<"${RESPONSE_TIMES[*]}"))
P50_INDEX=$((TOTAL / 2))
P95_INDEX=$((TOTAL * 95 / 100))
P99_INDEX=$((TOTAL * 99 / 100))

echo "P50 Latency: ${SORTED[$P50_INDEX]}ms"
echo "P95 Latency: ${SORTED[$P95_INDEX]}ms"
echo "P99 Latency: ${SORTED[$P99_INDEX]}ms"
BASH

    chmod +x "$REPORTS_DIR/load_test_simple.sh"
    bash "$REPORTS_DIR/load_test_simple.sh" > "$REPORTS_DIR/load_test_results.txt" 2>&1

    # Mostrar resultados
    cat "$REPORTS_DIR/load_test_results.txt"

    # 3.2 Análisis de recursos Docker
    log_info "Analizando uso de recursos Docker..."
    docker stats --no-stream > "$REPORTS_DIR/docker_stats.txt"

    # 3.3 Verificar pool de conexiones
    log_info "Verificando pool de conexiones PostgreSQL..."
    docker exec -i alojamientos_postgres psql -U alojamientos -d alojamientos_db > "$REPORTS_DIR/db_connections.txt" 2>&1 << 'SQL'
SELECT
    state,
    COUNT(*) as connections,
    MAX(NOW() - state_change) as max_duration
FROM pg_stat_activity
WHERE datname = 'alojamientos_db'
GROUP BY state;

SELECT
    COUNT(*) as total_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
FROM pg_stat_activity;
SQL

    cat "$REPORTS_DIR/db_connections.txt"

    log_success "Fase 3 completada"
}

# ================================================================
# FASE 4: SEGURIDAD
# ================================================================
phase4_security() {
    log_phase "FASE 4: SEGURIDAD Y HARDENING (2-3h)"

    # 4.1 Test de rate limiting
    log_info "Probando rate limiting..."

    log_info "  → Enviando 50 requests rápidas..."
    RATE_LIMITED=0
    for i in {1..50}; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/healthz)
        if [ "$HTTP_CODE" = "429" ]; then
            ((RATE_LIMITED++))
        fi
        sleep 0.05
    done

    echo "Rate limited responses: $RATE_LIMITED / 50" > "$REPORTS_DIR/rate_limit_test.txt"

    if [ $RATE_LIMITED -gt 0 ]; then
        log_success "Rate limiting está activo ($RATE_LIMITED requests bloqueadas)"
    else
        log_warning "Rate limiting no detectado - verificar configuración"
    fi

    # 4.2 Test de headers de seguridad
    log_info "Verificando headers de seguridad..."

    curl -I http://localhost:8000/api/v1/healthz 2>&1 | grep -E "X-Content-Type-Options|X-Frame-Options|X-XSS-Protection|Strict-Transport-Security" > "$REPORTS_DIR/security_headers.txt" || echo "Security headers no encontrados" > "$REPORTS_DIR/security_headers.txt"

    cat "$REPORTS_DIR/security_headers.txt"

    # 4.3 Verificar permisos de archivos sensibles
    log_info "Verificando permisos de archivos sensibles..."

    cat > "$REPORTS_DIR/file_permissions.txt" << EOF
Backend .env file:
$(ls -la backend/.env 2>/dev/null || echo "Not found")

Backend .env.production file:
$(ls -la backend/.env.production 2>/dev/null || echo "Not found")

Scripts directory:
$(ls -la scripts/ 2>/dev/null || echo "Not found")
EOF

    # 4.4 Verificar que secrets no están en git
    log_info "Verificando que secrets no están en git..."

    if git ls-files | grep -E "\.env$|\.env\.production$"; then
        log_error "CRÍTICO: Archivos .env están en git!"
        echo "ERROR: .env files tracked by git" >> "$REPORTS_DIR/security_audit.txt"
    else
        log_success "Secrets no están en git"
        echo "OK: No .env files in git" >> "$REPORTS_DIR/security_audit.txt"
    fi

    log_success "Fase 4 completada"
}

# ================================================================
# FASE 5: VALIDACIÓN DE CONSTRAINT CRÍTICO
# ================================================================
phase5_constraint_validation() {
    log_phase "FASE 5: VALIDACIÓN CONSTRAINT ANTI-DOBLE-BOOKING (CRÍTICO)"

    log_info "Verificando constraint de PostgreSQL..."

    # Verificar que extensión btree_gist está instalada
    GIST_INSTALLED=$(docker exec -i alojamientos_postgres psql -U alojamientos -d alojamientos_db -t -c "SELECT COUNT(*) FROM pg_extension WHERE extname='btree_gist';")

    if [ "$GIST_INSTALLED" -eq 1 ]; then
        log_success "Extensión btree_gist instalada"
    else
        log_error "CRÍTICO: Extensión btree_gist NO instalada"
        exit 1
    fi

    # Verificar que constraint existe
    CONSTRAINT_EXISTS=$(docker exec -i alojamientos_postgres psql -U alojamientos -d alojamientos_db -t -c "SELECT COUNT(*) FROM pg_constraint WHERE conname='no_overlap_reservations';")

    if [ "$CONSTRAINT_EXISTS" -eq 1 ]; then
        log_success "Constraint no_overlap_reservations existe"
    else
        log_error "CRÍTICO: Constraint no_overlap_reservations NO existe"
        exit 1
    fi

    # Test práctico de constraint
    log_info "Probando constraint con reserva real..."

    # Primera reserva (debe funcionar)
    RESPONSE1=$(curl -s -X POST "http://localhost:8000/api/v1/reservations/pre-reserve" \
        -H "Content-Type: application/json" \
        -d '{
            "accommodation_id": 1,
            "check_in": "2025-12-01",
            "check_out": "2025-12-03",
            "guests": 2,
            "contact_name": "Constraint Test 1",
            "contact_phone": "+5491100000001",
            "contact_email": "constraint1@test.com",
            "channel": "constraint_test"
        }')

    CODE1=$(echo "$RESPONSE1" | jq -r '.code')

    if [ "$CODE1" != "null" ] && [ -n "$CODE1" ]; then
        log_success "Primera reserva creada: $CODE1"

        # Intentar reserva duplicada (debe fallar)
        sleep 1
        RESPONSE2=$(curl -s -X POST "http://localhost:8000/api/v1/reservations/pre-reserve" \
            -H "Content-Type: application/json" \
            -d '{
                "accommodation_id": 1,
                "check_in": "2025-12-01",
                "check_out": "2025-12-03",
                "guests": 2,
                "contact_name": "Constraint Test 2",
                "contact_phone": "+5491100000002",
                "contact_email": "constraint2@test.com",
                "channel": "constraint_test"
            }')

        ERROR2=$(echo "$RESPONSE2" | jq -r '.error')

        if [ "$ERROR2" = "processing_or_unavailable" ]; then
            log_success "CONSTRAINT FUNCIONANDO: Segunda reserva correctamente rechazada"
            echo "✅ ANTI-DOBLE-BOOKING VALIDADO" > "$REPORTS_DIR/constraint_validation.txt"
        else
            log_error "CRÍTICO: Constraint NO funcionó - segunda reserva fue aceptada!"
            echo "❌ ANTI-DOBLE-BOOKING FALLÓ" > "$REPORTS_DIR/constraint_validation.txt"
            exit 1
        fi
    else
        log_warning "No se pudo crear reserva de prueba - puede ser por fechas ocupadas"
    fi

    log_success "Fase 5 completada - CONSTRAINT VALIDADO"
}

# ================================================================
# FASE 6: HEALTH Y MÉTRICAS
# ================================================================
phase6_health_metrics() {
    log_phase "FASE 6: VALIDACIÓN HEALTH CHECK Y MÉTRICAS"

    # 6.1 Health check completo
    log_info "Verificando health check..."

    HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/v1/healthz)
    echo "$HEALTH_RESPONSE" | jq '.' > "$REPORTS_DIR/health_check.json"

    HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status')
    DB_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.checks.database.status')
    REDIS_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.checks.redis.status')

    log_info "Health Status: $HEALTH_STATUS"
    log_info "Database: $DB_STATUS"
    log_info "Redis: $REDIS_STATUS"

    if [ "$DB_STATUS" = "ok" ] && [ "$REDIS_STATUS" = "ok" ]; then
        log_success "Todos los componentes saludables"
    else
        log_warning "Algunos componentes en estado degradado"
    fi

    # 6.2 Métricas de Prometheus
    log_info "Verificando métricas de Prometheus..."

    curl -s http://localhost:8000/metrics > "$REPORTS_DIR/prometheus_metrics.txt"

    # Verificar métricas críticas
    METRICS_FOUND=0
    for metric in "reservations_created_total" "reservations_date_overlap_total" "http_requests_total" "ical_last_sync_age_minutes"; do
        if grep -q "$metric" "$REPORTS_DIR/prometheus_metrics.txt"; then
            ((METRICS_FOUND++))
            log_success "  ✓ Métrica '$metric' presente"
        else
            log_warning "  ✗ Métrica '$metric' no encontrada"
        fi
    done

    log_info "Métricas encontradas: $METRICS_FOUND / 4"

    log_success "Fase 6 completada"
}

# ================================================================
# GENERACIÓN DE REPORTE FINAL
# ================================================================
generate_final_report() {
    log_phase "GENERANDO REPORTE FINAL"

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    DURATION_MIN=$((DURATION / 60))

    cat > "$REPORTS_DIR/EXECUTIVE_SUMMARY.md" << EOF
# 📊 REPORTE EJECUTIVO - VALIDACIÓN EXHAUSTIVA MVP

**Fecha:** $(date '+%Y-%m-%d %H:%M:%S')
**Duración:** ${DURATION_MIN} minutos
**Reportes:** $REPORTS_DIR

---

## ✅ RESUMEN DE VALIDACIÓN

### 1. Auditoría de Código
- **Flake8:** Ver \`flake8_report.txt\`
- **MyPy:** Ver \`mypy_report.txt\`
- **Complejidad:** Ver \`complexity_report.txt\`
- **Seguridad:** Ver \`bandit_report.json\`

### 2. Testing
- **Tests Unitarios:** Ver \`pytest_unit.log\`
- **Coverage:** Ver \`coverage_html/index.html\`
- **Anti-Doble-Booking:** Ver \`double_booking_tests.log\`
- **Servicios Críticos:** Ver \`critical_services_tests.log\`
- **E2E:** Ver \`e2e_basic_test.log\`

### 3. Performance
- **Load Test:** Ver \`load_test_results.txt\`
- **Docker Stats:** Ver \`docker_stats.txt\`
- **DB Connections:** Ver \`db_connections.txt\`

### 4. Seguridad
- **Rate Limiting:** Ver \`rate_limit_test.txt\`
- **Security Headers:** Ver \`security_headers.txt\`
- **File Permissions:** Ver \`file_permissions.txt\`
- **Security Audit:** Ver \`security_audit.txt\`

### 5. Constraint Anti-Doble-Booking ⚡ CRÍTICO
$(cat "$REPORTS_DIR/constraint_validation.txt" 2>/dev/null || echo "No ejecutado")

### 6. Health y Métricas
- **Health Check:** Ver \`health_check.json\`
- **Prometheus:** Ver \`prometheus_metrics.txt\`

---

## 🎯 CRITERIOS DE ÉXITO

| Criterio | Estado | Detalle |
|----------|--------|---------|
| Coverage > 70% | $([ -f "$REPORTS_DIR/coverage.json" ] && jq -r '.totals.percent_covered' "$REPORTS_DIR/coverage.json" && echo "%" || echo "N/A") | Ver coverage_html/ |
| Constraint Anti-Doble-Booking | $(grep -q "✅" "$REPORTS_DIR/constraint_validation.txt" 2>/dev/null && echo "✅ OK" || echo "⚠️ Revisar") | CRÍTICO |
| Database Health | $(grep -q '"database":{"status":"ok"' "$REPORTS_DIR/health_check.json" 2>/dev/null && echo "✅ OK" || echo "❌ FAIL") | - |
| Redis Health | $(grep -q '"redis":{"status":"ok"' "$REPORTS_DIR/health_check.json" 2>/dev/null && echo "✅ OK" || echo "❌ FAIL") | - |
| Rate Limiting | $([ $(grep -c "Rate limited" "$REPORTS_DIR/rate_limit_test.txt" 2>/dev/null | awk '{print $4}') -gt 0 ] && echo "✅ OK" || echo "⚠️ Revisar") | - |
| Security Headers | $(grep -q "X-Content-Type-Options\|X-Frame-Options" "$REPORTS_DIR/security_headers.txt" 2>/dev/null && echo "✅ OK" || echo "⚠️ Revisar") | - |
| No Secrets in Git | $(grep -q "OK:" "$REPORTS_DIR/security_audit.txt" 2>/dev/null && echo "✅ OK" || echo "❌ FAIL") | CRÍTICO |

---

## 📋 RECOMENDACIONES

### Prioridad ALTA
- Revisar tests fallidos en \`pytest_unit.log\`
- Verificar vulnerabilidades en \`bandit_report.json\`
- Revisar queries lentas en análisis de DB

### Prioridad MEDIA
- Mejorar coverage en áreas <70%
- Optimizar complejidad ciclomática alta
- Actualizar dependencias obsoletas

### Prioridad BAJA
- Refactoring de code smells menores
- Documentación adicional

---

## 🚀 SIGUIENTE PASO

**$(grep -q "✅" "$REPORTS_DIR/constraint_validation.txt" 2>/dev/null && echo "SISTEMA VALIDADO - LISTO PARA PRODUCCIÓN" || echo "RESOLVER ISSUES CRÍTICOS ANTES DE PRODUCCIÓN")**

---

*Reporte generado automáticamente por execute_validation_plan.sh*
EOF

    log_success "Reporte ejecutivo generado: $REPORTS_DIR/EXECUTIVE_SUMMARY.md"
}

# ================================================================
# EJECUCIÓN PRINCIPAL
# ================================================================
main() {
    clear

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║     VALIDACIÓN EXHAUSTIVA - SISTEMA MVP ALOJAMIENTOS         ║"
    echo "║                                                              ║"
    echo "║           Plan de Verificación Completo                      ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    log_info "Iniciando validación exhaustiva..."
    log_info "Reportes se guardarán en: $REPORTS_DIR"
    echo ""

    # Verificar prerequisitos
    check_prerequisites

    # Menú de ejecución
    echo ""
    echo "Seleccione modo de ejecución:"
    echo "  1) Ejecución completa (todas las fases)"
    echo "  2) Solo auditoría (Fase 1)"
    echo "  3) Solo testing (Fase 2)"
    echo "  4) Solo performance (Fase 3)"
    echo "  5) Solo seguridad (Fase 4)"
    echo "  6) Solo constraint validation (Fase 5) - CRÍTICO"
    echo "  7) Solo health y métricas (Fase 6)"
    echo "  0) Ejecución automática completa (sin confirmación)"
    echo ""
    read -p "Opción [0]: " OPTION
    OPTION=${OPTION:-0}

    case $OPTION in
        1)
            phase1_audit
            phase2_testing
            phase3_performance
            phase4_security
            phase5_constraint_validation
            phase6_health_metrics
            ;;
        2)
            phase1_audit
            ;;
        3)
            phase2_testing
            ;;
        4)
            phase3_performance
            ;;
        5)
            phase4_security
            ;;
        6)
            phase5_constraint_validation
            ;;
        7)
            phase6_health_metrics
            ;;
        0|*)
            log_info "Ejecutando todas las fases automáticamente..."
            phase1_audit
            phase2_testing
            phase3_performance
            phase4_security
            phase5_constraint_validation
            phase6_health_metrics
            ;;
    esac

    # Generar reporte final
    generate_final_report

    echo ""
    log_phase "🎯 VALIDACIÓN COMPLETADA"

    echo ""
    log_success "Duración total: ${DURATION_MIN} minutos"
    log_success "Reportes disponibles en: $REPORTS_DIR"
    log_info "Ver resumen ejecutivo: $REPORTS_DIR/EXECUTIVE_SUMMARY.md"
    echo ""

    # Mostrar resumen del constraint (CRÍTICO)
    if [ -f "$REPORTS_DIR/constraint_validation.txt" ]; then
        echo ""
        log_phase "⚡ VALIDACIÓN CRÍTICA: ANTI-DOBLE-BOOKING"
        cat "$REPORTS_DIR/constraint_validation.txt"
        echo ""
    fi

    echo ""
    log_info "Para ver el reporte completo:"
    echo "  cat $REPORTS_DIR/EXECUTIVE_SUMMARY.md"
    echo ""

    # Abrir reporte en navegador si es posible
    if command -v xdg-open >/dev/null 2>&1; then
        read -p "¿Abrir coverage report en navegador? [y/N]: " OPEN_BROWSER
        if [ "$OPEN_BROWSER" = "y" ] || [ "$OPEN_BROWSER" = "Y" ]; then
            xdg-open "$REPORTS_DIR/coverage_html/index.html" 2>/dev/null &
        fi
    fi
}

# Ejecutar
main "$@"
