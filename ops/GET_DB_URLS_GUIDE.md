# 🚀 Obtener DATABASE_URL y REDIS_URL (10 minutos)

**Última actualización:** 31 de octubre 2025

---

## 🗄️ Paso 1: PostgreSQL con Neon (2 minutos)

### Opción A: Neon.tech (RECOMENDADO)

1. **Ir a:** https://neon.tech
2. **Sign up** con GitHub o email
3. **Create Project:**
   - Name: `sist-cabanas-staging`
   - Region: `AWS / South America (São Paulo)` (más cercano) o `US East (Ohio)`
   - Postgres version: 16 (default)
4. **Habilitar extensión btree_gist:**
   - Ir a SQL Editor
   - Ejecutar: `CREATE EXTENSION IF NOT EXISTS btree_gist;`
   - Resultado esperado: `CREATE EXTENSION` o `extension "btree_gist" already exists`
5. **Copiar DATABASE_URL:**
   - Dashboard → Connection Details → Connection string
   - Formato: `postgresql://user:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require`
   - **IMPORTANTE:** Cambiar `?sslmode=require` a `?sslmode=require` (Neon lo incluye)

**Free Tier:** 10 GB storage, 100 horas compute/mes — suficiente para staging.

### Opción B: Supabase (Alternativa)

1. **Ir a:** https://supabase.com
2. **New Project:**
   - Name: `sist-cabanas-staging`
   - Database Password: (genera seguro)
   - Region: `South America (São Paulo)`
3. **Habilitar btree_gist:**
   - SQL Editor → New query
   - Ejecutar: `CREATE EXTENSION IF NOT EXISTS btree_gist;`
4. **Copiar DATABASE_URL:**
   - Settings → Database → Connection string (URI)
   - Formato: `postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres`

---

## 🔴 Paso 2: Redis con Upstash (5 minutos)

1. **Ir a:** https://upstash.com
2. **Sign up** con GitHub o email
3. **Create Database:**
   - Name: `sist-cabanas-staging`
   - Type: `Regional`
   - Region: `South America (São Paulo)` o `US East (Virginia)`
   - TLS: `Enabled` (default)
   - Eviction: `No eviction` (default)
4. **Copiar REDIS_URL:**
   - Database → Details → Connection
   - Click en `@upstash/redis` tab
   - Copiar `UPSTASH_REDIS_REST_URL` **NO**, necesitas el formato Redis URI:
   - Ir a `Redis` tab → copiar `redis://...` o `rediss://...`
   - Formato correcto: `rediss://default:[PASSWORD]@xxx-xxx.upstash.io:6379`

**Free Tier:** 10,000 commands/day — suficiente para staging y testing.

---

## ✅ Validar URLs antes de usar

### DATABASE_URL
```bash
# Probar conexión (requiere psql instalado)
psql "postgresql://user:pass@host/db?sslmode=require" -c "SELECT version();"

# Debería retornar: PostgreSQL 16.x ...
```

### REDIS_URL
```bash
# Probar conexión (requiere redis-cli instalado)
redis-cli -u "rediss://default:pass@host:6379" PING

# Debería retornar: PONG
```

---

## 🚀 Ejecutar Deploy

Una vez tengas ambas URLs:

```bash
cd /home/eevan/ProyectosIA/SIST_CABAÑAS
./ops/fast-track-deploy.sh
```

El script te pedirá:
1. `DATABASE_URL` → pegar y Enter
2. `REDIS_URL` → pegar y Enter

Luego ejecutará automáticamente:
- ✅ Validación de formato
- ✅ Carga de 14 secrets en Fly
- ✅ Deploy a Fly.io
- ✅ Health check
- ✅ Metrics check

**Tiempo total:** ~5-7 minutos (después de obtener URLs).

---

## 🔧 Troubleshooting

### Error: "extension btree_gist does not exist"
```sql
-- Ejecutar en SQL Editor de Neon/Supabase:
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

### Error: "could not connect to server"
- Verificar que DATABASE_URL tiene `?sslmode=require` al final
- Verificar que no hay espacios ni caracteres especiales sin escapar

### Error: Redis AUTH failed
- Verificar que REDIS_URL comienza con `rediss://` (con doble 's' para TLS)
- Verificar que el password no tiene caracteres especiales sin URL-encode

---

## 📋 Checklist

- [ ] Cuenta Neon creada
- [ ] Proyecto `sist-cabanas-staging` en Neon
- [ ] Extensión `btree_gist` habilitada
- [ ] DATABASE_URL copiada (postgresql://...)
- [ ] Cuenta Upstash creada
- [ ] Database Redis `sist-cabanas-staging` en Upstash
- [ ] REDIS_URL copiada (rediss://...)
- [ ] URLs validadas con psql/redis-cli (opcional)
- [ ] Script `./ops/fast-track-deploy.sh` ejecutado
- [ ] Health check OK (200)

**Próximo paso:** Ejecutar smoke & benchmark.
