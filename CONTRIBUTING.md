# Guía de Contribución

¡Gracias por tu interés en contribuir al Sistema MVP de Reservas de Alojamientos! Esta guía te ayudará a entender el flujo de trabajo y las convenciones del proyecto.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Puedo Contribuir?](#cómo-puedo-contribuir)
- [Configuración del Entorno](#configuración-del-entorno)
- [Flujo de Trabajo](#flujo-de-trabajo)
- [Convenciones de Código](#convenciones-de-código)
- [Convenciones de Commits](#convenciones-de-commits)
- [Testing](#testing)
- [Documentación](#documentación)
- [Pull Requests](#pull-requests)

---

## Código de Conducta

Este proyecto y todos sus participantes están regidos por nuestro código de conducta. Al participar, se espera que respetes este código:

- Usa un lenguaje acogedor e inclusivo
- Respeta diferentes puntos de vista y experiencias
- Acepta críticas constructivas con gracia
- Enfócate en lo que es mejor para la comunidad
- Muestra empatía hacia otros miembros de la comunidad

---

## ¿Cómo Puedo Contribuir?

### Reportar Bugs

Antes de reportar un bug:
1. Verifica que no exista un issue similar ya reportado
2. Reproduce el bug en la última versión del código
3. Recolecta información relevante (logs, versiones, pasos para reproducir)

**Template de Bug Report:**
```markdown
**Descripción:**
[Descripción clara del problema]

**Pasos para Reproducir:**
1. [Primer paso]
2. [Segundo paso]
3. [...]

**Comportamiento Esperado:**
[Lo que debería pasar]

**Comportamiento Actual:**
[Lo que realmente pasa]

**Entorno:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.12.3]
- PostgreSQL: [e.g., 16.2]
- Docker: [e.g., 24.0.7]

**Logs Relevantes:**
```
[Logs aquí]
```

**Información Adicional:**
[Cualquier otro detalle relevante]
```

### Sugerir Mejoras

Para sugerir una mejora o nueva funcionalidad:
1. Verifica que la sugerencia se alinea con la filosofía del proyecto (**SHIPPING > PERFECCIÓN**)
2. Asegúrate que no viola la regla **Anti-Feature Creep**
3. Crea un issue con el template de Feature Request

**Template de Feature Request:**
```markdown
**¿Resuelve un problema? Descríbelo:**
[Problema claro que resuelve]

**Solución Propuesta:**
[Descripción de la solución]

**Alternativas Consideradas:**
[Otras soluciones evaluadas]

**¿Es Crítico para MVP?**
[Sí/No y justificación]

**Alineación con Filosofía:**
- [ ] Mantiene SHIPPING > PERFECCIÓN
- [ ] No viola Anti-Feature Creep
- [ ] Tiene tests críticos definidos
- [ ] Documentación clara del cambio
```

---

## Configuración del Entorno

### Requisitos Previos

- Python 3.12+
- PostgreSQL 16 con extensión `btree_gist`
- Redis 7
- Docker + Docker Compose
- Git

### Setup Local

```bash
# 1. Fork y clone
git clone https://github.com/TU_USUARIO/SIST_CABANAS_MVP.git
cd SIST_CABANAS_MVP

# 2. Configurar Python virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o .venv\Scripts\activate  # Windows

# 3. Instalar dependencias
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si existe

# 4. Instalar pre-commit hooks (RECOMENDADO)
pip install pre-commit
pre-commit install
# Esto validará automáticamente el código antes de cada commit

# 5. Configurar .env
cp .env.template .env
# Editar .env con valores de desarrollo

# 6. Levantar servicios
docker-compose up -d postgres redis

# 7. Ejecutar migraciones
docker-compose exec api alembic upgrade head

# 8. Verificar instalación
pytest tests/ -v

# 9. Verificar pre-commit (opcional)
pre-commit run --all-files
```

### Pre-commit Hooks

El proyecto usa `pre-commit` para validar automáticamente:
- Formato de código (Black, isort)
- Linting (Flake8)
- Seguridad (Bandit)
- Sintaxis (YAML, JSON, Dockerfiles)
- Conventional Commits en mensajes

Ejecutar manualmente: `pre-commit run --all-files`
Omitir en un commit específico: `git commit --no-verify` (usar con precaución)

---

## Flujo de Trabajo

### 1. Crear Branch

```bash
# Actualizar main
git checkout main
git pull origin main

# Crear branch descriptivo
git checkout -b feature/nombre-descriptivo
# o
git checkout -b fix/descripcion-bug
# o
git checkout -b docs/actualizar-readme
```

**Convención de Nombres de Branch:**
- `feature/` - Nueva funcionalidad
- `fix/` - Corrección de bug
- `refactor/` - Refactorización de código
- `docs/` - Cambios en documentación
- `test/` - Añadir o modificar tests
- `chore/` - Tareas de mantenimiento

### 2. Desarrollar con TDD

```bash
# 1. Escribir test primero (Red)
# Crear test en tests/test_nueva_feature.py

# 2. Ejecutar test (debe fallar)
pytest tests/test_nueva_feature.py -v

# 3. Implementar código mínimo (Green)
# Escribir código en app/

# 4. Ejecutar test (debe pasar)
pytest tests/test_nueva_feature.py -v

# 5. Refactorizar si es necesario (Refactor)
# Mejorar código manteniendo tests verdes
```

### 3. Validar Antes de Commit

```bash
# Tests completos
pytest tests/ -v

# Linting (si está configurado)
flake8 app/ tests/
black app/ tests/ --check

# Type checking (si está configurado)
mypy app/

# Pre-deploy check
cd ..
./scripts/pre-deploy-check.sh
```

### 4. Commit

```bash
git add .
git commit -m "feat(scope): descripción clara del cambio"
```

Ver [Convenciones de Commits](#convenciones-de-commits) más abajo.

### 5. Push y Pull Request

```bash
git push origin feature/nombre-descriptivo
```

Luego crear Pull Request en GitHub con descripción detallada.

---

## Convenciones de Código

### Python Style Guide

Seguimos [PEP 8](https://pep8.org/) con algunas adaptaciones:

```python
# ✅ Bueno
async def create_prereservation(
    accommodation_id: int,
    check_in: date,
    check_out: date,
    guests: int,
    channel: str,
    contact: str
) -> dict:
    """
    Crea una pre-reserva con lock Redis y validación de constraint.

    Args:
        accommodation_id: ID del alojamiento
        check_in: Fecha de entrada (inclusive)
        check_out: Fecha de salida (exclusive)
        guests: Número de huéspedes
        channel: Canal de origen (whatsapp|email)
        contact: Teléfono o email del huésped

    Returns:
        Dict con código de reserva, expires_at y deposit

    Raises:
        ValueError: Si las fechas son inválidas
        IntegrityError: Si hay solapamiento de fechas
    """
    lock_key = f"lock:acc:{accommodation_id}:{check_in}:{check_out}"

    # Lock Redis primero
    if not await redis.set(lock_key, "locked", ex=1800, nx=True):
        raise ValueError("En proceso o no disponible")

    try:
        # Lógica de creación...
        return result
    finally:
        await redis.delete(lock_key)


# ❌ Malo
def create_prereservation(acc_id,ci,co,g,ch,ct):  # Sin tipos
    k=f"lock:acc:{acc_id}:{ci}:{co}"  # Nombres crípticos
    # Sin docstring
    if not redis.set(k,"locked",ex=1800,nx=True):return None  # Sin espacios
```

### Imports

```python
# Orden: stdlib → third-party → local
# Cada grupo separado por línea en blanco

# stdlib
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List

# third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from redis import asyncio as aioredis

# local
from app.core.config import settings
from app.core.database import get_db
from app.models.reservation import Reservation
from app.services.reservations import ReservationService
```

### Naming Conventions

```python
# Variables y funciones: snake_case
user_id = 123
check_in_date = date.today()

async def get_reservation_by_code(code: str):
    pass

# Clases: PascalCase
class ReservationService:
    pass

class WhatsAppWebhook:
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_GUESTS = 10
LOCK_TTL_SECONDS = 1800

# Archivos: snake_case
# ✅ reservation_service.py
# ✅ whatsapp_webhook.py
# ❌ ReservationService.py
# ❌ whatsappWebhook.py
```

### Async/Await

```python
# ✅ Bueno - Async desde el principio
async def process_webhook(payload: dict):
    async with get_db() as db:
        reservation = await db.execute(
            select(Reservation).where(Reservation.id == payload["id"])
        )
        return reservation.scalar_one_or_none()

# ❌ Malo - Mezclar sync/async innecesariamente
def process_webhook(payload: dict):  # Sync wrapper
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_process(payload))
```

---

## Convenciones de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<scope>): <descripción corta>

[cuerpo opcional]

[footer opcional]
```

### Tipos Válidos

- `feat` - Nueva funcionalidad
- `fix` - Corrección de bug
- `docs` - Cambios en documentación
- `style` - Formato, espacios, etc. (no afecta funcionalidad)
- `refactor` - Refactorización sin cambio funcional
- `perf` - Mejora de performance
- `test` - Añadir o modificar tests
- `chore` - Tareas de mantenimiento, build, etc.
- `ci` - Cambios en CI/CD

### Scopes Comunes

- `reservations` - Lógica de reservas
- `whatsapp` - Integración WhatsApp
- `mercadopago` - Integración Mercado Pago
- `ical` - Import/Export iCal
- `audio` - Pipeline de audio
- `nlu` - Detección de intención
- `health` - Health checks
- `metrics` - Métricas Prometheus
- `docker` - Docker/Compose
- `scripts` - Scripts de automatización
- `docs` - Documentación general

### Ejemplos

```bash
# ✅ Buenos commits
git commit -m "feat(reservations): agregar endpoint de confirmación de reserva"
git commit -m "fix(whatsapp): corregir validación de firma HMAC SHA-256"
git commit -m "docs(readme): actualizar guía de quick start"
git commit -m "test(double-booking): agregar test de concurrencia simultánea"
git commit -m "refactor(ical): extraer lógica de deduplicación a función separada"
git commit -m "perf(reservations): optimizar query de disponibilidad con índice"

# Con cuerpo explicativo
git commit -m "feat(reservations): implementar expiración automática de pre-reservas

- Job APScheduler cada 30 segundos
- Cambia estado de pre_reserved a expired si expires_at < now
- Libera lock Redis automáticamente
- Añade métrica reservation_expired_total

Closes #42"

# ❌ Malos commits
git commit -m "fix bug"  # Sin scope, descripción vaga
git commit -m "WIP"  # Work In Progress no debe llegar a main
git commit -m "asdasd"  # Sin sentido
git commit -m "Updated files"  # Sin contexto
```

---

## Testing

### Pirámide de Tests

```
       /\
      /  \     E2E (Pocos)
     /____\
    /      \   Integration (Algunos)
   /________\
  /          \ Unit (Muchos)
 /____________\
```

### Ubicación de Tests

```
backend/tests/
├── test_reservation_service.py      # Tests unitarios del service
├── test_double_booking.py           # Tests críticos de constraint
├── test_constraint_validation.py    # Tests de validación avanzada
├── test_whatsapp_webhook.py         # Tests de webhook WhatsApp
├── test_mercadopago_webhook.py      # Tests de webhook Mercado Pago
├── test_ical_import.py              # Tests de importación iCal
├── test_audio_transcription.py      # Tests de pipeline audio
├── test_nlu.py                      # Tests de NLU
├── test_health.py                   # Tests de health checks
├── test_metrics.py                  # Tests de métricas
└── conftest.py                      # Fixtures compartidas
```

### Tests Obligatorios

**Antes de cualquier PR, estos tests DEBEN pasar:**

```bash
# 1. Tests unitarios (SQLite fallback)
pytest tests/ -v

# 2. Tests de constraint (requiere Postgres real)
docker-compose up -d postgres redis
export TEST_DATABASE_URL=postgresql+asyncpg://alojamientos:password@localhost:5432/alojamientos_test_db
pytest tests/test_double_booking.py tests/test_constraint_validation.py -v

# 3. Coverage mínimo 80%
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
```

### Escribir Buenos Tests

```python
# ✅ Bueno - Descriptivo, completo, aislado
@pytest.mark.asyncio
async def test_create_prereservation_with_valid_dates_succeeds():
    """Pre-reserva con fechas válidas debe crearse exitosamente."""
    # Arrange
    accommodation_id = 1
    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)

    # Act
    result = await reservation_service.create_prereservation(
        accommodation_id=accommodation_id,
        check_in=check_in,
        check_out=check_out,
        guests=2,
        channel="whatsapp",
        contact="+5491112345678"
    )

    # Assert
    assert result["code"].startswith("RES")
    assert result["expires_at"] > datetime.now()
    assert result["deposit"] > 0
    assert result["total_price"] > 0


# ❌ Malo - Sin contexto, sin asserts claros
async def test_reservation():
    r = await create(1, date.today(), date.today() + timedelta(1), 2, "wa", "123")
    assert r
```

### Tests Críticos (NUNCA Skipear)

1. **Anti-Doble-Booking:**
   ```python
   async def test_overlapping_reservation_blocked()
   async def test_concurrent_reservations_only_one_succeeds()
   ```

2. **Validación de Firmas:**
   ```python
   async def test_whatsapp_invalid_signature_returns_403()
   async def test_mercadopago_tampered_payload_rejected()
   ```

3. **Locks Redis:**
   ```python
   async def test_redis_lock_prevents_double_reservation()
   async def test_lock_released_after_error()
   ```

4. **Expiración Pre-Reservas:**
   ```python
   async def test_expired_prereservation_cannot_be_confirmed()
   async def test_expiration_job_updates_status()
   ```

---

## Documentación

### Docstrings

Usamos formato Google:

```python
async def calculate_total_price(
    base_price: float,
    check_in: date,
    check_out: date,
    guests: int,
    season_multiplier: float = 1.0
) -> float:
    """
    Calcula el precio total de una reserva con multiplicadores.

    Args:
        base_price: Precio base por noche del alojamiento
        check_in: Fecha de entrada (inclusive)
        check_out: Fecha de salida (exclusive)
        guests: Número de huéspedes
        season_multiplier: Multiplicador de temporada (default: 1.0)

    Returns:
        Precio total calculado incluyendo todos los multiplicadores

    Raises:
        ValueError: Si check_out <= check_in o guests <= 0

    Example:
        >>> calculate_total_price(100.0, date(2025, 1, 1), date(2025, 1, 3), 2)
        200.0
    """
    if check_out <= check_in:
        raise ValueError("check_out debe ser posterior a check_in")

    nights = (check_out - check_in).days
    total = base_price * nights * season_multiplier

    return total
```

### README de Features

Cada feature compleja debe tener su README:

```
backend/app/services/ical/
├── __init__.py
├── importer.py
├── exporter.py
└── README.md  # ← Explicación de la feature
```

### ADRs (Architecture Decision Records)

Para decisiones arquitectónicas importantes, crear ADR:

```
docs/adr/
├── README.md
├── ADR-001-no-pms-externo.md
└── ADR-002-postgres-exclude-gist.md  # ← Nueva decisión
```

---

## Pull Requests

### Antes de Crear PR

- [ ] Todos los tests pasan (`pytest tests/ -v`)
- [ ] Coverage > 80% (`pytest --cov=app`)
- [ ] Lint y format ok (`flake8`, `black --check`)
- [ ] Commits siguen convención
- [ ] Branch actualizado con `main`
- [ ] Documentación actualizada
- [ ] CHANGELOG.md actualizado (si aplica)

### Template de PR

```markdown
## Descripción

[Descripción clara de los cambios]

## Tipo de Cambio

- [ ] Bug fix (cambio que corrige un issue)
- [ ] Nueva funcionalidad (cambio que añade funcionalidad)
- [ ] Breaking change (cambio que rompe compatibilidad)
- [ ] Documentación
- [ ] Refactorización

## ¿Cómo se Probó?

[Descripción de los tests realizados]

## Checklist

- [ ] Tests añadidos/actualizados
- [ ] Documentación actualizada
- [ ] CHANGELOG.md actualizado
- [ ] Commits siguen convención
- [ ] No hay warnings en tests
- [ ] Coverage > 80%

## Screenshots (si aplica)

[Imágenes o logs relevantes]

## Issues Relacionados

Closes #[número]
Relates to #[número]
```

### Proceso de Review

1. **Auto-review:** Revisa tu propio código antes de pedir review
2. **CI checks:** Espera que pasen los checks de GitHub Actions
3. **Review:** Al menos 1 aprobación requerida
4. **Cambios:** Responde a comentarios y actualiza
5. **Merge:** Squash and merge (mantiene historia limpia)

### Criterios de Aprobación

- ✅ Tests pasan
- ✅ Código sigue convenciones
- ✅ Documentación clara
- ✅ Sin feature creep
- ✅ Alineado con filosofía del proyecto
- ✅ Performance aceptable
- ✅ Seguridad validada

---

## Preguntas Frecuentes

**Q: ¿Puedo usar una librería nueva?**
A: Solo si es estrictamente necesaria. Evitar dependencias innecesarias.

**Q: ¿Debo añadir tests para un bugfix pequeño?**
A: Sí. Siempre. El test previene regresión.

**Q: ¿Puedo refactorizar código existente?**
A: Solo si los tests existentes pasan y no cambias funcionalidad.

**Q: ¿Cuándo crear un ADR?**
A: Para decisiones arquitectónicas que afectan el diseño general del sistema.

**Q: ¿Qué hacer si mi PR está bloqueado mucho tiempo?**
A: Comentar en el PR mencionando a los reviewers. Si no hay respuesta en 2 días, contactar por otro canal.

---

## Recursos Adicionales

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pytest Async](https://pytest-asyncio.readthedocs.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**¡Gracias por contribuir! 🎉**

---

_Última actualización: 2025-10-02_
