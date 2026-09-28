# Especificación de Dominio V1 — Sistema de Cabañas Ñecochea

**Estado:** Vigente
**Fecha:** 2026-09-28
**Alcance:** reglas de negocio del sistema `SIST_CABANAS_MVP`

---

## Cómo leer este documento

Este es el documento de reglas de negocio **canónico y único** del sistema. Reemplaza a los documentos de arquitectura recibidos en septiembre de 2026 y a cualquier valor suelto en el código.

**Convención de lectura.** Cada sección marca dos cosas distintas:

- **Origen** — qué documento o decisión respalda la regla.
- **Evidencia** — el archivo del código o la fuente externa donde puede verificarse.
- **Estado actual** — qué hace hoy el sistema. **No es la norma.** La norma es lo que dice la sección; el estado actual es la distancia que hay que recorrer.

Una regla puede estar en la norma y no estar implementada. La lista de esas distancias está en [`docs/GAPS_IMPLEMENTACION.md`](../GAPS_IMPLEMENTACION.md).

> **Advertencia permanente.** El `DOCUMENTO_MAESTRO_P0_SISTEMA_CABANAS.md` enuncia una métrica de sobreventa igual a cero. **Esa métrica se rechaza por falsa.** La documentación oficial de Airbnb documenta que su calendario importado se actualiza automáticamente **cada 3 horas**. Con sincronización iCal la sobreventa no es un riesgo residual: es un comportamiento normal. Ningún documento vigente debe afirmar sobreventa cero.

---

## 1. Constantes canónicas

**Origen:** decisión del operador, septiembre 2026.
**Evidencia:** valores actuales en `backend/app/services/reservations.py` (`DEPOSIT_PERCENTAGE_DEFAULT = 30`, `LOCK_TTL_SECONDS = 1800`, `PRERESERVATION_EXPIRY_MINUTES = 30`) y en `backend/alembic/versions/001_initial_schema.py` (`server_default="30"`).

| Parámetro | Valor canónico | Nota |
|---|---|---|
| Depósito (seña) | **50%** del total | Reemplaza al 30% actual |
| Bloqueo de pre-reserva, temporada `alta` | **7.200 s (2 h)** | |
| Bloqueo de pre-reserva, resto del año | **14.400 s (4 h)** | |
| TTL del lock Redis | **Igual al TTL de la pre-reserva** | Hoy es un valor global fijo de 1.800 s |
| Extensiones de bloqueo permitidas | **1** (campo `extended_once` ya existe) | Con recordatorio a mitad de TTL |
| Estadía mínima, 1 al 10 de enero | **5 noches** | |
| Estadía mínima, feriados largos | **3 noches** | |
| Estadía mínima, resto | **2 noches** | |

### Definición de temporada

| Temporada | Periodo | Depósito | Bloqueo |
|---|---|---|---|
| `alta` | **15 dic – 15 ene**, más **semana santa** | 50% | 2 h |
| `baja` (por defecto) | Resto del año | 50% | 4 h |

La temporada se resuelve **por la fecha de check-in** de la reserva. Si `check_in` cae en `alta`, el hold y el bloqueo son de 2 h, aunque la estadía termine en `baja`.

**Estado actual:** ninguna de estas constantes está implementada. El sistema usa 30% y 30 minutos de forma uniforme, y no tiene noción de temporada. Ver gaps **G2**, **G3** y **G8**.

### Consecuencia operativa del hold de 4 h

Con 3 a 4 cabañas, un hold de 4 horas bloquea inventario real durante 4 horas. Si el huésped abandona el pago, esa venta se pierde para la temporada. Dos mitigaciones, ambas en la norma:

1. **Recordatorio a mitad de TTL.** Enviar el link de pago de nuevo cuando haya transcurrido la mitad del bloqueo.
2. **Extensión única.** Ante el recordatorio, ofrecer una única extensión usando el campo `extended_once` ya existente en el esquema. Nunca más de una.

---

## 2. Máquina de estados

### 2.1 Estados de reserva

**Origen:** decisión del operador.
**Evidencia:** `backend/app/models/enums.py` — `ReservationStatus` con `pre_reserved, confirmed, cancelled, completed, no_show`.

| Estado | Significado | Transiciones permitidas | Bloquea inventario |
|---|---|---|---|
| `pre_reserved` | Hold activo, esperando depósito | → `confirmed`, `expired`, `cancelled` | **Sí** |
| `expired` | El TTL venció sin pago. **Terminal.** | — | No |
| `confirmed` | Depósito cobrado. Bloqueo firme. | → `completed`, `cancelled` | **Sí** |
| `completed` | Hospedaje finalizado. **Terminal.** | — | No |
| `cancelled` | Anulada por el operador o el huésped. **Terminal.** | — | No |
| `no_show` | El huésped no se presentó. **Terminal.** | — | No |

**`expired` es un estado nuevo.** Se distingue de `cancelled` de forma deliberada: `expired` es un lapse de interés del huésped y no penaliza; `cancelled` es una decisión y sí tiene consecuencia comercial.

La diferencia importa también en métricas: un sistema con muchos `expired` y pocos `confirmed` tiene un problema de fricción en el pago, no de demanda.

**Estado actual:** `expired` no existe en el enum. Es necesario verificar además si `backend/app/jobs/cleanup.py` **borra** la fila al vencer el TTL o la **transiciona**. Si borra, se pierde la trazabilidad de toda pre-reserva caducada, que es justamente el dato que sirve para diagnosticar el problema de fricción. Ver gap **G4** y nota de verificación asociada.

### 2.2 Estados de pago

**Origen:** decisión del operador.
**Evidencia:** `backend/app/models/enums.py` — `PaymentStatus` con `pending, paid, partially_paid, refunded, failed`. Búsqueda en el repositorio: `partially_paid` aparece **una sola vez**, en el enum. Hoy es código muerto.

Con depósito del 50%, `partially_paid` pasa a ser un estado de primera clase:

```
pending ──(seña 50%)──> partially_paid ──(saldo antes del check-in)──> paid
                                                                    │
                                        ┌───────────────────────────┴──────────┐
                                     refunded                              failed
```

| Estado | Significado |
|---|---|
| `pending` | Nada cobrado todavía |
| `partially_paid` | Cobrado el depósito, pendiente el saldo |
| `paid` | Total cobrado |
| `refunded` | Reembolsado, total o parcialmente |
| `failed` | El intento de cobro falló de forma terminal |

**Pendiente de producto (ver §9 del plan de reconciliación):** qué ocurre si el saldo nunca se paga. Dos opciones sobre la mesa — liberar la habitación 72 h antes del check-in, o mantener la reserva en `partially_paid` y exponerla en el panel como accionable. **Esta es la única decisión pendiente con impacto directo en el código.**

---

## 3. Modelo tarifario

**Origen:** `DOCUMENTO_MAESTRO_P0` §5.1 y `PMS_CABANAS_NECOCHEA_ESPECIFICACION_DEFINITIVA` §2, conciliados.
**Evidencia:** estado actual en `backend/app/models/accommodation.py` — solo existen `base_price` y `weekend_multiplier` (1.2).

**Estado actual:** el cálculo de precio es un placeholder reconocido como tal en el docstring de `create_prereservation`. Solo aplica un multiplicador de fin de semana; no hay concepto de temporada, ni de fecha, ni de estadía mínima. Consecuencia directa: **toda la facturación de temporada alta se calcula hoy con la tarifa base**. Ver gap **G2**.

### Norma

El precio de una reserva se resuelve en este orden:

1. **Tarifa por temporada** si existe una fila aplicable en `temporadas_tarifas` para esa cabaña y esas fechas.
2. **Fallback:** `base_price` de la cabaña, con `weekend_multiplier` aplicado a las noches de sábado y domingo dentro del rango `[check_in, check_out)`.

El fallback existe para que el sistema siga operando mientras la tabla de temporadas se puebla. **No es la norma de largo plazo**: una cabaña con temporada sin configurar es un error de configuración, no un estado normal.

### Tabla propuesta: `temporadas_tarifas`

```sql
CREATE TABLE temporadas_tarifas (
    id                 SERIAL PRIMARY KEY,
    accommodation_id   INTEGER NOT NULL REFERENCES accommodations(id) ON DELETE CASCADE,
    temporada          VARCHAR(10) NOT NULL CHECK (temporada IN ('alta','baja')),
    fecha_inicio       DATE NOT NULL,
    fecha_fin          DATE NOT NULL,
    precio_noche       NUMERIC(12,2) NOT NULL CHECK (precio_noche >= 0),
    noches_minimas     INTEGER NOT NULL DEFAULT 2 CHECK (noches_minimas >= 1),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ,
    CONSTRAINT ck_temporada_rango CHECK (fecha_fin > fecha_inicio)
);

CREATE INDEX idx_temporadas_lookup
    ON temporadas_tarifas (accommodation_id, temporada, fecha_inicio, fecha_fin);
```

Los rangos de fechas usan la misma semántica **half-open `[)`** que las reservas: `fecha_inicio` inclusivo, `fecha_fin` exclusivo. Es la misma decisión de `ADR-002`, y debe mantenerse coherente para que los chequeos de solapamiento sean comparables.

### Cálculo del total

```
noches           = (check_out - check_in).days
noches_minimas   = la de la fila de temporada que aplica, o 2 por defecto
total            = SUM(precio de cada noche)
```

Se cobra noche por noche, no un promedio: así una estadía que cruza el límite de dos temporadas paga el precio correcto en cada tramo. Si la estadía es menor que `noches_minimas`, **el sistema rechaza la reserva** y ofrece la fecha alternativa más cercana que sí cumpla el mínimo.

---

## 4. Inventario y bloqueos

**Origen:** `PMS_CABANAS_NECOCHEA_ESPECIFICACION_DEFINITIVA` §3 (invariante de mantenimiento).
**Evidencia:** estado actual — `backend/app/models/accommodation.py` solo tiene `active: Boolean`. Búsqueda de `accommodation_blocks` en el repositorio: **cero resultados**.

**Estado actual:** no existe forma de bloquear una cabaña por un rango de fechas. `active = false` la desactiva de forma permanente **y además la excluye del sincronismo iCal**, porque `backend/app/jobs/import_ical.py` filtra por `Accommodation.active == True`. No hay manera de bloquear una avería de tres días en plena temporada alta sin desactivar la cabaña entera. Ver gap **G6**.

### Norma: `accommodation_blocks`

```sql
CREATE TABLE accommodation_blocks (
    id                 SERIAL PRIMARY KEY,
    accommodation_id   INTEGER NOT NULL REFERENCES accommodations(id) ON DELETE CASCADE,
    start_date         DATE NOT NULL,
    end_date           DATE NOT NULL,
    reason             VARCHAR(200) NOT NULL,
    created_by         VARCHAR(120),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_block_rango CHECK (end_date > start_date)
);

CREATE INDEX idx_blocks_lookup
    ON accommodation_blocks (accommodation_id, start_date, end_date);
```

Rango **half-open `[)`**, coherente con `ADR-002`: un bloque del 10 al 15 impide check-in el 15.

Reglas:

- Un bloqueo **existe con independencia del estado de las reservas**. Si hay una reserva confirmada que cae dentro del rango, el sistema debe **alertar**, no modificar la reserva en silencio.
- Un bloqueo **debe reflejarse en el iCal export**. Si no se refleja, las OTAs lo venden. Esta es la parte del bloqueo que sí depende de la capa informativa, y por eso tiene que funcionar.
- `reason` es obligatorio. "Fuera de servicio" sin motivo no es accionable para el operador ni auditable después.

---

## 5. Disponibilidad

**Origen:** decisión del operador, septiembre 2026.
**Evidencia:** estado actual — `backend/app/routers/reservations.py` expone únicamente `POST /`, `POST /{code}/confirm` y `GET /{code}`. No existe ningún endpoint que responda qué cabañas están libres.

**Estado actual:** este es el gap más grave del sistema. `create_prereservation` recibe `accommodation_id` como **parámetro obligatorio**: nadie pregunta qué hay disponible. Con 3 o 4 cabañas, el NLU tiene que elegir una antes de saber si está libre; si la elegida está ocupada, el constraint la rechaza correctamente y el huésped recibe un error de conflicto de fechas **aunque haya otra cabaña libre**. El sistema tampoco puede sugerir alternativas, porque no sabe qué está libre. No hay sobreventa, pero tampoco hay autoservicio. Ver gap **G1**.

### Norma: `GET /availability`

```
GET /api/v1/availability?check_in=YYYY-MM-DD&check_out=YYYY-MM-DD&guests=N
```

**Solo lectura.** Devuelve las cabañas que pueden recibir una reserva que cumpla todas las reglas de dominio, para el rango `[check_in, check_out)`.

**Invariante central: lectura y escritura aplican exactamente las mismas reglas.** Un filtro de disponibilidad que acepte algo que `create_prereservation` va a rechazar es un bug, no una diferencia de criterio. La lectura es la proyección de la misma decisión, no una segunda implementación.

Criterios de inclusión, en este orden (el primero que falla excluye la cabaña):

1. `accommodations.active = true`
2. Sin solapamiento con reservas en `pre_reserved` o `confirmed` — **la misma condición del constraint `no_overlap_reservations`**
3. Sin solapamiento con filas de `accommodation_blocks`
4. `capacity >= guests`
5. `nights >= noches_minimas` de la temporada que aplica
6. El rango cumple `check_in < check_out`

**Respuesta:**

```json
{
  "check_in": "2027-01-08",
  "check_out": "2027-01-12",
  "guests": 4,
  "temporada": "alta",
  "noches_minimas": 5,
  "total_noches": 4,
  "cumple_minimo": false,
  "motivo_rechazo": "minimo_noches",
  "alternativa_mas_cercana": "2027-01-03",
  "available": [
    { "accommodation_id": 2, "name": "Cabaña Lago", "precio_noche": 95000.00, "precio_total": 380000.00, "deposito": 190000.00 }
  ]
}
```

**Por qué el contrato importa tanto.** Con 3 o 4 cabañas, el caso de negocio dominante es "esa cabaña está ocupada pero hay otra libre". Sin este endpoint, ese caso es un error para el huésped. Con él, el bot puede ofrecer alternativas reales, y el operador tiene una vista única de la disponibilidad que además usa en M1 (el protocolo de aprobación de solicitudes OTA).

El campo `motivo_rechazo` es obligatorio cuando no hay disponibilidad. Sin él, el bot no puede explicar por qué no puede aceptar la reserva, que es distinto de no tener inventario.

---

## 6. Canales y modelo de confianza

**Origen:** `PMS_Criterios_Produccion` §"Fuente maestra declarada", y `ADR-003` D1 y D2.
**Evidencia:** `ADR-003`, `backend/app/services/ical.py`, `backend/app/jobs/import_ical.py`.

### Qué puede hacer cada canal

| Canal | Puede escribir en la fuente maestra | Dirección | Latencia de propagación |
|---|---|---|---|
| WhatsApp Cloud API | **Sí** — es el camino de reserva directa | Push inmediato | Ninguna |
| Mercado Pago | **Sí**, vía webhook firmado | Push inmediato | Ninguna |
| iCal import | **Sí**, creando reservas de canal | Pull, cada 5 min del sistema | El sistema ve la OTA en ≤5 min |
| iCal export | No — solo informa | La OTA hace pull | **3 h en Airbnb, 2-6 h en Booking.com** |
| Panel admin | **Sí** | Directo | Ninguna |

**iCal no es un control de concurrencia.** Es un canal de propagación con retardo. Ninguna garantía de no sobreventa puede apoyarse en él.

### Ventanas de propagación, con fuente

| Plataforma | Ventana | Fuente |
|---|---|---|
| Airbnb | **3 horas**, automático | Documentado en [Airbnb Help, artículo 99](https://www.airbnb.com/help/article/99): *"Your Airbnb calendar automatically updates every 3 hours, and pulls in information from the other calendars you've connected."* |
| Airbnb, refresh manual | Variable, **limitado por tasa** | El mismo artículo: exceder el límite obliga a esperar al próximo ciclo automático. **No es una palanca operable.** |
| Booking.com | **2 a 6 horas** | Observado en la práctica, **no documentado oficialmente** |
| Airbnb, alcance de import | Hasta **2 años** de datos | Documentado en el mismo artículo. Eventos históricos o erróneos entran igual en el feed. |

La consecuencia aceptada, con sus mitigaciones, está enunciada en `ADR-003` §"Riesgo residual". Este documento no la reestima ni la suaviza.

### Regla de oro: un conflicto OTA nunca se descarta en silencio

**Estado actual:** incumplida. `backend/app/jobs/import_ical.py` envuelve cada importación en un `except Exception` genérico que hace `session.rollback()` sobre una **sesión compartida** y continúa con la siguiente cabaña. Un solo evento que choque con el constraint de exclusión revierte **todos** los eventos ya importados para esa cabaña en esa corrida, y solo deja un `log.error`.

El efecto es peor que una sobreventa: una reserva confirmada y pagada en Airbnb o Booking **desaparece del sistema sin alerta**. El operador no la ve. Ver gap **G4**.

**Norma:**

1. El rollback es **por evento**, no por corrida. Un evento fallido no puede arrastrar a los demás.
2. Un choque con el constraint se distingue de un fallo de red o de parseo, y se registra con su propia métrica.
3. Un choque es un **conflicto a escalar**, con alerta al operador. Nunca un `continue` silencioso.
4. El operador recibe la lista de reservas OTA confirmadas que el sistema no pudo incorporar, para que pueda actuar en la plataforma.

Este último punto es el que convierte la anomalía técnica en un problema de negocio visible. Sin él, el sistema puede estar "sincronizando bien" mientras tiene reservas fantasma en la OTA.

---

## 7. Integraciones y costos

### 7.1 WhatsApp

**Origen:** `DOCUMENTO_MAESTRO_P0` §11, corregido contra la tabla oficial de Meta.
**Evidencia:** [Meta — WhatsApp Business Platform pricing](https://business.whatsapp.com/products/platform-pricing).

Meta cobra **por mensaje entregado**, no por conversación, desde el 1 de julio de 2025. Desde el **1 de octubre de 2026** cobra además los mensajes de servicio y las plantillas de utilidad enviadas dentro de la ventana de 24 horas.

| Categoría | Argentina — tarifa A | Argentina — tarifa B | Nota |
|---|---|---|---|
| Marketing | $0,0618 | $0,07107 | Siempre se cobra |
| Utility (plantilla) | $0,0260 | $0,0299 | Dentro de la ventana de 24 h pasa a cobrarse |
| Authentication | $0,0260 | $0,0299 | |
| Service (respuesta libre) | $0,0260 | $0,0260 | **1.000 gratis por número y mes**, luego se cobra |

> **Las dos tarifas son reales y están en circulación.** La divergencia proviene de tablas que transcriben la tarjeta anterior y la posterior al 30 de septiembre de 2026. **La cifra exacta debe confirmarse en la consola de Meta antes de fijarla en un cálculo de presupuesto.** Ninguna de las dos columnas debe usarse como dato duro sin esa verificación.

**Palanca de costo no considerada en los documentos de entrada:** la ventana de **Free Entry Point**. Si la conversación de WhatsApp se origina en un anuncio Click-to-WhatsApp de Meta, **todos los mensajes quedan gratis durante 72 horas**. Aplicable solo a tráfico pagado, pero reduce a cero el costo de mensajería de las reservas directas de ese origen.

**Estimación de referencia para ~30 reservas/mes:** la mayoría de las respuestas de servicio caen bajo el cupo de 1.000 mensajes gratis, pero las plantillas de pre-llegada, check-in y post-estadía **sí se cobran**. Resultado: **~$5/mes, no $0**. La estimación de $0 del `DOCUMENTO_MAESTRO_P0` §11 es incorrecta.

**Estado actual:** ningún documento del repositorio refleja el modelo de cobro por mensaje. Ver gap **G11**.

### 7.2 Mercado Pago

Links de pago en Argentina: **~6,60%** con disponibilidad inmediata, bajando a **~1,56%** a 35 días, más IVA.

Con un depósito del 50% del total, la comisión es material. No es costo fijo, pero erosiona la seña.

**Pendiente de decisión operativa:** link de pago o Checkout Pro. Afecta el margen de la reserva y la velocidad de acreditación. Registrado como pendiente; no se fija aquí.

### 7.3 Costo de infraestructura

El costo de la infraestructura **no** es una constante: es el objeto de una decisión de infraestructura con impacto directo en la justification de `ADR-003`. El análisis completo, con fuente y fecha por línea, y el plan de migración están en [`docs/ops/COSTO_Y_MIGRACION_POSTGRES.md`](../ops/COSTO_Y_MIGRACION_POSTGRES.md).

Resumen para evitar que la cifra se cierre sin leer:

- **Hoy:** ~$50/mes, de los cuales **$38 son Fly Managed Postgres** (`fly.toml` documenta `flyctl postgres create`). No hay tier de hobby.
- **Objetivo tras migrar:** ~$13,58/mes, con PostgreSQL autoalojado en una Machine de 512 MB.
- **La diferencia decide la justificación económica de `ADR-003`.** Con $50/mes, el stack propio cuesta más que Beds24 (€18,25/mes). Con $13,58/mes, cuesta menos.

---

## 8. Precondiciones operativas

Estas condiciones **no son de código**. Son estados que deben existir en las plataformas externas antes de que el sistema pueda considerarse operativo. Ninguna se cumple automáticamente.

| # | Precondición | Verificación | Estado |
|---|---|---|---|
| P1 | **Instantly Book desactivado en Airbnb** | La OTA no debe poder auto-confirmar ninguna reserva | **PENDIENTE** |
| P2 | **Instantly Book desactivado en Booking.com** | Ídem | **PENDIENTE** |
| P3 | iCal export configurado en cada OTA, con la URL del sistema | La cabaña aparece bloqueada en la OTA tras el ciclo | **PENDIENTE** |
| P4 | iCal import configurado en el sistema por OTA | La reserva de la OTA aparece en el sistema | **PENDIENTE** |
| P5 | Plantillas de WhatsApp aprobadas por Meta | WhatsApp Business Manager | **PENDIENTE** |
| P6 | Procedimiento M1/M2/M3 escrito y conocido por el operador | Documento operativo | **PENDIENTE** |

**P1 y P2 son la base del control de sobreventa de `ADR-003`.** Mientras estén pendientes, ese control no está activo: el sistema tiene únicamente las capas 1 y 2 (constraint y lock). Es un estado legítimo y conocido, pero no es el estado que el ADR describe.

`P4` tiene un detalle no obvio: la URL de import iCal de Airbnb y Booking **puede rotar**. Si el sistema deja de ver reservas de una OTA, la primera verificación es que la URL cambió, no que la OTA falló.

---

## 9. Pendientes de producto

Ninguno bloquea la especificación. Todos están registrados aquí con su impacto.

| # | Decisión | Impacto |
|---|---|---|
| 1 | **Saldo impago con depósito del 50%**: ¿se libera la habitación 72 h antes del check-in, o la reserva queda `partially_paid` visible en el panel? | **Único con impacto directo en código.** Define la transición de pago y el flujo de cancelación. |
| 2 | Política de cancelación y reembolso. | Ninguno de los documentos entrantes la define. Mercado Pago admite reembolso total o parcial. |
| 3 | Canal de cobro: link de pago o Checkout Pro. | Margen de la reserva. |
| 4 | Umbral de re-evaluación de sync 2-way. | `ADR-003` §"Plan de revisión" fija el umbral en 20% de reservas OTA durante dos meses consecutivos, o un incidente real de sobreventa. |
| 5 | **Volumen objetivo de cabañas y reservas.** | Los documentos asumen 3-4 cabañas y ~30 reservas/mes; `DECISION_EJECUTIVA_OPCION_B` habla de escalar a 10+. **De esto depende si 512 MB de PostgreSQL alcanzan**, y por tanto si la migración de costo sigue siendo válida. |
| 6 | Ventana de downtime para la migración de PostgreSQL. | Aceptable en temporada baja. No aceptable en enero. |

---

## Referencias

- [`ADR-003: Fuente maestra y control de doble reserva`](../adr/003-fuente-maestra-y-control-de-sobreventa.md)
- [`ADR-001: No Integrar un PMS Externo en el MVP`](../adr/001-no-pms-externo.md)
- [`ADR-002: Rango de fechas half-open [)`](../adr/002-daterange-back-to-back.md)
- [`docs/ops/COSTO_Y_MIGRACION_POSTGRES.md`](../ops/COSTO_Y_MIGRACION_POSTGRES.md)
- [`docs/GAPS_IMPLEMENTACION.md`](../GAPS_IMPLEMENTACION.md)
- [Airbnb Help, artículo 99 — Sincronización de calendarios](https://www.airbnb.com/help/article/99)
- [Meta — WhatsApp Business Platform pricing](https://business.whatsapp.com/products/platform-pricing)
- [Fly.io — Managed Postgres pricing](https://fly.io/docs/mpg/)
- [Beds24 — Pricing](https://www.beds24.com/en/pricing/pricing)

---

*Documento canónico de reglas de negocio. Si un valor aparece en otro lugar y contradice este documento, este documento tiene razón y el otro está desactualizado.*
