# Dossier de traspaso — Sistema de reservas de cabañas

**Destinatario:** una sesión de trabajo sin conocimiento previo de este proyecto.
**Encargo:** rediseñar y replanificar la solución desde cero, usando este documento como
única fuente de información.
**Repositorio de referencia (solo lectura, para consultar evidencia):**
`github.com/eevans-d/SIST_CABANAS_MVP`, rama `main`, último commit `d0d62a1` (2025-11-09).

---

## Cómo leer este documento

Está escrito para que no necesites nada más. No hereda supuestos: todo lo que afirma como
hecho fue verificado leyendo el código y ejecutando comandos sobre el repositorio, y las
referencias tienen la forma `archivo:línea` para que puedas comprobarlas.

Cada afirmación está etiquetada:

- **[V]** Hecho verificado directamente sobre el código o el repositorio.
- **[D]** Declarado en la documentación del proyecto, sin verificar o **contradicho** por la
  evidencia. Trátalo como testimonio, no como requisito.
- **[S]** Supuesto o inferencia, con su base explícita.
- **[?]** Vacío: nadie lo definió nunca. Son preguntas abiertas, no omisiones de este informe.

**Secciones 1 a 8: evidencia y encargo. El Anexo C contiene las conclusiones de diseño de un
revisor previo y es deliberadamente separable — si preferís diseñar sin influencia, no lo
leas.**

---

## 1. El encargo

Diseñar y planificar desde cero un sistema de gestión de reservas para un complejo de cabañas.
Existió un intento previo (descrito abajo) que nunca llegó a producción. Ese intento aporta
conocimiento de dominio valioso y una lección de proceso importante, pero **su código no es la
base de partida**: el propietario decidió reescribir (§3).

El entregable esperado se detalla en §8.

---

## 2. El negocio

### 2.1 Problema y usuarios

**[V]** El sistema automatiza la toma de reservas de cabañas por WhatsApp y previene el
doble-booking. El dolor documentado del operador: gestionar reservas con `curl`, SQL y
terminal, estimado en 2-3 horas diarias.

Dos roles, no más:

- **Operador / dueño del complejo.** Un único usuario administrador. **[V]** La guía de
  configuración pide "mínimo 1 email (el del dueño/administrador)".
- **Huésped.** Contacta por WhatsApp. No tiene cuenta ni credenciales.

**[S]** El cliente es una persona concreta y conocida del desarrollador, no un mercado: la
documentación de despliegue dice literalmente "cuando tu amigo lo use". Hay un usuario real
esperando.

### 2.2 Escala y contexto

- **[?]** El número real de cabañas nunca se declaró. **[D]** Se proyecta capacidad para
  "10+ cabañas"; el punto de partida se describe como "1-2".
- **[D]** Umbral de éxito post-lanzamiento: ">100 reservas/mes sin bloqueos ni
  doble-bookings".
- **[S]** Argentina. Cuatro evidencias convergentes: moneda `ARS` por defecto en el esquema
  de pagos, NLU configurado en `es-AR`, teléfonos de ejemplo `+549...`, y Mercado Pago como
  pasarela. La región de hosting elegida es São Paulo (`gru`) por deprecación de Buenos Aires.

**Consecuencia de diseño:** es un sistema mono-tenant, de bajo volumen y un solo operador.
Cualquier propuesta debe ser proporcional a esa escala.

### 2.3 Flujo de negocio

**[D]** El flujo declarado, de punta a punta:

```
Mensaje del huésped → interpretación → cotización → retención temporal de fechas
→ pago de seña → confirmación → instrucciones de check-in
```

Canales de entrada de reservas:
- **WhatsApp** — canal principal del huésped.
- **iCal** — Airbnb y Booking bloquean fechas por importación de `.ics`. **[V]** Decisión
  explícita y argumentada de no integrar sus APIs ni construir un channel manager.
- **Carga directa** — el operador ingresa reservas telefónicas o presenciales.

### 2.4 Reglas de negocio establecidas

**[V] Integridad de fechas — la regla central y la mejor resuelta del proyecto anterior.**
Las reservas se modelan como un rango de fechas *half-open* `[)`: incluye el día de entrada,
excluye el de salida. Esto permite **back-to-back** (que una reserva empiece el mismo día que
otra termina), lo cual es práctica estándar en hotelería y aumenta la ocupación. La exclusión
mutua se impone en la base de datos, no en el código:

```sql
period daterange GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED

ALTER TABLE reservations ADD CONSTRAINT no_overlap_reservations
EXCLUDE USING gist (accommodation_id WITH =, period WITH &&)
WHERE (reservation_status IN ('pre_reserved','confirmed'));
```

Requiere PostgreSQL con la extensión `btree_gist`. La decisión está documentada en un ADR con
su alternativa descartada (rango cerrado `[]`, que bloquea el día de salida y reduce
ocupación). **Este diseño es correcto y merece conservarse; es la parte difícil del dominio.**

**[V] Estados de reserva** en el código anterior: `pre_reserved`, `confirmed`, `cancelled`,
`completed`, `no_show`. Los dos últimos nunca se asignaban en ninguna parte — enum
aspiracional. Solo `pre_reserved` y `confirmed` bloquean fechas.

**[V] Precio**: `precio_base × noches`, con un multiplicador para noches de fin de semana
(por defecto 1.2). Sin temporadas, sin feriados, sin mínimo de noches, sin cargo por huésped
adicional.

**[V] Retención**: la pre-reserva expiraba a los 30 minutos, con un job de expiración que la
cancelaba y liberaba las fechas.

### 2.5 Métricas de éxito declaradas

**[D]** Del plan de experiencia de usuario: doble-bookings = 0; tiempo de gestión diaria
< 15 min; confirmación de pre-reservas < 10 min; conversión a pre-reserva > 25%; conversión a
pago de seña > 60%.
**[D]** Objetivos técnicos: P95 de respuesta de texto < 3 s; tasa de error < 1%; desfase de
sincronización iCal < 20 min.

**[S]** La primera métrica —cero doble-bookings— es la única no negociable: un doble-booking
en un complejo real significa un huésped sin techo y una reputación dañada. Las demás son
deseables.

---

## 3. Decisiones ya tomadas por el propietario

**No las re-litigues.** Fueron tomadas con conocimiento de las alternativas y de sus costos.

| # | Decisión | Alcance |
|---|---|---|
| 1 | **Mono-tenant.** Un complejo real y concreto. | Sin `tenant_id`, sin onboarding de clientes, sin abstracción multi-propietario. |
| 2 | **Reescritura desde cero.** | El código anterior no es la base. Se conserva el *conocimiento* (esquema, invariantes, decisiones), no los archivos. |
| 3 | **WhatsApp conversacional completo.** | El huésped reserva conversando por WhatsApp. Es el diferencial del producto y se mantiene, pese a ser la pieza de mayor riesgo. |
| 4 | **Sin cobro automático en la v1.** | El operador confirma manualmente el pago de la seña (transferencia bancaria). Mercado Pago queda fuera del alcance inicial. |

**Nota sobre la decisión 2:** se tomó sabiendo que descarta ~10.000 líneas de tests y una
capa de observabilidad que sí eran de buena calidad. Fue deliberada, no un descuido.

**[V] Conflicto derivado de la decisión 4 que hay que resolver en el nuevo diseño:** una
retención de 30 minutos es incompatible con la verificación manual de una transferencia.
Nadie confirma un comprobante en ese plazo. La ventana de retención necesita rediseñarse
(duración, recordatorios, liberación) en función de un proceso con una persona en el medio.

### 3.1 Restricciones heredadas que siguen vigentes

- **[V] Monolito.** Prohibición explícita de microservicios.
- **[V] Sin PMS externo.** No integrar QloApps ni similares. ADR argumentado.
- **[V] Airbnb/Booking solo por iCal.** No construir un channel manager propio.
- **[V] Presupuesto operativo mínimo.** El despliegue anterior tenía una guarda de costos que
  abortaba si detectaba más de una instancia; se usaban niveles gratuitos de base de datos.
- **[S] Un solo desarrollador asistido por agentes de codificación.** El repositorio tiene un
  único autor. La documentación menciona "equipo dev", "QA team", "daily standups a las 9:00"
  y un "PM responsable: [Definir]" — ficción organizacional, no un hecho.
- **[V] Sobre el uso de LLM:** el proyecto anterior prohibía explícitamente usar un modelo de
  lenguaje para razonar ("la inteligencia proviene de regex y extracción de fechas"), mientras
  su propia hoja de ruta a 12 meses prometía "GPT-4 NLU". Es una contradicción **no resuelta**:
  queda a criterio del nuevo diseño, con el dato de que la aproximación por reglas que sí se
  implementó era de 111 líneas y claramente insuficiente (§5.4).

---

## 4. Vacíos que bloquean el diseño

**[?] Nada en la documentación del proyecto anterior define estos valores.** Sin ellos no se
puede cotizar ni gestionar excepciones. **No los inventes:** son una conversación de treinta
minutos con el operador. Trátalos como entrada requerida y hazlos explícitos en tu plan.

1. **Cuántas cabañas hay**, su capacidad y su precio base.
2. **Porcentaje de la seña.** El código anterior asumía 30% fijo; nunca fue confirmado por
   nadie. Y si es reembolsable.
3. **Política de cancelación.** Existía el endpoint; no existía la política. Sin plazos, sin
   penalidades, sin reglas de reembolso.
4. **Mínimo de noches**, y si varía por temporada o fin de semana.
5. **Temporadas y feriados.** Es la regla de precio más común en cabañas argentinas y estaba
   declarada fuera de alcance.
6. **Horarios reales de check-in y check-out.** Una única mención suelta (14:00 / 12:00) sin
   respaldo en ningún documento de decisión.
7. **Datos de cobro manual:** CBU/alias, titular, y qué se acepta como comprobante válido.

**[S]** Recomendación de modelado, independiente de los valores: todo esto es **dato
configurable**, no constantes en el código. El proyecto anterior tenía el 30% de seña y el
multiplicador 1.2 incrustados en la lógica.

---

## 5. Qué se construyó antes: evidencia

Contexto cuantitativo **[V]**: 70 commits entre 2025-09-29 y 2025-11-09, luego inactivo.
9.259 líneas de código de aplicación (Python), 10.336 líneas de tests, 2.320 de frontend
(TypeScript), y 12.216 líneas de documentación en 50 archivos Markdown — con 87 archivos `.md`
más borrados a lo largo del historial. **Nunca se desplegó.**

Stack **[V]**: FastAPI + SQLAlchemy async + PostgreSQL 16 + Redis 7; React 19 + Vite +
Tailwind para un panel de administración; despliegue previsto en Fly.io.

### 5.1 Lo que funcionaba

- **[V] Prevención de doble-booking** mediante la constraint `EXCLUDE` descrita en §2.4. Es
  el activo técnico más valioso del proyecto.
- **[V] Confirmación atómica**: `UPDATE ... WHERE id=? AND reservation_status='pre_reserved'`
  verificando `rowcount`, lo que detecta correctamente la doble confirmación concurrente sin
  necesidad de `SELECT FOR UPDATE`.
- **[V] Reintentos con backoff y jitter**, y clasificación correcta de errores reintentables
  (429, 5xx) frente a permanentes (4xx).
- **[V] Observabilidad**: 36 métricas Prometheus, identificador de traza por petición, logging
  estructurado con enmascarado de 7 campos sensibles, health checks. La capa más sólida.
- **[V] Verificación de firma de webhooks de WhatsApp** (HMAC-SHA256 con comparación en
  tiempo constante). Correcta.

### 5.2 Lo que aparentaba funcionar y no funcionaba

| Componente | Estado real verificado |
|---|---|
| **Mercado Pago** | **[V]** No crea preferencias de pago. El enlace que se envía al huésped es una URL construida a mano, `f"https://mpago.la/{reservation_code}"` (`services/button_handlers.py:410,462`), que no resuelve a ningún cobro. El esquema del webhook exige campos en la raíz que Mercado Pago no envía (manda `{"action":..., "data":{"id":...}}`), así que un webhook real habría sido rechazado con 400. La verificación de firma no sigue el esquema de manifest de MP, y si no hay secreto configurado, acepta todo. |
| **Email** | **[V]** `self.enabled = False` (`services/email.py:17`). Los tres métodos escriben un log y devuelven `True`. Existen 4 plantillas HTML que nadie renderiza. |
| **Consulta de disponibilidad** | **[V]** No existe. La función `_show_available_accommodations` (`services/button_handlers.py:341`) **recibe** `check_in` y `check_out` **y no los usa**: lista todos los alojamientos activos. La disponibilidad solo se descubría al chocar contra la constraint. |
| **Audio / transcripción** | **[V]** Muerto. La dependencia está comentada en `requirements.txt`; el endpoint siempre responde `audio_processing_not_available`. Arrastraba `ffmpeg` y librerías `libav*` a la imagen Docker. |
| **Circuit breaker** | **[V]** 270 líneas y 362 líneas de tests propios, con **cero** usos en toda la aplicación. |
| **Importación de iCal** | **[V]** Parser artesanal por `split("BEGIN:VEVENT")`. No maneja *line folding* de RFC 5545 ni `DTSTART;TZID=`, y falla con fechas que incluyen hora. Rompería con archivos reales de Airbnb o Booking. |
| **Panel de administración** | **[V]** El bloque de salud y rendimiento del dashboard está escrito a mano en el código (`health_status="healthy"`, `p95_latency=250`), no medido. |

### 5.3 Defectos verificados

| Severidad | Defecto | Ubicación |
|---|---|---|
| Crítica | `POST /admin/reservations/{id}/cancel` **siempre** devuelve 500: usa `reservation.notes`, campo que no existe en el modelo (se llama `internal_notes`, y no hay `@property` ni `synonym` que lo cubra). | `routers/admin.py:330,362,412` vs `models/reservation.py:67` |
| Crítica | El login del panel no puede funcionar: el frontend llama a `/auth/login`; en el backend no existe ninguna ruta `/auth` (la real es `/api/v1/admin/login`). | `frontend/.../services/auth.ts:10` |
| Crítica | El login de administrador emite un token con **solo una dirección de email**, sin contraseña, y no está limitado por entorno. | `routers/admin.py:64-74` |
| Crítica | El secreto de firma de tokens se autogenera por proceso si no está definido. Con varios workers, cada uno firma con un secreto distinto; cada reinicio invalida todas las sesiones. | `core/config.py:46` |
| Crítica | Los endpoints `/api/v1/reservations/*` y `/api/v1/ical/import` **no tienen autenticación**: cualquiera podía crear, confirmar o cancelar reservas, o inyectar bloqueos de calendario. | `routers/reservations.py` (solo `Depends(get_db)`) |
| Crítica | **Cuatro secretos reales versionados**, presentes en el árbol y en el historial de git: `ADMIN_CSRF_SECRET` y `GRAFANA_ADMIN_PASSWORD` en `.env.template:215,233`; `JWT_SECRET_KEY` e `ICAL_EXPORT_SECRET` en un documento de despliegue. Requieren **rotación**, no borrado. | verificado con `grep` |
| Crítica | La constraint `EXCLUDE` existe **solo en la migración, no en el modelo ORM**. En desarrollo la aplicación creaba el esquema con `Base.metadata.create_all()` (`main.py:43-45`), produciendo una base **sin protección anti-doble-booking**. | `models/reservation.py` |
| Crítica | **`alembic upgrade head` no puede completarse contra PostgreSQL.** La migración 006 crea cuatro índices con `postgresql_concurrently=True` sin `autocommit_block()`, y PostgreSQL prohíbe `CREATE INDEX CONCURRENTLY` dentro de la transacción en la que Alembic ejecuta cada migración. Falla siempre, de forma determinista. Ver §6.1. | `alembic/versions/006_perf_indexes.py` |
| Alta | Los dos workflows de despliegue se disparan al hacer push y **no dependen de los tests**: uno no declara `needs`, el otro declara `needs: []` bajo un comentario que afirma lo contrario. | `deploy-fly.yml`, `deploy-staging.yml:16` |
| Alta | El lock distribuido se anula ante cualquier fallo: `except Exception: locked = True`, sin log ni métrica. Si Redis caía, el sistema seguía adelante. | `services/reservations.py:105-111` |
| Alta | El compose de producción no compila: usa `target: production` y el Dockerfile no tiene *stages*. | `docker-compose.prod.yml:29` |
| Media | La idempotencia guarda un cuerpo de respuesta ficticio (`{"cached": true, ...}`) en vez del real. Deduplica, pero rompe el contrato de idempotencia HTTP. | `middleware/idempotency.py:317-321` |
| Media | Las primeras 22 líneas del `.gitignore` empiezan con un espacio, que Git no ignora. `build/`, `dist/`, `ssl/`, `*.pyo` no se estaban ignorando. | `.gitignore:1-22` |
| Media | Tres versiones de Python distintas: Docker usa 3.11, CI usa 3.12, `pyproject.toml` exige `>=3.12`. Se probaba en un runtime distinto al que se desplegaba. | verificado |

### 5.4 El canal de WhatsApp, en detalle

Es la pieza que la decisión 3 manda conservar como concepto, así que importa saber por qué la
implementación anterior no sirve de base:

- **[V]** La interpretación de mensajes eran **111 líneas** con cuatro expresiones regulares
  (`disponib|libre|hay`, `precio|costo|sale|cuanto`, `reserv|apart|tomo`,
  `servicio|incluye|wifi`). Devolvía **un solo intent** por mensaje, por cascada de
  `if` con salida temprana. Sin puntuación, sin desambiguación, sin múltiples intenciones.
- **[V] No había máquina de estados.** El campo `current_step` se escribe once veces en
  `services/button_handlers.py` y **nunca se lee para decidir nada**: sus únicas apariciones
  en lectura están dentro de ejemplos en docstrings. El ruteo dependía solo del identificador
  del botón pulsado, en una cadena de 21 ramas `if/elif button_id` dentro de un archivo de
  679 líneas.
- **[V] Nunca se ejercitó contra la API real.** Las cuatro funciones de envío empiezan con
  `if settings.ENVIRONMENT != "production": return {"status": "skipped"}`
  (`services/whatsapp.py:83,160,639,795`). Fuera de producción no se enviaba nada, y a
  producción no se llegó nunca.
- **[V]** Si faltaban datos, el bot respondía al huésped con nombres de campos en inglés:
  `"Para avanzar necesito: check_in, check_out, guests."`

**Riesgos externos a tener en cuenta [S]:** WhatsApp Cloud API exige verificación de negocio
ante Meta (puede llevar semanas y no depende del equipo), plantillas aprobadas para iniciar
conversaciones, y tarifa por conversación iniciada por el negocio. Conviene iniciar ese
trámite al principio del proyecto, en paralelo al desarrollo, no al llegar a la etapa de
integración.

### 5.5 Desproporción del andamiaje

**[V]** Para **un único destino de despliegue real** el repositorio mantenía: 7 archivos
`docker-compose`, 5 `nginx.conf`, 4 scripts de arranque con puertos y número de workers
divergentes, 7 rutas de despliegue por script, 8 workflows de CI (tres de los cuales
ejecutaban la misma suite en cada push), 2 plantillas `.env` con 74% de solapamiento, 2
configuraciones de Prometheus contradictorias, 19 scripts sueltos y 16 documentos de
operaciones con fechas congeladas.

**[V]** Nueve dependencias declaradas que **ningún módulo importa**: `spacy`, `numpy`,
`soundfile`, `icalendar`, `aiosmtplib`, `Jinja2`, `holidays`, `psutil`, `aiofiles`. Varios
cientos de megabytes de imagen sin uso.

**Lección transferible:** la complejidad operativa creció sin que nadie la usara. Un solo
camino para cada cosa.

---

## 6. Por qué fracasó: la lección importante

Esta sección es más útil que todo el análisis técnico anterior. **El proyecto no se estancó
por falta de código. Se estancó porque nada impedía declarar "terminado" sin evidencia.**

### 6.1 El hecho central: la integración continua nunca pasó. Ni una sola vez.

**[V]** El workflow de tests (`ci-tests.yml`) se creó el 2025-11-04. Sobre la rama `main`
acumula **10 ejecuciones, numeradas 1 a 10, y las diez concluyeron en `failure`** — desde la
primera, la del propio commit que lo creó, hasta la última del proyecto (2025-11-09). El
workflow de lint (`ci-lint.yml`) lleva **19 ejecuciones sin un solo éxito**. El de
`ci.yml` ("Quick Tests") también falla.

**Ninguno de los tres workflows del repositorio ha tenido jamás una ejecución exitosa.**

Y sin embargo, dos commits posteriores a esa primera falla agregaron **badges de CI al
README**: `c8de7e8` ("badge de CI en README") y `1bf794d` ("badges de Lint & Types"). Se
publicaron insignias de estado para workflows que nunca habían pasado.

**[V] Por qué falla el workflow de tests.** No llega a ejecutar un solo test. El paso
`alembic upgrade head` aborta en la migración 006, que crea índices con
`postgresql_concurrently=True`:

```
ERROR: CREATE INDEX CONCURRENTLY cannot run inside a transaction block
STATEMENT: CREATE INDEX CONCURRENTLY idx_reservation_expires_prereserved ...
```

Alembic ejecuta cada migración dentro de una transacción, y PostgreSQL prohíbe
`CREATE INDEX CONCURRENTLY` ahí. La solución habitual es `op.get_context().autocommit_block()`,
y **no aparece en ningún archivo de `alembic/`**. Es un defecto determinista y permanente, no
una deriva: `alembic upgrade head` **no puede completarse contra PostgreSQL**. Como el job
aborta ahí, `pytest` nunca corre — el log lo confirma: *"No files were found with the provided
path: backend/.pytest_cache"*.

Consecuencia práctica: el sistema **nunca fue migrado a una base PostgreSQL real por su propia
cadena de migraciones**, lo cual es coherente con que nunca se haya desplegado.

**[V] Qué pasa cuando los tests sí corren.** El workflow `ci.yml` ejecuta la suite sobre
SQLite, sin migraciones. Resultado en la ejecución más reciente:

```
47 failed, 272 passed, 19 skipped, 19 warnings, 33 errors in 35.04s
```

Los fallos se concentran en `test_auth_authz.py` y `test_input_validation.py` — es decir, en
las pruebas de autenticación, autorización, inyección SQL, XSS y SSRF. Ninguna cifra
publicada por el proyecto ("381/382 pasando", "99.7%") se parece a esto.

**[V] Y aun así, ese camino no prueba el núcleo.** El archivo de configuración de tests lee
`TEST_DATABASE_URL`, que ningún workflow define; su valor por defecto apunta a un usuario y una
base inexistentes, la conexión falla y el código cae **en silencio** a SQLite:

```python
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
SQLITE_FALLBACK_URL = "sqlite+aiosqlite:///./test_fallback.db"
...
if not await _can_connect(primary_engine):     # siempre verdadero en CI
    await primary_engine.dispose()             # → SQLite
```

SQLite no soporta `EXCLUDE USING gist`. Los **9 tests** que protegían la regla central del
producto —los de `test_double_booking.py` y `test_constraint_validation.py`— se auto-saltan con
`pytest.skip("Constraint EXCLUDE sólo soportado en PostgreSQL")`. **La prevención de
doble-booking, que es el requisito no negociable del sistema, no fue verificada nunca por la
integración continua.**

**[V]** Agravantes: no existe ningún umbral de cobertura en todo el repositorio (`fail_under`
o `--cov-fail-under`: cero apariciones). El archivo `pytest.ini` anula por completo la
configuración de `pyproject.toml`, incluidos `--strict-markers` y `filterwarnings = ["error"]`,
que nunca se aplicaron. 21 tests (los de extremo a extremo) nunca llegan a ejecutarse porque
quedan fuera de `testpaths`. Y las herramientas de lint se instalan **sin versiones fijas**
(`pip install flake8 black mypy ruff`), de modo que el resultado cambia solo con el tiempo: hoy
`black 26.5.1` marca 19 archivos, mientras que `black 23.12.1` —la versión que el propio
proyecto fija en `.pre-commit-config.yaml`— deja los 101 archivos limpios.

### 6.2 El síntoma

Sobre esa base, el proyecto **se declaró terminado al menos cinco veces** —27-sep, 02-oct,
09-oct, 26-oct, 28-oct— y el documento "canónico" del 3 de noviembre seguía teniendo el
despliegue a staging como pendiente. **[V]** Más de cinco semanas de "100% completado" sin un
solo despliegue.

**[V]** La cobertura publicada era 85% en el README, "80-85%" en un informe de calidad y
">80%" en el documento canónico. La cobertura **real medida** era **15%**, con "Routers API
0%, WhatsApp service 2%, main.py 0%". Ese dato existía en un archivo de notas internas del
proyecto y **ningún documento de estado lo incorporó**, ni siquiera el que citaba el informe
del que provenía.

**[V]** Otras contradicciones sin resolver entre documentos: número de tests (27 / 37 / 173 /
180 / 280 / 382 según la fuente), hosting (Fly.io vs Railway vs Neon+Upstash vs Supabase, los
cuatro simultáneamente "vivos"), región de despliegue, "monolito" vs "arquitectura de
microservicios", y un índice canónico que enlazaba cinco archivos inexistentes.

### 6.3 Qué se sigue de esto

El nuevo proyecto necesita, antes que cualquier funcionalidad, un mecanismo que haga
**imposible** repetir esto. Como mínimo:

1. **Un gate que nadie mira no es un gate.** Es la lección más dura de §6.1: el proyecto tenía
   tres workflows, ninguno pasó jamás, y se les pusieron badges igual. Antes de agregar el
   segundo control, el primero tiene que estar en verde y alguien tiene que notar cuándo deja
   de estarlo. Un control roto es peor que ninguno: da la apariencia de rigor sin el rigor.
2. **Prohibido el degradado silencioso.** Si la dependencia que hace válido un test no está,
   el test **falla**; no se salta ni se sustituye por algo más débil.
3. **Fija las versiones de todas las herramientas.** Un `pip install black` sin versión hace
   que el resultado del control cambie solo, sin que nadie toque el código.
4. **Prueba las migraciones aplicándolas de verdad**, contra el mismo motor que usa
   producción, en cada ejecución — y también el `downgrade`. El defecto de la migración 006
   habría aparecido en el primer minuto.
5. **Un solo comando de verificación**, idéntico en local y en integración continua, del que
   dependa el despliegue.
6. **Umbral de cobertura activo y con trinquete** (sube, nunca baja), fijado en un número
   medido y honesto, no aspiracional.
7. **"Terminado" se demuestra con la salida del comando, pegada.** No con un documento.
8. **Prohibidos los documentos de estado.** El estado es el tablero de tareas y el resultado
   de la verificación. El proyecto anterior generó 12.216 líneas de documentación y borró 87
   archivos por contradictorios; ninguno de ellos evitó el estancamiento, y varios lo
   ocultaron.
9. **Los porcentajes de avance son ruido.** Nadie los puede verificar. Sustitúyelos por
   criterios de salida binarios y comprobables.

---

## 7. Activos reutilizables

Lo único que vale la pena rescatar del intento anterior, en orden de valor:

1. **El diseño de integridad de reservas** (§2.4): rango `daterange` half-open y constraint
   `EXCLUDE USING gist` parcial por estado, sobre PostgreSQL con `btree_gist`. Correcto y
   probado conceptualmente. **Recomendación: declararlo también en el modelo ORM**, no solo en
   la migración — su ausencia allí fue lo que permitió que el entorno de desarrollo corriera
   sin protección.
2. **El patrón de confirmación atómica**: `UPDATE ... WHERE estado = esperado` + verificación
   de filas afectadas.
3. **Las dos decisiones de arquitectura documentadas** (no usar un PMS externo; rango
   half-open para permitir back-to-back). Están bien argumentadas y siguen siendo válidas.
4. **El conjunto de métricas y el enmascarado de datos sensibles en logs**, como referencia de
   qué vale la pena instrumentar.

Todo lo demás —integraciones, panel, NLU, capa de operaciones— se rehace.

---

## 8. Entregable esperado

Se espera de vos, en este orden:

1. **Diagnóstico propio y breve.** Podés discrepar de este documento; si lo hacés, decí en
   qué evidencia te apoyás.
2. **Propuesta de solución fundamentada**, proporcional a la escala descrita en §2.2: límites
   del sistema, componentes, modelo de datos, integraciones y requisitos de calidad
   verificables. Justificá las decisiones principales **y sus compromisos**. Evitá
   sobreingeniería: incorporar IA o tecnología más reciente no constituye una mejora por sí
   mismo, y en §5.5 hay evidencia de adónde lleva la complejidad no usada.
3. **Definición del entorno de trabajo de los agentes de codificación** (*harness*):
   instrucciones persistentes, tamaño de tarea, documentación mínima, entorno reproducible,
   controles automatizados, criterios de aceptación y condiciones explícitas para detenerse y
   pedir intervención humana. La §6 explica por qué esta parte no es accesoria.
4. **Hoja de ruta ejecutable**: etapas, prioridades, dependencias y —para cada etapa—
   **criterios de salida binarios y verificables por comando**, no porcentajes. Incluí
   seguridad, manejo de fallos, observabilidad, respaldo y restauración (probada), despliegue
   y reversión, costos operativos y evolución posterior.
5. **Autorrevisión**: puntos débiles de tu propia propuesta y supuestos pendientes.

**Dos condiciones de forma.** No prometas garantías absolutas: traducí la preparación para
producción en controles y evidencias verificables. Y mantené el resultado compacto — la
extensión no es una virtud, como demuestra §6.2.

---

## Anexo A — Preguntas abiertas que conviene cerrar antes de empezar

- Las siete de §4 (reglas de negocio), con el operador.
- ¿Cómo se resuelve el conflicto entre pago manual y ventana de retención (§3)?
- ¿Existe ya una cuenta de WhatsApp Business verificable ante Meta, o hay que iniciarlo?
- ¿El operador acepta verificar transferencias manualmente, y a qué volumen deja de ser viable?
- ¿Qué presupuesto mensual de infraestructura es aceptable?

## Anexo B — Cómo se verificó este documento

Los hechos marcados **[V]** se establecieron leyendo el código fuente y ejecutando comandos
sobre el repositorio en el commit `d0d62a1`: lectura directa de modelos, routers, servicios,
migraciones, workflows y configuración; conteo de líneas y de definiciones de test; búsqueda de
usos reales de cada dependencia declarada; y comprobación de rutas del frontend contra las
rutas registradas en el backend. Cada afirmación de la §5.3 fue confirmada individualmente
sobre el archivo y la línea citados. Los ítems **[D]** provienen de la documentación del
proyecto y se marcan así precisamente porque, en varios casos, la evidencia los contradice.

## Anexo C — Conclusiones de un revisor previo *(separable; no lo leas si preferís diseñar sin influencia)*

Un revisor técnico independiente analizó el material anterior y llegó a estas conclusiones.
**No son vinculantes y se espera que las cuestiones.** Se incluyen solo para no perder el
análisis; toda la evidencia que las sustenta ya está en las secciones 1 a 7.

- **Eliminar Redis.** A esta escala (≤10 cabañas, <100 reservas/mes) no aporta nada que
  PostgreSQL no dé. El lock distribuido era una optimización para evitar colisiones, no un
  mecanismo de corrección — la corrección la da la constraint. Estado conversacional,
  idempotencia y limitación de tasa caben en PostgreSQL. Se pierde: si algún día hicieran
  falta varias instancias con estado compartido, habría que reintroducirlo.
- **Panel renderizado en el servidor en vez de aplicación de página única.** Hay un solo
  usuario administrador. Una SPA obliga a un segundo artefacto de despliegue, CORS, token en
  `localStorage` y un pipeline de build; en el intento anterior produjo el login roto y cuatro
  endpoints sin interfaz. Se pierde: fluidez en la vista de calendario.
- **Interpretación determinista primero.** Una máquina de estados explícita decide; si se
  incorpora un modelo de lenguaje, que sea únicamente como extractor de valores (fechas,
  cantidad de huéspedes) validados por las mismas reglas, nunca eligiendo transiciones ni
  ejecutando acciones. El texto del huésped es entrada no confiable. La decisión de
  incorporarlo debería tomarse con datos: medir la tasa de extracción sobre un corpus de
  mensajes reales del operador antes de decidir.
- **Secuencia sugerida:** fundaciones y harness verificables → núcleo de reservas con prueba
  de concurrencia real → panel del operador → canal de WhatsApp → piloto en producción en
  paralelo a la operación manual. El razonamiento: el panel entrega valor por sí solo (saca al
  operador de la terminal), así que si WhatsApp se complica ya hay algo usable en producción.
- **Riesgo principal identificado:** conservar el bot conversacional y quitar el pago
  automático concentra lo más incierto —aprobación de Meta, ambigüedad del lenguaje natural—
  en la etapa más tardía.
