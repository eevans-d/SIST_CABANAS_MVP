# Security Audit Checklist - Sistema MVP Alojamientos

**Versión:** 1.0
**Última Actualización:** 2 de Octubre, 2025
**Audiencia:** Security Engineers, DevOps, Tech Leads

---

## 📋 Tabla de Contenidos

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Webhook Security](#webhook-security)
4. [Data Protection](#data-protection)
5. [API Security](#api-security)
6. [Database Security](#database-security)
7. [Infrastructure Security](#infrastructure-security)
8. [Dependency Security](#dependency-security)
9. [Secrets Management](#secrets-management)
10. [Monitoring & Incident Response](#monitoring--incident-response)

---

## 🎯 Overview

Este checklist cubre los aspectos críticos de seguridad del sistema MVP de alojamientos. Debe ejecutarse:

- **Pre-Producción:** 100% completo antes de deploy
- **Mensual:** Revisión completa
- **Post-Incident:** Revisión dirigida
- **Pre-Release:** Cada nueva versión

### Severity Levels

| Level | Icon | Descripción | Action Required |
|-------|------|-------------|-----------------|
| **CRITICAL** | 🔴 | Vulnerabilidad explotable, data breach potencial | Inmediato (< 24h) |
| **HIGH** | 🟠 | Riesgo significativo, exploit complejo | Urgente (< 7 días) |
| **MEDIUM** | 🟡 | Riesgo moderado, mitigaciones disponibles | Planeado (< 30 días) |
| **LOW** | 🟢 | Riesgo menor, best practice | Backlog |

---

## 🔐 Authentication & Authorization

### A1: Admin Dashboard Access

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| JWT tokens tienen expiración (<1h) | ☐ | 🔴 | Verificar `JWT_EXPIRE_MINUTES` |
| JWT secret key es cryptographically secure (>32 chars) | ☐ | 🔴 | Verificar `JWT_SECRET_KEY` |
| Refresh tokens rotan correctamente | ☐ | 🟠 | Implementar rotación |
| Rate limiting en /login endpoint | ☐ | 🟠 | Prevenir brute force |
| 2FA disponible para admin (opcional MVP) | ☐ | 🟡 | Roadmap post-MVP |
| Passwords hasheados con bcrypt/argon2 | ☐ | 🔴 | Verificar `passlib` config |
| Session timeout configurado | ☐ | 🟡 | Frontend + backend |

**Verificación:**

```bash
# Check JWT config
grep -r "JWT_SECRET_KEY\|JWT_EXPIRE_MINUTES" .env

# Test rate limiting
for i in {1..100}; do curl -X POST http://localhost/api/v1/admin/login; done
```

---

### A2: API Authentication

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Endpoints públicos son solo lectura | ☐ | 🔴 | GET /health, /metrics |
| Webhooks validan firmas HMAC | ☐ | 🔴 | WhatsApp, Mercado Pago |
| iCal export usa tokens HMAC no-enumerable | ☐ | 🟠 | No UUIDs secuenciales |
| Rate limiting por IP habilitado | ☐ | 🟠 | 60 req/min |
| CORS configurado restrictivamente | ☐ | 🟡 | Solo origins permitidos |

**Verificación:**

```python
# Test webhook sin firma
curl -X POST http://localhost/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'
# Debe retornar 403

# Test rate limiting
ab -n 1000 -c 10 http://localhost/api/v1/reservations
# Debe retornar 429 después de límite
```

---

## 🔗 Webhook Security

### W1: WhatsApp Business API

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| X-Hub-Signature-256 validado en TODOS los requests | ☐ | 🔴 | Ver `verify_whatsapp_signature()` |
| Secret key nunca logeado | ☐ | 🔴 | Revisar logs |
| Replay attack prevention (timestamp window) | ☐ | 🟠 | Implementar ventana 5 min |
| Request body almacenado temporalmente para debugging | ☐ | 🟡 | Solo en desarrollo |
| Webhook URL es HTTPS | ☐ | 🔴 | Let's Encrypt |

**Código de Validación:**

```python
import hmac
import hashlib

def verify_whatsapp_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validar firma HMAC SHA-256 de WhatsApp"""
    if not signature.startswith("sha256="):
        return False

    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    provided = signature.removeprefix("sha256=")

    return hmac.compare_digest(expected, provided)
```

**Test:**

```bash
# Test manual de firma
echo -n '{"test":"data"}' | openssl dgst -sha256 -hmac "YOUR_SECRET"
```

---

### W2: Mercado Pago Webhooks

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| x-signature validado (ts + v1) | ☐ | 🔴 | Ver `verify_mp_signature()` |
| Timestamp drift < 5 minutos | ☐ | 🟠 | Prevenir replay attacks |
| Idempotencia por payment_id | ☐ | 🔴 | No procesar duplicados |
| Secret separado por environment (prod/staging) | ☐ | 🟠 | .env por entorno |
| Logs no contienen payment_id completo | ☐ | 🟡 | Enmascarar últimos 4 dígitos |

**Código de Validación:**

```python
def verify_mp_signature(
    x_signature: str,
    x_request_id: str,
    data_id: str,
    secret: str
) -> bool:
    """Validar x-signature de Mercado Pago"""
    parts = dict(part.split("=") for part in x_signature.split(","))
    ts = parts.get("ts")
    v1 = parts.get("v1")

    if not ts or not v1:
        return False

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, v1)
```

---

## 🛡️ Data Protection

### D1: Personal Data (GDPR/LGPD)

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Passwords nunca almacenados en plaintext | ☐ | 🔴 | Solo hashes |
| PII encriptado en DB (opcional MVP) | ☐ | 🟡 | guest_email, guest_phone |
| Logs no contienen PII | ☐ | 🟠 | Enmascarar datos sensibles |
| Backup encryption habilitado | ☐ | 🟠 | Usar `pg_dump --encrypt` |
| Data retention policy definida | ☐ | 🟡 | Eliminar reservas viejas |
| GDPR right-to-erasure implementado (opcional MVP) | ☐ | 🟡 | Endpoint DELETE /users/{id} |

**Verificación:**

```bash
# Check logs por PII
grep -r "guest_email\|guest_phone\|password" backend/logs/

# Check DB encryption
psql -c "SHOW data_checksums;"
```

---

### D2: Database Security

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| PostgreSQL user NO es superuser | ☐ | 🔴 | Usar rol limitado |
| SSL/TLS habilitado para conexiones DB | ☐ | 🟠 | `sslmode=require` |
| Connection string NO contiene password hardcoded | ☐ | 🔴 | Usar .env |
| Backup encryption configurado | ☐ | 🟠 | GPG o provider encryption |
| Row Level Security habilitada (opcional MVP) | ☐ | 🟡 | Para multi-tenancy |
| DB password rotado regularmente | ☐ | 🟡 | Cada 90 días |

**PostgreSQL Hardening:**

```sql
-- Crear usuario limitado
CREATE USER alojamientos_app WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE alojamientos TO alojamientos_app;
GRANT USAGE ON SCHEMA public TO alojamientos_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO alojamientos_app;

-- Revocar privilegios peligrosos
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON pg_user FROM PUBLIC;
```

---

## 🌐 API Security

### API1: Input Validation

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Pydantic models validan todos los inputs | ☐ | 🔴 | Ver `schemas.py` |
| SQL injection prevention (SQLAlchemy ORM) | ☐ | 🔴 | No raw SQL queries |
| XSS prevention en respuestas | ☐ | 🟠 | Sanitizar outputs |
| Path traversal prevention | ☐ | 🟠 | Validar file paths |
| Max request size limitado (10MB) | ☐ | 🟡 | Nginx `client_max_body_size` |
| Content-Type validation | ☐ | 🟡 | Solo `application/json` |

**Test SQL Injection:**

```bash
# Intentar SQL injection
curl -X POST http://localhost/api/v1/reservations/pre-reserve \
  -H "Content-Type: application/json" \
  -d '{"guest_name": "Test OR 1=1--"}'

# Debe ser sanitizado por Pydantic/SQLAlchemy
```

---

### API2: Rate Limiting & DDoS

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Global rate limit configurado | ☐ | 🟠 | 1000 req/min |
| Per-IP rate limit configurado | ☐ | 🟠 | 60 req/min |
| Per-endpoint rate limit (críticos) | ☐ | 🟡 | `/pre-reserve` más estricto |
| Fail2ban o equivalente configurado | ☐ | 🟡 | Banear IPs maliciosas |
| Cloudflare o WAF frontal (opcional) | ☐ | 🟡 | Para producción |
| Bypass para /health y /metrics | ☐ | 🔴 | No limitar monitoring |

**Verificación:**

```bash
# Test rate limiting
ab -n 1000 -c 50 http://localhost/api/v1/reservations

# Verificar logs de límites excedidos
grep "rate_limit_exceeded" backend/logs/*.json
```

---

### API3: HTTPS & Transport Security

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| HTTPS habilitado (Let's Encrypt) | ☐ | 🔴 | Nginx SSL config |
| HTTP redirige a HTTPS (301) | ☐ | 🔴 | Nginx redirect |
| HSTS header configurado | ☐ | 🟠 | `Strict-Transport-Security` |
| SSL Labs score A o superior | ☐ | 🟡 | Test en ssllabs.com |
| Certificate auto-renewal configurado | ☐ | 🟠 | Certbot cron |
| TLS 1.2+ solamente (no TLS 1.0/1.1) | ☐ | 🟠 | Nginx `ssl_protocols` |

**Nginx SSL Config:**

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # ...resto de config
}

# Redirect HTTP -> HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 🔧 Infrastructure Security

### I1: Docker & Container Security

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Containers corren como non-root user | ☐ | 🟠 | `USER` en Dockerfile |
| Images escaneadas por vulnerabilidades | ☐ | 🟡 | Trivy, Snyk, o Grype |
| Base images oficiales y actualizadas | ☐ | 🟠 | `python:3.12-slim` |
| Secrets NO en Dockerfile | ☐ | 🔴 | Usar Docker secrets o .env |
| Network isolation configurado | ☐ | 🟡 | Docker networks separadas |
| Read-only filesystem donde sea posible | ☐ | 🟡 | `--read-only` flag |

**Dockerfile Seguro:**

```dockerfile
FROM python:3.12-slim

# Crear usuario non-root
RUN useradd -m -u 1000 appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

RUN pip install --no-cache-dir -r requirements.txt

# Cambiar a usuario non-root
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

**Scan de Vulnerabilidades:**

```bash
# Trivy scan
trivy image sistema-alojamientos:latest

# Grype scan
grype sistema-alojamientos:latest
```

---

### I2: Server Hardening

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| UFW/iptables firewall activo | ☐ | 🟠 | Solo puertos necesarios |
| SSH key-only authentication | ☐ | 🔴 | Deshabilitar password auth |
| Fail2ban configurado | ☐ | 🟡 | Ban IPs maliciosas |
| Automatic security updates habilitadas | ☐ | 🟠 | `unattended-upgrades` |
| Non-root user para deployments | ☐ | 🟠 | No usar root |
| Logs centralizados | ☐ | 🟡 | Syslog, Loki, o ELK |

**UFW Config:**

```bash
# Permitir solo puertos necesarios
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

---

## 📦 Dependency Security

### DEP1: Python Dependencies

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| requirements.txt con versiones fijas | ☐ | 🟠 | No `>=`, usar `==` |
| Safety check ejecutado regularmente | ☐ | 🟠 | `safety check` |
| Dependabot/Renovate configurado | ☐ | 🟡 | Auto-update PRs |
| Bandit scan en pre-commit | ☐ | 🟠 | Detectar issues seguridad |
| Auditar nuevas dependencias antes de agregar | ☐ | 🟡 | Revisar maintainers |

**Verificación:**

```bash
# Safety check
pip install safety
safety check -r requirements.txt

# Bandit scan
bandit -r backend/app/ -ll

# Outdated packages
pip list --outdated
```

---

### DEP2: Known Vulnerabilities

| Check | Status | Severity | CVE | Fix |
|-------|--------|----------|-----|-----|
| FastAPI actualizado | ☐ | 🟡 | - | 0.115+ |
| SQLAlchemy actualizado | ☐ | 🟡 | - | 2.0.35+ |
| httpx actualizado | ☐ | 🟡 | - | 0.27+ |
| Redis-py actualizado | ☐ | 🟡 | - | 5.0+ |
| Cryptography actualizado | ☐ | 🟠 | - | 43.0+ |

**Auto-Update con Dependabot:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "security"
```

---

## 🔑 Secrets Management

### S1: Environment Variables

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| .env NO commiteado a Git | ☐ | 🔴 | `.gitignore` verificado |
| .env.template sin valores reales | ☐ | 🔴 | Solo placeholders |
| Secrets rotados regularmente | ☐ | 🟡 | Cada 90 días |
| Secrets diferentes por environment | ☐ | 🟠 | prod != staging |
| Vault o similar para producción (opcional MVP) | ☐ | 🟡 | HashiCorp Vault, AWS Secrets Manager |

**Verificación:**

```bash
# Check .env no commiteado
git log --all --full-history -- "**/.env"
# Debe estar vacío

# Check secrets en código
git grep -i "password\|secret\|api_key" -- '*.py'
# Solo debe mostrar variables, no valores
```

---

### S2: Secrets in Logs

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Logs no contienen passwords | ☐ | 🔴 | Grep en logs |
| Logs no contienen API keys | ☐ | 🔴 | Grep en logs |
| Logs no contienen tokens JWT completos | ☐ | 🟠 | Enmascarar |
| Request bodies sanitizados en logs | ☐ | 🟡 | Filtrar campos sensibles |

**Structlog Sanitizer:**

```python
import structlog

def sanitize_event(logger, method_name, event_dict):
    """Sanitizar campos sensibles en logs"""
    sensitive_fields = ["password", "api_key", "secret", "token"]

    for field in sensitive_fields:
        if field in event_dict:
            event_dict[field] = "***REDACTED***"

    return event_dict

structlog.configure(
    processors=[
        sanitize_event,
        structlog.processors.JSONRenderer()
    ]
)
```

---

## 📊 Monitoring & Incident Response

### M1: Security Monitoring

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Failed login attempts monitoreados | ☐ | 🟠 | Alertar > 10/min |
| Rate limit exceeds monitoreados | ☐ | 🟡 | Dashboard Prometheus |
| Webhook signature failures alertados | ☐ | 🟠 | >5% = alerta |
| Database connection errors alertados | ☐ | 🟠 | Prometheus alert |
| Disk space monitoreado | ☐ | 🟠 | Alertar < 20% libre |
| SSL certificate expiration monitoreada | ☐ | 🟠 | Alertar < 30 días |

**Prometheus Alerts:**

```yaml
# alerts.yml
groups:
  - name: security
    rules:
      - alert: HighFailedLoginRate
        expr: rate(login_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High failed login rate detected"

      - alert: WebhookSignatureFailures
        expr: rate(webhook_signature_failures_total[5m]) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Multiple webhook signature validation failures"
```

---

### M2: Incident Response

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| Incident response plan documentado | ☐ | 🟠 | Ver `INCIDENT_RESPONSE.md` |
| Contactos de emergencia actualizados | ☐ | 🟡 | Slack, email, phone |
| Backup recovery procedure testeado | ☐ | 🟠 | Ultimo test: ________ |
| Rollback procedure documentado | ☐ | 🟠 | `make rollback` |
| Post-mortem template preparado | ☐ | 🟡 | Docs folder |

**Quick Incident Response:**

```bash
# 1. Identificar issue
tail -f /var/log/app/*.log | grep -i "error\|critical"

# 2. Rollback si es necesario
git revert HEAD
docker-compose down && docker-compose up -d

# 3. Restore DB si corrupto
make restore BACKUP_FILE=backup_2025-10-01.sql

# 4. Notificar stakeholders
# (usar canal Slack #incidents)

# 5. Documentar en post-mortem
```

---

## ✅ Pre-Production Checklist

Antes de deploy a producción, **TODOS** los items críticos (🔴) deben estar verificados:

### Critical (🔴) - MUST FIX

- [ ] JWT secret key seguro (>32 chars)
- [ ] Passwords hasheados (bcrypt/argon2)
- [ ] Webhook signatures validadas (WhatsApp, MP)
- [ ] HTTPS habilitado (Let's Encrypt)
- [ ] HTTP → HTTPS redirect configurado
- [ ] PostgreSQL user NO es superuser
- [ ] SSL/TLS para conexiones DB
- [ ] Connection strings en .env (no hardcoded)
- [ ] .env NO commiteado a Git
- [ ] Logs no contienen passwords/API keys
- [ ] Pydantic validation en todos los inputs
- [ ] SQLAlchemy ORM (no raw SQL)
- [ ] SSH key-only authentication
- [ ] Secrets NO en Dockerfile
- [ ] Bypass rate limiting para /health y /metrics

### High (🟠) - SHOULD FIX

- [ ] Rate limiting en /login
- [ ] Replay attack prevention (timestamps)
- [ ] Idempotencia webhooks MP
- [ ] Logs no contienen PII
- [ ] Backup encryption
- [ ] Global + per-IP rate limiting
- [ ] HSTS header configurado
- [ ] TLS 1.2+ solamente
- [ ] Containers non-root user
- [ ] Base images actualizadas
- [ ] UFW/iptables firewall activo
- [ ] Automatic security updates
- [ ] requirements.txt versiones fijas
- [ ] Safety + Bandit checks
- [ ] Security monitoring alerts

### Medium (🟡) - NICE TO HAVE

- [ ] 2FA para admin (post-MVP)
- [ ] iCal tokens HMAC
- [ ] Data retention policy
- [ ] Per-endpoint rate limits
- [ ] SSL Labs score A+
- [ ] Images scan (Trivy/Grype)
- [ ] Dependabot configurado
- [ ] Vault para secrets (opcional)
- [ ] Post-mortem template

---

## 🔗 Referencias

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Última Auditoría:** __________________
**Auditor:** __________________
**Score:** ____/100
**Próxima Auditoría:** __________________

---

**Mantenido por:** Sistema MVP Alojamientos Contributors
**Versión:** 1.0
**Última Actualización:** 2 de Octubre, 2025
