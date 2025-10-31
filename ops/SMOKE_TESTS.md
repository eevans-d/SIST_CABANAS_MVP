# 🧪 Smoke Tests - Post Deploy Validation

Script para validar el deploy del backend en staging.

## Uso

```bash
# Ejecutar contra staging (default)
./ops/smoke-tests.sh

# Ejecutar contra URL custom
BASE_URL=https://mi-app.fly.dev ./ops/smoke-tests.sh
```

## Tests Incluidos

1. **Health Check** (`/api/v1/healthz`)
   - Valida: DB, Redis, iCal sync age
   - Esperado: HTTP 200

2. **Readiness Check** (`/api/v1/readyz`)
   - Valida: app lista para recibir tráfico
   - Esperado: HTTP 200

3. **Prometheus Metrics** (`/metrics`)
   - Valida: métricas expuestas
   - Esperado: HTTP 200

4. **OpenAPI Docs** (`/docs`)
   - Valida: Swagger UI disponible
   - Esperado: HTTP 200

5. **OpenAPI JSON** (`/openapi.json`)
   - Valida: schema OpenAPI válido
   - Esperado: HTTP 200

6. **iCal Export** (`/api/v1/ical/export/1`)
   - Valida: endpoint iCal funcional
   - Esperado: HTTP 200 o 404 (si no hay datos)

7. **Admin Login** (`/api/v1/admin/login`)
   - Valida: validación de input funciona
   - Esperado: HTTP 422 o 400 (sin datos válidos)

8. **Database Connection**
   - Valida: PostgreSQL conectado
   - Vía: health check response

9. **Redis Connection**
   - Valida: Redis conectado
   - Vía: health check response

10. **CORS Headers**
    - Valida: CORS configurado
    - Vía: headers HTTP

## Criterio de Éxito

- ✅ **100% pass**: Todo OK
- ⚠️ **80%+ pass**: Mayormente OK, revisar warnings
- ❌ **<80% pass**: Fallos críticos, no promover a prod

## Próximos Tests (Post-MVP)

- [ ] Load testing con k6 (P95 < 3s)
- [ ] Security scan con OWASP ZAP
- [ ] Pre-reserva end-to-end
- [ ] Webhook signature validation
- [ ] iCal import/export completo
