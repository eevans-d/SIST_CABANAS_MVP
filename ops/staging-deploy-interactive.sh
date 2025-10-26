#!/bin/bash
# ops/staging-deploy-interactive.sh
# Interactive staging deployment orchestrator
# Usage: ./ops/staging-deploy-interactive.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config
APP_NAME="sist-cabanas-mvp"
ENV_FILE="env/.env.fly.staging"
STAGING_URL="https://sist-cabanas-mvp.fly.dev"

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

prompt_user() {
    local question=$1
    local default=$2
    read -rp "$(echo -e "${BLUE}${question}${NC}") [$default]: " response
    echo "${response:-$default}"
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🚀 STAGING DEPLOYMENT - Interactive Guide${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    echo ""
    echo "1. 📋 Pre-requisitos (verificar acceso)"
    echo "2. 🔐 Preparar secretos (copy + fill)"
    echo "3. 📦 Verificar servicios Fly"
    echo "4. 🔑 Cargar secretos a Fly"
    echo "5. 🚀 Desplegar app"
    echo "6. 🔍 Validaciones (health/metrics)"
    echo "7. ⚡ Benchmark runtime"
    echo "8. 🔄 Anti-doble-booking test"
    echo "9. 📊 Registrar reporte"
    echo "10. 🔍 Ver logs"
    echo "11. 🔧 Troubleshooting"
    echo "0. ❌ Salir"
    echo ""
}

# PASO 1: Pre-requisitos
step_prerequisites() {
    log_info "Verificando pre-requisitos..."
    echo ""

    # Fly auth
    if flyctl auth whoami > /dev/null 2>&1; then
        log_success "Flyctl autenticado como: $(flyctl auth whoami)"
    else
        log_error "No estás autenticado en Fly.io"
        log_info "Ejecuta: flyctl auth login"
        return 1
    fi

    # Git status
    if git diff --quiet && git diff --cached --quiet; then
        log_success "Directorio Git limpio"
    else
        log_warning "Tienes cambios no committeados"
        log_info "Considera hacer commit primero"
    fi

    # Check app exists
    if flyctl status -a "$APP_NAME" > /dev/null 2>&1; then
        log_success "App '$APP_NAME' existe en Fly"
    else
        log_warning "App '$APP_NAME' no existe en Fly"
        if prompt_user "¿Crear app?" "y" | grep -q "y"; then
            log_info "Creando app..."
            flyctl apps create "$APP_NAME" --org personal
            log_success "App creada"
        fi
    fi

    # Check env file
    if [ -f "$ENV_FILE" ]; then
        log_success "Archivo de env existe: $ENV_FILE"
    else
        log_warning "No existe $ENV_FILE"
        log_info "Copiar plantilla con PASO 2"
    fi

    echo ""
}

# PASO 2: Preparar secretos
step_prepare_secrets() {
    log_info "Preparando secretos..."
    echo ""

    if [ -f "$ENV_FILE" ]; then
        log_warning "Ya existe $ENV_FILE"
        if prompt_user "¿Sobrescribir con plantilla?" "n" | grep -q "y"; then
            cp env/.env.fly.staging.template "$ENV_FILE"
            log_success "Plantilla copiada"
        fi
    else
        cp env/.env.fly.staging.template "$ENV_FILE"
        log_success "Plantilla creada en $ENV_FILE"
    fi

    echo ""
    log_info "Abre el archivo con tu editor:"
    echo "  vim $ENV_FILE"
    echo ""
    log_warning "Requerido mínimo:"
    echo "  - DATABASE_URL"
    echo "  - REDIS_URL"
    echo "  - JWT_SECRET"
    echo "  - WHATSAPP_ACCESS_TOKEN"
    echo "  - MERCADOPAGO_ACCESS_TOKEN"
    echo ""

    if prompt_user "¿Ya llenaste los valores?" "n" | grep -q "y"; then
        # Validate syntax
        if bash -c "set -a; source $ENV_FILE; set +a; echo ✓" 2>/dev/null; then
            log_success "Sintaxis de env válida"
        else
            log_error "Error en sintaxis de $ENV_FILE"
            return 1
        fi
    else
        log_info "Edita el archivo y vuelve cuando termines"
        return 0
    fi

    echo ""
}

# PASO 3: Verificar servicios
step_verify_services() {
    log_info "Verificando servicios en Fly..."
    echo ""

    # App status
    log_info "Status de app:"
    flyctl status -a "$APP_NAME" | head -5
    echo ""

    # Postgres
    log_info "Status de PostgreSQL:"
    if flyctl postgres status -a sist-cabanas-db > /dev/null 2>&1; then
        flyctl postgres status -a sist-cabanas-db | head -3
    else
        log_warning "PostgreSQL app 'sist-cabanas-db' no encontrada"
        log_info "Puede que esté bajo otro nombre o en otro servicio"
    fi
    echo ""

    # Check env file
    if grep -q "REDIS_URL" "$ENV_FILE"; then
        log_success "REDIS_URL configurado en env"
    fi

    echo ""
}

# PASO 4: Cargar secretos
step_load_secrets() {
    log_info "Cargando secretos a Fly..."
    echo ""

    if [ ! -f "$ENV_FILE" ]; then
        log_error "No existe $ENV_FILE"
        return 1
    fi

    if [ ! -x "ops/set_fly_secrets.sh" ]; then
        log_error "Script ops/set_fly_secrets.sh no es ejecutable"
        return 1
    fi

    log_info "Ejecutando: ./ops/set_fly_secrets.sh $APP_NAME $ENV_FILE"
    ./ops/set_fly_secrets.sh "$APP_NAME" "$ENV_FILE"
    echo ""

    log_info "Verificando secretos cargados:"
    flyctl secrets list -a "$APP_NAME" | head -15
    echo ""
}

# PASO 5: Desplegar
step_deploy() {
    log_info "Desplegando app a Fly..."
    echo ""

    log_warning "Esto puede tomar 2-5 minutos"
    echo ""

    if prompt_user "¿Desplegar ahora?" "y" | grep -q "y"; then
        flyctl deploy --remote-only --strategy rolling -a "$APP_NAME"
        log_success "Deploy completado"
    else
        log_info "Deploy cancelado"
        return 0
    fi

    echo ""
    log_info "Monitoreando logs (Ctrl+C para salir):"
    sleep 2
    timeout 60 flyctl logs -a "$APP_NAME" -f || true
    echo ""
}

# PASO 6: Validaciones
step_validate_health() {
    log_info "Ejecutando validaciones..."
    echo ""

    # Healthz
    log_info "Probando /healthz..."
    if curl -s "$STAGING_URL/api/v1/healthz" > /tmp/health.json 2>&1; then
        python3 -m json.tool < /tmp/health.json 2>/dev/null || cat /tmp/health.json
        log_success "Health check OK"
    else
        log_error "Health check falló"
        return 1
    fi
    echo ""

    # Readyz
    log_info "Probando /readyz..."
    if curl -s "$STAGING_URL/api/v1/readyz" > /tmp/ready.json 2>&1; then
        python3 -m json.tool < /tmp/ready.json 2>/dev/null || cat /tmp/ready.json
        log_success "Readiness check OK"
    else
        log_error "Readiness check falló"
        return 1
    fi
    echo ""

    # Metrics
    log_info "Probando /metrics (primeras 5 líneas)..."
    if curl -s "$STAGING_URL/metrics" | head -5; then
        log_success "Metrics OK"
    else
        log_error "Metrics no accesible"
    fi
    echo ""
}

# PASO 7: Benchmark
step_benchmark() {
    log_info "Ejecutando benchmark..."
    echo ""

    if [ ! -x "ops/smoke_and_benchmark.sh" ]; then
        log_error "Script ops/smoke_and_benchmark.sh no ejecutable"
        return 1
    fi

    log_warning "Esto toma ~30 segundos"
    ./ops/smoke_and_benchmark.sh "$STAGING_URL"
    echo ""
}

# PASO 8: Anti-doble-booking
step_overlap_test() {
    log_info "Validando anti-doble-booking..."
    echo ""

    # Check if script exists
    if [ ! -f "backend/scripts/concurrency_overlap_test.py" ]; then
        log_error "Script no encontrado"
        return 1
    fi

    log_info "Nota: Esto requiere acomodaciones en DB"
    if prompt_user "¿Ejecutar test de overlap?" "y" | grep -q "y"; then
        ACC_ID=$(prompt_user "ID de acomodación a testear" "1")
        CHECK_IN=$(prompt_user "Check-in (YYYY-MM-DD)" "2025-11-15")
        CHECK_OUT=$(prompt_user "Check-out (YYYY-MM-DD)" "2025-11-17")

        RUN_MUTATING=1 PYTHONPATH=backend python backend/scripts/concurrency_overlap_test.py \
            --base-url "$STAGING_URL" \
            --accommodation-id "$ACC_ID" \
            --check-in "$CHECK_IN" \
            --check-out "$CHECK_OUT" \
            --concurrency 2 || true
    fi
    echo ""
}

# PASO 9: Registrar reporte
step_report() {
    log_info "Generando reporte..."
    echo ""

    TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
    REPORT_FILE="backend/docs/STAGING_REPORT_$TIMESTAMP.md"

    cat > "$REPORT_FILE" << 'EOF'
# Staging Deployment Report

Generado: $(date)
Base URL: https://sist-cabanas-mvp.fly.dev
Ambiente: staging

## Validaciones

### Health Check
```
[Ejecuta: curl -s https://sist-cabanas-mvp.fly.dev/api/v1/healthz | python -m json.tool]
```

### Benchmark
```
[Pega salida de: ./ops/smoke_and_benchmark.sh https://sist-cabanas-mvp.fly.dev]
```

### Anti-Doble-Booking
```
[Pega salida de: RUN_MUTATING=1 PYTHONPATH=backend python backend/scripts/concurrency_overlap_test.py ...]
```

## SLOs

- [ ] p95 /healthz < 200ms
- [ ] p95 /accommodations < 3s
- [ ] error-rate < 1%
- [ ] Overlay constraint activo (1 fail esperado)

## Checklist

- [ ] Health check: 200 OK
- [ ] Metrics: accesible
- [ ] Benchmark: p95 < 3s
- [ ] Anti-doble-booking: 1 falla por constraint
- [ ] No errores críticos en logs

## Status

✅ STAGING DEPLOYMENT COMPLETE

---

Siguiente: Esperar 24h estabilidad, luego promover a PRODUCCIÓN
EOF

    log_success "Reporte guardado: $REPORT_FILE"
    cat "$REPORT_FILE"
    echo ""
}

# PASO 10: Ver logs
step_logs() {
    log_info "Viendo logs de staging..."
    echo ""
    log_warning "Presiona Ctrl+C para salir"
    flyctl logs -a "$APP_NAME" -f
}

# PASO 11: Troubleshooting
step_troubleshoot() {
    log_info "Herramientas de troubleshooting..."
    echo ""

    echo "1. Ver últimos logs (200 líneas)"
    echo "2. DB status"
    echo "3. Restart app"
    echo "4. Rollback a versión anterior"
    echo "0. Volver al menú"
    echo ""

    read -rp "Selecciona opción: " opt
    case $opt in
        1) flyctl logs -a "$APP_NAME" --lines 200 | less ;;
        2) flyctl postgres status -a sist-cabanas-db 2>/dev/null || echo "PostgreSQL app no encontrado" ;;
        3) flyctl restart -a "$APP_NAME"; log_success "App reiniciada" ;;
        4) flyctl releases -a "$APP_NAME"; read -rp "Release ID a revertir: " rel_id; flyctl releases rollback "$rel_id" -a "$APP_NAME" ;;
        0) return ;;
    esac
    echo ""
}

# Main loop
main() {
    while true; do
        show_menu
        read -rp "Selecciona paso (0-11): " choice

        case $choice in
            1) step_prerequisites ;;
            2) step_prepare_secrets ;;
            3) step_verify_services ;;
            4) step_load_secrets ;;
            5) step_deploy ;;
            6) step_validate_health ;;
            7) step_benchmark ;;
            8) step_overlap_test ;;
            9) step_report ;;
            10) step_logs ;;
            11) step_troubleshoot ;;
            0)
                log_info "¡Hasta luego!"
                exit 0
                ;;
            *)
                log_error "Opción inválida"
                ;;
        esac

        read -rp "Presiona Enter para continuar..."
    done
}

# Run
main "$@"
