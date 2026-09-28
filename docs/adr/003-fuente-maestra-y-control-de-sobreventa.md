# ADR-003: Fuente maestra y control de doble reserva

Fecha: 2026-09-28

Estado: Aprobado

Decisor: Administrador SIST_CABANAS

Revisor: Project Lead

---

## Contexto

En septiembre de 2026 se recibieron tres documentos de arquitectura para el sistema de cabañas de Ñecochea. Los tres proponen arquitecturas incompatibles entre sí, y dos de ellos contradicen decisiones ya registradas en este repositorio.

El proyecto **no está en greenfield**. `SIST_CABANAS_MVP` es un sistema construido y funcional: backend FastAPI, dashboard React, PostgreSQL con constraint de exclusión para anti-doble-booking, Redis para locks optimistas, iCal bidireccional, Mercado Pago, WhatsApp Cloud API, 382 tests y configuración de deploy en Fly.io. `ADR-001` (*No Integrar un PMS Externo en el MVP*, Aprobado) prohíbe explícitamente integrar un PMS y fija una regla operativa de rechazo.

Sobre ese sistema existente llegaron tres propuestas:

| Documento | Propuesta | Conflicto |
|---|---|---|
| `DOCUMENTO_MAESTRO_P0_SISTEMA_CABANAS.md` | PostgreSQL como fuente maestra, n8n como orquestador, iCal hacia OTAs, WhatsApp Cloud API automatizado, ~$5/mes | Coincide en intención con `ADR-001` pero describe un stack (n8n en VPS) que no es el que existe |
| `PMS_CABANAS_NECOCHEA_ESPECIFICACION_DEFINITIVA.md` | **Beds24 como fuente maestra**, WhatsApp Business App manual, API 2-way de OTAs, iCal prohibido como canal principal, €18-28/mes | Contradice `ADR-001` de forma directa |
| `PMS_Criterios_Produccion.md` | Catálogo de criterios de producción para un PMS (17 dominios) | No es una decisión arquitectónica; es una rúbrica de evaluación |

Dos afirmaciones de estos documentos resultaron incorrectas al verificarlas contra fuentes primarias y contra el código:

**1. La latencia de iCal.** El `DOCUMENTO_MAESTRO_P0` §4.1 estima la latencia de sincronización iCal en "15 a 45 minutos" y enuncia **"0% overbooking"** como métrica principal. La documentación oficial de Airbnb (Help, artículo 99) dice literalmente: *"Your Airbnb calendar automatically updates every 3 hours, and pulls in information from the other calendars you've connected."* iCal es un mecanismo **pull**: la OTA no recibe un push cuando se confirma una reserva directa, consulta el feed en su propio ciclo. En Airbnb la ventana es de 3 horas; en Booking.com, 2 a 6 horas en la práctica.

Consecuencia directa: **la métrica de 0% de sobreventa no es alcanzable con sincronización iCal**, y afirmar lo contrario en un documento de arquitectura induce a error sobre el nivel de protección real del sistema.

**2. El costo de WhatsApp.** El mismo documento §11 asume "primeras 1.000 conversaciones de servicio/mes gratis" y un costo de "$0.00". Meta cobra **por mensaje entregado** desde el 1 de julio de 2025, y **desde el 1 de octubre de 2026** cobra también los mensajes de servicio y las plantillas de utilidad dentro de la ventana de 24 horas. Para Argentina, utility y service quedan en $0,0260 por mensaje, con 1.000 mensajes de servicio gratis por número y mes.

Un tercer punto, verificado contra `fly.toml`, corrigió la premisa económica de la comparación entre opciones: el repositorio documenta `flyctl postgres create`, es decir **Fly Managed Postgres, cuyo plan mínimo es de $38/mes y no tiene tier de hobby**. El costo real de infraestructura del stack propio ronda los $50/mes, no los $5 que describen los documentos de entrada. El análisis completo está en [`docs/ops/COSTO_Y_MIGRACION_POSTGRES.md`](../ops/COSTO_Y_MIGRACION_POSTGRES.md).

## Decisión

**Se mantiene PostgreSQL como fuente maestra única del sistema. No se integra ningún PMS externo.**

Esta decisión **reafirma y extiende `ADR-001`**; no lo reemplaza ni lo revierte. `ADR-001` sigue vigente en su razón de no integrar un PMS, y este ADR añade la capa de control de disponibilidad que faltaba para que la decisión sea coherente en operación real.

Se establecen cuatro decisiones:

### D1. Fuente maestra

Las tablas `reservations` y `accommodations` de PostgreSQL son la verdad. iCal, Mercado Pago, WhatsApp y el dashboard admin son **proyecciones** de esa verdad, nunca fuentes independientes. Una segunda copia de inventario requiere estar declarada como tal, ser distinguible y tener su desfase medido.

### D2. Cadena de control de disponibilidad

La disponibilidad se protege con cuatro capas, ordenadas de más fuerte a más débil:

| # | Capa | Naturaleza | Qué garantiza |
|---|---|---|---|
| 1 | Constraint `no_overlap_reservations` (`EXCLUDE USING gist`) | Detectiva, en base de datos | **Invariante transaccional dura.** No puede fallar. Es la garantía real. |
| 2 | Lock Redis `SET NX EX` | Preventiva, distribuida | Cubre la carrera entre peticiones simultáneas. Optimista: puede fallar o degradarse. |
| 3 | Aprobación del anfitrión en la OTA | Preventiva, en la OTA | Con Instantly Book desactivado, **ninguna OTA puede auto-confirmar**. Depende de que el operador consulte el panel. |
| 4 | Export iCal | **Informativa** | Propaga el bloqueo hacia las OTAs con 3 a 6 horas de retardo. |

**iCal no es un control de concurrencia.** Es la capa 4, y su función es informativa. Ninguna garantía de no sobreventa puede apoyarse en ella.

### D3. Instantly Book desactivado en Airbnb y Booking

Se desactiva Instantly Book en ambas plataformas. Consecuencia: una solicitud de reserva en OTA **nunca se auto-confirma**; siempre pasa por aprobación del anfitrión, que es un acto humano que puede consultar el panel.

Esta es una **acción de configuración de la propiedad, no un cambio de código**. Por eso necesita registro explícito:

- **Responsable:** [por definir]
- **Fecha de ejecución:** [por definir]
- **Evidencia:** captura de la configuración de Airbnb y de Booking, adjunta al issue de seguimiento
- **Verificación:** ninguna OTA debe poder auto-confirmar una reserva

> **Estado: PENDIENTE.** Hasta que se complete, la capa 3 de la cadena de control **no está activa** y el control de sobreventa descansa únicamente en las capas 1 y 2.

### D4. Constantes comerciales canónicas

Seña (depósito) del **50%**. Bloqueo de pre-reserva de **2 horas en temporada alta** y **4 horas en el resto**. El TTL del lock Redis coincide con el TTL de la pre-reserva. Estos valores reemplazan los que hoy están hardcodeados en el código (30% y 30 minutos) y en la migración inicial.

El detalle completo, incluyendo máquina de estados, tarifas por temporada y estadía mínima, está en [`docs/domain/ESPECIFICACION_DOMINIO_V1.md`](../domain/ESPECIFICACION_DOMINIO_V1.md).

## Justificación

### Por qué no Beds24 ni ningún PMS

1. **Ya existe un sistema funcionando.** Descartarlo significa descartar 7.150 líneas de Python, ~3.000 de TypeScript y 382 tests para volver a implementar capacidades que el sistema actual ya tiene.
2. **El control de sobreventa no mejora.** Beds24 ofrece sync 2-way real, pero el problema no es la latencia de la OTA: es que existe una decisión de negocio sobre cuánto inventario se arriesga a doble reserva. Cambiar de PMS no elimina la necesidad de decidir eso.
3. **La economics sí favorece al stack propio, pero solo tras la migración documentada.** Hoy el stack propio cuesta ~$50/mes frente a €18,25 de Beds24. Ese cuadro cambia a ~$13,58/mes al migrar fuera de Fly Managed Postgres. La migración está planificada, no ejecutada.
4. **Beds24 introduce una segunda fuente maestra**, que es exactamente lo que D1 prohíbe, y obliga a decidir cuál de las dos fuentes manda cuando discrepan.

### Pros de mantener el stack propio

- El control de doble-booking vive en un constraint transaccional que el operador controla y puede verificar.
- El flujo conversacional por WhatsApp con NLU es diferenciador propio y no existe PMS chico que lo cubra.
- Costo marginal de una unidad adicional muy bajo: €0,55/mes frente a reimplementar.
- Cero dependencia de un tercero para el camino crítico de la reserva.

### Cons

- El sync hacia OTAs es iCal, con 3 a 6 horas de retardo. No hay modo de eliminarlo sin un channel manager de pago.
- El operador es responsable de que Instantly Book esté efectivamente apagado en cada OTA.
- El dashboard admin está incompleto, y D3 depende de que sea usable (ver M1 abajo).

## Alternativas consideradas

### Alternativa 1: Beds24 como fuente maestra (propuesta por `PMS_CABANAS_NECOCHEA_ESPECIFICACION_DEFINITIVA`)

Beds24 como PMS, WhatsApp Business App manual, sync 2-way de OTAs, Google Calendar como espejo de solo lectura.

- **Pros:** sync 2-way real en menos de 30 s; cierra completamente la ventana de 3-6 h; sin mantenimiento de servidor; channel manager incluido (€0,55 por conexión).
- **Cons:** contradice `ADR-001`; obliga a descartar el sistema existente; costo de €18,25/mes sin averteduras; el chat de WhatsApp pasa a ser manual, perdiendo la automatización que hoy es el diferencial del producto.
- **Por qué fue rechazada:** contradice un ADR vigente sobre un sistema ya construido, y el beneficio principal (sync 2-way) se puede conseguir más adelante por ~€1-2/mes con un channel manager sin abandonar el control del dato. El costo de rechazo es alto y el beneficio no lo justifica hoy.

### Alternativa 2: n8n en VPS como orquestador (propuesta por `DOCUMENTO_MAESTRO_P0_SISTEMA_CABANAS`)

- **Pros:** n8n es visualmente accesible para un operador no técnico; el stack es barato según el documento.
- **Cons:** describe un sistema que **no existe**: el backend ya es FastAPI, no n8n. Adoptarlo implicaría una reescritura. Además contradice la propio `DECISION_EJECUTIVA_OPCION_B` del repositorio, que eligió panel visual. Y la premisa de costo (~$5/mes en un VPS) no sobrevive el contacto con Fly Managed Postgres.
- **Por qué fue rechazada:** resuelve un problema que el repositorio ya resolvió por otro camino. Se conserva la **intención** del documento (integraciones, constantes comerciales, criterios de producción) y se descarta su arquitectura.

### Alternativa 3: Aceptar la ventana de iCal sin mitigación

- **Pros:** cero esfuerzo, cero costo.
- **Cons:** la sobreventa pasa a ser el comportamiento normal en temporada alta, donde se concentra el 75-90% de la demanda. Contradice la promesa de 0% del `DOCUMENTO_MAESTRO_P0`.
- **Por qué fue rechazada:** no es una decisión, es una omisión. El riesgo queda sin gestionar.

### Alternativa 4: Híbrido — Postgres como fuente maestra, Beds24 solo como puente de canales

- **Pros:** sync 2-way conservando el control del dato; costo marginal de ~€1,10/mes.
- **Cons:** introduce una segunda copia de inventario que hay que distinguir y auditar constantemente; contradice la regla operativa de `ADR-001`; y es exactamente la salida de emergencia que D5 ya reserva para más adelante.
- **Por qué fue rechazada ahora:** es la opción correcta **más adelante**, si se cumple el umbral de D5. Adelantarla hoy agrega complejidad sin necesidad.

## Consecuencias

### Positivas

- El sistema tiene una sola fuente de verdad declarada, y la regla de la capa 1 es innegociable.
- El nivel de protección real queda documentado, en lugar de sobrevendido con un "0%" que la evidencia no sostiene.
- Se crea el espacio para decidir sobre sync 2-way con un umbral explícito en vez de por inercia.
- Quedan registradas las constantes comerciales que hoy están duplicadas y contradictorias en el código.

### Negativas

- La ventana de 3 a 6 h sigue existiendo. Apagar Instantly Book reduce su probabilidad, **no la elimina**.
- El control depende de la disciplina del operador: si no consulta el panel, la mitigación M1 no se aplica.
- El costo de infraestructura actual ($50/mes) no justifica la decisión por sí solo hasta que se ejecute la migración de PostgreSQL.

### Neutrales

- `ADR-001` permanece vigente sin cambios en su alcance.
- La sincronización iCal sigue siendo necesaria para propagar hacia las OTAs. Solo deja de ser presentada como control.

## Riesgo residual — enunciado sin eufemismo

> Una reserva directa confirmada por WhatsApp **solo** se refleja en el calendario de la OTA tras 3 horas (Airbnb) o hasta 6 horas (Booking.com). Durante esa ventana, un huésped puede solicitar esas mismas fechas y el operador puede aprobar la solicitud **sin ver el hold en el panel**, si no lo consulta primero.

Desactivar Instantly Book cierra la **auto-confirmación**. No cierra la **aprobación a ciegas**.

Mitigaciones adoptadas, todas a costo cero:

- **M1 — Protocolo de aprobación.** Ninguna solicitud OTA se aprueba sin abrir el panel. *Depende de que el panel sea usable; si no lo es, la mitigación es un checklist manual escrito.*
- **M2 — Aviso explícito al operador.** Ante cada confirmación directa, el sistema emite por WhatsApp un mensaje con las fechas y la instrucción literal de bloquearlas en Airbnb y Booking. No se confía en la propagación iCal.
- **M3 — Buffer de check-in.** Para check-ins dentro de las próximas 72 horas, la reserva directa exige confirmación telefónica y verificación previa contra el calendario de cada OTA.

**El refresh manual de Airbnb no sirve como palanca**: la documentación indica que está limitado por tasa y que excederlo obliga a esperar al próximo ciclo automático.

**Riesgo que queda abierto:** con M1, M2 y M3 aplicadas, una sobreventa requiere que el operador apruebe una solicitud sin mirar el panel **y** que la reserva directa se haya confirmado sin su intervención. Es improbable, pero **no es cero**.

Este ADR **no promete 0% de sobreventa**. Ningún documento vigente debe afirmarlo.

## Plan de revisión

Se re-evalúa esta decisión cuando se cumpla **cualquiera** de estas condiciones:

1. Más de 100 reservas/mes consistentes. *(heredado de `ADR-001`, sin cambios)*
2. Necesidad de gestión multi-propietario. *(heredado de `ADR-001`)*
3. Requisito de reporting fiscal complejo. *(heredado de `ADR-001`)*
4. **Umbral nuevo — volumen de reservas OTA:** si las reservas originadas en Airbnb o Booking superan el **20% del total mensual** durante dos meses consecutivos, se justifica pagar un channel manager (~$1-2/mes) por sync 2-way que cierre la ventana de este ADR por completo. Es la salida natural si la sobreventa pasa a tener costo material.
5. **Incidencia real de sobreventa:** un solo incidente documentado de doble reserva activa la evaluación de sync 2-way, independientemente de los volúmenes.

Condiciones heredadas de `ADR-001` que **no** cambian: la prohibición de integrar un PMS externo, y su regla operativa de rechazar cualquier propuesta de "usar un PMS para acelerar".

## Criterios de éxito

- [ ] Instantly Book desactivado en Airbnb y en Booking, con responsable, fecha y evidencia registrados en el issue de seguimiento.
- [ ] Ningún documento vigente afirma "0% overbooking".
- [ ] Todo documento vigente declara explícitamente que iCal no es un control de concurrencia.
- [ ] Las constantes canónicas (50%, 2 h / 4 h) están escritas en un único documento, sin duplicación contradictoria.
- [ ] El operador tiene un procedimiento M1/M2/M3 escrito y conocido.

## Notas

### Trazabilidad de los documentos entrantes

Los tres documentos recibidos en septiembre de 2026 se resuelven así:

| Documento | Destino | Razón |
|---|---|---|
| `DOCUMENTO_MAESTRO_P0_SISTEMA_CABANAS.md` | **Parcialmente adoptado.** Copiado en [`docs/entrantes/`](../entrantes/) como registro histórico. | Se adoptan sus constantes comerciales, la definición de las cadenas de integración y sus criterios de producción. Se rechazan su arquitectura (n8n), su latencia iCal de "15-45 min", su costo de WhatsApp de "$0" y su métrica de "0% overbooking". |
| `PMS_CABANAS_NECOCHEA_ESPECIFICACION_DEFINITIVA.md` | **Rechazado.** No se copia al repositorio. | Contradice `ADR-001` de forma directa al proponer Beds24 como fuente maestra. Su prohibición de iCal y su exigencia de API 2-way son correctas como diagnóstico, pero la solución que propone es descartada. Citada por título y fecha para trazabilidad. |
| `PMS_Criterios_Produccion.md` | **No es una decisión arquitectónica.** No se copia. | Es una rúbrica de evaluación de 17 dominios de calidad de un PMS. Se conserva como referencia conceptual: su criterio de que "una capacidad indispensable puede estar resuelta por un módulo externo siempre que esté integrado, sea observable y mantenga datos consistentes con el núcleo" es exactamente el principio de D1. |

### Referencias

- [Airbnb Help, artículo 99 — Sincronización de calendarios](https://www.airbnb.com/help/article/99) — fuente primaria de la ventana de 3 horas.
- [Meta — WhatsApp Business Platform pricing](https://business.whatsapp.com/products/platform-pricing) — modelo de cobro por mensaje.
- [Fly.io — Managed Postgres pricing](https://fly.io/docs/mpg/) — plan mínimo de $38/mes, sin tier de hobby.
- [Beds24 — Pricing](https://www.beds24.com/en/pricing/pricing) — costo real de la alternativa descartada.
- [`docs/domain/ESPECIFICACION_DOMINIO_V1.md`](../domain/ESPECIFICACION_DOMINIO_V1.md) — reglas de negocio canónicas.
- [`docs/ops/COSTO_Y_MIGRACION_POSTGRES.md`](../ops/COSTO_Y_MIGRACION_POSTGRES.md) — análisis de costo y plan de migración.
- [`docs/GAPS_IMPLEMENTACION.md`](../GAPS_IMPLEMENTACION.md) — 12 gaps verificados contra el código.

### Relacionado

- [ADR-001: No Integrar un PMS Externo en el MVP](001-no-pms-externo.md) — vigente, reafirmado por este ADR.
- [ADR-002: Rango de fechas half-open `[)` para reservas](002-daterange-back-to-back.md) — la base del constraint de la capa 1.
- [DECISION_EJECUTIVA_OPCION_B](DECISION_EJECUTIVA_OPCION_B.md) — la decisión vigente de panel visual para el operador.

---

*Este ADR sigue el formato [MADR](https://adr.github.io/madr/)*
