# Gaps de Implementación — Sistema de Cabañas Ñecochea

**Estado:** Vigente
**Fecha:** 2026-09-28
**Alcance de este documento:** registra la distancia entre lo que
[`ESPECIFICACION_DOMINIO_V1.md`](domain/ESPECIFICACION_DOMINIO_V1.md) prescribe y lo que el
código hace hoy.

> **Ninguno de estos gaps se implementa en la tarea que creó este documento.**
> La reconciliación es documental. Estos gaps están **verificados contra el código** y cada uno
> tiene un DoD binario para quien los implemente después, en otra tarea, con otro PR.

---

## Cómo se verificó cada gap

Todos los hallazgos se obtuvieron leyendo el código de la rama `main` en el commit `d0d62a1`, no
de documentación previa. Las referencias de línea corresponden a ese commit.

Orden de prioridad: primero los que **impiden operar correctamente**, después los que producen
**datos incorrectos**, después los de **higiene**.

| Severidad | Significado |
|---|---|
| **crítica** | Impide una funcionalidad descrita como existente. |
| **alta** | Produce datos、monetarios incorrectos o pérdida silenciosa. |
| **media** | Deuda con impacto real en operación. |
| **baja** | Higiene o consistencia. |

---

## Resumen

| ID | Gap | Severidad | Archivo principal |
|---|---|---|---|
| G1 | No hay consulta de disponibilidad por fechas | **crítica** | `backend/app/routers/reservations.py` |
| G2 | Sin tarifas por temporada | **alta** | `backend/app/services/reservations.py` |
| G3 | Sin estadía mínima | **alta** | `backend/app/services/reservations.py` |
| G4 | El importador iCal revierte toda la corrida | **alta** | `backend/app/jobs/import_ical.py` |
| G5 | Lock Redis con fail-open silencioso | **alta** | `backend/app/services/reservations.py` |
| G6 | Sin estado fuera de servicio por fechas | media | `backend/app/models/accommodation.py` |
| G7 | Capacidad de huéspedes no validada | media | `backend/app/services/reservations.py` |
| G8 | Constantes comerciales duplicadas en dos capas | media | `services/reservations.py` + `001_initial_schema.py` |
| G9 | Instantly Book sin registro ni evidencia | media | (no es código) |
| G10 | Repo público con secreto filtrado y runbook expuesto | media | `.env.template` |
| G11 | Costo de WhatsApp no modelado | baja | (no es código) |
| G12 | `partially_paid` es código muerto | baja | `backend/app/models/enums.py` |

---

## G1 — No hay consulta de disponibilidad por fechas

**Severidad:** crítica
**Archivos:** `backend/app/routers/reservations.py:110`, `backend/app/services/reservations.py:71`

### Comportamiento actual verificado

El router expone cinco rutas:

```
71:  @router.post("/pre-reserve", response_model=PreReservationResponse)
90:  @router.post(...)                    # confirmar
101: @router.post("/{code}/cancel", ...)
110: @router.get("/accommodations")
128: @router.get("/{code}")
```

`GET /accommodations` (línea 110) **no acepta parámetros de fecha y no filtra por disponibilidad**:

```python
@router.get("/accommodations")
async def list_accommodations(db: AsyncSession = Depends(get_db)):
    """List all active accommodations (for E2E tests)."""
    result = await db.execute(select(Accommodation).where(Accommodation.active.is_(True)))
    accommodations = result.scalars().all()
    return [
        {"id": acc.id, "name": acc.name, "type": acc.type,
         "capacity": acc.capacity, "base_price": str(acc.base_price),
         "active": acc.active}
        for acc in accommodations
    ]
```

Devuelve **todas** las cabañas activas, sin importar fechas. Su docstring dice literalmente
**"for E2E tests"**: es un helper de test, no una funcionalidad de producto.

`create_prereservation` recibe `accommodation_id` como **parámetro obligatorio** (línea 71). Nadie
pregunta qué hay libre.

### Por qué es crítico

Es un gap engañoso: la ruta **existe** en el lugar esperado, lo que hace que el sistema parezca
tener la capacidad. Un consumidor que la use recibe todas las cabañas y no puede distinguir una
libre de una ocupada.

Con 3 o 4 cabañas, el caso de negocio dominante es "esa cabaña está ocupada pero hay otra libre".
Hoy ese caso termina en `{"error": "date_overlap"}` para el huésped, aunque haya inventario
disponible, y el sistema **no puede sugerir alternativas porque no sabe qué hay libre**.

No hay sobreventa —el constraint la evita— pero tampoco hay autoservicio. Con un bot de WhatsApp
al frente, cada consulta de disponibilidad que no se puede resolver es un mensaje a un humano.

### Comportamiento requerido

Endpoint de solo lectura que devuelva las cabañas que pueden recibir una reserva que cumpla **todas**
las reglas de dominio, aplicando los mismos criterios que el camino de escritura.

Contrato completo en [`ESPECIFICACION_DOMINIO_V1.md` §5](domain/ESPECIFICACION_DOMINIO_V1.md).
Invariante central: **lectura y escritura aplican exactamente las mismas reglas**. Un filtro que
acepte algo que `pre-reserve` va a rechazar es un bug.

`motivo_rechazo` es obligatorio cuando no hay disponibilidad: sin él el bot no puede explicar por
qué no acepta la reserva, que es distinto de no tener inventario.

### DoD

- [ ] Existe `GET /api/v1/availability?check_in=&check_out=&guests=` devolviendo solo cabañas
      admissibles
- [ ] Acepta `guests` y excluye cabañas con `capacity < guests`
- [ ] Excluye cabañas con reserva en `pre_reserved` o `confirmed` que solape el rango
- [ ] Devuelve `motivo_rechazo` cuando el resultado es vacío
- [ ] **Test de paridad:** para un conjunto de fechas, toda cabaña devuelta por `/availability` es
      aceptada por `POST /pre-reserve` sin error de solapamiento, y toda cabaña rechazada por
      `/availability` es rechazada por `pre-reserve`. El test falla si hay discrepancia.
- [ ] `GET /accommodations` queda marcada como helper de test en su docstring, o se renombra para
      que no se confunda con la capacidad de producto

---

## G2 — Sin tarifas por temporada

**Severidad:** alta
**Archivos:** `backend/app/services/reservations.py:86-95`, `backend/app/models/accommodation.py`

### Comportamiento actual verificado

`accommodations` solo tiene `base_price` y `weekend_multiplier` (1.2). El cálculo (líneas 86-95):

```python
base_price = Decimal(str(acc.base_price))
weekend_mult = Decimal(getattr(acc, "weekend_multiplier", Decimal("1.2")))
weekend_nights = 0
for i in range(nights):
    if (check_in + timedelta(days=i)).weekday() in (5, 6):
        weekend_nights += 1
weekday_nights = nights - weekend_nights
total_price = (base_price * weekday_nights) + (base_price * weekend_mult * weekend_nights)
```

El propio docstring del módulo lo reconoce: *"NO se implementa todavía: Mercado Pago, pricing
avanzado, extensión de lock"*.

### Por qué es alta

Es un placeholder reconocido. **Toda la facturación de temporada alta se cobra a tarifa base.** Con
un 50% de depósito sobre un total mal calculado, el error monetario es directo y se propaga al
saldo pendiente.

### Comportamiento requerido

Tabla `temporadas_tarifas` y resolución por temporada, con `base_price` como fallback explícito
mientras la tabla se puebla. Definición SQL en
[`ESPECIFICACION_DOMINIO_V1.md` §3](domain/ESPECIFICACION_DOMINIO_V1.md).

Cobro noche por noche, para que una estadía que cruza el límite de dos temporadas pague el precio
correcto en cada tramo.

### DoD

- [ ] Existe la migración Alembic que crea `temporadas_tarifas` con su índice de lookup
- [ ] `create_prereservation` resuelve el precio desde la tabla cuando hay fila aplicable
- [ ] El rango de fechas de la tabla usa semántica half-open `[)`, igual que `ADR-002`
- [ ] **Test:** una estadía que cruza de `baja` a `alta` cobra el precio de cada tramo por separado
- [ ] **Test:** con la tabla vacía, el precio cae al comportamiento actual de `base_price` ×
      `weekend_multiplier` sin error
- [ ] Una estadía menor que `noches_minimas` es rechazada con un error identificable

---

## G3 — Sin estadía mínima

**Severidad:** alta
**Archivo:** `backend/app/services/reservations.py:76-79`

### Comportamiento actual verificado

Las únicas validaciones de entrada son:

```python
76: if check_in >= check_out:
78: if guests <= 0:
```

Búsqueda de `noches_minimas` en todo el repositorio: **cero resultados**. No existe el concepto
en ningún archivo.

### Por qué es alta

Una reserva de **1 noche en el pico de enero** se acepta hoy sin objeción. Ese es exactamente el
escenario que los documentos de arquitectura cite como razón de ser del sistema, y el que más
valor pierde el dueño.

### Comportamiento requerido

Estadía mínima de **5 noches** del 1 al 10 de enero, **3** en feriados largos, **2** en el resto.
Resuelta por la temporada del `check_in`. Al fallar, ofrecer la fecha alternativa más cercana que sí
cumpla el mínimo.

### DoD

- [ ] Existe el campo `noches_minimas` (en `temporadas_tarifas`, con default 2)
- [ ] `create_prereservation` rechaza estadías por debajo del mínimo y devuelve un error
      identificable, por ejemplo `{"error": "min_stay_not_met", "minimo": 5}`
- [ ] `/availability` aplica el mismo criterio y **rechaza** la cabaña, no la lista
- [ ] **Test:** 1 noche del 5 de enero es rechazada; 5 noches del 5 de enero, aceptada
- [ ] **Test:** 2 noches en temporada baja, aceptada; 1 noche en temporada baja, rechazada

---

## G4 — El importador iCal revierte toda la corrida

**Severidad:** alta
**Archivo:** `backend/app/jobs/import_ical.py:106-119`

### Comportamiento actual verificado

```python
106: except Exception as e:  # pragma: no cover
...
118:     await session.rollback()
119:     continue
```

La sesión es **compartida** por toda la corrida del job (línea 52 abre una sesión para todas las
cabañas). Un único evento que choque con el constraint revierte **todos los eventos ya importados
para esa cabaña en esa ejecución**, y el único rastro es un `log.error`.

El `except Exception` genérico no distingue entre:
- choque con el constraint de exclusión (el caso **esperado** cuando hay un hold vigente),
- fallo de red o de parseo del feed,
- error de programación.

### Por qué es alta — y por qué es peor que una sobreventa

Una sobreventa hace que dos huéspedes lean como una sola persona. Esto es distinto y peor: **una reserva
confirmada y pagada en Airbnb o Booking desaparece del sistema sin alerta.** El huésped cree que
tiene reserva; el operador no la ve; el iCal export sigue bloqueando las fechas, así que la
cabaña aparece ocupada para todos sin que nadie pueda explicar por qué.

El sistema puede reportarse como "sincronizando perfectamente" mientras tiene reservas fantasma en
la OTA.

### Comportamiento requerido

1. Rollback **por evento**, no por corrida.
2. Métrica y log propios para `import_rejected` (choque de constraint), distintos de
   `import_fetch_failed` y de los errores de parseo.
3. Un choque es un **conflicto a escalar**, con alerta. Nunca un `continue` silencioso.
4. El operador recibe la lista de reservas OTA confirmadas que no se pudieron incorporar, para
   poder actuar en la plataforma.

### DoD

- [ ] Cada evento se importa en su propia unidad transaccional; el fallo de uno no revierte los
      demás
- [ ] Existe un error de dominio identificable para choque de solapamiento, distinto de la
      excepción genérica
- [ ] `ICAL_SYNC_ERRORS` distingue `import_rejected` de `import_fetch_failed` (hoy son
      indistinguibles)
- [ ] **Test:** dos eventos, el primero en conflicto y el segundo sin conflicto. El segundo queda
      importado. **Hoy ambos se pierden.**
- [ ] Un choque de constraint emite alerta con `accommodation_id`, `source` y el rango de fechas
- [ ] Existe un mecanismo para que el operador vea las reservas OTA no incorporadas

---

## G5 — Lock Redis con fail-open silencioso

**Severidad:** alta
**Archivo:** `backend/app/services/reservations.py:112-113`

### Comportamiento actual verificado

```python
112: except Exception:  # Fallback: en entorno de test sin Redis operativo
113:     locked = True  # confiamos en constraint DB para anti solapamiento
```

El comentario dice "en entorno de test", pero la condición es `except Exception`: **cualquier**
fallo de Redis, en cualquier entorno, asume que el lock se logró.

### Por qué es alta

La doble capa de anti-doble-booking que declara la arquitectura se degrada a una sola, **en
silencio**, sin métrica ni log. Un timeout de Redis en producción no produce ningún síntoma
observable.

No produce sobreventa —el constraint sigue ahí— pero produce dos cosas peores que eso:

1. **Un mensaje de error incorrecto.** El perdedor de la carrera recibe `{"error": "date_overlap"}`,
   que dice "esas fechas están ocupadas" cuando la realidad es "otra persona acaba de reservar esta
   cabaña". Para 3 o 4 cabañas, ese mensaje es un fallo visible para el huésped y cierra la
   conversación.
2. **Pérdida de la recomendación alternativa.** El sistema no puede ofrecer otra cabaña.

### Comportamiento requerido

- Distinguir el entorno de test del entorno real. En producción, un fallo de Redis **no** puede
  asumir el lock adquirido.
- El sistema debe seguir operando sobre la capa 2 (el constraint), pero **degradado y visible**.
- El `IntegrityError` de solapamiento debe distinguirse de otros errores de integridad para poder
  devolver un mensaje útil.

### DoD

- [ ] El `except Exception` genérico desaparece; el fallback a constraint **solo** aplica cuando el
      entorno lo declara explícitamente
- [ ] En producción, un fallo de Redis deja el sistema en estado `degraded` y **no** asume el lock
- [ ] Existe la métrica `redis_lock_unavailable_total`, incrementada en cada fallo de adquisición
- [ ] El mensaje de conflicto sugiere cabaña alternativa cuando hay inventario libre
- [ ] **Test:** con Redis caído, dos peticiones simultáneas sobre las mismas fechas → exactamente una
      confirma, la otra recibe un mensaje que no dice "date_overlap"
- [ ] **Test:** con Redis caído, el sistema no reporta éxito silencioso; el health check refleja la
      degradación

---

## G6 — Sin estado fuera de servicio por fechas

**Severidad:** media
**Archivos:** `backend/app/models/accommodation.py`, `backend/app/jobs/import_ical.py:52`

### Comportamiento actual verificado

`accommodations` tiene un solo campo de estado: `active: Boolean`. Búsqueda de
`accommodation_blocks` en el repositorio: **cero resultados**.

Peor: `import_ical.py:52` filtra por `Accommodation.active == True`, así que desactivar una cabaña
**también la saca del sincronismo iCal**. No es un estado de "avería", es un estado de "no existe".

### Por qué importa

No hay forma de bloquear una avería de tres días en plena temporada alta sin desactivar la cabaña
completa, lo que además la saca de la rotación de iCal y por tanto la expone a ventas en la OTA.
Es peor que no tener la función: el mecanismo disponible produce un resultado incorrecto.

### Comportamiento requerido

Tabla `accommodation_blocks` con rango half-open `[)`, `reason` obligatorio, independiente del estado
de las reservas. Un bloqueo debe reflejarse en el iCal export. Definición en
[`ESPECIFICACION_DOMINIO_V1.md` §4](domain/ESPECIFICACION_DOMINIO_V1.md).

### DoD

- [ ] Existe la migración que crea `accommodation_blocks` con su índice
- [ ] `create_prereservation` rechaza fechas dentro de un bloque
- [ ] `/availability` excluye cabañas con bloqueo
- [ ] El iCal export incluye los rangos bloqueados
- [ ] Desactivar una cabaña (`active = false`) **no** la excluye del export iCal, solo de la
      disponibilidad
- [ ] **Test:** un bloque del 10 al 15 impide check-in el 15 (semántica half-open)
- [ ] `reason` es obligatorio: insertar sin él falla

---

## G7 — Capacidad de huéspedes no validada

**Severidad:** media
**Archivo:** `backend/app/services/reservations.py:78`

### Comportamiento actual verificado

```python
78: if guests <= 0:
```

`capacity` existe en el modelo como `Integer NOT NULL` (`001_initial_schema.py:39`) y se devuelve en
`GET /accommodations`. **Nunca se compara con `guests`.**

### Por qué importa

Un grupo de 8 personas entra en una cabaña declarada para 4. Con 3 o 4 cabañas y pocas unidades, es
un problema de seguridad del alojamiento, no solo de datos.

### DoD

- [ ] `create_prereservation` rechaza `guests > acc.capacity`
- [ ] El error es identificable, por ejemplo `{"error": "capacity_exceeded", "capacity": 4}`
- [ ] `/availability` excluye cabañas con `capacity < guests`
- [ ] **Test:** 5 huéspedes en una cabaña de 4 es rechazado

---

## G8 — Constantes comerciales duplicadas en dos capas

**Severidad:** media
**Archivos:** `backend/app/services/reservations.py:31-33`,
`backend/alembic/versions/001_initial_schema.py:80`

### Comportamiento actual verificado

Dos capas con el mismo valor, que hoy es 30% y 30 minutos:

```python
# services/reservations.py
31: LOCK_TTL_SECONDS = 1800  # 30 minutos
32: PRERESERVATION_EXPIRY_MINUTES = 30
33: DEPOSIT_PERCENTAGE_DEFAULT = 30
```

```python
# alembic/versions/001_initial_schema.py
80: sa.Column("deposit_percentage", sa.Integer(), server_default="30", nullable=False),
```

También referencian `deposit_percentage`: `services/ical.py`, `schemas/admin.py`, `routers/admin.py`,
`models/reservation.py`, `frontend/admin-dashboard/src/types/index.ts`, y los fixtures
`tests/conftest.py`, `create_test_data.py`, `scripts/seed_test_data.py`,
`tests/test_double_booking.py`, `tests/test_constraint_validation.py`.

### Por qué importa

Cambiar el valor requiere acordarse de los dos sitios. Editar la migración `001` **no es opción**:
las migraciones aplicadas no se reescriben. Sin una migración nueva, el `server_default` sigue en 30
y las inserciones que no pasan por el servicio quedan desalineadas.

### Comportamiento requerido

Depósito **50%**. Bloqueo **7.200 s** en `alta` y **14.400 s** en el resto, con el TTL del lock igual
al de la pre-reserva. Migración Alembic nueva, nunca edición de la `001`.

### DoD

- [ ] Existe una migración Alembic **nueva** que cambia el default de `deposit_percentage` a 50
- [ ] `DEPOSIT_PERCENTAGE_DEFAULT` vale 50
- [ ] El TTL del lock y el de la pre-reserva se derivan de la **misma** constante, por temporada
- [ ] Ninguna constante duplicada queda en dos capas
- [ ] Los fixtures y tests que asumen 30% están actualizados
- [ ] `frontend/admin-dashboard/src/types/index.ts` refleja el nuevo valor
- [ ] **Test:** una reserva creada sin `deposit_percentage` explícito guarda 50

---

## G9 — Instantly Book sin registro ni evidencia

**Severidad:** media
**Tipo:** no es código. Es una precondición operativa.

### Comportamiento actual verificado

Búsqueda de `instant_book` en el repositorio: **cero resultados**. El concepto no existe en ninguna
parte del código ni de la documentación.

Es correcto que no exista en el código: apagarlo es una **acción de configuración de la propiedad
en Airbnb y Booking**, no algo que el sistema pueda hacer. El problema es que no está **registrado**.

### Por qué importa

La capa 3 de la cadena de control de sobreventa de `ADR-003` **depende por completo** de este ajuste
externo. Si no se hace, o si alguien lo reactiva sin querer, el control no está activo y nada en el
sistema lo va a detectar ni a avisar.

Es un punto único de falla con cero monitoreo.

### Comportamiento requerido

Registro explícito con responsable, fecha de ejecución y evidencia (captura de la configuración de
cada plataforma), más un procedimiento de verificación.

### DoD

- [ ] Existe un issue con responsable asignado
- [ ] Hay captura de la configuración de Airbnb con Instantly Book desactivado
- [ ] Hay captura de la configuración de Booking con Instantly Book desactivado
- [ ] Un segundo operador puede reproducir la verificación sin ayuda del primero
- [ ] Existe un recordatorio de verificación periódica (por ejemplo, trimestral)

---

## G10 — Repo público con secreto filtrado y documentación operativa expuesta

**Severidad:** media
**Archivo:** `.env.template` (ya corregido en el commit `bec5a07`)

### Comportamiento actual verificado — hallazgos del barrido de secretos

**Barrido completado. Resultado:**

| Verificación | Resultado |
|---|---|
| Archivos `.env` trackeados | Ninguno. Solo `.env.template`, `backend/.env.template`, `frontend/admin-dashboard/.env.example` |
| `.env` en el historial de git | **Nunca** se commiteó ninguno |
| Claves privadas (`.pem`, `.key`, `.p12`, `id_rsa`) | Ninguna |
| Credenciales con formato reconocible (AWS, GitHub, Slack, OpenAI, Google) | Ninguna |
| `.gitignore` cubre `.env`, `env/*.env`, `nginx/ssl/*.key`, `frontend/**/.env.local` | Sí |

**Hallazgo: un secreto real estaba commiteado.**

```
.env.template:215
  ADMIN_CSRF_SECRET=WIWaM_CbERF1PW3zMYRrvsbL7IirUnOK
```

- **Es un valor generado, no un placeholder.** El formato coincide exactamente con el default en
  runtime de `backend/app/core/config.py:81`: `default_factory=lambda: secrets.token_urlsafe(24)`,
  que produce 32 caracteres base64url.
- **Era el único valor real** entre todas las variables `*SECRET*`, `*TOKEN*`, `*KEY*` y
  `*PASSWORD*` del template. Las demás son placeholders (`YOUR_SECURE_DB_PASSWORD_HERE`,
  `optional_webhook_secret`) o están vacías.
- **Introducido en** `c201b4a`, 2025-10-18.
- **El repositorio es público** (`private: false`) desde su creación.

**Remediación ya aplicada** (commit `bec5a07`): el valor fue reemplazado por una variable vacía con
comentario que apunta al default de runtime.

### Lo que NO se corrigió, y por qué

Requiere acceso del operador a la infraestructura y una decisión de política:

1. **Rotar `ADMIN_CSRF_SECRET`** en cualquier despliegue real, si es que ese valor llegó a usarse.
2. **Purgar el valor del historial de git.** Sigue en `c201b4a`. Es visible para cualquiera que
   clone el repositorio.
3. **Decidir si el repositorio pasa a privado.** Con el secreto removido, privatizar sigue siendo
   recomendable: el repo expone topología de despliegue (`fly.toml` con costos y regiones), la
   matriz de nombres de secretos (`ops/FLY_SECRETS_MATRIX.md`), la guía de obtención de secretos
   (`ops/GUIA_OBTENER_SECRETOS_PASO_A_PASO.md`) y el runbook de incidentes
   (`ops/INCIDENT_RESPONSE_RUNBOOK.md`).

**Ninguno de los tres se hizo en esta tarea.** Requieren acceso a la cuenta y una decisión de
política que corresponde al operador.

### DoD

- [ ] `ADMIN_CSRF_SECRET` rotado en todos los entornos desplegados
- [ ] Se verificó si el valor se usó alguna vez; si sí, se documenta la fecha de exposición
- [ ] Decisión registrada sobre purgar el historial (y ejecutada, si corresponde)
- [ ] Decisión registrada sobre privacidad del repositorio
- [ ] Un escaneo de secretos automatizado corre en CI, para que esto no se repita

---

## G11 — Costo de WhatsApp no modelado

**Severidad:** baja
**Tipo:** no es código.

### Comportamiento actual verificado

Ningún documento del repositorio refleja el modelo de cobro de Meta. El `DOCUMENTO_MAESTRO_P0` §11
afirma "primeras 1.000 conversaciones de servicio/mes gratis" y costo **$0**, lo que es incorrecto
desde julio de 2025, cuando Meta pasó a cobrar **por mensaje entregado**.

Desde el **1 de octubre de 2026** cobran también los mensajes de servicio y las plantillas de
utilidad dentro de la ventana de 24 h. Para Argentina, utility y service quedan en $0,0260.

### Por qué importa

Un supuesto de $0 en un documento de arquitectura produce un presupuesto irreal y decisiones
económicas tomadas sobre datos falsos. La estimación realista es **~$5/mes** para 30 reservas.

### Comportamiento requerido

Tabla de costos por categoría en la documentación, con la advertencia de verificar en la consola de
Meta. Ya está en
[`ESPECIFICACION_DOMINIO_V1.md` §7.1](domain/ESPECIFICACION_DOMINIO_V1.md).

### DoD

- [ ] Ningún documento vigente afirma costo de WhatsApp de $0
- [ ] La tabla documenta las dos tarifas en circulación y advierte verificar en la consola
- [ ] Se considera la palanca de Free Entry Point (72 h gratis desde Click-to-WhatsApp)

---

## G12 — `partially_paid` es código muerto

**Severidad:** baja
**Archivo:** `backend/app/models/enums.py`

### Comportamiento actual verificado

Búsqueda en el repositorio: `partially_paid` aparece **una sola vez**, en la definición del enum
`PaymentStatus`. No se usa en ningún servicio, router, test ni script.

### Por qué importa

No es un bug: es una capacidad preparada que el modelo de negocio no necesita. **Con el depósito
del 50% pasa a ser necesario** (§2.2 de la especificación), porque aparece un estado intermedio
entre "cobré la seña" y "cobré todo".

El riesgo no es que esté muerto hoy. Es que, al subir a 50% sin tocar el flujo de pagos, el sistema
pase de "cobró la seña" directo a "cobró todo" o a "falló", y que el saldo intermedio no exista.

### DoD

- [ ] `partially_paid` se usa en el flujo de pagos
- [ ] **Test:** un pago parcial del 50% deja la reserva en `partially_paid`, no en `paid`
- [ ] El panel admin distingue `partially_paid` de `paid` y de `pending`
- [ ] Hay una métrica de reservas con saldo pendiente

---

## Orden de ejecución sugerido

1. **G1** — sin él no hay autoservicio; bloquea el valor del bot.
2. **G4** y **G5** — pérdida silenciosa de datos y degradación silenciosa. Ambos son
   incorreccion de datos, no features.
3. **G2** y **G3** — afectan el dinero directamente.
4. **G8** — depende de G2: las constantes se mueven con el modelo de temporada.
5. **G6** y **G7** — validación de entrada.
6. **G10** — acciones de operador con acceso a infraestructura.
7. **G9** — acción de operador, sin código.
8. **G11** y **G12** — baja prioridad.

**G1, G4 y G5 deberían resolverse antes de poner el sistema frente a huéspedes reales.** G4 y G5 son
defectos que degradan el comportamiento en silencio; G1 es una capacidad faltante que se nota.

---

## Referencias

- [`docs/domain/ESPECIFICACION_DOMINIO_V1.md`](domain/ESPECIFICACION_DOMINIO_V1.md) — la norma que estos gaps incumplen
- [`docs/adr/003-fuente-maestra-y-control-de-sobreventa.md`](adr/003-fuente-maestra-y-control-de-sobreventa.md) — decisión de arquitectura
- [`ADR-002`](adr/002-daterange-back-to-back.md) — semántica half-open `[)`
- `backend/app/services/reservations.py`, `backend/app/jobs/import_ical.py`,
  `backend/app/jobs/cleanup.py`, `backend/app/routers/reservations.py`,
  `backend/app/models/accommodation.py`, `backend/app/models/enums.py`
- `backend/alembic/versions/001_initial_schema.py`

---

*Verificado contra `main` en el commit `d0d62a1`. Los números de línea corresponden a ese commit.*
