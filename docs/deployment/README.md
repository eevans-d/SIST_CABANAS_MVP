# 🚀 Deployment Documentation

Esta carpeta contiene toda la documentación necesaria para el despliegue del sistema a staging y producción.

---

## 📚 Documentos Disponibles

### 1. [STAGING_DEPLOY_GUIDE.md](STAGING_DEPLOY_GUIDE.md)

**Descripción:** Guía completa paso a paso para deploy a entorno staging.

**Contenido:**
- Pre-requisitos y preparación
- Provisión de servidor (DigitalOcean, AWS, Hetzner)
- Configuración inicial (Docker, firewall, fail2ban)
- Deploy de la aplicación
- Configuración de SSL con Let's Encrypt
- Verificación post-deploy
- Troubleshooting común

**Cuándo usar:**
- Primer deploy a staging
- Setup de nuevo servidor
- Onboarding de nuevo DevOps

**Tiempo estimado:** 2-3 horas

---

### 2. [ROLLBACK_PLAN.md](ROLLBACK_PLAN.md)

**Descripción:** Procedimientos de rollback organizados por severidad.

**Contenido:**
- Estrategia de rollback (SEV1, SEV2, SEV3, SEV4)
- Rollback completo (código + DB)
- Rollback parcial (solo API o configuración)
- Recuperación de datos (backup/restore)
- Checklist post-rollback
- Templates de comunicación

**Cuándo usar:**
- Deploy falló o introduce bugs críticos
- Necesitas restaurar versión anterior
- Training de equipo en procedimientos de emergencia

**Tiempo estimado:** 5-30 minutos (según severidad)

---

## 🛠️ Scripts Relacionados

Estos scripts están en `../../scripts/` pero son esenciales para deployment:

### [server-setup.sh](../../scripts/server-setup.sh)

Automatiza el setup inicial de un servidor Ubuntu 22.04:
- Actualización de sistema
- Instalación de Docker
- Configuración de firewall (UFW)
- Setup de fail2ban
- Configuración de límites del sistema

**Uso:**
```bash
# En el servidor (como root)
bash server-setup.sh
```

---

### [post-deploy-verify.sh](../../scripts/post-deploy-verify.sh)

Verifica que el deploy fue exitoso:
- Tests de infraestructura (Docker, contenedores)
- Tests de conectividad (DNS, HTTP/HTTPS)
- Tests de API (health, DB, Redis)
- Tests de seguridad (SSL, headers)
- Tests funcionales (webhooks, endpoints)

**Uso:**
```bash
# Desde tu máquina local o el servidor
bash scripts/post-deploy-verify.sh staging.alojamientos.com

# O para localhost
bash scripts/post-deploy-verify.sh localhost
```

---

### [pre-deploy-check.sh](../../scripts/pre-deploy-check.sh)

Ejecuta validaciones antes del deploy:
- Tests pasando
- Variables de entorno configuradas
- Docker disponible
- Git en branch correcto
- Backup de DB reciente

**Uso:**
```bash
bash scripts/pre-deploy-check.sh
```

---

### [deploy.sh](../../scripts/deploy.sh)

Deploy automatizado:
- Pull de código
- Build de imágenes
- Migraciones de DB
- Restart de servicios

**Uso:**
```bash
bash scripts/deploy.sh
```

---

## 📋 Workflow Recomendado

### Primera vez (Nuevo servidor)

```bash
# 1. Provisionar servidor (DigitalOcean/AWS/Hetzner)
# Ver: STAGING_DEPLOY_GUIDE.md § Provisión del Servidor

# 2. Configurar DNS
# A record: staging.alojamientos.com → <IP_SERVIDOR>

# 3. Setup inicial del servidor (como root)
ssh root@<IP_SERVIDOR>
bash server-setup.sh

# 4. Clonar repo y configurar
cd /opt/apps
git clone git@github.com:eevans-d/SIST_CABANAS_MVP.git
cd SIST_CABANAS_MVP
cp .env.template .env
nano .env  # Configurar variables

# 5. Deploy
bash scripts/pre-deploy-check.sh
bash scripts/deploy.sh

# 6. Configurar SSL
sudo certbot certonly --standalone -d staging.alojamientos.com

# 7. Verificar
bash scripts/post-deploy-verify.sh staging.alojamientos.com
```

**Tiempo total:** 2-3 horas

---

### Deploy subsecuente (Actualización)

```bash
# 1. Pre-deploy checks
bash scripts/pre-deploy-check.sh

# 2. Deploy
bash scripts/deploy.sh

# 3. Verificar
bash scripts/post-deploy-verify.sh staging.alojamientos.com

# 4. Si algo falla → Rollback
# Ver: ROLLBACK_PLAN.md
```

**Tiempo total:** 10-15 minutos

---

## 🚨 En Caso de Emergencia

### Sistema caído (SEV1)

```bash
# 1. Ver logs
docker compose logs --tail 100 api

# 2. Rollback inmediato
git checkout v0.9.9  # Último tag estable
docker compose down && docker compose up -d --build

# 3. Verificar
curl https://staging.alojamientos.com/api/v1/healthz
```

**Ver detalles:** [ROLLBACK_PLAN.md § SEV1](ROLLBACK_PLAN.md#sev1---crítico-sistema-caído)

---

### Feature rota (SEV2)

```bash
# 1. Identificar commit problemático
git log --oneline -10

# 2. Revertir commit
git revert <commit_hash> --no-edit

# 3. Redeploy
docker compose up -d --build api
```

**Ver detalles:** [ROLLBACK_PLAN.md § SEV2](ROLLBACK_PLAN.md#sev2---mayor-funcionalidad-crítica-rota)

---

## 📊 Métricas de Deployment

### Objetivos

| Métrica | Objetivo | Actual |
|---------|----------|--------|
| **Deploy time** | < 15 min | TBD |
| **Downtime** | < 30 seg | TBD |
| **Rollback time** | < 10 min | TBD |
| **Success rate** | > 95% | TBD |

---

## 🔗 Referencias

### Documentación Principal
- [README.md](../../README.md)
- [PRODUCTION_SETUP.md](../../PRODUCTION_SETUP.md)
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

### Seguridad
- [Security Audit Checklist](../security/AUDIT_CHECKLIST.md)

### Scripts
- [scripts/README.md](../../scripts/README.md)

---

## ❓ FAQ

**Q: ¿Puedo usar estos procedimientos para producción?**
A: Sí, pero ejecuta el [Security Audit Checklist](../security/AUDIT_CHECKLIST.md) completo primero.

**Q: ¿Qué hacer si el rollback falla?**
A: Restaurar desde backup de DB más reciente. Ver [ROLLBACK_PLAN.md § Recuperación de Datos](ROLLBACK_PLAN.md#recuperación-de-datos).

**Q: ¿Cómo pruebo el deploy sin afectar staging?**
A: Usa Docker Compose local con `make dev`.

**Q: ¿Necesito configurar backups automáticos?**
A: Sí, después del primer deploy. Ver [PRODUCTION_SETUP.md](../../PRODUCTION_SETUP.md).

---

**Última actualización:** 4 de Octubre, 2025
**Mantenido por:** DevOps Team
**Preguntas:** Abrir issue en GitHub
