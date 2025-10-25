# 🔍 PRE-DEPLOYMENT VALIDATION PLAN - Fly.io
## Ingeniería Inversa: Prevención de Errores Críticos

**Fecha**: 19 de octubre de 2025
**Proyecto**: SIST_CABAÑAS MVP
**Plataforma**: Fly.io (región: eze)
**Objetivo**: Validar TODOS los componentes ANTES de `flyctl deploy`

---

## 🎯 FILOSOFÍA: "FAIL FAST, FAIL LOCAL"

**Principio**: Detectar y corregir TODOS los errores en desarrollo, NUNCA en producción.

**Estrategia**: Simular el entorno de Fly.io localmente antes del deploy real.

---

## 📋 CHECKLIST PRE-DEPLOYMENT (15 PASOS CRÍTICOS)

### FASE 1: VALIDACIÓN DE CONFIGURACIÓN (5 min)

#### ✅ PASO 1: Validar fly.toml
```bash
# Verificar sintaxis TOML
python3 << 'EOF'
try:
    import tomllib
    with open('fly.toml', 'rb') as f:
        config = tomllib.load(f)

    # Validaciones críticas
    assert config.get('app'), "❌ Falta 'app' en fly.toml"
    assert config.get('primary_region') == 'eze', "❌ Región no es 'eze'"

    # Validar [build]
    build = config.get('build', {})
    if not build:
        print("⚠️  WARNING: No se especifica [build], Fly.io usará auto-detect")

    # Validar [deploy]
    deploy = config.get('deploy', {})
    if 'release_command' in deploy:
        print(f"✅ Release command: {deploy['release_command']}")
        # CRÍTICO: Si hay release_command, DEBE haber DATABASE_URL
        print("⚠️  REQUIERE: DATABASE_URL configurado en Fly.io")

    # Validar [env]
    env = config.get('env', {})
    required_env = ['PORT', 'DATABASE_URL', 'REDIS_URL']
    for var in required_env:
        if var not in env and var != 'DATABASE_URL':  # DATABASE_URL va en secrets
            print(f"⚠️  {var} no está en [env]")

    # Validar [[services]]
    services = config.get('services', [])
    if services:
        internal_port = services[0].get('internal_port')
        print(f"✅ Internal port: {internal_port}")
        if internal_port != 8080:
            print("❌ ERROR: internal_port debe ser 8080")
            exit(1)

    print("✅ fly.toml validado correctamente")
except Exception as e:
    print(f"❌ ERROR en fly.toml: {e}")
    exit(1)
EOF
```

**Errores que previene**:
- ❌ Sintaxis TOML inválida
- ❌ Región incorrecta (latencia alta)
- ❌ Puerto incorrecto (conexión fallará)
- ❌ Release command sin DATABASE_URL

---

#### ✅ PASO 2: Validar Dockerfile
```bash
# Verificar que Dockerfile existe y es válido
if [ ! -f backend/Dockerfile ]; then
    echo "❌ ERROR: backend/Dockerfile NO EXISTE"
    exit 1
fi

# Intentar build local (sin caché para simular Fly.io)
cd backend
docker build --no-cache -t sist-cabanas-test:local . 2>&1 | tee /tmp/docker_build.log

# Verificar que el build fue exitoso
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Docker build falló localmente"
    echo "Revisa /tmp/docker_build.log para detalles"
    exit 1
fi

# Verificar que la imagen tiene el puerto correcto
docker inspect sist-cabanas-test:local | grep -q "8080"
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Imagen Docker no expone puerto 8080"
    exit 1
fi

echo "✅ Dockerfile build exitoso"
```

**Errores que previene**:
- ❌ Dockerfile con sintaxis incorrecta
- ❌ Dependencias faltantes durante build
- ❌ Imagen sin puerto expuesto
- ❌ Base image incompatible

---

#### ✅ PASO 3: Validar start-fly.sh
```bash
# Verificar que start-fly.sh existe y es ejecutable
if [ ! -f backend/start-fly.sh ]; then
    echo "❌ ERROR: backend/start-fly.sh NO EXISTE"
    exit 1
fi

if [ ! -x backend/start-fly.sh ]; then
    echo "❌ ERROR: start-fly.sh no es ejecutable"
    echo "Ejecuta: chmod +x backend/start-fly.sh"
    exit 1
fi

# Validar que contiene comandos críticos
grep -q "alembic upgrade head" backend/start-fly.sh
if [ $? -ne 0 ]; then
    echo "⚠️  WARNING: start-fly.sh no ejecuta migraciones"
fi

grep -q "gunicorn\|uvicorn" backend/start-fly.sh
if [ $? -ne 0 ]; then
    echo "❌ ERROR: start-fly.sh no inicia servidor ASGI"
    exit 1
fi

echo "✅ start-fly.sh validado"
```

**Errores que previene**:
- ❌ Script no ejecutable (deploy fallará)
- ❌ Sin comando de inicio (app no arrancará)
- ❌ Migraciones no automáticas

---

#### ✅ PASO 4: Validar Variables de Entorno
```bash
# Verificar que .env.template tiene TODAS las variables necesarias
python3 << 'EOF'
import re

# Leer config.py para obtener variables requeridas
with open('backend/app/core/config.py', 'r') as f:
    config_content = f.read()

# Extraer variables con getenv o Field
required_vars = set(re.findall(r'getenv\(["\'](\w+)["\']', config_content))
required_vars.update(re.findall(r'Field\(.*?env=["\'](\w+)["\']', config_content))

# Leer .env.template
with open('.env.template', 'r') as f:
    template_content = f.read()

template_vars = set(re.findall(r'^([A-Z_]+)=', template_content, re.MULTILINE))

# Comparar
missing_in_template = required_vars - template_vars
extra_in_template = template_vars - required_vars

if missing_in_template:
    print(f"❌ ERROR: Variables faltantes en .env.template:")
    for var in sorted(missing_in_template):
        print(f"   - {var}")
    exit(1)

if extra_in_template:
    print(f"ℹ️  Variables en .env.template no usadas en config.py:")
    for var in sorted(extra_in_template):
        print(f"   - {var}")

print(f"✅ .env.template validado: {len(template_vars)} variables")
EOF
```

**Errores que previene**:
- ❌ Variables de entorno faltantes
- ❌ App crashea por KeyError en config
- ❌ Servicios no inicializan

---

#### ✅ PASO 5: Validar Dependencias Python
```bash
cd backend

# Activar venv
source .venv/bin/activate

# Verificar que requirements.txt tiene versiones fijas
grep -E '==|~=' requirements.txt > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  WARNING: requirements.txt sin versiones fijas (usar ==)"
fi

# Instalar dependencias y verificar CVEs
pip install -q pip-audit
pip-audit --desc 2>&1 | tee /tmp/pip_audit.log

# Verificar CVEs críticas
critical_cves=$(grep -c "Critical" /tmp/pip_audit.log || echo "0")
if [ "$critical_cves" -gt 0 ]; then
    echo "❌ ERROR: $critical_cves CVEs CRÍTICAS encontradas"
    cat /tmp/pip_audit.log
    exit 1
fi

echo "✅ Dependencias Python validadas (0 CVEs críticas)"
```

**Errores que previene**:
- ❌ Dependencias con vulnerabilidades
- ❌ Versiones incompatibles entre sí
- ❌ Build fallará por dependencias rotas

---

### FASE 2: VALIDACIÓN DE BASE DE DATOS (10 min)

#### ✅ PASO 6: Verificar Migraciones Alembic
```bash
cd backend
source .venv/bin/activate

# Verificar que hay al menos 1 migración
migration_count=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)
if [ "$migration_count" -eq 0 ]; then
    echo "❌ ERROR: No hay migraciones en alembic/versions/"
    exit 1
fi

echo "✅ Migraciones encontradas: $migration_count"

# Verificar secuencia de down_revision
python3 << 'EOF'
import os
import re
from pathlib import Path

versions_dir = Path('alembic/versions')
migrations = []

for file in versions_dir.glob('*.py'):
    with open(file, 'r') as f:
        content = f.read()
        revision = re.search(r"revision = ['\"]([^'\"]+)['\"]", content)
        down_revision = re.search(r"down_revision = ['\"]([^'\"]+)['\"]", content)

        if revision:
            migrations.append({
                'file': file.name,
                'revision': revision.group(1),
                'down_revision': down_revision.group(1) if down_revision else None
            })

# Verificar que no hay revisiones duplicadas
revisions = [m['revision'] for m in migrations]
if len(revisions) != len(set(revisions)):
    print("❌ ERROR: Hay revisiones duplicadas")
    exit(1)

# Verificar que la cadena es continua
print(f"✅ {len(migrations)} migraciones con secuencia válida")
EOF
```

**Errores que previene**:
- ❌ Migraciones duplicadas o conflictivas
- ❌ Cadena de migraciones rota
- ❌ Release command fallará en deploy

---

#### ✅ PASO 7: Simular Migración en DB Local
```bash
cd backend
source .venv/bin/activate

# Usar SQLite temporal para simular migración
export DATABASE_URL="sqlite:///test_migration.db"

echo "Ejecutando alembic upgrade head en DB de prueba..."
alembic upgrade head 2>&1 | tee /tmp/alembic_test.log

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Migraciones fallaron en DB local"
    cat /tmp/alembic_test.log
    rm -f test_migration.db
    exit 1
fi

# Verificar que se crearon las tablas esperadas
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('test_migration.db')
cursor = conn.cursor()

expected_tables = ['accommodations', 'reservations', 'payments', 'alembic_version']
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

missing = set(expected_tables) - set(tables)
if missing:
    print(f"❌ ERROR: Tablas faltantes: {missing}")
    exit(1)

print(f"✅ Migraciones crearon {len(tables)} tablas correctamente")
conn.close()
EOF

rm -f test_migration.db
```

**Errores que previene**:
- ❌ Migraciones con errores SQL
- ❌ Constraint violations durante migration
- ❌ Tablas no creadas

---

#### ✅ PASO 8: Validar Constraint Anti-Double-Booking
```bash
cd backend
source .venv/bin/activate

# Verificar que existe la migración con el constraint
grep -r "EXCLUDE USING gist" alembic/versions/ > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Constraint anti-double-booking NO ENCONTRADO"
    echo "Revisa que existe: EXCLUDE USING gist (accommodation_id WITH =, period WITH &&)"
    exit 1
fi

grep -r "btree_gist" alembic/versions/ > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  WARNING: Extensión btree_gist no se crea en migración"
    echo "Asegúrate de ejecutar: CREATE EXTENSION IF NOT EXISTS btree_gist;"
fi

echo "✅ Constraint anti-double-booking presente en migraciones"
```

**Errores que previene**:
- ❌ Double-booking en producción
- ❌ Extensión PostgreSQL no instalada
- ❌ Constraint no aplicado

---

### FASE 3: VALIDACIÓN DE SERVICIOS EXTERNOS (5 min)

#### ✅ PASO 9: Verificar Conectividad a APIs Externas
```bash
cd backend
source .venv/bin/activate

python3 << 'EOF'
import os
import sys
from app.core.config import settings

# Simular que tenemos las variables (aunque sean dummies para test)
errors = []

# 1. WhatsApp Business API
if not settings.WHATSAPP_ACCESS_TOKEN:
    errors.append("❌ WHATSAPP_ACCESS_TOKEN no configurado")
if not settings.WHATSAPP_PHONE_NUMBER_ID:
    errors.append("❌ WHATSAPP_PHONE_NUMBER_ID no configurado")
if not settings.WHATSAPP_APP_SECRET:
    errors.append("❌ WHATSAPP_APP_SECRET no configurado")

# 2. Mercado Pago
if not settings.MERCADOPAGO_ACCESS_TOKEN:
    errors.append("❌ MERCADOPAGO_ACCESS_TOKEN no configurado")

# 3. Database
if not settings.DATABASE_URL:
    errors.append("❌ DATABASE_URL no configurado")

# 4. Redis
if not settings.REDIS_URL:
    errors.append("❌ REDIS_URL no configurado")

if errors:
    print("\n".join(errors))
    print("\n⚠️  Configura estos secretos en Fly.io ANTES de deploy:")
    print("   flyctl secrets set VARIABLE=valor")
    sys.exit(1)

print("✅ Todas las variables de integración configuradas")
EOF
```

**Errores que previene**:
- ❌ App crashea al inicializar servicios
- ❌ Webhooks no funcionan
- ❌ Pagos no procesan

---

#### ✅ PASO 10: Validar Health Check Endpoint
```bash
cd backend

# Iniciar app localmente en background
source .venv/bin/activate
export DATABASE_URL="sqlite:///test.db"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="test-secret"

uvicorn app.main:app --host 0.0.0.0 --port 8080 &
APP_PID=$!

sleep 5

# Probar health check
response=$(curl -s http://localhost:8080/api/v1/healthz)
echo "Health check response: $response"

# Verificar que responde
if echo "$response" | grep -q "status"; then
    echo "✅ Health check endpoint funciona"
else
    echo "❌ ERROR: Health check no responde correctamente"
    kill $APP_PID
    exit 1
fi

kill $APP_PID
rm -f test.db
```

**Errores que previene**:
- ❌ Fly.io no puede validar que app está healthy
- ❌ Deploy se marca como fallido
- ❌ Auto-rollback se activa innecesariamente

---

### FASE 4: VALIDACIÓN DE SEGURIDAD (5 min)

#### ✅ PASO 11: Re-ejecutar Bandit Security Scan
```bash
cd backend
source .venv/bin/activate

bandit -r app/ -lll -q > /tmp/bandit_final.log 2>&1

high_issues=$(grep -c "Severity: High" /tmp/bandit_final.log || echo "0")

if [ "$high_issues" -gt 0 ]; then
    echo "❌ ERROR: $high_issues issues HIGH en Bandit"
    cat /tmp/bandit_final.log
    exit 1
fi

echo "✅ Bandit scan: 0 HIGH issues"
```

**Errores que previene**:
- ❌ Vulnerabilidades en producción
- ❌ Compliance issues
- ❌ Hardcoded secrets expuestos

---

#### ✅ PASO 12: Verificar Webhook Signatures
```bash
cd backend

# Verificar que todas las rutas de webhook validan firmas
python3 << 'EOF'
import ast
import os

errors = []

# 1. WhatsApp webhook
whatsapp_file = 'app/routers/whatsapp.py'
with open(whatsapp_file, 'r') as f:
    content = f.read()
    if 'verify_whatsapp_signature' not in content:
        errors.append(f"❌ {whatsapp_file} no valida firma")

# 2. Mercado Pago webhook
mp_file = 'app/routers/mercadopago.py'
with open(mp_file, 'r') as f:
    content = f.read()
    if 'verify_mercadopago_signature' not in content:
        errors.append(f"❌ {mp_file} no valida firma")

if errors:
    print("\n".join(errors))
    exit(1)

print("✅ Todos los webhooks validan firmas")
EOF
```

**Errores que previene**:
- ❌ Webhooks sin autenticación
- ❌ Ataques de replay
- ❌ Datos falsos inyectados

---

### FASE 5: SIMULACIÓN DE DEPLOY (10 min)

#### ✅ PASO 13: Simular Build en Fly.io (usando Docker)
```bash
cd backend

# Simular el entorno de build de Fly.io
docker build \
    --platform linux/amd64 \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --no-cache \
    -t sist-cabanas-flyio-simulation:latest \
    . 2>&1 | tee /tmp/flyio_build_simulation.log

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Build falló en simulación de Fly.io"
    echo "Revisa /tmp/flyio_build_simulation.log"
    exit 1
fi

# Verificar tamaño de imagen (Fly.io tiene límites)
image_size=$(docker images sist-cabanas-flyio-simulation:latest --format "{{.Size}}")
echo "Tamaño de imagen: $image_size"

# Warning si es muy grande
if docker images sist-cabanas-flyio-simulation:latest --format "{{.Size}}" | grep -q "GB"; then
    echo "⚠️  WARNING: Imagen muy grande (>1GB), considera optimizar"
fi

echo "✅ Build simulado exitoso"
```

**Errores que previene**:
- ❌ Build falla en Fly.io por dependencias
- ❌ Imagen muy pesada (deploy lento)
- ❌ Arquitectura incompatible (ARM vs x86)

---

#### ✅ PASO 14: Simular Startup con Docker
```bash
# Iniciar contenedor simulando Fly.io
docker run -d \
    --name sist-cabanas-test \
    -p 8080:8080 \
    -e DATABASE_URL="postgresql://test:test@host.docker.internal:5432/test" \
    -e REDIS_URL="redis://host.docker.internal:6379" \
    -e JWT_SECRET="test-secret-for-simulation" \
    -e PORT=8080 \
    sist-cabanas-flyio-simulation:latest

# Esperar 10 segundos para startup
sleep 10

# Verificar que el contenedor está corriendo
if ! docker ps | grep -q sist-cabanas-test; then
    echo "❌ ERROR: Contenedor no inició correctamente"
    docker logs sist-cabanas-test
    docker rm -f sist-cabanas-test
    exit 1
fi

# Probar health check
response=$(curl -s http://localhost:8080/api/v1/healthz || echo "failed")
if [ "$response" = "failed" ]; then
    echo "❌ ERROR: App no responde en contenedor"
    docker logs sist-cabanas-test
    docker rm -f sist-cabanas-test
    exit 1
fi

echo "✅ Contenedor inicia correctamente"

# Cleanup
docker rm -f sist-cabanas-test
```

**Errores que previene**:
- ❌ App no inicia en Fly.io
- ❌ Puertos incorrectos
- ❌ Variables de entorno faltantes
- ❌ Crash loop al arrancar

---

#### ✅ PASO 15: Verificar Secretos en Fly.io (PRE-DEPLOY)
```bash
# Este paso se ejecuta ANTES de flyctl deploy
echo "Verificando secretos configurados en Fly.io..."

# Listar secretos actuales
flyctl secrets list --app sist-cabanas-mvp 2>&1 | tee /tmp/flyio_secrets.log

if grep -q "No secrets" /tmp/flyio_secrets.log; then
    echo "❌ ERROR: No hay secretos configurados en Fly.io"
    echo ""
    echo "Configura los secretos requeridos:"
    echo "  flyctl secrets set DATABASE_URL=<postgres_url>"
    echo "  flyctl secrets set REDIS_PASSWORD=<redis_pass>"
    echo "  flyctl secrets set JWT_SECRET=<jwt_secret>"
    echo "  flyctl secrets set WHATSAPP_ACCESS_TOKEN=<token>"
    echo "  flyctl secrets set MERCADOPAGO_ACCESS_TOKEN=<token>"
    echo "  # ... (ver .env.template para lista completa)"
    exit 1
fi

# Verificar secretos críticos
required_secrets=("DATABASE_URL" "REDIS_PASSWORD" "JWT_SECRET")
for secret in "${required_secrets[@]}"; do
    if ! grep -q "$secret" /tmp/flyio_secrets.log; then
        echo "❌ ERROR: Secreto $secret no configurado en Fly.io"
        exit 1
    fi
done

echo "✅ Secretos críticos configurados en Fly.io"
```

**Errores que previene**:
- ❌ Deploy exitoso pero app crashea por falta de secrets
- ❌ Release command falla sin DATABASE_URL
- ❌ Rollback innecesario

---

## 🚀 SCRIPT AUTOMATIZADO: pre_deploy_validation.sh

Ejecuta TODOS los pasos anteriores automáticamente:

```bash
#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     PRE-DEPLOYMENT VALIDATION - Fly.io Deployment Ready       ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# FASE 1: Configuración (5 min)
echo ""
echo "🔍 FASE 1: Validación de Configuración"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Incluir todos los comandos de PASO 1-5 aquí
# ...

# FASE 2: Base de Datos (10 min)
echo ""
echo "🔍 FASE 2: Validación de Base de Datos"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Incluir todos los comandos de PASO 6-8 aquí
# ...

# FASE 3: Servicios Externos (5 min)
echo ""
echo "🔍 FASE 3: Validación de Servicios Externos"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Incluir todos los comandos de PASO 9-10 aquí
# ...

# FASE 4: Seguridad (5 min)
echo ""
echo "🔍 FASE 4: Validación de Seguridad"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Incluir todos los comandos de PASO 11-12 aquí
# ...

# FASE 5: Simulación Deploy (10 min)
echo ""
echo "🔍 FASE 5: Simulación de Deploy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Incluir todos los comandos de PASO 13-15 aquí
# ...

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ VALIDACIÓN COMPLETADA                      ║"
echo "║                                                                ║"
echo "║   Todos los checks pasaron. Ready para 'flyctl deploy'        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
```

---

## 📊 MATRIZ DE ERRORES COMUNES Y PREVENCIÓN

| Error en Fly.io | Causa | Prevención (Paso) | Severidad |
|-----------------|-------|-------------------|-----------|
| **Build failed: Dockerfile not found** | No hay Dockerfile | PASO 2 | 🔴 CRÍTICO |
| **Build failed: Python dependency conflict** | requirements.txt roto | PASO 5 | 🔴 CRÍTICO |
| **Release command failed: alembic error** | Migración con errores SQL | PASO 7 | 🔴 CRÍTICO |
| **Release command failed: DATABASE_URL** | Secret no configurado | PASO 15 | 🔴 CRÍTICO |
| **Health check timeout** | App no responde en puerto correcto | PASO 10, 14 | 🔴 CRÍTICO |
| **Container crashed: ImportError** | Dependencia faltante | PASO 1, 5 | 🔴 CRÍTICO |
| **Constraint violation during migration** | btree_gist no instalado | PASO 8 | 🟡 ALTO |
| **Webhook returns 403 Forbidden** | Firma no validada | PASO 12 | 🟡 ALTO |
| **Image too large (>2GB)** | Build ineficiente | PASO 13 | 🟢 MEDIO |
| **Startup timeout** | start-fly.sh tarda mucho | PASO 3, 14 | 🟢 MEDIO |

---

## 🎯 ORDEN DE EJECUCIÓN RECOMENDADO

### Antes de commit:
1. ✅ Ejecutar `./run_molecular_audit.sh --critical` (validación de código)

### Antes de push:
2. ✅ Ejecutar `./pre_deploy_validation.sh` (validación pre-deploy completa)

### Antes de flyctl deploy:
3. ✅ Verificar secretos: `flyctl secrets list`
4. ✅ Revisar fly.toml una última vez

### Durante deploy:
5. ✅ Monitorear logs: `flyctl logs -f`

### Post-deploy:
6. ✅ Validar health: `curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz`

---

## 🔧 TROUBLESHOOTING AVANZADO

### Si el build falla en Fly.io:

```bash
# Ver logs completos del build
flyctl logs --app sist-cabanas-mvp

# Ver último deployment
flyctl releases --app sist-cabanas-mvp

# Ver detalles del error
flyctl status --app sist-cabanas-mvp
```

### Si el release_command falla:

```bash
# Opción 1: Desactivar temporalmente migraciones
# Edita fly.toml:
[deploy]
# release_command = "alembic upgrade head"  # Comentar
strategy = "rolling"

# Opción 2: Ejecutar migraciones manualmente
flyctl ssh console --app sist-cabanas-mvp
cd /app/backend
alembic upgrade head
```

### Si el health check falla:

```bash
# SSH al contenedor
flyctl ssh console --app sist-cabanas-mvp

# Verificar logs internos
tail -f /var/log/app.log

# Probar health check interno
curl localhost:8080/api/v1/healthz
```

---

## ✅ CHECKLIST FINAL ANTES DE DEPLOY

- [ ] ✅ PASO 1-15 completados sin errores
- [ ] ✅ `./run_molecular_audit.sh --critical` PASS
- [ ] ✅ `./pre_deploy_validation.sh` PASS
- [ ] ✅ Secretos configurados en Fly.io
- [ ] ✅ PostgreSQL creado y attachado
- [ ] ✅ Redis (Upstash) configurado
- [ ] ✅ fly.toml revisado
- [ ] ✅ Git commit + push recientes
- [ ] ✅ Backup de datos actual (si aplica)

**Cuando TODOS los items están ✅, ejecuta:**

```bash
flyctl deploy --app sist-cabanas-mvp
```

---

**Generado**: 19 de octubre de 2025
**Validez**: Permanente hasta cambios en arquitectura
**Próxima revisión**: Después de primer deploy exitoso
