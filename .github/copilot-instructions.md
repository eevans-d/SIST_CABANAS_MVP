# Instrucciones de Alto Nivel para el Agente de IA - Sistema de Reservas MVP

## 1. Contexto y Filosofía del Proyecto

- **Objetivo:** Construir un **sistema de automatización de reservas**, no un sistema de agentes de IA complejos. La lógica se basa en reglas, NLU simple (regex y `dateparser`) y plantillas.
- **Filosofía Principal:** **SHIPPING > PERFECCIÓN**. La meta es entregar un producto funcional rápidamente. Implementa la solución más simple que cumpla con los requisitos y pase los tests. No refactorices ni añadas funcionalidades si no es estrictamente necesario.
- **Stack Tecnológico (No Negociable):**
  - **Backend:** Monolito con FastAPI, SQLAlchemy (async), PostgreSQL 16, Redis 7.
  - **Frontend:** React 18 + Vite + Tailwind.
  - **Integraciones:** WhatsApp, Mercado Pago, iCal.

---

## 2. Reglas de Oro y Patrones Críticos

### REGLA #1: La Prevención de Doble-Booking es la Máxima Prioridad
Este es el problema más crítico a resolver. La solución se basa en dos mecanismos:

1.  **Constraint a Nivel de Base de Datos (PostgreSQL):**
    - Se usa una extensión `btree_gist` y un `EXCLUDE USING gist` en un campo `daterange` para que la base de datos rechace atómicamente cualquier intento de reserva que se solape en fechas para el mismo alojamiento.
    - Espera y maneja `IntegrityError` en el código.

2.  **Bloqueo Pesimista (Redis):**
    - Antes de intentar escribir en la base de datos, adquiere un bloqueo distribuido en Redis (`SET lock:... NX EX ...`).
    - Esto previene que dos procesos intenten escribir en la base de datos al mismo tiempo, reduciendo la contención y los fallos por `IntegrityError`.

### REGLA #2: Webhooks Seguros y Contratos Unificados
- **Validación de Firmas:** Todos los webhooks entrantes (WhatsApp, Mercado Pago) DEBEN ser validados usando sus firmas (`X-Hub-Signature-256`, `x-signature`) y el secreto correspondiente. Rechaza cualquier solicitud sin una firma válida.
- **Normalización:** Inmediatamente después de validar, normaliza el payload del webhook a un "Contrato de Mensaje Unificado" interno. Esto desacopla el resto del sistema del formato específico de cada proveedor.

### REGLA #3: Estructura de Proyecto Fija
- Sigue la estructura de directorios existente. La lógica de negocio principal reside en `backend/app/services`. Los endpoints de la API están en `backend/app/routers`.

---

## 3. Flujos de Trabajo y Comandos

- **Comandos:** Usa el `Makefile` para todas las tareas (`make test`, `make up`, `make logs`). Es la única fuente de verdad para ejecutar operaciones.
- **Testing:**
  - La mayoría de los tests se ejecutan contra una base de datos SQLite en memoria para velocidad y aislamiento.
  - Los tests críticos de concurrencia y solapamiento de fechas (`test_double_booking.py`) están configurados para usar una base de datos PostgreSQL real para validar el constraint `gist`, ya que SQLite no lo soporta.
- **Configuración:** Todos los secretos y configuraciones específicas del entorno deben cargarse desde variables de entorno. El archivo `.env.template` sirve como referencia.

---

## 4. Qué NO Hacer (Anti-Patrones)

- **NO construyas microservicios:** El sistema es y debe permanecer como un monolito.
- **NO introduzcas complejidad innecesaria:** Evita abstracciones "por si acaso", optimizaciones prematuras o patrones de diseño complejos si una solución más simple funciona.
- **NO uses un LLM para razonar:** El sistema es determinístico. Las respuestas se basan en plantillas y la "inteligencia" proviene de regex y extracción de fechas.
- **NO integres un PMS externo:** El MVP no incluye integración con sistemas de gestión hotelera (QloApps, etc.). La decisión está documentada en un ADR y no debe ser revertida.
