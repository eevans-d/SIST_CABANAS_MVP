# 🔬 PLAN MAESTRO DE AUDITORÍA MOLECULAR - SIST_CABAÑAS MVP

**Objetivo**: Detectar y remediar TODOS los errores, inconsistencias y problemas antes de deployment a producción.

**Enfoque**: Modular, sistemático, con criterios cuantificables.

**Tiempo Estimado Total**: 4-6 horas

**Fecha**: Octubre 18, 2025

---

## 📋 ÍNDICE DE MÓDULOS

| # | Módulo | Prioridad | Tiempo | Estado |
|---|--------|-----------|--------|--------|
| 1 | [Análisis Estático - Código Backend](#módulo-1-análisis-estático---código-backend) | 🔴 CRÍTICO | 45 min | ⏳ PENDING |
| 2 | [Análisis Estático - Código Frontend](#módulo-2-análisis-estático---código-frontend) | 🟡 ALTO | 30 min | ⏳ PENDING |
| 3 | [Análisis de Configuración](#módulo-3-análisis-de-configuración) | 🔴 CRÍTICO | 30 min | ⏳ PENDING |
| 4 | [Análisis de Base de Datos](#módulo-4-análisis-de-base-de-datos) | 🔴 CRÍTICO | 40 min | ⏳ PENDING |
| 5 | [Análisis de Tests](#módulo-5-análisis-de-tests) | 🟡 ALTO | 45 min | ⏳ PENDING |
| 6 | [Análisis de Seguridad](#módulo-6-análisis-de-seguridad) | 🔴 CRÍTICO | 30 min | ⏳ PENDING |
| 7 | [Análisis de Integraciones](#módulo-7-análisis-de-integraciones) | 🟡 ALTO | 35 min | ⏳ PENDING |
| 8 | [Análisis de Performance](#módulo-8-análisis-de-performance) | 🟢 MEDIO | 25 min | ⏳ PENDING |
| 9 | [Análisis de Documentación](#módulo-9-análisis-de-documentación) | 🟢 MEDIO | 20 min | ⏳ PENDING |
| 10 | [Análisis de Deployment](#módulo-10-análisis-de-deployment) | 🔴 CRÍTICO | 40 min | ⏳ PENDING |

---

## 🎯 CRITERIOS DE ÉXITO

- ✅ **0 errores críticos** (bloquean deployment)
- ✅ **< 5 errores altos** (deben arreglarse en sprint 1)
- ✅ **< 15 warnings medios** (backlog aceptable)
- ✅ **100% cobertura de integraciones críticas** (WhatsApp, MP, Para Irnos)
- ✅ **85%+ test coverage** (validado)
- ✅ **0 CVEs críticos** (seguridad)

---

## MÓDULO 1: Análisis Estático - Código Backend

### 🎯 Objetivo
Detectar errores de sintaxis, imports rotos, type hints incorrectos, código muerto, y violaciones de estándares.

### 📋 Checklist

- [ ] **1.1 Validación de imports**
  ```bash
  cd backend
  python3 -c "import app.main; print('✅ app.main OK')"
  python3 -c "import app.core.config; print('✅ config OK')"
  python3 -c "import app.services.reservations; print('✅ reservations OK')"
  python3 -c "import app.services.whatsapp; print('✅ whatsapp OK')"
  python3 -c "import app.services.mercadopago; print('✅ mercadopago OK')"
  python3 -c "import app.services.ical; print('✅ ical OK')"
  python3 -c "import app.services.nlu; print('✅ nlu OK')"
  python3 -c "import app.services.audio; print('✅ audio OK')"
  ```
  **Criterio**: Todos deben importar sin errores

- [ ] **1.2 Verificación de sintaxis (Flake8)**
  ```bash
  cd backend
  flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
  ```
  **Criterio**: 0 errores de sintaxis

- [ ] **1.3 Type checking (mypy)**
  ```bash
  cd backend
  mypy app/ --ignore-missing-imports --no-error-summary 2>&1 | grep -E "error:|Error"
  ```
  **Criterio**: < 10 type errors (no críticos)

- [ ] **1.4 Código muerto (vulture)**
  ```bash
  cd backend
  vulture app/ --min-confidence 80
  ```
  **Criterio**: Identificar código no usado

- [ ] **1.5 Complejidad ciclomática**
  ```bash
  cd backend
  radon cc app/ -s -a
  ```
  **Criterio**: No funciones con complejidad > 15

- [ ] **1.6 Dependencias circulares**
  ```bash
  cd backend
  python3 -m pytest --co -q 2>&1 | grep -i "circular"
  ```
  **Criterio**: 0 imports circulares

- [ ] **1.7 Validación de todos los routers**
  ```bash
  cd backend
  ls app/routers/*.py | while read f; do
    echo "Checking $f..."
    python3 -c "import ${f//\//.} ${f//.py/}" 2>&1 | grep -i error
  done
  ```
  **Criterio**: Todos los routers importan OK

### 🔧 Comandos de Verificación Rápida

```bash
# Script all-in-one
cd backend
echo "=== BACKEND STATIC ANALYSIS ===" && \
python3 -m flake8 app/ --count --statistics --exit-zero && \
python3 -m pytest app/ --collect-only -q && \
echo "✅ Backend static analysis complete"
```

### ✅ Criterios de Aceptación
- [ ] 0 errores de import
- [ ] 0 errores de sintaxis (Flake8 E9/F*)
- [ ] Complejidad promedio < 10
- [ ] 100% de routers funcionan

### 🚨 Plan de Remediación
- **Import errors**: Verificar requirements.txt, instalar dependencias faltantes
- **Syntax errors**: Fix inmediato, bloquea deployment
- **High complexity**: Refactor en sprint 1 (no bloqueante)

---

## MÓDULO 2: Análisis Estático - Código Frontend

### 🎯 Objetivo
Detectar errores TypeScript, imports rotos, ESLint violations, componentes no usados.

### 📋 Checklist

- [ ] **2.1 TypeScript compilation**
  ```bash
  cd frontend/admin-dashboard
  npm run build 2>&1 | tee build.log
  grep -i "error" build.log
  ```
  **Criterio**: 0 TypeScript errors

- [ ] **2.2 ESLint validation**
  ```bash
  cd frontend/admin-dashboard
  npm run lint -- --max-warnings 10
  ```
  **Criterio**: < 10 warnings

- [ ] **2.3 Unused imports**
  ```bash
  cd frontend/admin-dashboard
  npx eslint src/ --ext .ts,.tsx --rule 'no-unused-vars: error' 2>&1 | grep -c "no-unused-vars"
  ```
  **Criterio**: < 5 unused imports

- [ ] **2.4 Missing dependencies**
  ```bash
  cd frontend/admin-dashboard
  npm audit --audit-level=high
  ```
  **Criterio**: 0 high/critical vulnerabilities

- [ ] **2.5 Bundle size check**
  ```bash
  cd frontend/admin-dashboard
  npm run build
  du -sh dist/
  ```
  **Criterio**: < 2MB total bundle

### 🔧 Comandos de Verificación

```bash
cd frontend/admin-dashboard
echo "=== FRONTEND STATIC ANALYSIS ===" && \
npm run type-check && \
npm run lint -- --max-warnings 10 && \
npm audit --audit-level=moderate && \
echo "✅ Frontend static analysis complete"
```

### ✅ Criterios de Aceptación
- [ ] Build exitoso sin TypeScript errors
- [ ] < 10 ESLint warnings
- [ ] 0 vulnerabilidades críticas en npm

---

## MÓDULO 3: Análisis de Configuración

### 🎯 Objetivo
Validar consistencia entre .env, fly.toml, docker-compose, y configuración real.

### 📋 Checklist

- [ ] **3.1 Validación .env.template**
  ```bash
  cd /home/eevan/ProyectosIA/SIST_CABAÑAS
  # Verificar que todas las variables tienen valor
  grep -E "^[A-Z_]+=.*$" .env.template | grep -v "^#" | wc -l
  # Comparar con config.py
  grep "Field\|str\|int" backend/app/core/config.py | grep -oE "[A-Z_]+" | sort -u > /tmp/config_vars.txt
  grep -oE "^[A-Z_]+=" .env.template | tr -d '=' | sort -u > /tmp/env_vars.txt
  diff /tmp/config_vars.txt /tmp/env_vars.txt
  ```
  **Criterio**: Todas las variables de config.py están en .env.template

- [ ] **3.2 Validación fly.toml**
  ```bash
  # Verificar sintaxis TOML
  python3 -c "import toml; toml.load('fly.toml'); print('✅ fly.toml valid')"

  # Verificar región
  grep "primary_region" fly.toml | grep -q "eze" && echo "✅ Region OK" || echo "❌ Region error"

  # Verificar puerto
  grep "internal_port" fly.toml | grep -q "8080" && echo "✅ Port OK" || echo "❌ Port error"
  ```
  **Criterio**: fly.toml sintácticamente correcto, región=eze, puerto=8080

- [ ] **3.3 Validación docker-compose.yml**
  ```bash
  docker-compose config -q && echo "✅ docker-compose.yml valid" || echo "❌ docker-compose.yml error"
  ```
  **Criterio**: YAML válido

- [ ] **3.4 Validación Dockerfile**
  ```bash
  cd backend
  docker build -t test-build --target builder . 2>&1 | tee /tmp/docker_build.log
  grep -i "error" /tmp/docker_build.log
  ```
  **Criterio**: Dockerfile builds sin errores

- [ ] **3.5 Consistencia de puertos**
  ```bash
  # Backend usa puerto 8080 en Fly.io, 8000 local
  grep -r "PORT.*8080" backend/ | wc -l
  grep "internal_port.*8080" fly.toml
  grep "EXPOSE 8080" backend/Dockerfile
  ```
  **Criterio**: Consistencia en configuración de puertos

- [ ] **3.6 Secretos en .env.template match config.py**
  ```bash
  python3 << 'EOF'
  import re

  # Leer config.py
  with open('backend/app/core/config.py') as f:
      config_content = f.read()
      config_vars = set(re.findall(r'(\w+):\s*(?:str|int|bool|Optional)', config_content))

  # Leer .env.template
  with open('.env.template') as f:
      env_vars = set(re.findall(r'^([A-Z_]+)=', f.read(), re.MULTILINE))

  missing = config_vars - env_vars
  extra = env_vars - config_vars

  print(f"Missing in .env.template: {missing}")
  print(f"Extra in .env.template: {extra}")
  print(f"✅ Match: {len(missing) == 0 and len(extra) < 5}")
  EOF
  ```
  **Criterio**: < 5 variables extra/faltantes

### ✅ Criterios de Aceptación
- [ ] .env.template tiene TODAS las variables de config.py
- [ ] fly.toml sintácticamente válido
- [ ] docker-compose.yml válido
- [ ] Dockerfile builds correctamente
- [ ] Consistencia de puertos/variables

---

## MÓDULO 4: Análisis de Base de Datos

### 🎯 Objetivo
Validar migraciones, modelos, constraints, indexes, y consistencia de schema.

### 📋 Checklist

- [ ] **4.1 Migraciones Alembic ordenadas**
  ```bash
  cd backend
  ls -1 alembic/versions/*.py | sort
  # Verificar que cada migración apunta a la anterior
  grep -h "down_revision" alembic/versions/*.py | sort
  ```
  **Criterio**: Secuencia de migraciones correcta

- [ ] **4.2 Validación de modelos SQLAlchemy**
  ```bash
  cd backend
  python3 << 'EOF'
  from app.models import Accommodation, Reservation, Payment
  from sqlalchemy import inspect

  # Verificar que todos los modelos tienen __tablename__
  models = [Accommodation, Reservation, Payment]
  for m in models:
      assert hasattr(m, '__tablename__'), f"{m} missing __tablename__"
      print(f"✅ {m.__name__} OK")

  # Verificar relaciones
  print(f"Accommodation columns: {len(inspect(Accommodation).columns)}")
  print(f"Reservation columns: {len(inspect(Reservation).columns)}")
  EOF
  ```
  **Criterio**: Todos los modelos válidos

- [ ] **4.3 Constraint anti doble-booking**
  ```bash
  cd backend
  grep -r "no_overlap_reservations\|EXCLUDE USING gist" alembic/versions/
  ```
  **Criterio**: Constraint presente en migración

- [ ] **4.4 Verificación de indexes**
  ```bash
  cd backend
  python3 << 'EOF'
  from sqlalchemy import inspect, create_engine
  from app.core.config import settings
  from app.models import Base

  # Conectar a DB de test
  engine = create_engine("sqlite:///test.db")
  Base.metadata.create_all(engine)

  # Verificar indexes
  inspector = inspect(engine)
  for table in ['accommodations', 'reservations', 'payments']:
      indexes = inspector.get_indexes(table)
      print(f"{table}: {len(indexes)} indexes")
  EOF
  ```
  **Criterio**: Accommodations ≥2 indexes, Reservations ≥3 indexes

- [ ] **4.5 Foreign keys correctas**
  ```bash
  cd backend
  grep -r "ForeignKey" app/models/*.py | grep -v "^#"
  ```
  **Criterio**: Todas las FKs apuntan a tablas existentes

- [ ] **4.6 Enums consistentes**
  ```bash
  cd backend
  python3 << 'EOF'
  from app.models.enums import ReservationStatus, PaymentStatus, ChannelSource

  # Verificar que enums tienen valores
  assert len(ReservationStatus.__members__) >= 4, "ReservationStatus incomplete"
  assert len(PaymentStatus.__members__) >= 3, "PaymentStatus incomplete"
  assert len(ChannelSource.__members__) >= 3, "ChannelSource incomplete"

  print(f"✅ ReservationStatus: {list(ReservationStatus.__members__.keys())}")
  print(f"✅ PaymentStatus: {list(PaymentStatus.__members__.keys())}")
  print(f"✅ ChannelSource: {list(ChannelSource.__members__.keys())}")
  EOF
  ```
  **Criterio**: Todos los enums tienen ≥3 valores

### ✅ Criterios de Aceptación
- [ ] Secuencia de migraciones correcta
- [ ] Constraint anti doble-booking activo
- [ ] Indexes en tablas críticas
- [ ] Foreign keys válidas
- [ ] Enums completos

---

## MÓDULO 5: Análisis de Tests

### 🎯 Objetivo
Validar cobertura de tests, edge cases, y tests E2E críticos.

### 📋 Checklist

- [ ] **5.1 Ejecutar todos los tests**
  ```bash
  cd backend
  python3 -m pytest tests/ -v --tb=short --maxfail=5 2>&1 | tee /tmp/pytest.log
  grep -E "PASSED|FAILED|ERROR" /tmp/pytest.log | tail -20
  ```
  **Criterio**: ≥ 90% tests PASSED

- [ ] **5.2 Cobertura de código**
  ```bash
  cd backend
  python3 -m pytest tests/ --cov=app --cov-report=term --cov-report=html
  ```
  **Criterio**: ≥ 85% coverage

- [ ] **5.3 Tests críticos específicos**
  ```bash
  cd backend
  # Test anti doble-booking
  python3 -m pytest tests/test_double_booking.py -v

  # Test constraint validation
  python3 -m pytest tests/test_constraint_validation.py -v

  # Test agent consistency
  python3 -m pytest tests/test_agent_consistency.py -v

  # Test iCal import
  python3 -m pytest tests/ -k "ical" -v
  ```
  **Criterio**: 100% de tests críticos PASSED

- [ ] **5.4 Tests E2E (si están implementados)**
  ```bash
  cd backend
  python3 -m pytest tests/test_e2e_flows.py -v --tb=short
  ```
  **Criterio**: Identificar cuántos E2E fallan (acceptable: SKIP)

- [ ] **5.5 Tests de integración (WhatsApp, MP)**
  ```bash
  cd backend
  python3 -m pytest tests/ -k "whatsapp or mercadopago" -v
  ```
  **Criterio**: ≥ 80% PASSED

- [ ] **5.6 Performance tests (si existen)**
  ```bash
  cd backend
  python3 -m pytest tests/ -k "performance or load" -v
  ```
  **Criterio**: Identificar si existen

### ✅ Criterios de Aceptación
- [ ] ≥ 90% tests passing
- [ ] ≥ 85% code coverage
- [ ] 100% tests críticos (doble-booking, constraints) PASSED
- [ ] Tests de integraciones funcionan

---

## MÓDULO 6: Análisis de Seguridad

### 🎯 Objetivo
Detectar vulnerabilidades, secrets expuestos, CVEs, y problemas de autenticación.

### 📋 Checklist

- [ ] **6.1 Scan de vulnerabilidades (Bandit)**
  ```bash
  cd backend
  bandit -r app/ -f json -o /tmp/bandit.json
  cat /tmp/bandit.json | python3 -m json.tool | grep -E "issue_severity|issue_text" | head -20
  ```
  **Criterio**: 0 HIGH severity issues

- [ ] **6.2 Secrets en código (truffleHog o grep)**
  ```bash
  cd /home/eevan/ProyectosIA/SIST_CABAÑAS
  # Buscar posibles secrets hardcoded
  grep -r "password.*=.*[\"']" --include="*.py" --include="*.ts" --exclude-dir=node_modules --exclude-dir=.git | grep -v "POSTGRES_PASSWORD\|DB_PASSWORD" | head -10

  # Buscar API keys
  grep -r "api_key.*=.*[\"']" --include="*.py" --include="*.ts" --exclude-dir=node_modules --exclude-dir=.git | head -10
  ```
  **Criterio**: 0 secrets hardcoded

- [ ] **6.3 Dependencias vulnerables (Python)**
  ```bash
  cd backend
  pip-audit --desc 2>&1 | tee /tmp/pip_audit.log
  grep -i "critical\|high" /tmp/pip_audit.log
  ```
  **Criterio**: 0 critical CVEs

- [ ] **6.4 Dependencias vulnerables (NPM)**
  ```bash
  cd frontend/admin-dashboard
  npm audit --audit-level=high 2>&1 | tee /tmp/npm_audit.log
  grep -E "critical|high" /tmp/npm_audit.log | wc -l
  ```
  **Criterio**: 0 critical, < 3 high

- [ ] **6.5 Validación JWT**
  ```bash
  cd backend
  grep -r "jwt.decode\|jwt.encode" app/ | grep -v "verify_signature"
  # Verificar que siempre se valida signature
  ```
  **Criterio**: Todas las llamadas jwt.decode tienen verify=True

- [ ] **6.6 Webhook signature validation**
  ```bash
  cd backend
  # WhatsApp
  grep -A10 "webhook.*whatsapp" app/routers/webhooks.py | grep -i "signature"

  # Mercado Pago
  grep -A10 "webhook.*mercadopago" app/routers/webhooks.py | grep -i "signature"
  ```
  **Criterio**: Ambos webhooks validan firma

- [ ] **6.7 SQL Injection protection**
  ```bash
  cd backend
  # Buscar string concatenation en queries
  grep -r "execute.*f\"" app/ --include="*.py" | grep -v "^#"
  ```
  **Criterio**: 0 f-strings en queries SQL (usar parámetros)

- [ ] **6.8 CORS configuration**
  ```bash
  cd backend
  grep -A5 "CORSMiddleware" app/main.py
  ```
  **Criterio**: ALLOWED_ORIGINS no es "*" en producción

### ✅ Criterios de Aceptación
- [ ] 0 HIGH severity issues (Bandit)
- [ ] 0 secrets hardcoded
- [ ] 0 critical CVEs
- [ ] JWT signature validation activa
- [ ] Webhooks validan firmas
- [ ] CORS configurado correctamente

---

## MÓDULO 7: Análisis de Integraciones

### 🎯 Objetivo
Validar que WhatsApp, Mercado Pago, iCal, y Para Irnos están correctamente implementados.

### 📋 Checklist

- [ ] **7.1 WhatsApp Business API**
  ```bash
  cd backend
  # Verificar que service existe y tiene métodos correctos
  python3 << 'EOF'
  from app.services.whatsapp import WhatsAppService
  import inspect

  methods = [m for m in dir(WhatsAppService) if not m.startswith('_')]
  required = ['send_message', 'send_template', 'mark_as_read']

  for r in required:
      assert r in methods, f"Missing method: {r}"
      print(f"✅ {r} exists")
  EOF

  # Verificar que webhook valida firma
  grep -A20 "webhooks/whatsapp" app/routers/webhooks.py | grep -i "verify.*signature"
  ```
  **Criterio**: Service completo, webhook valida firma

- [ ] **7.2 Mercado Pago**
  ```bash
  cd backend
  python3 << 'EOF'
  from app.services.mercadopago import MercadoPagoService
  import inspect

  methods = [m for m in dir(MercadoPagoService) if not m.startswith('_')]
  required = ['create_payment_link', 'get_payment']

  for r in required:
      assert r in methods, f"Missing method: {r}"
      print(f"✅ {r} exists")
  EOF

  # Verificar webhook
  grep -A20 "webhooks/mercadopago" app/routers/webhooks.py | grep -i "signature"
  ```
  **Criterio**: Service completo, webhook con signature validation

- [ ] **7.3 iCal (Airbnb, Booking)**
  ```bash
  cd backend
  python3 << 'EOF'
  from app.services.ical import ICalService
  import inspect

  methods = [m for m in dir(ICalService) if not m.startswith('_')]
  required = ['export_calendar', 'import_events']

  for r in required:
      assert r in methods, f"Missing method: {r}"
      print(f"✅ {r} exists")
  EOF

  # Verificar que background job existe
  grep -r "run_ical_sync" backend/app/jobs/
  ```
  **Criterio**: Export/Import funcionan, background job activo

- [ ] **7.4 Para Irnos Integration**
  ```bash
  # Verificar documentación
  test -f docs/integrations/PARA_IRNOS_INTEGRATION.md && echo "✅ Docs exist" || echo "❌ Missing docs"

  # Verificar que modelo soporta para_irnos
  grep -r "para_irnos" backend/app/models/accommodation.py backend/app/services/ical.py

  # Verificar test
  grep -A30 "test_ical_import_para_irnos" backend/tests/test_e2e_flows.py
  ```
  **Criterio**: Documentación + modelo + test existen

- [ ] **7.5 Audio/Whisper STT**
  ```bash
  cd backend
  python3 << 'EOF'
  from app.services.audio import AudioProcessor

  assert hasattr(AudioProcessor, 'transcribe_audio'), "Missing transcribe_audio"
  print("✅ AudioProcessor OK")
  EOF
  ```
  **Criterio**: AudioProcessor con transcribe_audio

- [ ] **7.6 NLU Service**
  ```bash
  cd backend
  python3 << 'EOF'
  from app.services.nlu import NLUService

  methods = [m for m in dir(NLUService) if not m.startswith('_')]
  assert 'analyze_message' in methods, "Missing analyze_message"
  print(f"✅ NLUService OK: {methods}")
  EOF
  ```
  **Criterio**: NLU con analyze_message

### ✅ Criterios de Aceptación
- [ ] WhatsApp service completo + webhook validado
- [ ] Mercado Pago service completo + webhook validado
- [ ] iCal export/import funcionan + background job activo
- [ ] Para Irnos documentado + implementado + testeado
- [ ] Audio/NLU services completos

---

## MÓDULO 8: Análisis de Performance

### 🎯 Objetivo
Identificar bottlenecks, queries N+1, memory leaks, y optimizaciones necesarias.

### 📋 Checklist

- [ ] **8.1 Queries N+1**
  ```bash
  cd backend
  # Buscar queries sin eager loading
  grep -r "\.all()\|\.first()" app/services/ | head -20

  # Verificar uso de joinedload/selectinload
  grep -r "joinedload\|selectinload" app/services/ | wc -l
  ```
  **Criterio**: ≥ 5 usos de joinedload (optimizaciones presentes)

- [ ] **8.2 Índices en queries frecuentes**
  ```bash
  cd backend
  # Verificar que campos filtrados tienen índices
  grep -r "filter.*accommodation_id" app/ | wc -l
  grep "accommodation_id.*index=True" app/models/reservation.py
  ```
  **Criterio**: Campos filtrados tienen index=True

- [ ] **8.3 Redis caching**
  ```bash
  cd backend
  # Verificar uso de Redis para cache
  grep -r "redis\|cache" app/services/ | grep -v "^#" | wc -l
  ```
  **Criterio**: ≥ 10 usos de Redis (locks, rate limit, cache)

- [ ] **8.4 Connection pooling**
  ```bash
  cd backend
  grep -A5 "create_async_engine" app/core/database.py
  # Verificar DB_POOL_SIZE
  grep "DB_POOL_SIZE" .env.template
  ```
  **Criterio**: Pool configurado (size ≥ 20)

- [ ] **8.5 Gunicorn workers**
  ```bash
  grep "GUNICORN_WORKERS" backend/start-fly.sh .env.template
  ```
  **Criterio**: Workers configurables (default 2)

- [ ] **8.6 Load test (opcional, si hay script k6)**
  ```bash
  # Si existe script k6
  test -f tests/load/prereservation.js && k6 run tests/load/prereservation.js || echo "⏭️ Load test not found (optional)"
  ```
  **Criterio**: P95 < 3s (si se ejecuta)

### ✅ Criterios de Aceptación
- [ ] Eager loading usado donde corresponde
- [ ] Índices en campos críticos
- [ ] Redis caching activo
- [ ] Connection pool configurado
- [ ] Gunicorn workers optimizado

---

## MÓDULO 9: Análisis de Documentación

### 🎯 Objetivo
Validar que documentación está actualizada, completa, y sin referencias rotas.

### 📋 Checklist

- [ ] **9.1 README principal actualizado**
  ```bash
  # Verificar que README tiene secciones clave
  grep -E "Features|Installation|Usage|Deployment" README.md
  ```
  **Criterio**: README con secciones principales

- [ ] **9.2 Documentación de deployment**
  ```bash
  ls -lh FLY_README.md docs/operations/FLY_DEPLOYMENT_GUIDE.md
  # Verificar que no hay referencias a Railway si cambiamos a Fly.io
  grep -ri "railway" docs/ | grep -v "RAILWAY_" | wc -l
  ```
  **Criterio**: Docs de Fly.io presentes, referencias a Railway controladas

- [ ] **9.3 Documentación de integraciones**
  ```bash
  ls -lh docs/integrations/*.md
  test -f docs/integrations/PARA_IRNOS_INTEGRATION.md && echo "✅ Para Irnos docs"
  ```
  **Criterio**: Integraciones documentadas

- [ ] **9.4 API documentation (OpenAPI/Swagger)**
  ```bash
  cd backend
  # Verificar que FastAPI genera docs
  python3 << 'EOF'
  from app.main import app
  assert "/docs" in [r.path for r in app.routes], "Missing /docs"
  assert "/openapi.json" in [r.path for r in app.routes], "Missing /openapi.json"
  print("✅ API docs available at /docs")
  EOF
  ```
  **Criterio**: /docs y /openapi.json disponibles

- [ ] **9.5 Comentarios en código crítico**
  ```bash
  cd backend
  # Verificar docstrings en servicios
  grep -c "\"\"\"" app/services/reservations.py
  grep -c "\"\"\"" app/services/ical.py
  ```
  **Criterio**: ≥ 10 docstrings por servicio crítico

- [ ] **9.6 Changelog o historial de versiones**
  ```bash
  test -f CHANGELOG.md && echo "✅ CHANGELOG exists" || echo "⚠️ Missing CHANGELOG (optional)"
  ```
  **Criterio**: Opcional para MVP

### ✅ Criterios de Aceptación
- [ ] README actualizado
- [ ] Documentación Fly.io completa
- [ ] Integraciones documentadas (Para Irnos, iCal)
- [ ] API docs (/docs) funcionan
- [ ] Código crítico con docstrings

---

## MÓDULO 10: Análisis de Deployment

### 🎯 Objetivo
Validar que configuración de deployment es correcta, health checks funcionan, y rollback está configurado.

### 📋 Checklist

- [ ] **10.1 Dockerfile build test**
  ```bash
  cd backend
  docker build -t sist-cabanas-test:latest -f Dockerfile .
  docker images | grep sist-cabanas-test
  ```
  **Criterio**: Build exitoso

- [ ] **10.2 Docker multi-stage optimizado**
  ```bash
  cd backend
  grep -E "FROM.*as builder|FROM.*as runtime" Dockerfile
  ```
  **Criterio**: Multi-stage presente (optimización)

- [ ] **10.3 Health check endpoint**
  ```bash
  cd backend
  # Verificar que healthz existe
  grep -A20 "/healthz" app/routers/health.py

  # Verificar checks internos
  grep -E "database|redis|ical" app/routers/health.py
  ```
  **Criterio**: /healthz con checks de DB, Redis, iCal

- [ ] **10.4 Readiness endpoint**
  ```bash
  grep -A10 "/readyz" app/routers/health.py
  ```
  **Criterio**: /readyz existe (opcional)

- [ ] **10.5 Fly.io health check configurado**
  ```bash
  grep -A5 "http_service" fly.toml | grep "health_check"
  ```
  **Criterio**: Health check en fly.toml apunta a /healthz

- [ ] **10.6 Start script funcional**
  ```bash
  # Verificar permisos
  test -x backend/start-fly.sh && echo "✅ Executable" || echo "❌ Not executable"

  # Verificar que hace health checks
  grep -E "nc -z|curl.*healthz" backend/start-fly.sh
  ```
  **Criterio**: start-fly.sh ejecutable y con health checks

- [ ] **10.7 Migraciones automáticas en startup**
  ```bash
  grep "alembic upgrade head" backend/start-fly.sh
  ```
  **Criterio**: Migraciones se ejecutan en startup

- [ ] **10.8 Zero-downtime deploy configurado**
  ```bash
  grep -A5 "\[deploy\]" fly.toml | grep "max_unavailable.*0"
  ```
  **Criterio**: max_unavailable = 0

- [ ] **10.9 Auto-rollback configurado**
  ```bash
  grep -A3 "\[experimental\]" fly.toml | grep "auto_rollback.*true"
  ```
  **Criterio**: auto_rollback = true

- [ ] **10.10 Prometheus metrics expuestos**
  ```bash
  cd backend
  grep -r "/metrics" app/main.py
  ```
  **Criterio**: /metrics endpoint disponible

### ✅ Criterios de Aceptación
- [ ] Dockerfile build exitoso
- [ ] Health checks (/healthz) funcionan
- [ ] Fly.io configurado para zero-downtime
- [ ] Auto-rollback activo
- [ ] Start script ejecuta migraciones
- [ ] Metrics expuestos

---

## 📊 REPORTE FINAL

### Template de Reporte

```markdown
# 🔬 AUDITORÍA MOLECULAR - REPORTE FINAL

**Fecha**: [Fecha]
**Ejecutado por**: [Nombre]
**Duración**: [Tiempo]

## Resumen Ejecutivo

| Métrica | Valor | Status |
|---------|-------|--------|
| **Módulos auditados** | X/10 | ⏳ |
| **Errores críticos** | X | 🔴/🟢 |
| **Errores altos** | X | 🟡/🟢 |
| **Warnings medios** | X | 🟢 |
| **Test coverage** | X% | 🟢 |
| **CVEs críticos** | X | 🟢 |

## Status por Módulo

1. ✅/❌ Análisis Estático Backend: [Status]
2. ✅/❌ Análisis Estático Frontend: [Status]
3. ✅/❌ Análisis Configuración: [Status]
4. ✅/❌ Análisis Base de Datos: [Status]
5. ✅/❌ Análisis Tests: [Status]
6. ✅/❌ Análisis Seguridad: [Status]
7. ✅/❌ Análisis Integraciones: [Status]
8. ✅/❌ Análisis Performance: [Status]
9. ✅/❌ Análisis Documentación: [Status]
10. ✅/❌ Análisis Deployment: [Status]

## Hallazgos Críticos

[Listar errores críticos encontrados]

## Recomendaciones

[Listar acciones requeridas]

## Conclusión

✅ READY FOR PRODUCTION / ❌ BLOQUEADO

**Próximos pasos**:
1. [Acción 1]
2. [Acción 2]
```

---

## 🚀 EJECUCIÓN DEL PLAN

### Orden Sugerido

1. **FASE 1 - Críticos** (2h):
   - Módulo 1: Backend Estático
   - Módulo 3: Configuración
   - Módulo 4: Base de Datos
   - Módulo 6: Seguridad
   - Módulo 10: Deployment

2. **FASE 2 - Altos** (1.5h):
   - Módulo 2: Frontend Estático
   - Módulo 5: Tests
   - Módulo 7: Integraciones

3. **FASE 3 - Medios** (1h):
   - Módulo 8: Performance
   - Módulo 9: Documentación

### Automatización

Crear script `run_audit.sh`:

```bash
#!/bin/bash
# Script de auditoría automatizada

echo "🔬 Iniciando Auditoría Molecular..."
echo "=================================="

cd /home/eevan/ProyectosIA/SIST_CABAÑAS

# Timestamp
START=$(date +%s)

# Módulo 1
echo "[1/10] Análisis Estático Backend..."
cd backend && python3 -m flake8 app/ --count && cd ..

# Módulo 3
echo "[3/10] Análisis Configuración..."
python3 -c "import toml; toml.load('fly.toml'); print('✅')"

# Módulo 4
echo "[4/10] Análisis Base de Datos..."
cd backend && python3 -c "from app.models import Base; print('✅')" && cd ..

# Módulo 5
echo "[5/10] Análisis Tests..."
cd backend && python3 -m pytest tests/ -q && cd ..

# Módulo 6
echo "[6/10] Análisis Seguridad..."
cd backend && bandit -r app/ -lll -q && cd ..

# ... más módulos

END=$(date +%s)
DURATION=$((END - START))

echo "=================================="
echo "✅ Auditoría completada en ${DURATION}s"
```

---

**FIN DEL PLAN MAESTRO DE AUDITORÍA**

Este plan debe ejecutarse ANTES de cualquier deployment a producción.
