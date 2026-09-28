# ADRs (Architecture Decision Records)

Este directorio contiene las decisiones arquitectónicas formales del proyecto.

## Lista de ADRs

| ID | Título | Fecha | Estado | Resumen Breve |
|----|--------|-------|--------|----------------|
| ADR-001 | No Integrar un PMS Externo en el MVP | 2025-09-24 | Aprobado | Mantener modelo propio mínimo; evitar complejidad y dependencia externa hasta post-MVP (>100 reservas/mes). |
| ADR-002 | Rango de fechas half-open `[)` para reservas (Back-to-back) | 2025-09-28 | Aprobado | Permite check-out el mismo día del check-in siguiente mediante `daterange` generado y `EXCLUDE USING gist`. |
| ADR-003 | Fuente maestra y control de doble reserva | 2026-09-28 | Aprobado | Reafirma ADR-001. Fija la cadena de 4 capas de control de disponibilidad y declara que iCal no es control de concurrencia. |

### Documentos de referencia asociados

| Documento | Propósito |
|-----------|-----------|
| [`docs/domain/ESPECIFICACION_DOMINIO_V1.md`](../domain/ESPECIFICACION_DOMINIO_V1.md) | Reglas de negocio canónicas. **Fuente única de verdad.** Si un valor aparece en otro lugar y la contradice, este documento tiene razón. |
| [`docs/GAPS_IMPLEMENTACION.md`](../GAPS_IMPLEMENTACION.md) | 12 gaps verificados entre la norma y el código, con DoD binario. |
| [`docs/ops/COSTO_Y_MIGRACION_POSTGRES.md`](../ops/COSTO_Y_MIGRACION_POSTGRES.md) | Costo real de infraestructura y plan de migración de PostgreSQL. |
| [`docs/entrantes/`](../entrantes/) | Documentos de arquitectura entrantes, archivados como superados. |

## Convenciones
- Formato archivo: `ADR-XXX-nombre-kebab.md`
- Estados: Propuesto → Aprobado → (Opcional) Reemplazado/Obsoleto
- Cambios mayores deben generar un nuevo ADR en lugar de editar retroactivamente uno aprobado.

## Cuándo crear un nuevo ADR
Crea un ADR si la decisión:
1. Afecta arquitectura técnica (persistencia, integración externa, despliegue) o
2. Cambia invariantes de negocio críticos (anti doble-booking, flujo pre-reservas) o
3. Introduce dependencia de terceros significativa.

## Plantilla sugerida
```
# ADR-XXX — Título
Fecha:
Estado:
Decisor(es):

## Contexto
...
## Decisión
...
## Razones
- ...
## Alternativas Consideradas
| Alternativa | Motivo descarte |
## Consecuencias
- Positivas
- Negativas
## Plan de Revisión
Criterios / métricas para re-evaluar
```

---
Mantener este índice actualizado en cada PR que agregue un ADR nuevo.
