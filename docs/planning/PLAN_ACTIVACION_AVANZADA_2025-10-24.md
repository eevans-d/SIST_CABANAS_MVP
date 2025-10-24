# Plan de Activación Avanzada – SIST_CABAÑAS MVP

Fecha: 2025-10-24  
Autor: Equipo Operaciones / Backend  
Estado: Listo para ejecución (validación 15/15 OK)

---

## 1) Resumen ejecutivo

- Objetivo: Activar el sistema en Fly.io en ~20–30 minutos con riesgo controlado, dejando integraciones externas para una segunda fase.
- Estado verificado hoy:
  - Validación pre-deploy: ✅ EXITOSA (15/15)
  - flyctl: ✅ instalado y autenticado (v0.3.202)
  - Scripts de activación: ✅ presentes (START_ACTIVATION.sh, activation_complete.sh, fase_1/2/3)
  - Warnings no bloqueantes: ⚠️ health check sin validación de Redis; ⚠️ cambios sin commit si hubiera locales; (aceptables para primer deploy)
- Diferencias detectadas respecto al diagnóstico previo:
  - “ACTIVACION_RAPIDA.sh”: ❌ no existe; reemplazos funcionales ✅ START_ACTIVATION.sh y activation_complete.sh
  - “333 tests”: no evidenciados; existe una suite amplia (~98 archivos de test). Base previa: 180+ tests / 85% coverage.
- Decisión recomendada: proceder con Fases A–C para tener la app en producción hoy; dejar integraciones (WhatsApp/MP/iCal) para Fase D (misma tarde o día siguiente).

---

## 2) Diagnóstico vs evidencia (contraste)

- Desarrollo backend: Claim “100%”:  
  Evidencia: `backend/` completo; endpoints health/ready/metrics; validación de imports críticos OK.  
  Veredicto: ✅ MVP backend completo y listo.

- Frontend (dashboard admin): Claim “100%”:  
  Evidencia: `frontend/admin-dashboard/` con `package.json` y `vite.config.ts`.  
  Veredicto: ✅ Proyecto presente; build no verificado aún (fuera del scope del primer deploy backend). 

- Documentación “64+ docs”:  
  Evidencia: >100 archivos en `docs/`.  
  Veredicto: ✅ más que suficiente.

- Tests “333”:  
  Evidencia: ~98 archivos en `backend/tests/`.  
  Veredicto: ⚠️ número exacto no verificable ahora; suite amplia y útil.

- Deployment “0%”:  
  Evidencia: `fly.toml` listo; validación 15/15; no se ejecutó `flyctl deploy` aún.  
  Veredicto: ✅ pendiente ejecutar.

- Producción “inactivo”:  
  Evidencia: no hay URL viva actual.  
  Veredicto: ✅ correcto.

- Credenciales externas (WhatsApp/MP):  
  Evidencia: no seteadas en Fly aún.  
  Veredicto: ✅ diferible para Fase D.

- Base de datos “no provisionada”:  
  Evidencia: Postgres en Fly aún no creado/attach.  
  Veredicto: ✅ se resuelve en Fase A.

- “Pydantic mismatch” / “marcadores pytest”:  
  Evidencia: no reproducido en validación actual; no bloquea el deploy.  
  Veredicto: ⚠️ monitorear tras el deploy y en CI.

---

## 3) Plan de activación intensivo (por fases)

### Fase A — Infra mínima + secretos (8–12 min)
- Contrato (inputs/outputs):
  - Inputs: app `sist-cabanas-mvp` en Fly (región eze).  
  - Outputs: Postgres creado y attach; secretos mínimos en Fly: `JWT_SECRET`, `REDIS_PASSWORD`, `ICS_SALT`, `ADMIN_CSRF_SECRET`, `GRAFANA_ADMIN_PASSWORD`.
- Pasos (script ya disponible):
  - Ejecutar `fase_1_setup.sh` (crea Postgres, attach, genera y setea secretos).
- Criterios de éxito:
  - `DATABASE_URL` presente en la app; `flyctl secrets list` muestra los 5 secretos.
- Riesgos y mitigación:
  - Cuotas o límites: usar `shared-cpu-1x`; reintento si falla.  
  - Fallo en attach: reintentar; como fallback, setear `DATABASE_URL` manualmente.

### Fase B — Deploy + migraciones + health (3–5 min)
- Contrato:
  - Inputs: `fly.toml` listo; release/migrations definidas.  
  - Outputs: release OK; health checks PASSING.
- Pasos (script ya disponible):
  - Ejecutar `fase_2_deploy.sh` (revalida; deploy; logs en vivo ~30s).
- Criterios de éxito:
  - `flyctl deploy` exit code 0; `flyctl status` HEALTHY; `/api/v1/healthz` 200 OK.
- Riesgos y mitigación:
  - Build error: revisar logs; invalidar cache y reintentar.  
  - Health timeout: verificar DB connectivity; ajustar grace period si hiciera falta.

### Fase C — Smoke tests + observabilidad (3–5 min)
- Contrato:
  - Inputs: app en ejecución.  
  - Outputs: 5 checks OK (health, ready, metrics, homepage, DB via SSH).
- Pasos (script ya disponible):
  - Ejecutar `fase_3_smoke_tests.sh` y documentar resultados.
- Criterios de éxito:
  - 5/5 PASSED; métricas accesibles; readiness ✅.
- Riesgos y mitigación:
  - SSH no disponible (WireGuard): validar DB indirectamente con health/metrics y posponer SSH.

### Fase D — Integraciones externas (30–60 min) — no bloquea go-live
- WhatsApp / Mercado Pago / iCal.
- Pasos:
  - Añadir secretos oficiales (tokens/firmas) en Fly.  
  - Probar webhooks con firmas válidas y sandbox de MP.  
  - Verificar iCal export/import y el gauge `ical_last_sync_age_minutes`.
- Criterios de éxito:
  - Webhooks 200 OK con firmas válidas; idempotencia confirmada.

### Fase E — Operación inicial (día 0–3)
- SLOs y métricas:
  - P95 texto < 3s; audio < 15s; error rate < 1%.  
  - Prometheus en `/metrics`; salud en `/healthz` y `/readyz`.
- Runbooks:
  - Rollback con `flyctl releases rollback`.  
  - Monitoreo de logs y alertas iniciales.

---

## 4) Checklist y criterios de éxito

- [ ] Fase A: Postgres creado + attach; 5 secretos configurados.  
- [ ] Fase B: Deploy exitoso; healthz 200; status HEALTHY.  
- [ ] Fase C: 5/5 smoke tests PASSED; métricas accesibles.  
- [ ] Fase D: Webhooks (WhatsApp/MP) verificados; iCal sync operativa.  
- [ ] Fase E: Monitoreo día 0–3 sin incidentes críticos.

Éxito del hito “Go-Live”: Fases A–C completadas y green; URL productiva entregada.

---

## 5) Timeline y responsables

- A (Infra): 10 min — Owner: DevOps  
- B (Deploy): 5 min — Owner: DevOps/Backend  
- C (Smoke): 5 min — Owner: QA/Backend  
- D (Integraciones): 30–60 min — Owner: Integraciones/Producto  
- E (Operación): continuo — Owner: Ops

Total a producción (sin integraciones): ~20–30 min.

---

## 6) Notas operativas y diferencias clave

- El script mencionado como `ACTIVACION_RAPIDA.sh` en diagnósticos previos no existe en el repo; utilice `START_ACTIVATION.sh` (launcher) o `activation_complete.sh` (orquestador) para el mismo objetivo.
- Warnings de validación actuales son no bloqueantes y aceptables para el primer despliegue.
- El número exacto de tests ("333") no está contrastado aquí; la suite existente es amplia y suficiente para smoke/regresión inicial.

---

## 7) Próximas acciones

1) [Hoy] Ejecutar activación automática:  
- `activation_complete.sh` (orquesta Fases A–C con confirmaciones)  
- Entregable: URL productiva + resultados de smoke tests.

2) [Hoy/tarde o Mañana] Integraciones externas (Fase D):  
- Cargar secretos oficiales (WhatsApp/MP), probar webhooks, verificar iCal.

3) [Día 0–3] Operación:  
- Monitorear métricas, logs y salud; preparar umbrales y alertas.

---

## 8) Anexos de referencia

- Scripts: `START_ACTIVATION.sh`, `activation_complete.sh`, `fase_1_setup.sh`, `fase_2_deploy.sh`, `fase_3_smoke_tests.sh`  
- Validación: `pre_deploy_validation.sh` (PASS 15/15)  
- Config: `fly.toml`  
- Documentación: `ACTIVATION_GUIDE.md`, `QUICK_START.sh`, `DEPLOY_READY_CHECKLIST.md`
