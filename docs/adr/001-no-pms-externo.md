# ADR-001: No Integrar PMS Externo en el MVP

**Status:** Aceptado
**Fecha:** 2025-09-29
**Autores:** Sistema Alojamientos Contributors
**Revisores:** Project Lead

---

## Contexto

Durante la planificación del MVP, surgió la pregunta de si integrar un Property Management System (PMS) existente como Odoo, HotelDruid, QloApps, u otros sistemas de gestión hotelera para acelerar el desarrollo.

Los PMS existentes ofrecen funcionalidades como:
- Gestión de propiedades múltiples
- Reservas y calendarios
- Facturación y contabilidad
- Reportes y analytics
- Channel managers
- Gestión de housekeeping

Sin embargo, el proyecto tiene requisitos específicos que lo diferencian:
- Conversacional WhatsApp con NLU
- Anti-doble-booking con locks Redis distribuidos
- Pre-reservas efímeras con expiración automática
- Integración directa con Mercado Pago
- Pipeline de audio STT con Whisper
- iCal bidireccional con HMAC tokens

El MVP debe entregarse en 10-12 días con funcionalidad core operativa.

## Decisión

**NO** se integrará ningún PMS externo durante el alcance del MVP.

El sistema se construirá con:
- FastAPI monolítico
- Modelo de datos mínimo (accommodations, reservations, payments)
- Lógica de negocio directa sin capas de abstracción
- Enfoque en diferenciadores clave (WhatsApp, anti-doble-booking, audio)

## Justificación

### Pros
- **Control Total:** Implementación directa de constraint EXCLUDE USING gist para anti-doble-booking
- **Velocidad:** No hay curva de aprendizaje de API externa o configuración compleja
- **Simplicidad:** Modelo de datos mínimo sin features innecesarias
- **Flexibilidad:** Adaptación rápida a requisitos específicos sin limitaciones de plataforma
- **Mantenibilidad:** Una codebase, stack conocido, debugging directo
- **Costo:** Sin licencias, sin overhead de integración

### Cons
- **Features Propias:** Hay que implementar calendarios, reportes, etc. desde cero
- **Multi-Property:** Falta gestión nativa de múltiples propiedades
- **Contabilidad:** Sin integración contable automática
- **Experiencia:** Se pierde expertise de PMS maduros en gestión hotelera

## Alternativas Consideradas

### Alternativa 1: Odoo con módulo Hospitality
- **Pros:**
  - ERP completo con contabilidad, CRM, reportes
  - Módulos hoteleros existentes
  - Comunidad grande, bien documentado
- **Cons:**
  - Curva de aprendizaje alta (Python + XML + QWeb + ORM propio)
  - Overhead significativo para MVP simple
  - Dificultad para integrar locks Redis custom
  - Constraint anti-doble-booking requeriría workarounds
- **Por qué fue rechazada:** Complejidad excesiva, no alineado con SHIPPING > PERFECCIÓN

### Alternativa 2: QloApps (fork de PrestaShop para hoteles)
- **Pros:**
  - Específico para alojamientos
  - UI web completa
  - Gestión de bookings, habitaciones, tarifas
- **Cons:**
  - PHP (stack diferente al proyecto)
  - API REST limitada para integraciones profundas
  - Difícil implementar conversación WhatsApp
  - No diseñado para pre-reservas efímeras con TTL
- **Por qué fue rechazada:** Stack incompatible, integraciones complejas

### Alternativa 3: HotelDruid
- **Pros:**
  - Open source, enfocado en pequeñas propiedades
  - Ligero comparado con Odoo
- **Cons:**
  - PHP, menos moderno que FastAPI
  - Sin API REST robusta
  - Falta integración WhatsApp y NLU
  - Comunidad más pequeña
- **Por qué fue rechazada:** Limitaciones de integración, stack diferente

## Consecuencias

### Positivas
- **Mayor Control:** Control total sobre lógica crítica (anti-doble-booking, locks, expiraciones)
- **Velocidad de Desarrollo:** Sin tiempo invertido en aprender APIs externas o configuraciones complejas
- **Stack Unificado:** Todo en Python/FastAPI, mismo paradigma async
- **Debugging Simplificado:** Un solo codebase, logs directos, sin capas de abstracción
- **MVP más Rápido:** Entrega en 10-12 días factible

### Negativas
- **Features Limitadas:** Solo funcionalidades core MVP, sin reportes avanzados ni contabilidad
- **Multi-Property Post-MVP:** Requerirá desarrollo custom si se necesita gestionar múltiples propiedades
- **Reinventando Ruedas:** Algunas features comunes de PMS hay que implementarlas desde cero

### Neutrales
- **Re-evaluación Post-MVP:** Decisión puede revisarse después de 100+ reservas/mes o necesidades fiscales complejas
- **Modelo de Datos Extensible:** Schema PostgreSQL permite añadir propiedades/features sin migración mayor

## Criterios de Éxito

- [x] MVP entregado en 10-12 días (cumplido: 10 días)
- [x] Anti-doble-booking funcional con pruebas de concurrencia (37 tests pasando)
- [x] Conversación WhatsApp con normalización de mensajes (implementado)
- [x] iCal import/export bidi con Airbnb/Booking (funcionando)
- [x] Integración Mercado Pago con validación de firmas (operativa)
- [x] Pipeline audio STT con Whisper (confidence >0.6)
- [ ] >100 reservas/mes sin bloqueos ni doble-bookings (pendiente post-lanzamiento)

## Notas

Esta decisión es **DEFINITIVA** para el alcance del MVP (10-12 días).

**Regla Operativa:**
- Cualquier propuesta de "usar un PMS para acelerar" → Rechazar y remitir a este ADR
- Re-evaluación sólo post-MVP cuando:
  - >100 reservas/mes consistentes
  - Necesidad de gestión multi-propietario
  - Requisitos de reporting fiscal complejo
  - Feedback de usuarios indica necesidad de features avanzadas

**Indicador de Desviación:**
- Si aparece código o dependencias que intenten mapear entidades externas de un PMS → Detener PR y simplificar

### Referencias
- [Copilot Instructions - ADR: No Integrar PMS Externo en el MVP](../.github/copilot-instructions.md#adr-no-integrar-pms-externo-en-el-mvp)
- [CONTRIBUTING.md - Filosofía del Proyecto](../CONTRIBUTING.md#filosofía-del-proyecto)

### Relacionado
- ADR-002: Monolito FastAPI vs Microservicios (pendiente)
- ADR-003: PostgreSQL Constraint vs Application-Level Locking (pendiente)

---

*Este ADR documenta una decisión arquitectural crítica del proyecto y debe respetarse durante el ciclo de vida del MVP.*
