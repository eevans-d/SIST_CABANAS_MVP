# Costo de Infraestructura y Plan de Migración de PostgreSQL

**Estado:** Propuesta — pendiente de decisión operativa
**Fecha de verificación de precios:** 2026-09-28
**Fecha del documento:** 2026-09-28
**Alcance:** decisión de infraestructura. **No es código de aplicación.**

---

## Resumen ejecutivo

El stack propio cuesta hoy **~$50/mes**. El candidato rechazo, Beds24, cuesta **€18,25/mes**. Es decir: **el stack propio es hoy 2,5 veces más caro**, y la justificación económica de `ADR-003` no se sostiene con estos números.

La causa es una sola línea de configuración: **`fly.toml` documenta Fly Managed Postgres, cuyo plan mínimo cuesta $38/mes y no tiene tier de hobby.** Esa línea es el **85% de la factura de infraestructura**.

Migrando a PostgreSQL autoalojado en una Machine de Fly, el total baja a **~$13,58/mes** — un **ahorro de ~$36/mes**, y por debajo de Beds24.

**Este documento planifica la migración. No la ejecuta.** La ejecución es una decisión operativa posterior, con fecha.

---

## 1. Lo que dice la configuración actual

`fly.toml`, en el encabezado:

```
# Servicios necesarios:
#   1. Backend (FastAPI) - esta app
#   2. PostgreSQL 16 - flyctl postgres create
#   3. Redis - Upstash Redis (integración oficial)
```

Y en la máquina:

```toml
[vm]
  size = "shared-cpu-1x"   # 1 vCPU, 256MB RAM (free tier)
```

Y en el servicio HTTP:

```toml
min_machines_running = 1
auto_stop_machines = false   # Mantener siempre activo para webhooks
```

`flyctl postgres create` crea un **Managed Postgres**. Ese es el costo dominante.

> **Nota sobre el comentario `free tier`.** El `shared-cpu-1x` de 256 MB no es free tier en el sentido de "no se paga". Su lista es de **$1,94/mes** y, con `min_machines_running = 1` y `auto_stop_machines = false`, corre de forma continua. El comentario es engañoso y conviene corregirlo junto con la migración.

---

## 2. Costo actual verificado

Cada línea con su fuente. Verificado el **2026-09-28**.

| Componente | Configuración | Costo/mes | Fuente |
|---|---|---|---|
| Fly Machine (app) | `shared-cpu-1x` 256MB, siempre encendida | **$1,94** | [fly.io/pricing](https://fly.io/pricing/) — $0,0027/h |
| **Fly Managed Postgres Basic** | `shared-2x` 1 GB, vía `flyctl postgres create` | **$38,00** | [fly.io/docs/mpg](https://fly.io/docs/mpg/) |
| IPv4 dedicado | 1 dirección | **$2,00** | [fly.io/docs/about/pricing](https://fly.io/docs/about/pricing/) |
| Storage de Postgres | 10 GB × $0,28 | **$2,80** | fly.io/docs/mpg — $0,28/GB provisionado |
| Redis | Upstash, tier gratuito | **~$0** | — |
| **Subtotal infraestructura** | | **~$44,74** | |
| WhatsApp | ver §4 | ~$5,00 | Meta rate card |
| **Total actual** | | **~$50/mes** | |

**Participación de cada línea en la factura de infraestructura:**

```
Managed Postgres   $38,00  ████████████████████████████  85%
Storage            $2,80   ██                         6%
IPv4               $2,00   ██                         4%
Machine app        $1,94   █                          4%
Redis              $0,00                              0%
```

**Fly Managed Postgres no tiene tier de hobby.** $38 es el piso, no un techo.

### La alternativa descartada, para comparación

| Producto | Costo/mes | Fuente |
|---|---|---|
| Beds24, 4 cabañas + 2 conexiones de canal | **€18,25** (~USD 20) | [beds24.com/en/pricing](https://www.beds24.com/en/pricing/pricing) — base €15,50 + €0,55/unidad adicional + €0,55/conexión |

Cálculo: `15,50 + (3 × 0,55) + (2 × 0,55) = 18,25 €`

---

## 3. Plan de migración

### 3.1 Objetivo

PostgreSQL autoalojado en una Fly Machine, con los datos en un volumen persistente.

| Componente | Configuración objetivo | Costo/mes |
|---|---|---|
| Fly Machine (app) | `shared-cpu-1x` 256MB, siempre encendida | $1,94 |
| **Fly Machine (PostgreSQL)** | `shared-cpu-2x` 512MB | **$3,89** |
| Volumen de datos | 5 GB × $0,15 (volúmenes) | $0,75 |
| IPv4 dedicado | 1 dirección, solo para la app | $2,00 |
| Redis | Upstash, tier gratuito | ~$0 |
| **Subtotal infraestructura** | | **~$8,58** |
| WhatsApp | | ~$5,00 |
| **Total objetivo** | | **~$13,58/mes** |

**Ahorro: $44,74 − $8,58 = $36,16/mes de infraestructura**, o ~$36/mes sobre el total.

> Nota de catálogo: los volúmenes de Fly se cobran a **$0,15/GB/mes**, distinto del storage de Managed Postgres a $0,28/GB. Son productos distintos con listas distintas.

### 3.2 Por qué 512 MB alcanzan

Esto es lo que hace viable la migración, y conviene dejarlo escrito porque es la objeción obvia:

- **Volumen de datos.** 3 a 4 cabañas y ~30 reservas/mes. La tabla `reservations` acumula del orden de **cientos de filas al año**, no millones.
- **Índices.** El `btree_gist` de la restricción de exclusión trabaja sobre una tabla minúscula a esta escala. No es un problema de memoria.
- **Punto de vida real.** El sistema está diseñado para 3-4 cabañas. Si crece a 20+ cabañas, este cálculo deja de aplicar y hay que revisarlo.

### 3.3 Qué se gana y qué se pierde

**Se gana:** ~$36/mes. Y con ello, la justificación económica de `ADR-003` vuelve a ser sólida.

**Se pierde:**

| Capacidad que se pierde | Por qué se acepta |
|---|---|
| Alta disponibilidad | 30 reservas/mes. Una caída de la base unas horas significa perder captación, no perder Reservas: **la reserva también existe en el hilo de WhatsApp** y se puede reingresar. |
| Backups gestionados | El repositorio ya tiene `ops/backup/backup_database.sh` y `ops/backup/restore_database.sh`. Hay que probarlos, no solo tenerlos. |
| Failover automático | No hay réplica. Un incidente de disco se atiende restaurando desde backup. |
| Actualizaciones gestionadas | Las actualizaciones de PostgreSQL pasan a ser manuales, con ventana elegida. |

**El riesgo asumido, enunciado sin adornos:** durante una ventana de migración, y ante una caída no recuperable desde backup, se pierden las reservas registradas en el sistema para ese período. El mitigated es que el hilo de WhatsApp conserva el contenido de cada reserva.

---

## 4. Costo de WhatsApp (contexto)

Incluido en el total por completitud. Fuente: [Meta — WhatsApp Business Platform pricing](https://business.whatsapp.com/products/platform-pricing), tarifas de Argentina vigentes desde el 1 de octubre de 2026.

| Categoría | Tarifa A | Tarifa B |
|---|---|---|
| Marketing | $0,0618 | $0,07107 |
| Utility | $0,0260 | $0,0299 |
| Service | $0,0260 (1.000 gratis/mes/número) | $0,0260 |

Las dos tarifas están en circulación en fuentes públicas; la divergencia proviene de tablas que transcriben la tarjeta previa y la posterior al 30 de septiembre de 2026. **Confirmar en la consola de Meta antes de usar cualquiera como dato duro.**

Estimación para ~30 reservas/mes: **~$5/mes**, porque las plantillas de pre-llegada, check-in y post-estadía se cobran. El supuesto de $0 que figura en el documento de entrada es incorrecto.

Detalle completo en [`docs/domain/ESPECIFICACION_DOMINIO_V1.md`](../domain/ESPECIFICACION_DOMINIO_V1.md) §7.

---

## 5. Respeto de la Política COST GUARD

`fly.toml` contiene una política explícita que este plan **debe respetar**:

```
# ══════════════════════════════════════════════
# ⚠️  Política ANTI-DUPLICADOS / COST GUARD
# ══════════════════════════════════════════════
# - App única permitida: app = "sist-cabanas-mvp"
# - Región primaria única: primary_region = "gru"
# - Single instance (máximo 1 máquina RUNNING)
# - Antes de cualquier deploy, ejecutar:
#       export DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"
#       ./ops/deploy-check.sh
```

La existencia de esta política indica que **ya hubo deploys duplicados**. Una migración de base de datos es exactamente el tipo de operación donde eso se repite.

**Reglas que la migración debe seguir:**

1. **La app `sist-cabanas-mvp` se despliega una sola vez.** Nunca crear una app paralela "de prueba" sin antes eliminarla.
2. **Región `gru` (São Paulo) únicamente** para base y aplicación. Sin regiones secundarias durante la migración.
3. **`export DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"` y `./ops/deploy-check.sh` antes de cada deploy**, sin excepción.
4. **Una sola máquina de base corriendo a la vez.** Durante la migración, una instancia de la base vieja y una de la nueva coexistiendo temporalmente duplican ese costo. La ventana de coexistencia debe ser lo más corta posible, y la instancia vieja debe destruirse explícitamente al terminar, no quedar abandonada.
5. **Verificar `fly apps list` y `fly postgres list` antes y después** de la migración, para confirmar que no quedó nada huérfano.

> La coexistencia temporal entre la base vieja y la nueva es **técnicamente necesaria** para una migración sin pérdida de datos. El punto 4 no la prohíbe: le pone un límite de tiempo y una obligación de limpieza. Lo que no se acepta es una segunda base de datos olvidada después de la migración.

---

## 6. Checklist de verificación post-migración

Cada punto es binario. La migración no se da por buena hasta que todos pasan.

**Infraestructura**
- [ ] `fly apps list` muestra exactamente una app: `sist-cabanas-mvp`
- [ ] `fly postgres list` **no** muestra clusters: la base vieja fue destruida
- [ ] `fly volumes list` muestra el volumen nuevo montado y con la capacidad esperada
- [ ] Ambas máquinas en `gru`
- [ ] `fly machine list` no muestra máquinas detenidas huérfanas

**Datos e integridad**
- [ ] El conteo de `reservations` coincide exactamente entre la base vieja y la nueva
- [ ] La extensión `btree_gist` está instalada: `SELECT extname FROM pg_extension WHERE extname = 'btree_gist';` devuelve una fila
- [ ] La restricción de exclusión existe y sigue activa: `\d+ reservations` muestra `no_overlap_reservations`
- [ ] **Prueba funcional de anti-doble-booking:** intentar insertar dos reservas solapadas sobre la misma cabaña y fechas. La segunda debe fallar con `IntegrityError`
- [ ] La revisión registrada en la tabla `alembic_version` coincide con la última migración aplicada (`006_perf_indexes`)

**Backups** *(crítico: se está cediendo backups gestionados)*
- [ ] `ops/backup/backup_database.sh` genera un dump sin error
- [ ] `ops/backup/restore_database.sh` restaura ese dump en una base limpia **de prueba**, y el conteo de reservas coincide
- [ ] La restauración se probó **antes** de dar por buena la migración, no después
- [ ] El backup quedó **fuera** de la máquina, en almacenamiento externo. Un backup en el mismo volumen que los datos no es un backup.

**Aplicación**
- [ ] `GET /api/v1/healthz` responde `healthy` (DB y Redis conectados)
- [ ] `GET /api/v1/readyz` responde correcto
- [ ] `GET /metrics` expone las series esperadas
- [ ] La caada de reservas se ve igual en el panel admin que antes de migrar
- [ ] El feed iCal export sigue sirviendo y devuelve el mismo conjunto de eventos

**Costo**
- [ ] El panel de Fly muestra el nuevo consumo esperado (~$8,58/mes de infra)
- [ ] No quedan recursos huérfanos facturando

---

## 7. Cuándo ejecutar la migración

**No en temporada alta.** La ventana de downtime es el factor de riesgo dominante: durante la migración hay un momento en que el sistema no acepta reservas, y las reservas perdidas se recuperan del hilo de WhatsApp a mano.

| Momento | ¿Apto? | Motivo |
|---|---|---|
| Temporada baja, en la ventana de menor ocupación | **Sí** | Downtime tolerable, volumen bajo que reingresar |
| Temporada alta | **No** | Se pierde captación sin supervisión |
| **Enero** | **Nunca** | Es el pico absoluto de demanda. Ventana de downtime inviable. |

**Pendiente de decisión (6 en la lista de la especificación de dominio):** la ventana concreta. La migración necesita una fecha acordada antes de tocar nada.

---

## 8. Alternativa: no migrar

La decisión honesta es que **la migración no es obligatoria**, y hay una alternativa legítima: aceptar $38/mes, pagar el total de ~$50/mes, y reconocer que el stack propio cuesta más que Beds24.

En ese caso, `ADR-003` se sostiene por otras razones — el sistema ya existe, el control de doble-booking está en un constraint transaccional, y el chat por WhatsApp es el diferencial del producto — pero **pierde la justificación económica**, y eso debería quedar dicho en el ADR en lugar de dejarlo implícito.

Lo que **no** es una salida válida es seguir con $38/mes sin registrarlo: es el estado actual, y no está documentado en ningún lado.

---

## Referencias

- [Fly.io — Pricing](https://fly.io/pricing/)
- [Fly.io — Resource Pricing](https://fly.io/docs/about/pricing/)
- [Fly.io — Managed Postgres](https://fly.io/docs/mpg/)
- [Beds24 — Pricing](https://www.beds24.com/en/pricing/pricing)
- [Meta — WhatsApp Business Platform pricing](https://business.whatsapp.com/products/platform-pricing)
- [`docs/domain/ESPECIFICACION_DOMINIO_V1.md`](../domain/ESPECIFICACION_DOMINIO_V1.md) §7
- [`ADR-003`](../adr/003-fuente-maestra-y-control-de-sobreventa.md)
- `ops/backup/backup_database.sh`, `ops/backup/restore_database.sh`, `ops/deploy-check.sh`

---

*Los precios verificados lo fueron el 2026-09-28. Los servicios de terceros cambian sin aviso: reverificar antes de ejecutar cualquier decisión basada en estas cifras.*
