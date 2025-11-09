# Documentos Vivos (Fuente Única de Verdad)

Este archivo lista la documentación que se mantiene ACTIVA y soportada. Todo lo que no esté aquí pasa a estado "archivado" o será eliminado para evitar confusión.

## Mantener

| Documento | Propósito | Frecuencia actualización |
|-----------|----------|--------------------------|
| `README.md` | Visión general, quick start local | Según cambios funcionales |
| `backend/README.md` | Detalles operativos backend | Cuando cambia pipeline/migraciones |
| `docs/RAILWAY_SETUP.md` | Guía de despliegue rápido en Railway | Al modificar hosting inicial |
| `ESTADO_ACTUAL_VALIDADO_2025-11-03.md` | Estado validado del sistema (snapshot) | Reemplazar con nuevo snapshot si cambia versión mayor |
| `docs/adr/*.md` | Decisiones arquitectónicas formales | Solo nuevas decisiones relevantes |
| `docs/integrations/integrations_analysis.md` | Resumen integraciones actuales y futuras | Cuando se suma/quita integración |
| `.github/pull_request_template.md` | Checklist calidad en PR | Al cambiar políticas de revisión |
| `CONTRIBUTING.md` | Guía de contribución | Ocasional |
| `LICENSE` | Licencia | Solo si se cambia licencia |

## Archivo QA
| Documento | Propósito | Nota |
|-----------|----------|------|
| `docs/qa/MINIMAX_TESTING_REPORT_2025-10-29.md` | Evidencia de pruebas históricas Minimax M2 | Conservado como registro histórico, no se actualiza |

## Eliminados / Deprecados (serán borrados)

Los siguientes tipos de archivos quedan marcados para eliminación porque su contenido está superado por los documentos vivos anteriores:

- Logs diarios y resúmenes de sesión antiguos (`docs/archive/*.md` como `DAILY_LOG_2025-*`, `SESSION_SUMMARY_*`).
- Documentos de fases intermedias (`FASE_*.md`, `OPCION_*.md`).
- Matrices y consolidaciones previas (`CONSOLIDATION_STATUS.md`, `MATRIZ_DECISION_SIGUIENTE_FASE.md`).
- Validaciones de performance antiguas (`PERFORMANCE_VALIDATION_RESULTS.md`) ya reflejadas en el estado validado.
- Scripts auxiliares en `docs/archive/root-cleanup/` (migrados a `ops/` o innecesarios).

## Política

1. Cada nuevo documento debe responder: ¿Resuelve una necesidad activa? ¿Evita duplicar contenido existente?
2. Si un documento se vuelve histórico, muévelo a `docs/archive/` y quítalo de esta lista.
3. Mantén esta lista sincronizada: si algo se agrega o se elimina del repositorio, reflejarlo aquí.

## Próximos pasos

- Limpiar directorio `docs/archive/` dejando solo lo estrictamente necesario (posible futura eliminación completa si no hace falta rastreo histórico).
- Cuando se agregue hosting alternativo (p.ej. Supabase + Render), crear un doc `HOSTING_OPTIONS.md` y enlazar desde aquí.
