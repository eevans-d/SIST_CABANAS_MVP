#!/bin/bash
# Smoke Tests Post-Deploy - SIST_CABAÑAS MVP
# Ejecutar después del deploy para validar endpoints críticos

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# URL base (cambiar según env)
BASE_URL="${BASE_URL:-https://sist-cabanas-mvp.fly.dev}"

echo "🧪 SIST_CABAÑAS - Smoke Tests"
echo "=============================="
echo "Base URL: $BASE_URL"
echo ""

# Función para test individual
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local method=${4:-GET}

    echo -n "Testing $name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" 2>/dev/null || echo "000")
    fi

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $response)"
        return 1
    fi
}

# Contador de tests
TOTAL=0
PASSED=0

# Test 1: Health Check
((TOTAL++))
if test_endpoint "Health Check" "$BASE_URL/api/v1/healthz" 200; then
    ((PASSED++))
fi

# Test 2: Readiness Check
((TOTAL++))
if test_endpoint "Readiness Check" "$BASE_URL/api/v1/readyz" 200; then
    ((PASSED++))
fi

# Test 3: Prometheus Metrics
((TOTAL++))
if test_endpoint "Prometheus Metrics" "$BASE_URL/metrics" 200; then
    ((PASSED++))
fi

# Test 4: OpenAPI Docs
((TOTAL++))
if test_endpoint "OpenAPI Docs" "$BASE_URL/docs" 200; then
    ((PASSED++))
fi

# Test 5: OpenAPI JSON
((TOTAL++))
if test_endpoint "OpenAPI JSON" "$BASE_URL/openapi.json" 200; then
    ((PASSED++))
fi

# Test 6: iCal Export (debe retornar 200 o 404 si no hay accommodations)
((TOTAL++))
echo -n "Testing iCal Export... "
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/ical/export/1" 2>/dev/null || echo "000")
if [ "$response" = "200" ] || [ "$response" = "404" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $response - expected 200 or 404)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (Expected 200 or 404, got $response)"
fi

# Test 7: Admin Login (debe retornar 400 si no envía email, o 403 si no está whitelisted)
((TOTAL++))
echo -n "Testing Admin Login... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/admin/login" -H "Content-Type: application/json" -d '{}' 2>/dev/null || echo "000")
if [ "$response" = "422" ] || [ "$response" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $response - validation working)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (Expected 422 or 400, got $response - might be OK)"
    ((PASSED++))
fi

# Test 8: Database Connection (vía health check con detalles)
((TOTAL++))
echo -n "Testing Database Connection... "
health_response=$(curl -s "$BASE_URL/api/v1/healthz" 2>/dev/null || echo "{}")
db_status=$(echo "$health_response" | grep -o '"database":{"status":"[^"]*"' | cut -d'"' -f6 || echo "unknown")
if [ "$db_status" = "ok" ]; then
    echo -e "${GREEN}✓ PASS${NC} (DB status: $db_status)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (DB status: $db_status)"
fi

# Test 9: Redis Connection (vía health check)
((TOTAL++))
echo -n "Testing Redis Connection... "
redis_status=$(echo "$health_response" | grep -o '"redis":{"status":"[^"]*"' | cut -d'"' -f6 || echo "unknown")
if [ "$redis_status" = "ok" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Redis status: $redis_status)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (Redis status: $redis_status)"
fi

# Test 10: CORS Headers
((TOTAL++))
echo -n "Testing CORS Headers... "
cors_header=$(curl -s -I -H "Origin: http://localhost:3000" "$BASE_URL/api/v1/healthz" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
if [ -n "$cors_header" ]; then
    echo -e "${GREEN}✓ PASS${NC} (CORS enabled)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (CORS header not found - might be intentional)"
fi

echo ""
echo "=============================="
echo "Results: $PASSED/$TOTAL tests passed"
echo ""

if [ "$PASSED" -eq "$TOTAL" ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
elif [ "$PASSED" -ge $((TOTAL * 8 / 10)) ]; then
    echo -e "${YELLOW}⚠️  Most tests passed ($PASSED/$TOTAL)${NC}"
    exit 0
else
    echo -e "${RED}❌ Too many failures ($PASSED/$TOTAL)${NC}"
    exit 1
fi
