#!/usr/bin/env bash
set -euo pipefail

# 🧪 Production Smoke Tests
# Ejecuta tests básicos contra un sistema en producción

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${BASE_URL:-https://localhost}"
TIMEOUT=10

log_info() { echo -e "${BLUE}[TEST]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

PASSED=0
FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    log_info "$test_name"
    if eval "$test_command" > /dev/null 2>&1; then
        log_success "$test_name"
        PASSED=$((PASSED+1))
    else
        log_error "$test_name"
        FAILED=$((FAILED+1))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 PRODUCTION SMOKE TESTS"
echo "  Target: $BASE_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Health Check
run_test "Health endpoint responds" \
    "curl -sf --max-time $TIMEOUT \"$BASE_URL/api/v1/healthz\""

# Test 2: Health status
run_test "Health status is healthy" \
    "curl -sf --max-time $TIMEOUT \"$BASE_URL/api/v1/healthz\" | grep -q '\"status\":\"healthy\"'"

# Test 3: Metrics endpoint
run_test "Metrics endpoint accessible" \
    "curl -sf --max-time $TIMEOUT \"$BASE_URL/metrics\""

# Test 4: API docs (opcional en prod)
run_test "OpenAPI schema accessible" \
    "curl -sf --max-time $TIMEOUT \"$BASE_URL/openapi.json\""

# Test 5: HTTPS redirect (si aplica)
if [[ "$BASE_URL" == https://* ]]; then
    HTTP_URL="${BASE_URL/https:/http:}"
    run_test "HTTP redirects to HTTPS" \
        "curl -sI --max-time $TIMEOUT \"$HTTP_URL\" | grep -q '301\\|302'"
fi

# Test 6: Security headers
run_test "Security headers present" \
    "curl -sI --max-time $TIMEOUT \"$BASE_URL/api/v1/healthz\" | grep -qi 'x-frame-options\\|strict-transport-security'"

# Test 7: CORS headers (si aplica)
run_test "CORS configured" \
    "curl -sI --max-time $TIMEOUT \"$BASE_URL/api/v1/healthz\" | grep -qi 'access-control-allow'"

# Test 8: Response time acceptable
run_test "Health endpoint responds < 2s" \
    "timeout 2s curl -sf \"$BASE_URL/api/v1/healthz\" > /dev/null"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
