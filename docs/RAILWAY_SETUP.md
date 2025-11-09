# Guía Express de Puesta en Marcha en Railway (Backend FastAPI + Postgres + Redis)

Esta guía te permite desplegar y probar el sistema sin integrar WhatsApp ni Mercado Pago al inicio. En ~10 minutos deberías tener la API online, con prevención de doble-booking activa.


## 1) Requisitos y decisiones

- Cuenta en Railway (free tier).
- Repositorio GitHub: `SIST_CABANAS_MVP` (este repo).
- No se requieren secrets de WhatsApp/Mercado Pago para el arranque inicial.

Notas clave del sistema:
- Anti doble-booking = combinación de:
  - Constraint en Postgres: `EXCLUDE USING gist` sobre un `daterange`.
  - Lock pesimista con Redis (SET NX EX), previo a escribir.
- Para que el constraint funcione, la DB debe tener la extensión `btree_gist`.


## 2) Crear servicios en Railway

1. Crea un nuevo Proyecto en Railway.
2. Agrega un servicio PostgreSQL (acepta los valores por defecto).
3. Agrega un servicio Redis (acepta los valores por defecto, con password habilitada).

Obtén:
- `DATABASE_URL` (cadena de conexión directa a Postgres, puerto 5432).
- `REDIS_URL` (debe incluir la contraseña; formato `redis://:password@host:port/0`).


## 3) Habilitar extensión `btree_gist` en Postgres

En la consola SQL de Railway (o conectando con un cliente), ejecuta:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

Si ya existe, no falla. Esto habilita el constraint anti solapamiento que usa el sistema.


## 4) Conectar el repo y crear el servicio Web

1. En Railway → New → Deploy from GitHub Repo → selecciona `SIST_CABANAS_MVP`.
2. Crea un "Web Service" desde el repo:
   - Subdirectorio de build: `backend`
   - Tipo de build: Dockerfile (usa `backend/Dockerfile` del repo)
   - No sobrescribas el comando: el contenedor ya arranca con `start-fly.sh` (genérico) que:
     - Valida variables.
     - Espera Postgres/Redis.
     - Ejecuta `alembic upgrade head` (migraciones).
     - Lanza Gunicorn+Uvicorn.
3. Health Check:
   - Railway define `$PORT` automáticamente; el contenedor lo respeta.
   - Endpoint recomendado: `/api/v1/healthz`.


## 5) Variables de entorno (mínimas para arrancar)

Configura en Railway → Service → Variables (o a nivel de proyecto):

Requeridas (núcleo):
- `DATABASE_URL` → la de Postgres (puerto 5432). Ejemplo: `postgresql+asyncpg://user:pass@host:5432/db`.
- `REDIS_URL` → tu instancia de Redis con password.
- `JWT_SECRET` → un secreto aleatorio (32+ chars). Ejemplo para generar:
  ```bash
  openssl rand -base64 32
  ```
- `ADMIN_ALLOWED_EMAILS` → tu correo (para acceso admin), coma-separado si hay varios.
- `BASE_URL` → la URL pública que te dará Railway, ej: `https://<tu-app>.up.railway.app`.
- `DOMAIN` → dominio raíz (si usas custom domain; si no, puedes poner el host de Railway sin https).
- `INTEGRATIONS_REQUIRED` → `false` (para permitir arrancar sin WhatsApp/Mercado Pago).
- `DB_SSL` → `true` si la cadena de Railway exige SSL (muchas veces lo hace). Si tu DSN ya funciona sin SSL explícito, puedes omitirla. El backend soporta SSL opcional y lo activa cuando `DB_SSL=true`.

Opcionales (integraciones, puedes dejarlas vacías al inicio):
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_APP_SECRET`
- `WHATSAPP_PHONE_ID`
- `WHATSAPP_VERIFY_TOKEN`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_WEBHOOK_SECRET`


## 6) Despliegue y verificación

1. Ejecuta Deploy en el Web Service.
2. Observa logs. Debes ver:
   - "✅ PostgreSQL is ready" y "✅ Redis is ready" (o aviso si es Upstash externo).
   - "🔄 Running database migrations..." → "✅ Database migrations completed".
   - "🚀 Starting Gunicorn + Uvicorn workers...".
3. Abre en el navegador:
   - Health: `GET /api/v1/healthz` → debe mostrar `status: ok`.
   - Docs: `GET /docs` → Swagger UI de la API.


## 7) Pruebas funcionales mínimas (sin integraciones)

- Flujos básicos de reserva (vía endpoints REST en `/docs`).
- Anti-double-booking:
  - Intenta crear dos reservas con fechas solapadas para el mismo alojamiento → la segunda debe fallar con `IntegrityError` (mapeada a 409/422 según la capa).
  - Verifica que los locks Redis funcionan (evitan carreras).


## 8) Cobertura en Pull Requests (CI)

- Cuando abras o actualices un PR en GitHub, el workflow de tests publicará un comentario "sticky" con la cobertura.
- También verás el porcentaje total en el Job Summary del workflow.


## 9) Activar WhatsApp y Mercado Pago (cuando tu amigo lo use)

Cuando quieras integrarlas:
1. Cambia `INTEGRATIONS_REQUIRED` a `true` (o elimínala para que sea true por defecto).
2. Carga las variables:
   - WhatsApp: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_PHONE_ID`, `WHATSAPP_VERIFY_TOKEN`.
   - Mercado Pago: `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET`.
3. Reinicia/Deploy y prueba los webhooks. Importante: firmar y validar HMAC (ya implementado).


## 10) Solución de problemas (rápida)

- Falla en migraciones:
  - Verifica `DATABASE_URL` (usuario/clave/host/puerto/db) y permisos.
  - Asegúrate de haber creado `btree_gist`.
  - Railway a veces requiere SSL: pon `DB_SSL=true`.
- Health en rojo:
  - Postgres/Redis no accesibles (revisa URLs/puertos/password).
  - Variables obligatorias ausentes.
- Doble-booking no bloquea:
  - Confirma que estás usando la misma propiedad y fechas solapadas.
  - Verifica que la migración creó el constraint `EXCLUDE USING gist`.
  - Revisa logs por `IntegrityError`.


## 11) (Opcional) Evolución futura

- Si el free tier de Railway se queda corto:
  - Migrar DB a Supabase o Neon; mantener app en Railway o Render; usar Redis en Upstash (serverless).
  - El backend ya soporta `DB_SSL=true` y migraciones directas a 5432.


## 12) Checklist final

- [ ] Railway Project creado con Postgres y Redis.
- [ ] `CREATE EXTENSION IF NOT EXISTS btree_gist;` ejecutado.
- [ ] Web Service creado desde GitHub con `backend/Dockerfile`.
- [ ] Variables mínimas cargadas (incluye `INTEGRATIONS_REQUIRED=false`).
- [ ] Deploy ok; `/api/v1/healthz` en verde.
- [ ] Anti-double-booking validado con inserción solapada.
- [ ] PR abierto/actualizado; comentario de cobertura visible.

---

Si necesitas que automatice alguna verificación (anti-overlap, locks, etc.), avísame cuando el servicio esté online y continúo con los checks remotos y documentación del entorno final.
