# 🔑 Guía Completa: Obtener Todos los Secretos y Valores para Fly.io

Fecha: 2025-10-28
Propósito: Lista paso a paso de CADA secreto, API key, URL y valor necesario, con instrucciones claras y directas de dónde obtener cada uno.

---

## 📋 Tabla de Contenidos Rápida

| Sección | Valores | Prioridad |
|---------|---------|-----------|
| 1. Base de Datos (PostgreSQL) | DATABASE_URL | CRÍTICA |
| 2. Cache (Redis) | REDIS_URL | CRÍTICA |
| 3. Seguridad y JWT | JWT_SECRET, ICS_SALT | CRÍTICA |
| 4. WhatsApp Business | 5 claves | CRÍTICA |
| 5. Mercado Pago | 2 claves | CRÍTICA |
| 6. Admin y CORS | 2 claves | IMPORTANTE |
| 7. Parámetros Operativos | 5 claves (opcionales) | OPCIONAL |

---

## 1️⃣ BASE DE DATOS (PostgreSQL)

### 1.1) DATABASE_URL

**¿Qué es?**
- URL de conexión a PostgreSQL con usuario, contraseña, host, puerto y base de datos.

**¿Dónde obtenerlo?**

#### Opción A: PostgreSQL Managed en Fly.io (Recomendado)
1. Ve a https://fly.io/dashboard
2. Inicia sesión con tu cuenta Fly.io
3. En la consola, ejecuta:
   ```bash
   flyctl postgres create --name sist-cabanas-db --region eze
   ```
4. Espera ~2 minutos a que se despliegue
5. Ejecuta:
   ```bash
   flyctl postgres users create db_user -a sist-cabanas-db
   flyctl postgres connect -a sist-cabanas-db
   # Una vez dentro del psql:
   CREATE DATABASE alojamientos;
   \c alojamientos
   CREATE EXTENSION btree_gist;
   \q
   ```
6. Obtén la URL con:
   ```bash
   flyctl postgres users list -a sist-cabanas-db
   # O más fácil, ejecuta:
   flyctl secrets list -a sist-cabanas-mvp 2>/dev/null | grep DATABASE_URL || echo "Aún no disponible"
   ```

**Formato esperado:**
```
postgresql+asyncpg://db_user:password@sist-cabanas-db.internal:5432/alojamientos
```

#### Opción B: PostgreSQL Externo (RDS/Neon/Supabase)
- **RDS (AWS)**:
  1. Ve a https://console.aws.amazon.com/rds
  2. Crea instancia PostgreSQL 16
  3. En "Connectivity & security" → Copia el "Endpoint"
  4. Copia el puerto (default 5432)
  5. Usa credenciales que configuraste al crear

- **Neon** (recomendado por facilidad):
  1. Ve a https://console.neon.tech
  2. Crea proyecto
  3. En "Connection string", copia la URL completa
  4. Asegura que incluya **?sslmode=require** al final

- **Supabase** (basado en Postgres):
  1. Ve a https://supabase.com/dashboard
  2. Crea proyecto
  3. En "Settings" → "Database" → Copia "Connection string" (JDBC o psycopg2)
  4. Reemplaza `[YOUR-PASSWORD]` con tu contraseña

**Validación:**
```bash
# Instala psql si no lo tienes (Homebrew en Mac o apt-get en Linux)
psql postgresql+asyncpg://db_user:password@host:5432/alojamientos -c "CREATE EXTENSION IF NOT EXISTS btree_gist; SELECT 1 as ok;"
```

---

## 2️⃣ CACHE (Redis)

### 2.1) REDIS_URL

**¿Qué es?**
- URL de conexión a Redis (servidor de caché y locks).

**¿Dónde obtenerlo?**

#### Opción A: Upstash (Recomendado - Simple y Rápido)
1. Ve a https://console.upstash.com
2. Regístrate o inicia sesión
3. Haz clic en "Create Database"
4. Selecciona región cercana a tu app (ej. "us-east-1" si usas eze de Fly)
5. Nombre: "sist-cabanas-cache" (opcional)
6. Elige plan Free (suficiente para MVP)
7. Haz clic en "Create"
8. En la página de la DB, ve a "REST API" o "Redis CLI" → Copia la URL debajo de "UPSTASH_REDIS_REST_URL"
   - Alternativa: busca en "Details" la sección "Redis URL" o "Connection String"
9. Copia la línea que empieza con `redis://`

**Formato esperado:**
```
redis://:your-password@us1-your-instance-id.upstash.io:6379/0
```

#### Opción B: Redis en Fly.io
1. En tu app de Fly, ejecuta:
   ```bash
   flyctl redis create --name sist-cabanas-redis --region eze
   ```
2. Espera ~1 minuto
3. Ejecuta:
   ```bash
   flyctl redis users list -a sist-cabanas-redis
   flyctl secrets list -a sist-cabanas-mvp | grep REDIS
   ```

**Validación:**
```bash
# Si tienes redis-cli instalado
redis-cli -u "redis://:password@host:6379/0" PING
# Esperado: PONG
```

---

## 3️⃣ SEGURIDAD Y JWT

### 3.1) JWT_SECRET

**¿Qué es?**
- Secreto para firmar y verificar tokens JWT (autenticación del Admin).

**¿Cómo obtenerlo?**
- **Opción A (Recomendado):** Genéralo con openssl:
  ```bash
  openssl rand -hex 32
  ```
  Salida ejemplo:
  ```
  a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
  ```

- **Opción B:** Usando Python:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

- **Opción C:** Usa scripts/generate_production_secrets.sh (si existe):
  ```bash
  bash scripts/generate_production_secrets.sh
  ```

**Notas:**
- Mínimo 32 caracteres (hexadecimal o alfanumérico)
- NUNCA lo compartas ni lo subas a Git (está en .gitignore)
- Guárdalo en un lugar seguro (1Password, LastPass, etc.)

### 3.2) ICS_SALT

**¿Qué es?**
- Secreto para generar tokens seguros de sincronización iCal (export de calendario).

**¿Cómo obtenerlo?**
- Ejecuta el mismo comando que JWT_SECRET:
  ```bash
  openssl rand -hex 32
  ```

**Notas:**
- Diferente del JWT_SECRET
- Usado para crear URLs de export iCal privadas

---

## 4️⃣ WHATSAPP BUSINESS CLOUD API

### 4.1) WHATSAPP_ACCESS_TOKEN

**¿Dónde obtenerlo?**

1. Ve a https://developers.facebook.com/apps
2. Inicia sesión con tu cuenta Facebook/Meta
3. Crea una app nueva (si no tienes):
   - Haz clic en "My Apps" → "Create App"
   - Selecciona "Business" como tipo
   - Nombre: "Reservas Cabañas" (o similar)
   - Email: tu@email.com
   - Haz clic en "Create App"

4. Ve a "Settings" → "Basic" → Copia el **App ID** (guardarlo, lo usarás después)

5. En el menú izquierdo, busca "WhatsApp" y haz clic en "Set Up"

6. En "Get Started with WhatsApp Business Platform":
   - Selecciona tu número de teléfono (el que usarás para la app)
   - O haz clic en "Create a test phone number"

7. Ve a "WhatsApp" → "Getting Started" (o "API Setup")

8. En "Temporary access token" → Copia el token largo (empieza con `EAABa...`)

**Formato esperado:**
```
EAABaXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Notas:**
- Este token es temporal (~1 hora). Para producción, necesitas un token permanente (pasos más adelante).
- Guardalo en un lugar seguro.

### 4.2) WHATSAPP_APP_SECRET

**¿Dónde obtenerlo?**

1. Ve a https://developers.facebook.com/apps
2. Selecciona tu app (del paso anterior)
3. Ve a "Settings" → "Basic"
4. En la sección "App Secret", haz clic en "Show"
5. Copia el valor (será una cadena de ~32 caracteres)

**Formato esperado:**
```
abc123def456ghi789jkl012mno345pqr
```

**Notas:**
- Nunca lo compartas públicamente
- Es diferente del JWT_SECRET

### 4.3) WHATSAPP_PHONE_ID

**¿Dónde obtenerlo?**

1. Ve a https://developers.facebook.com/apps
2. Selecciona tu app
3. Ve a "WhatsApp" → "Getting Started" (o "API Setup")
4. En la sección de números de teléfono, busca la columna "Phone Number ID"
5. Copia el ID numérico (ej. `116123456789012`)

**Formato esperado:**
```
116123456789012
```

**Notas:**
- Es diferente del número de teléfono real
- Lo necesitas para enviar mensajes

### 4.4) WHATSAPP_VERIFY_TOKEN

**¿Qué es?**
- Token que usas para verificar webhooks entrantes de WhatsApp.

**¿Cómo obtenerlo?**
- **Tú lo defines** (no viene de Meta). Genera uno:
  ```bash
  openssl rand -hex 16
  ```
  Salida ejemplo:
  ```
  a1b2c3d4e5f6g7h8
  ```

**Notas:**
- Guárdalo en un lugar seguro
- Lo necesitas para configurar el webhook en Meta (próximo paso)

### 4.5) WHATSAPP_APP_SECRET (ya está en 4.2, pero confirmamos aquí)

---

## 5️⃣ MERCADO PAGO

### 5.1) MERCADOPAGO_ACCESS_TOKEN

**¿Dónde obtenerlo?**

1. Ve a https://www.mercadopago.com.ar/developers (o tu país: .com.br, .com.mx, etc.)
2. Inicia sesión con tu cuenta de Mercado Pago
3. En el menú izquierdo, ve a "Credenciales"
4. Si no tienes app, haz clic en "Crear nueva aplicación"
5. Nombre: "Reservas Sistema" (o similar)
6. Tipo: "Integración web"
7. Haz clic en "Crear"
8. En la sección "Token de acceso", bajo "Credenciales de Producción", haz clic en "Mostrar"
9. Copia el token largo (empieza con `APP_USR-...`)

**Formato esperado:**
```
APP_USR-1234567890123456789012345678901234567890
```

**Notas:**
- Hay dos tipos: "Sandbox" (para testing) y "Producción" (real)
- Para staging en Fly, usa **Producción** (el real) pero en modo sandbox dentro del backend
- El token incluye la cadena "APP_USR-" al inicio

### 5.2) MERCADOPAGO_WEBHOOK_SECRET

**¿Dónde obtenerlo?**

1. Ve a https://www.mercadopago.com.ar/developers (o tu país)
2. Inicia sesión
3. Ve a "Credenciales" → Tu app
4. En la sección "Webhooks", haz clic en "Agregar webhook"
5. URL: `https://tu-dominio-fly.fly.dev/api/v1/webhooks/mercadopago` (reemplaza con tu URL real)
6. Eventos: selecciona "payment" (pagos)
7. En "Headers personalizados", Mercado Pago te dará un "Webhook Secret" (o genéralo)
8. Copia el valor

**Formato esperado:**
```
tu_secreto_webhook_mp_aqui_32_caracteres
```

**Notas:**
- Mercado Pago te lo proporciona cuando configuras el webhook
- Si no lo ves, genera uno manualmente:
  ```bash
  openssl rand -hex 32
  ```

---

## 6️⃣ ADMIN Y CORS

### 6.1) ADMIN_ALLOWED_EMAILS

**¿Qué es?**
- Lista de emails autorizados para acceder al Admin Dashboard (separados por coma).

**¿Cómo obtenerlo?**
- Define TÚ mismo quién(es) pueden ser admin. Ejemplos:
  ```
  admin@misabanas.com
  admin@misabanas.com,dueno@misabanas.com
  dueno.cabanas@gmail.com
  ```

**Notas:**
- Mínimo 1 email (el del dueño/administrador)
- Separa múltiples con comas (sin espacios)
- Debes actualizar esto en el backend si cambias

### 6.2) ALLOWED_ORIGINS

**¿Qué es?**
- Dominios permitidos para solicitudes CORS (dónde está alojado el Admin).

**¿Cómo obtenerlo?**
- Define dónde estará alojado el Admin. Ejemplos:
  ```
  https://admin.misabanas.com
  https://admin.misabanas.com,https://misabanas.com
  https://sist-cabanas-mvp.fly.dev
  ```

**Notas:**
- Para Fly.io, el default es `https://sist-cabanas-mvp.fly.dev` (si esa es tu app)
- Si usas subdominio custom (CNAME), pon esa URL
- Para local/dev: `http://localhost:3000,http://localhost:3001`
- Separa múltiples con comas (sin espacios)

---

## 7️⃣ PARÁMETROS OPERATIVOS (Opcionales - Ya tienen defaults)

### 7.1) RATE_LIMIT_ENABLED
**Valor:** `true` o `false`
**Default:** `true`
**Descripción:** Activa/desactiva rate limiting por IP

### 7.2) RATE_LIMIT_REQUESTS
**Valor:** número (ej. `100`)
**Default:** `100`
**Descripción:** Máximo de requests por ventana de tiempo

### 7.3) RATE_LIMIT_WINDOW_SECONDS
**Valor:** número (ej. `60`)
**Default:** `60`
**Descripción:** Segundos de la ventana de rate limit

### 7.4) JOB_EXPIRATION_INTERVAL_SECONDS
**Valor:** número (ej. `60`)
**Default:** `60`
**Descripción:** Intervalo en segundos para limpiar pre-reservas expiradas

### 7.5) JOB_ICAL_INTERVAL_SECONDS
**Valor:** número (ej. `300`)
**Default:** `300`
**Descripción:** Intervalo en segundos para sincronizar iCal (5 min = 300)

---

## 🎯 Checklist de Recopilación

Marca conforme obtengas cada valor:

### Críticos (Sin estos NO funciona)
- [ ] DATABASE_URL
- [ ] REDIS_URL
- [ ] JWT_SECRET
- [ ] ICS_SALT
- [ ] WHATSAPP_ACCESS_TOKEN
- [ ] WHATSAPP_APP_SECRET
- [ ] WHATSAPP_PHONE_ID
- [ ] WHATSAPP_VERIFY_TOKEN
- [ ] MERCADOPAGO_ACCESS_TOKEN
- [ ] MERCADOPAGO_WEBHOOK_SECRET

### Importantes (Necesarios para Admin)
- [ ] ADMIN_ALLOWED_EMAILS
- [ ] ALLOWED_ORIGINS

### Opcionales (Ya tienen valores por defecto)
- [ ] RATE_LIMIT_ENABLED
- [ ] RATE_LIMIT_REQUESTS
- [ ] RATE_LIMIT_WINDOW_SECONDS
- [ ] JOB_EXPIRATION_INTERVAL_SECONDS
- [ ] JOB_ICAL_INTERVAL_SECONDS

---

## 📝 Template para Copiar y Completar

Una vez que tengas todos los valores, cópialos aquí en orden:

```bash
# Conectividad
DATABASE_URL=postgresql+asyncpg://db_user:password@host:5432/alojamientos
REDIS_URL=redis://:password@host:6379/0

# Seguridad
JWT_SECRET=tu_secret_jwt_hex_32_caracteres
ICS_SALT=tu_salt_ics_hex_32_caracteres

# WhatsApp
WHATSAPP_ACCESS_TOKEN=EAABaxxxxxxxxxxxxx
WHATSAPP_APP_SECRET=abc123def456ghi789jkl012mno345pqr
WHATSAPP_PHONE_ID=116123456789012
WHATSAPP_VERIFY_TOKEN=a1b2c3d4e5f6g7h8

# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN=APP_USR-1234567890123456789012345678901234567890
MERCADOPAGO_WEBHOOK_SECRET=tu_secreto_webhook_mp_32_caracteres

# Admin
ADMIN_ALLOWED_EMAILS=admin@misabanas.com
ALLOWED_ORIGINS=https://admin.misabanas.com,https://sist-cabanas-mvp.fly.dev

# Operativos (opcionales)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
JOB_EXPIRATION_INTERVAL_SECONDS=60
JOB_ICAL_INTERVAL_SECONDS=300
```

---

## ⚙️ Próximo Paso: Cargar en env/.env.fly.staging

Una vez que tengas todos los valores:

1. Abre `env/.env.fly.staging` (o cópialo desde `env/.env.fly.staging.template`)
2. Reemplaza cada placeholder con los valores reales
3. Guarda el archivo
4. **NO lo subas a Git** (ya está en .gitignore)
5. Ejecuta:
   ```bash
   ./ops/set_fly_secrets.sh sist-cabanas-mvp env/.env.fly.staging
   ```

---

## 🚨 Seguridad: Buenas Prácticas

1. **NUNCA** hagas push de `env/.env.fly.staging` a Git (ya está en .gitignore ✓)
2. **NUNCA** compartas screenshots de la terminal con secretos visibles
3. **USA** 1Password, LastPass, o Vault para guardar copias cifradas
4. **ROTA** tokens cada 90 días (especialmente ACCESS_TOKEN de WhatsApp)
5. **DOCUMENTA** en privado (Notion, Confluence) quién cambió qué y cuándo

---

## 🆘 Troubleshooting

| Problema | Solución |
|----------|----------|
| "DATABASE_URL inválido" | Verifica que PostgreSQL esté online; prueba la URL con `psql` |
| "REDIS_URL rechazada" | Verifica credenciales de Upstash; prueba con `redis-cli` |
| "WhatsApp token expirado" | Tokens temp duran ~1h; regenera en Meta o usa token permanente |
| "Mercado Pago rechazo de firma" | Verifica que MERCADOPAGO_WEBHOOK_SECRET sea exacto; no hay espacios |
| "CORS error en Admin" | Asegura que ALLOWED_ORIGINS incluya el dominio del Admin (sin trailing /) |

---

## 📞 Referencias Rápidas

- **Fly.io CLI:** https://fly.io/docs/hands-on/install/
- **WhatsApp Business:** https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- **Mercado Pago Docs:** https://www.mercadopago.com.ar/developers/es
- **Upstash Console:** https://console.upstash.com
- **Neon PostgreSQL:** https://neon.tech/

---

## ✅ Confirmación Final

Cuando hayas completado TODOS los valores críticos y importantes:

```bash
# Verifica que el archivo .env.fly.staging está completo
cat env/.env.fly.staging | grep -E "^[A-Z_]+=" | wc -l
# Deberías ver: 12 (mínimo)

# Luego, carga los secretos en Fly
./ops/set_fly_secrets.sh sist-cabanas-mvp env/.env.fly.staging

# Por último, despliega
fly deploy
```

---

**Próximo documento:** Cuando hayas completado esta guía, ejecuta `fly deploy` y ve al `PLAN_COMPLETO_FLYIO_UX_ADMIN.md` para los siguientes pasos.
