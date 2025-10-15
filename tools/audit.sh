#!/usr/bin/env bash
# tools/audit.sh - Sistema MVP - Comprehensive Audit Script
#
# Este script ejecuta una auditoría completa del sistema sin realizar cambios.
# Genera reportes en el directorio reports/ para análisis posterior.
#
# Uso: ./tools/audit.sh [--quick] [--security-only] [--performance-only]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPORTS_DIR="reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_PREFIX="${REPORTS_DIR}/audit_${TIMESTAMP}"

# Parse arguments
QUICK_MODE=false
SECURITY_ONLY=false
PERFORMANCE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --security-only)
            SECURITY_ONLY=true
            shift
            ;;
        --performance-only)
            PERFORMANCE_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick] [--security-only] [--performance-only]"
            exit 1
            ;;
    esac
done

# Create reports directory
mkdir -p "${REPORTS_DIR}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Sistema MVP - Auditoría Completa del Sistema       ║${NC}"
echo -e "${BLUE}║  Timestamp: $(date +'%Y-%m-%d %H:%M:%S')                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# 1. INFORMACIÓN DEL SISTEMA
# ============================================================================
if [ "$PERFORMANCE_ONLY" = false ]; then
    echo -e "${GREEN}[1/7] Recopilando información del sistema...${NC}"
    {
        echo "=== SYSTEM INFO ==="
        echo "Hostname: $(hostname)"
        echo "OS: $(uname -s) $(uname -r)"
        echo "Architecture: $(uname -m)"
        echo "Python: $(python3 --version 2>&1)"
        echo "Docker: $(docker --version 2>&1 || echo 'Not installed')"
        echo "Git Branch: $(git branch --show-current 2>&1 || echo 'Not a git repo')"
        echo "Git Commit: $(git rev-parse --short HEAD 2>&1 || echo 'Not a git repo')"
        echo ""
        echo "=== DISK USAGE ==="
        df -h | grep -E '^Filesystem|/$|/var|/tmp'
        echo ""
        echo "=== MEMORY ==="
        free -h
    } > "${REPORT_PREFIX}_system_info.txt"
    echo -e "${GREEN}✓ System info: ${REPORT_PREFIX}_system_info.txt${NC}"
fi

# ============================================================================
# 2. ESTRUCTURA DEL PROYECTO
# ============================================================================
if [ "$PERFORMANCE_ONLY" = false ]; then
    echo -e "${GREEN}[2/7] Analizando estructura del proyecto...${NC}"
    {
        echo "=== PROJECT STRUCTURE ==="
        echo "Backend files:"
        find backend -type f -name "*.py" | wc -l
        echo "Test files:"
        find backend/tests -type f -name "test_*.py" | wc -l
        echo "Docker files:"
        find . -maxdepth 2 -name "Dockerfile*" -o -name "docker-compose*.yml"
        echo "Documentation files:"
        find docs -type f -name "*.md" | wc -l 2>/dev/null || echo "0"
        echo ""
        echo "=== TOP 10 LARGEST FILES ==="
        find backend -type f -exec du -h {} + | sort -rh | head -10
        echo ""
        echo "=== RECENT CHANGES (Last 7 days) ==="
        git log --since="7 days ago" --oneline --no-merges | head -20 || echo "Not available"
    } > "${REPORT_PREFIX}_structure.txt"
    echo -e "${GREEN}✓ Project structure: ${REPORT_PREFIX}_structure.txt${NC}"
fi

# ============================================================================
# 3. SEGURIDAD - DEPENDENCY SCANNING
# ============================================================================
if [ "$PERFORMANCE_ONLY" = false ]; then
    echo -e "${GREEN}[3/7] Escaneando dependencias (seguridad)...${NC}"

    # Python - pip-audit
    if command -v pip-audit &> /dev/null; then
        echo "  Running pip-audit..."
        pip-audit -r backend/requirements.txt --format json --output "${REPORT_PREFIX}_pip_audit.json" 2>&1 || true
        echo -e "${GREEN}✓ pip-audit: ${REPORT_PREFIX}_pip_audit.json${NC}"
    else
        echo -e "${YELLOW}⚠ pip-audit not installed. Install: pip install pip-audit${NC}"
    fi

    # Python - safety
    if command -v safety &> /dev/null; then
        echo "  Running safety..."
        safety check -r backend/requirements.txt --json --output "${REPORT_PREFIX}_safety.json" 2>&1 || true
        echo -e "${GREEN}✓ Safety: ${REPORT_PREFIX}_safety.json${NC}"
    else
        echo -e "${YELLOW}⚠ safety not installed. Install: pip install safety${NC}"
    fi

    # Trivy filesystem scan
    if command -v trivy &> /dev/null; then
        echo "  Running trivy..."
        trivy fs --format json --output "${REPORT_PREFIX}_trivy_fs.json" --severity CRITICAL,HIGH backend/ 2>&1 || true
        echo -e "${GREEN}✓ Trivy FS: ${REPORT_PREFIX}_trivy_fs.json${NC}"
    else
        echo -e "${YELLOW}⚠ trivy not installed. Visit: https://aquasecurity.github.io/trivy/${NC}"
    fi

    # Docker image scan (if image exists)
    if docker images | grep -q "alojamientos-api"; then
        if command -v trivy &> /dev/null; then
            echo "  Running trivy on Docker image..."
            trivy image --format json --output "${REPORT_PREFIX}_trivy_image.json" alojamientos-api:latest 2>&1 || true
            echo -e "${GREEN}✓ Trivy Image: ${REPORT_PREFIX}_trivy_image.json${NC}"
        fi
    fi
fi

# ============================================================================
# 4. SEGURIDAD - SECRETS SCANNING
# ============================================================================
if [ "$PERFORMANCE_ONLY" = false ]; then
    echo -e "${GREEN}[4/7] Buscando secretos hardcodeados...${NC}"

    if command -v gitleaks &> /dev/null; then
        echo "  Running gitleaks..."
        gitleaks detect --no-git --source . --report-format json --report-path "${REPORT_PREFIX}_gitleaks.json" 2>&1 || true
        echo -e "${GREEN}✓ Gitleaks: ${REPORT_PREFIX}_gitleaks.json${NC}"
    else
        echo -e "${YELLOW}⚠ gitleaks not installed. Visit: https://github.com/gitleaks/gitleaks${NC}"
    fi

    # Basic manual checks
    {
        echo "=== MANUAL SECRET CHECKS ==="
        echo "Searching for potential secrets in code..."
        echo ""
        echo "API Keys patterns:"
        grep -rn "api[_-]key\s*=\s*['\"]" backend/ --include="*.py" || echo "None found"
        echo ""
        echo "Password patterns:"
        grep -rn "password\s*=\s*['\"][^{]" backend/ --include="*.py" || echo "None found"
        echo ""
        echo "Token patterns:"
        grep -rn "token\s*=\s*['\"][A-Za-z0-9]" backend/ --include="*.py" || echo "None found"
    } > "${REPORT_PREFIX}_manual_secrets.txt"
    echo -e "${GREEN}✓ Manual secret scan: ${REPORT_PREFIX}_manual_secrets.txt${NC}"
fi

# ============================================================================
# 5. TESTING - COVERAGE & QUALITY
# ============================================================================
if [ "$SECURITY_ONLY" = false ]; then
    echo -e "${GREEN}[5/7] Analizando cobertura de tests...${NC}"

    if [ -f backend/requirements.txt ]; then
        # Check if pytest is available
        if command -v pytest &> /dev/null || python3 -m pytest --version &> /dev/null; then
            echo "  Running pytest with coverage..."
            cd backend
            python3 -m pytest --cov=app --cov-report=json --cov-report=term \
                --junit-xml="../${REPORT_PREFIX}_test_results.xml" \
                > "../${REPORT_PREFIX}_test_output.txt" 2>&1 || true
            if [ -f coverage.json ]; then
                mv coverage.json "../${REPORT_PREFIX}_coverage.json"
                echo -e "${GREEN}✓ Coverage: ${REPORT_PREFIX}_coverage.json${NC}"
            fi
            cd ..
        else
            echo -e "${YELLOW}⚠ pytest not installed. Run tests manually.${NC}"
        fi
    fi

    # Count test files and cases
    {
        echo "=== TEST STATISTICS ==="
        echo "Test files: $(find backend/tests -name 'test_*.py' | wc -l)"
        echo "Test functions: $(grep -r "^def test_" backend/tests --include="*.py" | wc -l)"
        echo "Async test functions: $(grep -r "^async def test_" backend/tests --include="*.py" | wc -l)"
        echo "Fixtures: $(grep -r "@pytest.fixture" backend/tests --include="*.py" | wc -l)"
        echo ""
        echo "=== TEST CATEGORIES ==="
        find backend/tests -name 'test_*.py' -exec basename {} \; | sed 's/test_//' | sed 's/.py//' | sort | uniq -c
    } > "${REPORT_PREFIX}_test_stats.txt"
    echo -e "${GREEN}✓ Test stats: ${REPORT_PREFIX}_test_stats.txt${NC}"
fi

# ============================================================================
# 6. PERFORMANCE - CODE ANALYSIS
# ============================================================================
if [ "$SECURITY_ONLY" = false ]; then
    echo -e "${GREEN}[6/7] Analizando performance del código...${NC}"

    {
        echo "=== CODE METRICS ==="
        echo "Total Python LOC:"
        find backend/app -name "*.py" -exec wc -l {} + | tail -1
        echo ""
        echo "Average function length:"
        find backend/app -name "*.py" -exec grep -c "^def \|^async def " {} + | awk '{sum+=$1; count++} END {print sum/count " functions"}'
        echo ""
        echo "=== POTENTIAL PERFORMANCE ISSUES ==="
        echo "Synchronous I/O in async functions:"
        grep -rn "\.read()\|\.write()\|open(" backend/app --include="*.py" | grep -v "async" | head -10 || echo "None found"
        echo ""
        echo "Missing async database operations:"
        grep -rn "session\.execute(" backend/app --include="*.py" | grep -v "await" | head -10 || echo "None found"
        echo ""
        echo "=== COMPLEXITY HOTSPOTS ==="
        echo "Files with >500 LOC:"
        find backend/app -name "*.py" -exec wc -l {} + | sort -rn | awk '$1 > 500' | head -10
    } > "${REPORT_PREFIX}_performance.txt"
    echo -e "${GREEN}✓ Performance analysis: ${REPORT_PREFIX}_performance.txt${NC}"
fi

# ============================================================================
# 7. CONFIGURATION & ENVIRONMENT
# ============================================================================
if [ "$PERFORMANCE_ONLY" = false ]; then
    echo -e "${GREEN}[7/7] Verificando configuración...${NC}"

    {
        echo "=== CONFIGURATION FILES ==="
        ls -lh .env* docker-compose*.yml 2>/dev/null || echo "Configuration files not found"
        echo ""
        echo "=== ENVIRONMENT VARIABLES (from .env.template) ==="
        if [ -f .env.template ]; then
            grep "^[A-Z]" .env.template | grep -v "^#" | head -20
        else
            echo ".env.template not found"
        fi
        echo ""
        echo "=== DOCKER COMPOSE SERVICES ==="
        if [ -f docker-compose.yml ]; then
            grep "^\s*[a-z].*:" docker-compose.yml | grep -v "#"
        fi
        echo ""
        echo "=== MONITORING CONFIGURATION ==="
        ls -lh monitoring/ 2>/dev/null || echo "Monitoring directory not found"
    } > "${REPORT_PREFIX}_configuration.txt"
    echo -e "${GREEN}✓ Configuration: ${REPORT_PREFIX}_configuration.txt${NC}"
fi

# ============================================================================
# SUMMARY REPORT
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Auditoría completa generada${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo "Reportes generados en: ${REPORTS_DIR}/"
ls -lh "${REPORT_PREFIX}"* | awk '{print "  - " $9 " (" $5 ")"}'
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "  1. Revisar vulnerabilidades: ${REPORT_PREFIX}_*audit*.json"
echo "  2. Verificar secretos: ${REPORT_PREFIX}_gitleaks.json"
echo "  3. Analizar cobertura: ${REPORT_PREFIX}_coverage.json"
echo "  4. Revisar performance: ${REPORT_PREFIX}_performance.txt"
echo ""
echo -e "${BLUE}Para análisis detallado, ejecutar:${NC}"
echo "  python3 tools/summarize_vulns.py ${REPORTS_DIR}"
echo ""

# Generate quick summary
{
    echo "=== QUICK SUMMARY ==="
    echo "Audit completed at: $(date)"
    echo ""
    echo "Files analyzed:"
    find backend/app -name "*.py" | wc -l
    echo ""
    echo "Tests available:"
    find backend/tests -name "test_*.py" | wc -l
    echo ""
    if [ -f "${REPORT_PREFIX}_pip_audit.json" ]; then
        echo "Python vulnerabilities found:"
        cat "${REPORT_PREFIX}_pip_audit.json" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('vulnerabilities', [])))" 2>/dev/null || echo "Parse error"
    fi
    echo ""
    echo "Review complete reports in: ${REPORTS_DIR}/"
} > "${REPORT_PREFIX}_SUMMARY.txt"

echo -e "${GREEN}✓ Summary: ${REPORT_PREFIX}_SUMMARY.txt${NC}"
