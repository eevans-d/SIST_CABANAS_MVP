# ADR-001 — No Integrar un PMS Externo en el MVP

Fecha: 2025-09-24
Estado: Aprobado
Decisor: Equipo Producto / Técnico

## Contexto
El MVP del Sistema Agéntico de Alojamientos debe entregarse en 10–12 días y se centra en:
- Conversación automatizada (WhatsApp texto + audio) con NLU básico
- Pre-reservas efímeras (locks Redis + constraint Postgres daterange)
- Prevención 100% doble-booking
- Pagos con Mercado Pago (seña 30%)
- Sincronización iCal básica (import/export)

Se evaluó la posibilidad de integrar un PMS open source (Odoo + módulos hotel, HotelDruid, QloApps, etc.) para “ahorrar” tiempo en capas administrativas.

## Decisión
NO se integrará ningún PMS externo durante el alcance del MVP. Se implementará un modelo de datos propio mínimo y servicios internos ligeros.

## Razones Principales
1. Complejidad operativa y curva de aprendizaje agregan >2–3 días (rompe timeline).
2. Los PMS no resuelven los diferenciadores clave (locks efímeros, flujo conversacional, Mercado Pago, audio STT/NLU).
3. Riesgo de feature creep (reportes, multi-propietario, contabilidad) fuera del alcance MVP.
4. Dependencia de modelos rígidos / APIs incompletas → pérdida de control sobre validaciones críticas.
5. El modelo necesario es pequeño y ya definido (accommodations, reservations, availability_calendar, payment_records, whatsapp_messages).

## Qué Sí Reutilizamos
- Librerías específicas (holidays, dateparser, icalendar/ics, faster-whisper)
- Snippets probados para logging estructurado y middlewares
- Estilos/plantilla HTML ligera para dashboard (sin acoplar PMS)

## Riesgos si se Ignora
- Retraso del MVP > 30–40%
- Aumento de deuda técnica por adaptaciones rápidas al modelo de un PMS
- Dificultad para introducir lógica de pre-reserva efímera sin hacks
- Dilución del foco en la automatización conversacional

## Métricas de Revisión Futuras
Revaluar integración de PMS SOLO si se cumplen simultáneamente:
- >100 reservas confirmadas/mes sostenidas 2 meses
- Necesidad de funcionalidades avanzadas (multi-propietario, reporting fiscal, tarifas dinámicas complejas)
- Capacidad de dedicar sprint de integración sin afectar roadmap

## Señales de Desviación (Trigger de Alerta)
- PRs que agregan mapeos/persistencia de entidades de PMS externos
- Propuestas de “usar PMS para acelerar” sin evidencia temporal concreta
- Dependencias nuevas que introducen frameworks de terceros pesados

## Alternativas Consideradas
| Alternativa | Motivo de descarte |
|-------------|--------------------|
| Odoo + módulos hotel | Curva alta, modularización pesada, overkill para MVP |
| HotelDruid | Stack distinto (PHP), API limitada, mantenimiento incierto |
| QloApps (PrestaShop) | E-commerce orientado, reuso bajo para flujos conversacionales |
| Construir solo calendar + pricing y delegar reservas | Pierde control de lógica anti-doble-booking |

## Consecuencias
- Mayor velocidad de entrega y control sobre flujos críticos
- Código focalizado y pequeño → más fácil de testear
- Refuerzo explícito del alcance: evita expansión innecesaria

## Follow-up
Crear (si no existe) script de seed + endpoints básicos admin en sprint 2. Revisar este ADR en reunión post-MVP (fecha estimada +30 días del GO LIVE).

---
Este ADR complementa lo documentado en `.github/copilot-instructions.md` y debe mantenerse visible para evitar desvíos estratégicos.