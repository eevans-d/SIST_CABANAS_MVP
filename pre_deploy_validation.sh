#!/bin/bash
# 🔍 PRE-DEPLOYMENT VALIDATION SCRIPT
# =====================================
# Valida TODOS los componentes antes de flyctl deploy
# 
# Uso: ./pre_deploy_validation.sh
#
# Exit codes:
#   0 = Ready para deploy
#   1 = Errores encontrados, NO DEPLOY

# NO usar set -e para permitir que todas las validaciones se ejecuten
set +e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Header
cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║     PRE-DEPLOYMENT VALIDATION - Fly.io Deployment Ready       ║
╚════════════════════════════════════════════════════════════════╝
EOF

START_TIME=$(date +%s)

# ============================================================================
# FASE 1: VALIDACIÓN DE CONFIGURACIÓN
# ============================================================================

log_section "FASE 1: Validación de Configuración"

# PASO 1: Validar fly.toml
log_info "PASO 1: Validando fly.toml..."

if [ ! -f fly.toml ]; then
    log_error "fly.toml NO EXISTE"
else
    python3 << 'PYEOF'
try:
    import tomllib
    with open('fly.toml', 'rb') as f:
        config = tomllib.load(f)
    
    # Validaciones críticas
    if not config.get('app'):
        print("❌ ERROR: Falta 'app' en fly.toml")
        exit(1)
    
    if config.get('primary_region') != 'eze':
        print("⚠️  WARNING: Región no es 'eze' (Buenos Aires)")
    
    # Validar [deploy]
    deploy = config.get('deploy', {})
    if 'release_command' in deploy:
        print(f"✅ Release command: {deploy['release_command']}")
    
    # Validar [[services]]
    services = config.get('services', [])
    if services and services[0].get('internal_port') != 8080:
        print("❌ ERROR: internal_port debe ser 8080")
        exit(1)
    
    print("✅ fly.toml válido")
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
PYEOF
    
    pyexit=$?
    if [ $pyexit -eq 0 ]; then
        log_success "fly.toml válido"
    else
        log_error "fly.toml tiene errores"
    fi
fi

# PASO 2: Validar Dockerfile
log_info "PASO 2: Validando Dockerfile..."

if [ ! -f backend/Dockerfile ]; then
    log_error "backend/Dockerfile NO EXISTE"
else
    # Verificar líneas críticas
    grep -q "FROM python:" backend/Dockerfile || log_warning "No especifica base image Python"
    grep -q "EXPOSE 8080" backend/Dockerfile || log_error "No expone puerto 8080"
    grep -q "start-fly.sh" backend/Dockerfile && log_success "Usa start-fly.sh" || log_warning "No usa start-fly.sh"
    
    log_success "Dockerfile presente y validado"
fi

# PASO 3: Validar start-fly.sh
log_info "PASO 3: Validando start-fly.sh..."

if [ ! -f backend/start-fly.sh ]; then
    log_error "backend/start-fly.sh NO EXISTE"
elif [ ! -x backend/start-fly.sh ]; then
    log_error "start-fly.sh no es ejecutable (chmod +x requerido)"
else
    grep -q "alembic upgrade head" backend/start-fly.sh && log_success "Migraciones automáticas" || log_warning "Sin migraciones"
    grep -qE "gunicorn|uvicorn" backend/start-fly.sh && log_success "Servidor ASGI configurado" || log_error "Sin comando de inicio"
fi

# PASO 4: Validar Variables de Entorno
log_info "PASO 4: Validando .env.template..."

if [ ! -f .env.template ]; then
    log_error ".env.template NO EXISTE"
else
    var_count=$(grep -cE "^[A-Z_]+=.*$" .env.template | grep -v "^#" || echo "0")
    if [ "$var_count" -gt 40 ]; then
        log_success ".env.template tiene $var_count variables"
    else
        log_warning ".env.template tiene pocas variables ($var_count)"
    fi
fi

# PASO 5: Validar Dependencias Python
log_info "PASO 5: Validando dependencias Python..."

if [ ! -f backend/requirements.txt ]; then
    log_error "backend/requirements.txt NO EXISTE"
else
    cd backend
    
    if [ -d .venv ]; then
        source .venv/bin/activate
    fi
    
    # Verificar versiones fijas
    if grep -qE '==|~=' requirements.txt; then
        log_success "requirements.txt con versiones fijas"
    else
        log_warning "requirements.txt sin versiones fijas"
    fi
    
    # CVE check (si pip-audit está disponible)
    if command -v pip-audit &> /dev/null; then
        log_info "Ejecutando pip-audit..."
        if pip-audit --desc > /tmp/pip_audit_pre.log 2>&1; then
            log_success "0 CVEs críticas en dependencias"
        else
            critical=$(grep -c "Critical" /tmp/pip_audit_pre.log || echo "0")
            if [ "$critical" -gt 0 ]; then
                log_error "$critical CVEs CRÍTICAS encontradas"
            else
                log_success "pip-audit completado"
            fi
        fi
    else
        log_warning "pip-audit no instalado (skip CVE check)"
    fi
    
    cd ..
fi

# ============================================================================
# FASE 2: VALIDACIÓN DE BASE DE DATOS
# ============================================================================

log_section "FASE 2: Validación de Base de Datos"

# PASO 6: Verificar Migraciones
log_info "PASO 6: Verificando migraciones Alembic..."

if [ ! -d backend/alembic/versions ]; then
    log_error "Directorio alembic/versions NO EXISTE"
else
    migration_count=$(ls -1 backend/alembic/versions/*.py 2>/dev/null | wc -l)
    if [ "$migration_count" -eq 0 ]; then
        log_error "No hay migraciones en alembic/versions/"
    else
        log_success "$migration_count migraciones encontradas"
    fi
fi

# PASO 7: Validar Constraint Anti-Double-Booking
log_info "PASO 7: Validando constraint anti-double-booking..."

if grep -rq "EXCLUDE USING gist" backend/alembic/versions/ 2>/dev/null; then
    log_success "Constraint anti-double-booking PRESENTE"
else
    log_error "Constraint anti-double-booking NO ENCONTRADO"
fi

if grep -rq "btree_gist" backend/alembic/versions/ 2>/dev/null; then
    log_success "Extensión btree_gist configurada"
else
    log_warning "btree_gist no detectada en migraciones"
fi

# ============================================================================
# FASE 3: VALIDACIÓN DE SERVICIOS EXTERNOS
# ============================================================================

log_section "FASE 3: Validación de Servicios Externos"

# PASO 8: Verificar Imports
log_info "PASO 8: Verificando imports críticos..."

cd backend

if [ -d .venv ]; then
    source .venv/bin/activate
fi

critical_imports=(
    "app.main"
    "app.core.config"
    "app.services.reservations"
    "app.services.whatsapp"
    "app.services.mercadopago"
    "app.services.ical"
)

import_errors=0
for imp in "${critical_imports[@]}"; do
    if python3 -c "import $imp" 2>/dev/null; then
        log_success "$imp OK"
    else
        log_error "$imp FAILED"
        ((import_errors++))
    fi
done

if [ $import_errors -eq 0 ]; then
    log_success "Todos los imports críticos OK"
fi

cd ..

# ============================================================================
# FASE 4: VALIDACIÓN DE SEGURIDAD
# ============================================================================

log_section "FASE 4: Validación de Seguridad"

# PASO 9: Bandit Security Scan
log_info "PASO 9: Ejecutando Bandit security scan..."

cd backend

if [ -d .venv ]; then
    source .venv/bin/activate
fi

if command -v bandit &> /dev/null; then
    bandit -r app/ -lll -q > /tmp/bandit_pre.log 2>&1
    
    if grep -q "Severity: High" /tmp/bandit_pre.log 2>/dev/null; then
        high_count=$(grep "Severity: High" /tmp/bandit_pre.log | wc -l)
        log_error "$high_count issues HIGH encontrados"
        grep -A3 "Severity: High" /tmp/bandit_pre.log | head -10
    else
        log_success "Bandit: 0 HIGH issues"
    fi
else
    log_warning "Bandit no instalado"
fi

cd ..

# PASO 10: Verificar Webhook Signatures
log_info "PASO 10: Verificando validación de webhook signatures..."

if grep -rq "verify_whatsapp_signature" backend/app/routers/ 2>/dev/null; then
    log_success "WhatsApp webhook valida firma"
else
    log_error "WhatsApp webhook NO valida firma"
fi

if grep -rq "verify_mercadopago_signature" backend/app/routers/ 2>/dev/null; then
    log_success "Mercado Pago webhook valida firma"
else
    log_error "Mercado Pago webhook NO valida firma"
fi

# ============================================================================
# FASE 5: VALIDACIÓN DE DEPLOYMENT
# ============================================================================

log_section "FASE 5: Validación de Deployment"

# PASO 11: Verificar Health Check
log_info "PASO 11: Verificando health check endpoint..."

if grep -rq "/healthz" backend/app/routers/health.py 2>/dev/null; then
    log_success "Health check endpoint presente"
    
    # Verificar que tiene checks de DB y Redis
    if grep -A20 "/healthz" backend/app/routers/health.py | grep -q "database"; then
        log_success "Health check valida DB"
    else
        log_warning "Health check sin validación de DB"
    fi
    
    if grep -A20 "/healthz" backend/app/routers/health.py | grep -q "redis"; then
        log_success "Health check valida Redis"
    else
        log_warning "Health check sin validación de Redis"
    fi
else
    log_error "Health check endpoint NO ENCONTRADO"
fi

# PASO 12: Verificar Metrics Endpoint
log_info "PASO 12: Verificando metrics endpoint..."

if grep -rq "/metrics" backend/app/main.py 2>/dev/null; then
    log_success "Metrics endpoint presente"
else
    log_warning "Metrics endpoint no detectado"
fi

# PASO 13: Verificar Zero-Downtime Config
log_info "PASO 13: Verificando zero-downtime deployment..."

if grep -A5 "\[deploy\]" fly.toml 2>/dev/null | grep -q "max_unavailable.*0"; then
    log_success "Zero-downtime configurado (max_unavailable=0)"
else
    log_warning "Zero-downtime NO configurado"
fi

if grep -A3 "\[experimental\]" fly.toml 2>/dev/null | grep -q "auto_rollback.*true"; then
    log_success "Auto-rollback activado"
else
    log_warning "Auto-rollback NO activado"
fi

# PASO 14: Verificar Git Status
log_info "PASO 14: Verificando estado de Git..."

if git diff-index --quiet HEAD -- 2>/dev/null; then
    log_success "Working tree limpio (todos los cambios committed)"
else
    log_warning "Hay cambios sin commit"
    git status --short
fi

# PASO 15: Verificar Fly.io CLI
log_info "PASO 15: Verificando Fly.io CLI..."

if command -v flyctl &> /dev/null; then
    flyctl_version=$(flyctl version | head -1)
    log_success "flyctl instalado: $flyctl_version"
    
    # Verificar autenticación
    if flyctl auth whoami &> /dev/null; then
        log_success "flyctl autenticado"
    else
        log_error "flyctl NO autenticado (ejecuta: flyctl auth login)"
    fi
else
    log_error "flyctl NO instalado"
    echo "Instala desde: https://fly.io/docs/hands-on/install-flyctl/"
fi

# ============================================================================
# REPORTE FINAL
# ============================================================================

log_section "REPORTE FINAL"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
log_info "Duración total: ${DURATION}s"
echo ""

if [ $ERRORS -eq 0 ]; then
    cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║                  ✅ VALIDACIÓN EXITOSA                         ║
║                                                                ║
║   Todos los checks críticos pasaron.                          ║
║   El proyecto está READY FOR DEPLOYMENT a Fly.io              ║
║                                                                ║
║   Próximo paso:                                               ║
║   $ flyctl deploy --app sist-cabanas-mvp                      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF
    
    echo ""
    log_info "Errores:  $ERRORS"
    log_info "Warnings: $WARNINGS"
    echo ""
    
    exit 0
else
    cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║                  ❌ VALIDACIÓN FALLIDA                         ║
║                                                                ║
║   Se encontraron errores críticos que BLOQUEAN el deploy.     ║
║   Revisa los errores arriba y corrígelos antes de desplegar.  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF
    
    echo ""
    log_error "Errores:  $ERRORS (BLOQUEANTES)"
    log_warning "Warnings: $WARNINGS"
    echo ""
    
    exit 1
fi
