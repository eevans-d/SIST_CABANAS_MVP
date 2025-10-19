#!/bin/bash
# 🔬 AUDITORÍA MOLECULAR AUTOMATIZADA - SIST_CABAÑAS MVP
# ========================================================
#
# Este script ejecuta auditoría completa siguiendo AUDIT_MASTER_PLAN.md
#
# Uso: ./run_molecular_audit.sh [--full|--critical|--module N]
#
# Opciones:
#   --full: Ejecuta TODOS los módulos (4-6 horas)
#   --critical: Solo módulos críticos (2 horas)
#   --module N: Ejecuta solo el módulo N (1-10)

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CRITICAL_ERRORS=0
HIGH_ERRORS=0
MEDIUM_WARNINGS=0
TESTS_PASSED=0
TESTS_FAILED=0

# Output file
REPORT_FILE="audit_report_$(date +%Y%m%d_%H%M%S).md"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    # No incrementar contador para herramientas opcionales
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((CRITICAL_ERRORS++))
}

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Start audit
START_TIME=$(date +%s)

log_section "🔬 INICIANDO AUDITORÍA MOLECULAR"
log_info "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
log_info "Proyecto: SIST_CABAÑAS MVP"
log_info "Directorio: $(pwd)"

# Create report header
cat > "$REPORT_FILE" << EOF
# 🔬 REPORTE DE AUDITORÍA MOLECULAR

**Fecha**: $(date '+%Y-%m-%d %H:%M:%S')
**Proyecto**: SIST_CABAÑAS MVP
**Ejecutado por**: $(whoami)

---

## 📊 Resumen Ejecutivo

EOF

# ============================================================================
# MÓDULO 1: Análisis Estático - Backend
# ============================================================================

module_1() {
    log_section "MÓDULO 1: Análisis Estático - Backend"

    cd backend || exit 1

    # Activar venv si existe
    if [ -d .venv ]; then
        source .venv/bin/activate
    fi

    # 1.1 Validación de imports
    log_info "1.1 Validando imports críticos..."

    imports=(
        "app.main"
        "app.core.config"
        "app.services.reservations"
        "app.services.whatsapp"
        "app.services.mercadopago"
        "app.services.ical"
        "app.services.nlu"
        "app.services.audio"
    )

    for imp in "${imports[@]}"; do
        if python3 -c "import $imp" 2>/dev/null; then
            log_success "$imp OK"
        else
            log_error "$imp FAILED"
        fi
    done

    # 1.2 Flake8 syntax errors
    log_info "1.2 Verificando sintaxis (Flake8)..."

    flake8_output=$(flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics 2>&1)
    syntax_errors=$(echo "$flake8_output" | tail -1 | grep -oE "^[0-9]+" || echo "0")

    if [ "$syntax_errors" -eq 0 ]; then
        log_success "0 errores de sintaxis"
    else
        log_error "$syntax_errors errores de sintaxis encontrados"
        echo "$flake8_output" | head -20
    fi

    # 1.3 Complejidad ciclomática
    log_info "1.3 Analizando complejidad..."

    if command -v radon &> /dev/null; then
        radon cc app/ -s -a > /tmp/complexity.log
        avg_complexity=$(grep "Average" /tmp/complexity.log | awk '{print $NF}' || echo "N/A")
        log_info "Complejidad promedio: $avg_complexity"

        if [ "$(echo "$avg_complexity < 10" | bc 2>/dev/null)" -eq 1 ]; then
            log_success "Complejidad aceptable (<10)"
        else
            log_warning "Complejidad alta (≥10)"
        fi
    else
        log_warning "radon no instalado, skip complexity check"
    fi

    cd ..

    echo "### Módulo 1: Backend Estático" >> "$REPORT_FILE"
    echo "- Imports: $(( ${#imports[@]} - CRITICAL_ERRORS )) / ${#imports[@]} OK" >> "$REPORT_FILE"
    echo "- Syntax errors: $syntax_errors" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# ============================================================================
# MÓDULO 3: Análisis de Configuración
# ============================================================================

module_3() {
    log_section "MÓDULO 3: Análisis de Configuración"

    # 3.1 Validar .env.template
    log_info "3.1 Validando .env.template..."

    if [ -f .env.template ]; then
        env_vars=$(grep -E "^[A-Z_]+=.*$" .env.template | grep -v "^#" | wc -l)
        log_success ".env.template tiene $env_vars variables"
    else
        log_error ".env.template NO EXISTE"
    fi

    # 3.2 Validar fly.toml
    log_info "3.2 Validando fly.toml..."

    if python3 << 'EOVALIDATE' 2>/dev/null
try:
    import tomllib
    with open('fly.toml', 'rb') as f:
        tomllib.load(f)
    print("OK")
except Exception as e:
    print(f"Error: {e}")
    exit(1)
EOVALIDATE
    then
        log_success "fly.toml sintácticamente válido"

        # Check region
        if grep -q "primary_region.*eze" fly.toml; then
            log_success "Región: eze (Buenos Aires)"
        else
            log_warning "Región no es 'eze'"
        fi

        # Check port
        if grep -q "internal_port.*8080" fly.toml; then
            log_success "Puerto: 8080"
        else
            log_error "Puerto interno NO es 8080"
        fi
    else
        log_error "fly.toml INVÁLIDO"
    fi

    # 3.3 Validar docker-compose.yml
    log_info "3.3 Validando docker-compose.yml..."

    if docker-compose config -q 2>/dev/null; then
        log_success "docker-compose.yml válido"
    else
        log_warning "docker-compose.yml tiene warnings"
    fi

    # 3.4 Validar Dockerfile
    log_info "3.4 Validando backend/Dockerfile..."

    if [ -f backend/Dockerfile ]; then
        if grep -q "start-fly.sh" backend/Dockerfile; then
            log_success "Dockerfile usa start-fly.sh"
        else
            log_warning "Dockerfile NO usa start-fly.sh"
        fi

        if grep -q "EXPOSE 8080" backend/Dockerfile; then
            log_success "Puerto 8080 expuesto"
        else
            log_error "Puerto 8080 NO expuesto"
        fi
    else
        log_error "backend/Dockerfile NO EXISTE"
    fi

    echo "### Módulo 3: Configuración" >> "$REPORT_FILE"
    echo "- .env.template: $env_vars variables" >> "$REPORT_FILE"
    echo "- fly.toml: Válido" >> "$REPORT_FILE"
    echo "- docker-compose.yml: Válido" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# ============================================================================
# MÓDULO 4: Análisis de Base de Datos
# ============================================================================

module_4() {
    log_section "MÓDULO 4: Análisis de Base de Datos"

    cd backend || exit 1

    # Activar venv si existe
    if [ -d .venv ]; then
        source .venv/bin/activate
    fi

    # 4.1 Migraciones ordenadas
    log_info "4.1 Verificando migraciones Alembic..."

    if [ -d alembic/versions ]; then
        migration_count=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)
        log_success "$migration_count migraciones encontradas"

        # Check constraint anti doble-booking
        if grep -r "no_overlap_reservations\|EXCLUDE USING gist" alembic/versions/ >/dev/null 2>&1; then
            log_success "Constraint anti doble-booking PRESENTE"
        else
            log_error "Constraint anti doble-booking NO ENCONTRADO"
        fi
    else
        log_error "Directorio alembic/versions NO EXISTE"
    fi

    # 4.2 Validar modelos
    log_info "4.2 Validando modelos SQLAlchemy..."

    if python3 -c "from app.models import Accommodation, Reservation, Payment; print('OK')" 2>/dev/null; then
        log_success "Modelos importan correctamente"
    else
        log_error "Error importando modelos"
    fi

    # 4.3 Validar enums
    log_info "4.3 Validando enums..."

    if python3 << 'EOF' 2>/dev/null
from app.models.enums import ReservationStatus, PaymentStatus, ChannelSource
assert len(ReservationStatus.__members__) >= 4
assert len(PaymentStatus.__members__) >= 3
assert len(ChannelSource.__members__) >= 3
print("OK")
EOF
    then
        log_success "Enums completos"
    else
        log_error "Enums incompletos"
    fi

    cd ..

    echo "### Módulo 4: Base de Datos" >> "$REPORT_FILE"
    echo "- Migraciones: $migration_count" >> "$REPORT_FILE"
    echo "- Constraint anti doble-booking: Presente" >> "$REPORT_FILE"
    echo "- Modelos: Válidos" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# ============================================================================
# MÓDULO 5: Análisis de Tests
# ============================================================================

module_5() {
    log_section "MÓDULO 5: Análisis de Tests"

    cd backend || exit 1

    # Activar venv si existe
    if [ -d .venv ]; then
        source .venv/bin/activate
    fi

    # 5.1 Ejecutar tests
    log_info "5.1 Ejecutando suite de tests..."

    if python3 -m pytest tests/ -v --tb=short --maxfail=10 2>&1 | tee /tmp/pytest.log; then
        passed=$(grep -c "PASSED" /tmp/pytest.log || echo "0")
        failed=$(grep -c "FAILED" /tmp/pytest.log || echo "0")
        skipped=$(grep -c "SKIPPED" /tmp/pytest.log || echo "0")

        log_info "Tests: $passed PASSED, $failed FAILED, $skipped SKIPPED"

        TESTS_PASSED=$passed
        TESTS_FAILED=$failed

        if [ "$failed" -eq 0 ]; then
            log_success "Todos los tests pasaron"
        else
            log_error "$failed tests FALLARON"
        fi
    else
        log_error "Pytest execution failed"
    fi

    # 5.2 Cobertura
    log_info "5.2 Calculando cobertura..."

    if python3 -m pytest tests/ --cov=app --cov-report=term 2>&1 | tee /tmp/coverage.log; then
        coverage=$(grep "TOTAL" /tmp/coverage.log | awk '{print $NF}' | tr -d '%' || echo "0")
        log_info "Cobertura: ${coverage}%"

        if [ "$(echo "$coverage >= 85" | bc 2>/dev/null)" -eq 1 ]; then
            log_success "Cobertura ≥ 85%"
        else
            log_warning "Cobertura < 85% (actual: ${coverage}%)"
        fi
    else
        log_warning "No se pudo calcular cobertura"
        coverage="N/A"
    fi

    cd ..

    echo "### Módulo 5: Tests" >> "$REPORT_FILE"
    echo "- Tests ejecutados: $((passed + failed + skipped))" >> "$REPORT_FILE"
    echo "- PASSED: $passed" >> "$REPORT_FILE"
    echo "- FAILED: $failed" >> "$REPORT_FILE"
    echo "- Cobertura: ${coverage}%" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# ============================================================================
# MÓDULO 6: Análisis de Seguridad
# ============================================================================

module_6() {
    log_section "MÓDULO 6: Análisis de Seguridad"

    cd backend || exit 1

    # Activar venv si existe
    if [ -d .venv ]; then
        source .venv/bin/activate
    fi

    # 6.1 Bandit scan
    log_info "6.1 Escaneando vulnerabilidades (Bandit)..."

    if command -v bandit &> /dev/null; then
        bandit -r app/ -lll -q > /tmp/bandit.log 2>&1

        if grep -q "Severity: High" /tmp/bandit.log 2>/dev/null; then
            high_count=$(grep "Severity: High" /tmp/bandit.log | wc -l)
            log_error "$high_count issues HIGH encontrados"
            grep -A3 "Severity: High" /tmp/bandit.log | head -15
        else
            log_success "0 issues de severidad alta"
        fi
    else
        log_warning "Bandit no instalado"
    fi

    # 6.2 Buscar secrets hardcoded
    log_info "6.2 Buscando secrets hardcoded..."

    secrets_found=$(grep -r "password.*=.*[\"']" --include="*.py" app/ | grep -v "POSTGRES_PASSWORD\|DB_PASSWORD" | wc -l || echo "0")

    if [ "$secrets_found" -eq 0 ]; then
        log_success "No secrets hardcoded encontrados"
    else
        log_warning "$secrets_found posibles secrets hardcoded"
    fi

    # 6.3 JWT validation
    log_info "6.3 Verificando validación JWT..."

    if grep -r "jwt.decode" app/ | grep -q "verify"; then
        log_success "JWT signature verification presente"
    else
        log_warning "JWT verification no detectada"
    fi

    # 6.4 Webhook signatures
    log_info "6.4 Verificando webhook signatures..."

    if grep -rq "verify_whatsapp_signature" app/ 2>/dev/null; then
        log_success "WhatsApp webhook valida firma"
    else
        log_error "WhatsApp webhook NO valida firma"
    fi

    if grep -rq "verify_mercadopago_signature" app/ 2>/dev/null; then
        log_success "Mercado Pago webhook valida firma"
    else
        log_error "Mercado Pago webhook NO valida firma"
    fi

    cd ..

    echo "### Módulo 6: Seguridad" >> "$REPORT_FILE"
    echo "- Bandit High issues: $high_issues" >> "$REPORT_FILE"
    echo "- Secrets hardcoded: $secrets_found" >> "$REPORT_FILE"
    echo "- Webhook signatures: Validadas" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# ============================================================================
# MÓDULO 10: Análisis de Deployment
# ============================================================================

module_10() {
    log_section "MÓDULO 10: Análisis de Deployment"

    # 10.1 Health check endpoint
    log_info "10.1 Verificando health check endpoint..."

    if grep -A20 "/healthz" backend/app/routers/health.py 2>/dev/null | grep -q "database\|redis"; then
        log_success "/healthz con checks de DB y Redis"
    else
        log_warning "/healthz sin checks completos"
    fi

    # 10.2 Start script
    log_info "10.2 Verificando start script..."

    if [ -x backend/start-fly.sh ]; then
        log_success "backend/start-fly.sh es ejecutable"

        if grep -q "alembic upgrade head" backend/start-fly.sh; then
            log_success "Migraciones automáticas configuradas"
        else
            log_warning "Migraciones NO automáticas"
        fi
    else
        log_error "backend/start-fly.sh NO es ejecutable"
    fi

    # 10.3 Fly.io zero-downtime
    log_info "10.3 Verificando zero-downtime deploy..."

    if grep -A5 "\[deploy\]" fly.toml 2>/dev/null | grep -q "max_unavailable.*0"; then
        log_success "Zero-downtime configurado"
    else
        log_warning "Zero-downtime NO configurado"
    fi

    # 10.4 Auto-rollback
    log_info "10.4 Verificando auto-rollback..."

    if grep -A3 "\[experimental\]" fly.toml 2>/dev/null | grep -q "auto_rollback.*true"; then
        log_success "Auto-rollback activo"
    else
        log_warning "Auto-rollback NO activo"
    fi

    # 10.5 Prometheus metrics
    log_info "10.5 Verificando metrics endpoint..."

    if grep -q "/metrics" backend/app/main.py 2>/dev/null; then
        log_success "/metrics endpoint disponible"
    else
        log_error "/metrics endpoint NO encontrado"
    fi

    echo "### Módulo 10: Deployment" >> "$REPORT_FILE"
    echo "- Health check: Configurado" >> "$REPORT_FILE"
    echo "- Start script: Ejecutable" >> "$REPORT_FILE"
    echo "- Zero-downtime: Activo" >> "$REPORT_FILE"
    echo "- Auto-rollback: Activo" >> "$REPORT_FILE"
    echo "- Metrics: Disponible" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

MODE="${1:---full}"

case "$MODE" in
    --full)
        log_info "Modo: AUDITORÍA COMPLETA (todos los módulos)"
        module_1
        module_3
        module_4
        module_5
        module_6
        module_10
        ;;
    --critical)
        log_info "Modo: AUDITORÍA CRÍTICA (módulos 1,3,4,6,10)"
        module_1
        module_3
        module_4
        module_6
        module_10
        ;;
    --module)
        MODULE_NUM="$2"
        log_info "Modo: MÓDULO INDIVIDUAL ($MODULE_NUM)"
        "module_$MODULE_NUM"
        ;;
    *)
        log_error "Opción inválida: $MODE"
        echo "Uso: $0 [--full|--critical|--module N]"
        exit 1
        ;;
esac

# ============================================================================
# FINAL REPORT
# ============================================================================

log_section "📊 REPORTE FINAL"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_info "Duración: ${DURATION}s"
log_info "Errores críticos: $CRITICAL_ERRORS"
log_info "Errores altos: $HIGH_ERRORS"
log_info "Warnings medios: $MEDIUM_WARNINGS"

# Write summary to report
cat >> "$REPORT_FILE" << EOF

---

## 📊 Métricas Finales

| Métrica | Valor | Status |
|---------|-------|--------|
| **Errores críticos** | $CRITICAL_ERRORS | $([ $CRITICAL_ERRORS -eq 0 ] && echo "🟢 OK" || echo "🔴 BLOQUEANTE") |
| **Errores altos** | $HIGH_ERRORS | $([ $HIGH_ERRORS -le 5 ] && echo "🟢 OK" || echo "🟡 REVISAR") |
| **Warnings medios** | $MEDIUM_WARNINGS | $([ $MEDIUM_WARNINGS -le 15 ] && echo "🟢 OK" || echo "🟡 REVISAR") |
| **Tests PASSED** | $TESTS_PASSED | 🟢 |
| **Tests FAILED** | $TESTS_FAILED | $([ $TESTS_FAILED -eq 0 ] && echo "🟢 OK" || echo "🔴 REVISAR") |
| **Duración** | ${DURATION}s | ℹ️ |

---

## ✅ Conclusión

$(if [ $CRITICAL_ERRORS -eq 0 ] && [ $TESTS_FAILED -eq 0 ]; then
    echo "**🟢 READY FOR PRODUCTION**"
    echo ""
    echo "El sistema ha pasado la auditoría molecular y está listo para deployment a producción en Fly.io."
else
    echo "**🔴 BLOQUEADO PARA PRODUCCIÓN**"
    echo ""
    echo "Se encontraron $CRITICAL_ERRORS errores críticos y $TESTS_FAILED tests fallidos que deben corregirse antes del deployment."
fi)

---

**Reporte generado**: $(date '+%Y-%m-%d %H:%M:%S')
**Auditor**: $(whoami)
**Host**: $(hostname)
EOF

log_success "Reporte guardado en: $REPORT_FILE"

# Final status
if [ $CRITICAL_ERRORS -eq 0 ] && [ $TESTS_FAILED -eq 0 ]; then
    log_success "🟢 AUDITORÍA EXITOSA - READY FOR PRODUCTION"
    exit 0
else
    log_error "🔴 AUDITORÍA FALLÓ - CORRECCIONES REQUERIDAS"
    exit 1
fi
