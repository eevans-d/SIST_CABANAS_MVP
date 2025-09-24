# ADRs (Architecture Decision Records)

Este directorio contiene las decisiones arquitectónicas formales del proyecto.

## Lista de ADRs

| ID | Título | Fecha | Estado | Resumen Breve |
|----|--------|-------|--------|----------------|
| ADR-001 | No Integrar un PMS Externo en el MVP | 2025-09-24 | Aprobado | Mantener modelo propio mínimo; evitar complejidad y dependencia externa hasta post-MVP (>100 reservas/mes). |

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