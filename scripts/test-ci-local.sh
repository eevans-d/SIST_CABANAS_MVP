#!/bin/bash
# Test local de CI workflow - Simula GitHub Actions CI

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                  🧪 TEST LOCAL - CI WORKFLOW SIMULATION                      ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función de test
test_step() {
    local name="$1"
    local command="$2"

    echo -e "${YELLOW}▶ Testing: $name${NC}"
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: $name${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL: $name${NC}"
        return 1
    fi
}

cd "$(dirname "$0")/.."

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FASE 1: Verificación de Estructura"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar archivos críticos
test_step "Workflow ci.yml existe" "[ -f .github/workflows/ci.yml ]"
test_step "Workflow deploy-staging.yml existe" "[ -f .github/workflows/deploy-staging.yml ]"
test_step "Workflow security-scan.yml existe" "[ -f .github/workflows/security-scan.yml ]"
test_step "Documentación CI/CD existe" "[ -f docs/ci-cd/GITHUB_ACTIONS_GUIDE.md ]"
test_step "Backend requirements.txt existe" "[ -f backend/requirements.txt ]"
test_step "Backend tests/ directorio existe" "[ -d backend/tests ]"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FASE 2: Validación YAML"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Validar YAML
test_step "ci.yml sintaxis válida" "python3 -c \"import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))\""
test_step "deploy-staging.yml sintaxis válida" "python3 -c \"import yaml; yaml.safe_load(open('.github/workflows/deploy-staging.yml'))\""
test_step "security-scan.yml sintaxis válida" "python3 -c \"import yaml; yaml.safe_load(open('.github/workflows/security-scan.yml'))\""

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FASE 3: Verificación de Código Python"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar código Python (sin ejecutar tests completos)
cd backend

# Check if venv exists
if [ -d "../.venv" ]; then
    echo "ℹ️  Usando entorno virtual .venv"
    source ../.venv/bin/activate
fi

test_step "Python 3.12 disponible" "python3 --version | grep -q '3.12'"
test_step "pip instalado" "pip --version"

# Check imports sin ejecutar nada
test_step "Backend app importable" "python3 -c 'import sys; sys.path.insert(0, \".\"); from app.main import app'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FASE 4: Verificación de Herramientas de Linting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check herramientas (solo verificar si existen)
test_step "black instalado" "which black || pip show black"
test_step "flake8 instalado" "which flake8 || pip show flake8"
test_step "isort instalado" "which isort || pip show isort"
test_step "bandit instalado" "which bandit || pip show bandit"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RESUMEN DE TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "✅ Workflows GitHub Actions: Sintaxis válida"
echo "✅ Documentación CI/CD: Completa"
echo "✅ Estructura del proyecto: Correcta"
echo "✅ Python backend: Importable"
echo ""
echo "🎯 SIGUIENTE PASO: Crear PR o push a main para ejecutar CI workflow real"
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                  ✅ TEST LOCAL COMPLETADO - LISTO PARA CI                   ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
