# GitHub Actions - Guía de CI/CD

**Versión:** 1.0
**Última actualización:** 4 de Octubre, 2025
**Estado:** ✅ Activo

---

## 📋 Tabla de Contenidos

1. [Overview](#overview)
2. [Workflows Disponibles](#workflows-disponibles)
3. [Configuración Inicial](#configuración-inicial)
4. [CI Workflow (ci.yml)](#ci-workflow)
5. [Deploy Staging (deploy-staging.yml)](#deploy-staging)
6. [Security Scan (security-scan.yml)](#security-scan)
7. [Secrets Requeridos](#secrets-requeridos)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Agregar Nuevos Workflows](#agregar-nuevos-workflows)

---

## Overview

Este sistema de CI/CD automatiza:

- ✅ **Testing automático** en cada PR y push a main
- ✅ **Linting y code quality** checks
- ✅ **Security scanning** semanal y en PRs
- ✅ **Deploy automático** a staging cuando se hace merge a main
- ✅ **Coverage reports** integrados con Codecov
- ✅ **Rollback automático** si el deploy falla

### Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Lint   │  │  Tests   │  │ Security │  │  Deploy  │  │
│  │          │  │ SQLite   │  │   Scan   │  │ Staging  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│       │             │              │              │        │
│       └─────────────┴──────────────┴──────────────┘        │
│                         │                                   │
│                    ┌────▼────┐                             │
│                    │  Tests  │                             │
│                    │Postgres │                             │
│                    └─────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflows Disponibles

### 1. **CI - Tests and Linting** (`ci.yml`)

**Trigger:** Push a `main`, Pull Requests, Manual

**Duración:** 5-10 minutos

**Jobs:**
- `lint`: Code quality checks (Black, Flake8, isort, Bandit)
- `tests-sqlite`: Tests rápidos con SQLite (fallback)
- `tests-postgres-redis`: Tests completos con PostgreSQL + Redis
- `security`: Dependency vulnerability scan con Safety

**Status Badge:**
```markdown
![CI Status](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml/badge.svg)
```

### 2. **Deploy to Staging** (`deploy-staging.yml`)

**Trigger:** Push a `main`, Manual

**Duración:** 3-5 minutos

**Jobs:**
- `deploy`: SSH al servidor, pull código, rebuild containers
- `notify`: Notificación del resultado (opcional)

**Requiere:**
- Servidor staging configurado
- SSH keys en GitHub Secrets
- Scripts de pre/post-deploy

### 3. **Security Scan** (`security-scan.yml`)

**Trigger:** Lunes a las 2 AM UTC, Manual

**Duración:** 10-15 minutos

**Jobs:**
- `trivy`: Container vulnerability scanning
- `dependency-review`: Python dependencies con Safety
- `secret-scan`: Búsqueda de secrets con GitLeaks
- `summary`: Resumen de resultados

**Reports:** SARIF files subidos a GitHub Security tab

---

## Configuración Inicial

### Paso 1: Habilitar GitHub Actions

Ya está habilitado automáticamente en este repo. Verifica en:
```
Settings → Actions → General → Allow all actions
```

### Paso 2: Configurar Secrets

Ir a `Settings → Secrets and variables → Actions` y agregar:

#### Para Deploy Staging:
```bash
STAGING_SSH_KEY       # Private SSH key para conectar al servidor
STAGING_HOST          # IP o dominio del servidor (ej: staging.alojamientos.com)
STAGING_USER          # Usuario SSH (ej: ubuntu, root)
```

#### Para Coverage (Opcional):
```bash
CODECOV_TOKEN         # Token de https://codecov.io
```

#### Para Notificaciones (Opcional):
```bash
SLACK_WEBHOOK_URL     # Webhook de Slack para notificaciones
```

### Paso 3: Configurar Environment

Crear environment `staging`:
```
Settings → Environments → New environment
Name: staging
```

Agregar protection rules (opcional):
- ✅ Required reviewers (1 aprobación antes de deploy)
- ✅ Wait timer (5 minutos de espera)

---

## CI Workflow

### Archivo: `.github/workflows/ci.yml`

### Job: `lint` (Code Quality)

Ejecuta en paralelo:

1. **Black** - Formateo de código
   ```bash
   black --check backend/app backend/tests
   ```

2. **isort** - Orden de imports
   ```bash
   isort --check-only backend/app backend/tests
   ```

3. **Flake8** - Linting
   ```bash
   flake8 backend/app backend/tests --max-line-length=120
   ```

4. **Bandit** - Security linting
   ```bash
   bandit -r backend/app -ll
   ```

**Resultado:** JSON report subido como artifact

### Job: `tests-sqlite` (Tests Rápidos)

- **Duración:** ~2 minutos
- **Base de datos:** SQLite (en memoria)
- **Redis:** FakeRedis
- **Coverage:** Subido a Codecov con flag `sqlite`

**Excluye:**
- `test_double_booking.py` (requiere PostgreSQL + btree_gist)
- `test_constraint_validation.py` (requiere PostgreSQL + btree_gist)

### Job: `tests-postgres-redis` (Tests Completos)

- **Duración:** ~5 minutos
- **Base de datos:** PostgreSQL 16 con extensiones
- **Redis:** Redis 7
- **Coverage:** Subido a Codecov con flag `postgres`

**Services:**
```yaml
postgres:
  image: postgres:16
  env:
    POSTGRES_USER: alojamientos
    POSTGRES_PASSWORD: password
    POSTGRES_DB: alojamientos_test_db
  ports:
    - 5432:5432

redis:
  image: redis:7
  ports:
    - 6379:6379
```

**Incluye TODOS los tests**, incluyendo los de constraint anti-doble-booking.

### Job: `security` (Dependency Scan)

Usa **Safety** para escanear vulnerabilidades conocidas en `requirements.txt`.

**Output:** JSON report con detalles de CVEs encontrados.

---

## Deploy Staging

### Archivo: `.github/workflows/deploy-staging.yml`

### Flujo de Deploy

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SSH al servidor staging                                  │
│    - Usa SSH key de GitHub Secrets                          │
│    - Agrega host a known_hosts                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Git pull origin/main                                     │
│    - git reset --hard origin/main                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Pre-deploy checks                                        │
│    - Ejecuta scripts/pre-deploy-check.sh                    │
│    - Si falla → ABORT                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Deploy                                                    │
│    - docker compose down                                     │
│    - docker compose pull                                     │
│    - docker compose up -d --build                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Wait 30 segundos                                         │
│    - Tiempo para que servicios se inicialicen              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Post-deploy verification                                 │
│    - Ejecuta scripts/post-deploy-verify.sh                  │
│    - Si falla → ROLLBACK automático                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Success! ✅                                              │
│    - Notificación opcional                                  │
└─────────────────────────────────────────────────────────────┘
```

### Rollback Automático

Si `post-deploy-verify.sh` falla:

```bash
git checkout HEAD^              # Volver al commit anterior
docker compose down             # Bajar containers
docker compose up -d --build    # Re-deploy versión anterior
```

### Deploy Manual

Para hacer deploy manual sin push a main:

```bash
# Ir a GitHub Actions → Deploy to Staging → Run workflow
```

O desde CLI:
```bash
gh workflow run deploy-staging.yml
```

---

## Security Scan

### Archivo: `.github/workflows/security-scan.yml`

### Job: `trivy` (Container Scan)

Escanea la imagen Docker en busca de vulnerabilidades.

**Output:**
- SARIF file → GitHub Security tab
- JSON report → Artifact

**Severidades:** CRITICAL, HIGH, MEDIUM

### Job: `dependency-review` (Python Deps)

Usa **Safety** para escanear `requirements.txt`.

**Output:** JSON report con CVEs

### Job: `secret-scan` (GitLeaks)

Busca secrets expuestos en el código (API keys, passwords, tokens).

**Falsos positivos:** Agregar al `.gitleaksignore`:
```
# .gitleaksignore
dummy_token_in_tests
example_secret_for_docs
```

### Resultados

Ver en: **Security tab → Code scanning alerts**

---

## Secrets Requeridos

### Crear SSH Key para Deploy

```bash
# En tu máquina local
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/staging_deploy

# Copiar public key al servidor
ssh-copy-id -i ~/.ssh/staging_deploy.pub ubuntu@staging.alojamientos.com

# Copiar private key a GitHub Secrets
cat ~/.ssh/staging_deploy
# Pegar contenido en GitHub → Settings → Secrets → STAGING_SSH_KEY
```

### Variables de Environment

Agregar en `Settings → Environments → staging`:

```
STAGING_HOST=staging.alojamientos.com
STAGING_USER=ubuntu
```

---

## Troubleshooting

### ❌ Tests fallan en CI pero pasan localmente

**Problema:** Diferencias de entorno

**Solución:**
```bash
# Verificar versión de Python
python --version  # Debe ser 3.12

# Verificar dependencias
pip list | grep -E "fastapi|sqlalchemy|pytest"

# Ejecutar tests como lo hace CI
pytest tests/ \
  --cov=app \
  --cov-report=term-missing \
  -v
```

### ❌ Deploy falla en SSH connection

**Problema:** SSH key o host incorrectos

**Solución:**
```bash
# Verificar que el servidor es accesible
ssh ubuntu@staging.alojamientos.com "echo OK"

# Verificar que SSH key tiene permisos correctos
chmod 600 ~/.ssh/staging_deploy

# Test manual del deploy
ssh ubuntu@staging.alojamientos.com << 'EOF'
  cd /opt/apps/SIST_CABANAS_MVP
  git pull origin main
  docker compose ps
EOF
```

### ❌ Coverage no sube a Codecov

**Problema:** Token no configurado o inválido

**Solución:**
1. Ir a https://codecov.io y crear cuenta
2. Agregar repo `SIST_CABANAS_MVP`
3. Copiar token
4. Agregarlo a GitHub Secrets como `CODECOV_TOKEN`

**Alternativa:** Codecov es opcional. Puedes ver coverage localmente:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### ❌ Security scan reporta falsos positivos

**Problema:** Trivy/Safety marcan vulnerabilidades en dependencias que no afectan

**Solución:**
```bash
# Para Trivy - crear .trivyignore
echo "CVE-2024-XXXXX" >> .trivyignore

# Para Safety - upgrade dependencias
pip install --upgrade <package>
pip freeze > requirements.txt
```

### ❌ Workflow se queda stuck

**Problema:** Job esperando indefinidamente

**Solución:**
```bash
# Cancelar workflow
gh run cancel <run-id>

# O en GitHub UI: Actions → Select run → Cancel workflow
```

**Prevención:** Todos los jobs tienen `timeout-minutes` configurado.

---

## Best Practices

### ✅ DO

1. **Siempre revisar logs de CI antes de merge**
   ```bash
   # Ver runs recientes
   gh run list --workflow=ci.yml

   # Ver detalles de un run
   gh run view <run-id>
   ```

2. **Ejecutar tests localmente antes de push**
   ```bash
   pytest tests/ -v
   ```

3. **Usar feature branches para cambios grandes**
   ```bash
   git checkout -b feature/nueva-funcionalidad
   # Hacer cambios
   git push origin feature/nueva-funcionalidad
   # Crear PR en GitHub
   ```

4. **Revisar security scan semanalmente**
   ```
   Actions → Security Scan → Latest run
   ```

5. **Mantener secrets actualizados**
   - Rotar SSH keys cada 3-6 meses
   - Verificar que tokens no hayan expirado

### ❌ DON'T

1. **NO hacer push directo a main sin CI**
   - Siempre esperar que CI pase en PR

2. **NO ignorar warnings de security scan**
   - Al menos revisar y documentar por qué se ignora

3. **NO commitear secrets al código**
   - Usar `.env` y GitHub Secrets

4. **NO saltear pre-commit hooks**
   - Están ahí para prevenir errores

5. **NO hacer deploy manual sin verificar CI**
   - El deploy automático ya verifica todo

---

## Agregar Nuevos Workflows

### Template Básico

```yaml
name: My New Workflow

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  my-job:
    name: My Job Description
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Do something
        run: |
          echo "Hello World"
```

### Agregar Job a CI Existente

Editar `.github/workflows/ci.yml`:

```yaml
jobs:
  # ... jobs existentes ...

  my-new-check:
    name: My New Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run check
        run: |
          # Tu comando aquí
```

### Testing Workflow Localmente

Usar **act** para ejecutar workflows localmente:

```bash
# Instalar act
brew install act  # macOS
# o
sudo snap install act  # Linux

# Ejecutar workflow
act -W .github/workflows/ci.yml
```

---

## Métricas y Monitoring

### Ver Status de Workflows

```bash
# Lista de runs recientes
gh run list

# Status de último run
gh run view

# Logs de un job específico
gh run view <run-id> --log
```

### Badge Status en README

Agregar a `README.md`:

```markdown
## CI/CD Status

[![CI](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml)
[![Deploy](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/deploy-staging.yml)
[![Security](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/security-scan.yml)
[![codecov](https://codecov.io/gh/eevans-d/SIST_CABANAS_MVP/branch/main/graph/badge.svg)](https://codecov.io/gh/eevans-d/SIST_CABANAS_MVP)
```

### Success Rate

Objetivo: **> 95% de workflows exitosos**

Calcular:
```bash
TOTAL=$(gh run list --json conclusion --jq 'length')
SUCCESS=$(gh run list --json conclusion --jq '[.[] | select(.conclusion=="success")] | length')
echo "Success rate: $(echo "scale=2; $SUCCESS*100/$TOTAL" | bc)%"
```

---

## FAQ

### ¿Por qué hay dos jobs de tests (SQLite y Postgres)?

- **SQLite**: Rápido (~2 min), feedback inmediato
- **Postgres**: Completo (~5 min), incluye tests de constraints

Ambos deben pasar para merge.

### ¿Cuándo se ejecuta el deploy automático?

Cuando se hace **merge a main** y:
- ✅ Todos los tests pasan
- ✅ Linting pasa
- ✅ Security scan no tiene CRITICAL issues

### ¿Puedo hacer deploy manual?

Sí:
```bash
gh workflow run deploy-staging.yml
```

O en GitHub UI: Actions → Deploy to Staging → Run workflow

### ¿Qué pasa si el deploy falla?

Rollback automático al commit anterior. Ver logs para debug.

### ¿Cómo ver logs de un workflow fallido?

```bash
gh run list --workflow=ci.yml
gh run view <run-id> --log
```

### ¿Puedo desactivar un workflow temporalmente?

Sí, editar el archivo `.yml` y comentar el trigger:
```yaml
# on:
#   push:
#     branches: [ main ]
```

O desactivar en: Actions → Select workflow → Disable workflow

---

## Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub CLI](https://cli.github.com/manual/gh_workflow)
- [Act - Local Testing](https://github.com/nektos/act)

---

**Última actualización:** 4 de Octubre, 2025
**Mantenido por:** DevOps Team
**Contacto:** Para issues, crear ticket en GitHub Issues
