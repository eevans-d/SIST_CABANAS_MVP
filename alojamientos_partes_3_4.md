# Sistema de Alojamientos - Parte 3 y 4
## Implementación, DevOps, Calidad y Diseño Conversacional

---

## Parte 3: Implementación, DevOps y Calidad

### 1) Hoja de ruta de implementación (10–12 días)

**Día 1 — Fundaciones e Infra**
- VPS Ubuntu 22.04/24.04 (2 vCPU, 4 GB RAM), DNS apuntando al servidor
- Seguridad base: usuario no root, UFW (22, 80, 443), fail2ban
- Repo inicial con estructura, .env.template y Makefile
- Docker/Compose instalado; compose up con Postgres, Redis y API "hello"
- Nginx reverse proxy con SSL (Let's Encrypt) o Caddy
- **Entregables:** docker-compose.yml, nginx.conf/caddyfile, /healthz de API

**Día 2 — Datos y migraciones**
- SQLAlchemy modelos y Alembic inicial (tablas: accommodations, reservations, availability_calendar, payment_records, conversations, messages, imported_blocks, pricing_rules, domain_events)
- Constraint anti-solape en Postgres con daterange + gist
- Semillas mínimas: 2–3 alojamientos, reglas de precio base
- **Entregables:** Alembic revision inicial, script seed de datos demo

**Día 3 — WhatsApp Cloud (webhook + envío)**
- Webhook GET verificación (verify_token), POST recepción con validación X-Hub-Signature-256
- Normalizador de mensajes a contrato unificado
- Cliente de envío de texto (sesión de 24h)
- **Entregables:** Endpoint /webhooks/whatsapp, servicio whatsapp_client

**Día 4 — Audio STT y NLU básico**
- FFmpeg en contenedor, faster-whisper/whisper base
- Transcripción de OGG/Opus a texto; umbral de confianza con fallback
- NLU: intents/entidades con spaCy + reglas (fecha, huéspedes)
- **Entregables:** Servicio audio_pipeline, detect_intent y extract_entities

**Día 5 — Calendario y pricing**
- Servicio de disponibilidad: combina availability_calendar + imported_blocks + reservas
- Pricing engine: base_price * multiplicadores (fin de semana, feriados) + min_stay
- iCal export: endpoint ICS por unidad
- **Entregables:** /ical/accommodation/{id}/{token}.ics, check_availability y calc_total

**Día 6 — iCal import + jobs**
- Importadores por plataforma (URL configurable por unidad)
- APScheduler para polling cada 15 min; dedupe con imported_blocks
- Resolución de conflictos por prioridad de fuente
- **Entregables:** Job import_ical, métricas de último fetch

**Día 7 — Pre-reserva + locks Redis**
- Create pre-reservation con lock Redis (SET NX EX 1800)
- Insert en DB con exclusión; manejo de violación de constraint
- Extensión de lock (+900s) una sola vez; expiración automática
- **Entregables:** /pre-reserve endpoint y flujo integrado

**Día 8 — Pagos Mercado Pago**
- Preferencias con external_reference=reservation_code; webhook /webhooks/mercadopago
- Idempotencia: uniq mp_payment_id; verificación server-to-server
- Confirmación de reserva: paid + confirmed; liberar lock; actualizar iCal
- **Entregables:** mp_client, webhook handler, tests de webhook

**Día 9 — Dashboard staff**
- Bootstrap/Alpine: conversaciones activas, pre-reservas por vencer, calendario
- Acciones: confirmar pago, extender pre-reserva, escalar conversación
- **Entregables:** /admin/dashboard y acciones POST

**Día 10 — Calidad y observabilidad**
- Logs JSON, trace-id; métricas Prometheus (latencia, errores)
- Healthz ampliado (DB/Redis/WA/MP/iCal age)
- Pruebas E2E: flujo completo WA → pre-reserva → pago → confirmación

### 2) Infraestructura como código (IaC)

**Estructura de repo sugerida:**
```
- backend/
  - app/ (main.py, core/, routers/, services/, models/, jobs/, utils/)
  - alembic/ (migrations)
  - requirements.txt, Dockerfile
- nginx/ (nginx.conf)
- compose/ (docker-compose.yml, .env.template)
- scripts/ (deploy.sh, backup.sh, restore.sh, seed_demo.sh)
- tests/ (unit/, integration/, e2e/, k6/)
- Makefile, .github/workflows/ci.yml
```

**Dockerfile backend (ejemplo slim):**
```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.prod.yml (resumen):**
```yaml
version: "3.9"
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL","pg_isready -U ${DB_USER} -d ${DB_NAME}"]

  redis:
    image: redis:7-alpine
    command: ["redis-server","--appendonly","yes","--requirepass","${REDIS_PASS}"]

  api:
    build:
      context: ..
      dockerfile: backend/Dockerfile
    env_file: .env
    depends_on: [postgres, redis]
    ports: ["8000:8000"]

  nginx:
    image: nginx:alpine
    volumes:
      - ../nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports: ["80:80", "443:443"]
    depends_on: [api]
```

**.env.template (clave):**
```
BASE_URL=https://tu-dominio.com
DB_NAME=alojamientos
DATABASE_URL=postgresql+psycopg://alojamientos:superseguro@postgres:5432/alojamientos
REDIS_URL=redis://:superredis@redis:6379/0
WHATSAPP_ACCESS_TOKEN=...
MP_ACCESS_TOKEN=...
SMTP_HOST=smtp.gmail.com
DASHBOARD_JWT_SECRET=...
ICS_SALT=random-hex
```

### 3) CI/CD (GitHub Actions)

**.github/workflows/ci.yml:**
```yaml
name: CI-CD
on:
  push: { branches: ["main"] }
  pull_request: { branches: ["main"] }

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov ruff mypy
          ruff check backend
          mypy backend --ignore-missing-imports
          pytest -q --cov=backend

  docker:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} -f backend/Dockerfile .
      - uses: aquasecurity/trivy-action@0.20.0
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          severity: 'HIGH,CRITICAL'

  deploy:
    needs: docker
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SSH_HOST }}
          script: |
            cd /opt/alojamientos
            git pull --rebase
            docker compose up -d --build
            docker compose exec -T api alembic upgrade head
```

### 4) Testing y Observabilidad

**Unit tests (pytest):**
```python
def test_lock_prevents_double_booking(lock_manager):
    ok = lock_manager.create("1","2024-12-15","2024-12-18","549351...")
    assert ok is True
    again = lock_manager.create("1","2024-12-15","2024-12-18","549351...")
    assert again is False
```

**Métricas y logs:**
- Instrumentación con prometheus-fastapi-instrumentator
- JSON logs con request_id, user, endpoint, status, latency_ms
- /healthz → { db, redis, whatsapp, mp, ical_age }
- Alertas críticas: WhatsApp down > 5 min, MP webhook fallando

**Backups:**
```bash
#!/usr/bin/env bash
DATE=$(date +%F_%H%M)
docker compose exec -T postgres pg_dump -U ${DB_USER} ${DB_NAME} | gzip > /opt/backups/pg_${DATE}.sql.gz
```

---

## Parte 4: Diseño Conversacional, NLU/STT/TTS y Dashboard

### 1) Diseño conversacional

**Persona del agente:**
- Recepcionista virtual experto, cálido, resolutivo, tono argentino (vos/ustedes)
- Claro y corto: un mensaje resuelve un paso con CTA
- Evitar "no" directo: proponer alternativa ("Podemos ofrecerte…")
- Emojis moderados: ✅⏰📅🏠💳📍

**Contexto y memoria:**
- Slots por sesión: check_in, check_out, guests, unit_preferida
- Caducar sesión inactiva: 12h
- Quiet hours: 21:00–08:00

**Escalamiento humano:**
- Triggers: reclamos, pagos rechazados 2 veces, STT < 0.6
- "Te derivo a un humano en minutos y seguimos por acá"

### 2) Intents, entidades y slot filling

**Intents:** disponibilidad, precio, reservar, servicios, políticas, ubicación, cancelar_modificar, saludo, fallback, hablar_humano

**Entidades:**
- fechas: check_in, check_out (DD/MM/AAAA; "este finde"; feriados AR)
- huéspedes: número de personas, adultos/niños
- tipo_unidad: cabaña, departamento, casa
- preferencias: wifi, pileta, pet-friendly, cochera

**Slot filling:**
- Requeridos: check_in, check_out, guests
- "¿Para qué fechas te querés alojar? Día de entrada y salida"
- "¿Para cuántas personas sería?"

### 3) NLU (spaCy + reglas + dateparser)

**Pipeline propuesto:**
```python
import dateparser, re
from datetime import date, timedelta

def parse_dates(text):
    # "este finde": sábado-domingo próximos
    if "finde" in text or "fin de semana" in text:
        today = date.today()
        offset = (5 - today.weekday()) % 7  # 5=sábado
        check_in = today + timedelta(days=offset)
        check_out = check_in + timedelta(days=2)
        return check_in, check_out
    
    # rangos explícitos "15/12 al 18/12"
    m = re.search(r'(\d{1,2}/\d{1,2})(?:/\d{2,4})?\s*(?:al|-|a)\s*(\d{1,2}/\d{1,2})', text)
    if m:
        d1 = dateparser.parse(m.group(1), languages=['es'])
        d2 = dateparser.parse(m.group(2), languages=['es'])
        return d1.date(), d2.date()
    return None, None

def parse_guests(text):
    m = re.search(r'(\d+)\s*(personas?|pax|hu(e|é)spedes?)', text, re.I)
    return int(m.group(1)) if m else None
```

### 4) STT/TTS (WhatsApp audio)

**STT (faster-whisper):**
- Convertir OGG/Opus a WAV PCM 16k mono
- faster-whisper modelo base: language="es", vad_filter=True
- Threshold confianza: 0.6
- Audios > 3 min → pedir texto breve

**TTS (opcional):**
- eSpeak-NG: `espeak-ng -v es-la -s 170 -w out.wav "Texto..."`
- Solo cuando huésped envía audio primero o lo solicita

### 5) Plantillas de mensajes

**Saludo:**
"¡Hola! 👋 Soy el asistente de reservas de {Nombre}. ¿Para qué fechas y cuántas personas sería el alojamiento?"

**Oferta de disponibilidad:**
"¡Sí! Del {dd/mm} al {dd/mm} para {N} personas tenemos:
- 🏠 {Unidad A} — ${precio_noche}/noche. Total ${total} por {noches} noches
- 🏠 {Unidad B} — ${precio_noche}/noche. Total ${total}
¿Querés que te la reserve por 30 min mientras decidís?"

**Pre-reserva:**
"Perfecto. Te aparto {Unidad} del {dd/mm} al {dd/mm} por 30 minutos. Seña del {porc}%: ${monto}. Te paso link de pago ⬇️"

**Confirmación:**
"✅ ¡Reserva confirmada!
Código: {RES...}
{Unidad} del {dd/mm} al {dd/mm}
Check-in: {hora} — Check-out: {hora}
Dirección: {maps_link}"

**Fallback suave:**
"Creo que entendí parte de tu consulta. ¿Podés confirmarme fechas de entrada y salida y cuántas personas son?"

### 6) Dashboard: UX y funcionalidad

**Principios UX:**
- 2 clics/10 segundos: confirmar pago, extender pre-reserva
- Estados evidentes: colores por prioridad
- Mobile-first

**Vistas principales:**
- **Home:** Métricas del día, alertas de vencimientos
- **Conversaciones:** Lista con filtros, historial, player de audio
- **Pre-reservas:** Tabla con vencimiento, extender +15 min
- **Calendario:** Vista mensual por unidad, hover con detalles
- **Configuración:** Por unidad (capacidad, precios, tokens iCal)

**Acciones rápidas (API):**
- POST /admin/reservations/{id}/confirm-payment
- POST /admin/pre-reservations/{id}/extend
- POST /admin/conversations/{id}/escalate

### 7) Posicionamiento en plataformas

**Respuesta ultrarrápida:**
- Para Irnos/AlquilerArgentina: IMAP poll 60–120s; auto-responder
- Airbnb: tasa de respuesta < 1h; disponibilidad actualizada
- Booking: responder < 24h; evitar cancelaciones

**Calendario actualizado:**
- Import cada 15 min; export inmediato tras confirmar
- Evitar "bajo consulta" prolongado

**Contenido optimizado:**
- **Para Irnos:** Tono argentino, palabras clave locales ("finde", "parrilla")
- **Booking:** Profesional, multiidioma breve (ES/EN)
- **Airbnb:** Storytelling, 20+ fotos, tips locales

### 8) Ejemplos de flujos (WhatsApp)

**Flujo corto ideal:**
- Huésped: "Hola, para 4 del 5 al 8/1"
- Bot: "Tenemos Cabaña Robles $45.000/noche (Total $135.000). ¿Te reservo por 30 min?"
- Huésped: "Cabaña"
- Bot: "Seña 30%: $40.500. Pagá acá: {link}. Vence 17:30."
- Webhook MP → Bot: "✅ Confirmado. Código RES240105001."

**Flujo con repregunta:**
- Huésped: "¿Hay libre el finde para 2?"
- Bot: "¿Te referís a este fin de semana o el siguiente?"
- Huésped: "El siguiente"
- Bot: "Perfecto: del 13 al 15/9 para 2 personas tenemos..."

### 9) Instrumentación conversacional

**Métricas útiles:**
- t_resp_text_p95, t_resp_audio_p95
- tasa_fallback (% de mensajes con repregunta)
- tasa_escalado (% conversaciones escaladas)
- conf_media_stt, conf_media_intent
- conversión consulta→pre-reserva→confirmada
- edad_ical_min (última sync)

### 10) Pasos para go-live

1. Clonar repo en /opt/alojamientos
2. Crear compose/.env desde .env.template
3. Configurar DNS a la IP del VPS
4. Obtener SSL (Caddy auto o certbot)
5. `docker compose up -d`
6. `docker compose exec api alembic upgrade head`
7. Ejecutar scripts/seed_demo.sh
8. Probar /healthz y /admin/dashboard
9. Configurar webhooks WhatsApp y Mercado Pago

---

**Runbooks de incidentes comunes:**
- **WhatsApp no recibe:** Verificar SSL, URL en Meta, firma X-Hub-Signature-256
- **Pagos no confirman:** Revisar logs webhook MP, validar payment_id
- **Doble-booking:** Confirmar constraint no_overlap_reservations activo