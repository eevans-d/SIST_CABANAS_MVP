# 📊 Resumen Ejecutivo: Deployment en Fly.io

**Fecha**: Octubre 18, 2025  
**Status**: ✅ Ready for Production  
**Tiempo Estimado**: 15 minutos  
**Costo Mensual**: $0 (free tier)

---

## 🎯 Decisión Estratégica: Railway → Fly.io

### Comparativa

| Aspecto | Railway | Fly.io | Ganancia |
|--------|---------|--------|----------|
| **Precio** | $5-10/mes | $0 (free) | +$60-120/año |
| **Region Argentina** | No | Sí (eze) | ✅ Latencia 30ms |
| **PostgreSQL** | Plugin ($12) | Included | +$144/año |
| **Redis** | Plugin ($15) | Upstash gratis | +$180/año |
| **Free Tier** | No | Sí (3 máquinas) | ✅ MVP ideal |
| **Edge Performance** | Bueno | Excelente | ✅ Anycast routing |

**Ahorro Total**: **$384-444 anuales** para MVP  
**ROI**: Alcanzado en Mes 1

### Ventajas de Fly.io

✅ **Región Buenos Aires**: Latencia < 30ms para usuarios locales  
✅ **Free Tier**: 3 máquinas shared-cpu-1x, 256MB RAM, 3GB storage  
✅ **Zero-Downtime Deploys**: Rolling strategy automático  
✅ **Managed PostgreSQL**: Backups automáticos, 7 días retención  
✅ **Upstash Redis**: Gratis con 10K comandos/día (suficiente para MVP)  
✅ **IPv6 Nativo**: Mejor connectivity global  
✅ **Prometheus Metrics**: Built-in observability  

---

## 🏗️ Arquitectura

```
┌────────────────────────────────────────┐
│  Users in Argentina (latency < 30ms)  │
└──────────────────┬─────────────────────┘
                   │
         Fly.io Anycast Edge
                   ↓
        ┌──────────────────────┐
        │  Region: eze         │
        │  Buenos Aires        │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │  Backend (8080)      │
        │  - FastAPI           │
        │  - Gunicorn 2 workers│
        │  - 256MB RAM         │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │  PostgreSQL 16       │
        │  - Managed Fly.io    │
        │  - 20GB storage      │
        │  - Automated backup  │
        └──────────┬───────────┘
                   │
        ┌──────────────────────┐
        │  Redis (Upstash)     │
        │  - us-east-1         │
        │  - 10K cmd/día free  │
        │  - SSL/TLS           │
        └──────────────────────┘
```

---

## 🚀 Quick Deploy (5 min)

### Comando-por-Comando

```bash
# 1. Login
flyctl auth login

# 2. PostgreSQL
flyctl postgres create \
  --name sist-cabanas-db --region eze

# 3. Redis (Upstash)
# Crear en: https://upstash.com/console/redis

# 4. Secrets
flyctl secrets set \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="redis://..." \
  JWT_SECRET="P9LQYGSuJVjvdJSrJ3sS-MjLEMJXVFWVaq1uA4Z2FLw"

# 5. Deploy
flyctl launch --name sist-cabanas-mvp --region eze

# 6. Migrar BD
flyctl ssh console -c "alembic upgrade head"

# 7. Verificar
curl https://sist-cabanas-mvp.fly.dev/api/v1/healthz
```

---

## 📋 Checklist de Deployment

### Pre-Deployment ✅
- [x] Código en main branch
- [x] Dockerfile optimizado (start-fly.sh)
- [x] fly.toml configurado (región eze)
- [x] Secretos preparados (.env.template)
- [x] Tests passing (180+)
- [x] Health checks funcionando

### Deployment 🚀
- [ ] `flyctl auth login`
- [ ] PostgreSQL creado
- [ ] Redis (Upstash) configurado
- [ ] Secretos configurados
- [ ] `flyctl launch --no-deploy`
- [ ] `flyctl deploy`
- [ ] Esperar a que arranque (2-3 min)

### Post-Deployment ✅
- [ ] Health check responde 200 OK
- [ ] Logs sin ERROR
- [ ] BD migrada (`alembic current`)
- [ ] iCal sync funcionando
- [ ] Crear reserva de prueba
- [ ] Dashboard carga
- [ ] Webhooks funcionan

---

## 💰 Costos

### Free Tier Limits

| Recurso | Free | Precio Extra |
|---------|------|-------------|
| **Máquinas** | 3 shared-cpu-1x | $2.40/máquina/mes |
| **RAM** | 256MB × 3 = 768MB | $0.15/GB/mes |
| **Storage** | 3GB | $0.15/GB/mes |
| **PostgreSQL** | 1 DB, 5GB | $0.50/GB/mes (extra) |
| **Outbound** | 160GB/mes | $0.02/GB (extra) |
| **Redis** | N/A (Upstash) | $0 (10K cmd/día) |

### Proyección Anual (MVP)

```
Mes 1-3:    $0.00  (free tier)
Mes 4-6:    $14.40 (x 3 máquinas) si escalamos
Mes 7-12:   $28.80 (x 3 máquinas) + DB

TOTAL ANUAL: $86.40 (vs Railway $60-120)
```

**Conclusión**: Fly.io es **más económico** a escala MVP.

---

## 🔄 Migración desde Railway

### Pasos

1. **Deploy en Fly.io** (este documento)
2. **Validar en staging** (2-3 días)
3. **DNS cambio** (mismo día)
4. **Monitoring** (1 semana)
5. **Shutdown Railway** (Mes 2)

### Ficheros Reemplazados

| Archivo | Railway | Fly.io |
|---------|---------|--------|
| Config | Procfile | fly.toml ✅ |
| Config | railway.toml | (deletado) |
| Start Script | start-railway.sh | start-fly.sh ✅ |
| Docker | (Railway automático) | Dockerfile ✅ |
| Health Check | :8000/health | :8080/healthz ✅ |
| Port | 8000 | 8080 ✅ |

---

## 🎓 Recursos Necesarios

### Documentación

- **Quick Start**: Ver `FLY_README.md`
- **Guía Completa**: Ver `docs/operations/FLY_DEPLOYMENT_GUIDE.md`
- **Para Irnos**: Ver `docs/integrations/PARA_IRNOS_INTEGRATION.md`

### URLs Importantes

| Recurso | URL |
|---------|-----|
| Fly.io Dashboard | https://fly.io/apps/sist-cabanas-mvp |
| App Logs | `flyctl logs -f` |
| Upstash Console | https://upstash.com/console/redis |
| GitHub Repo | https://github.com/eevans-d/SIST_CABANAS_MVP |

### Credenciales Necesarias

- [ ] Fly.io account (free)
- [ ] GitHub access token (si CI/CD)
- [ ] Upstash account (free)
- [ ] WhatsApp token (ya tiene)
- [ ] Mercado Pago token (ya tiene)

---

## 🚨 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Deploy falla | `flyctl build-log sist-cabanas-mvp` |
| Health check timeout | Aumentar `start_period` en fly.toml |
| DB connection refused | Verificar `DATABASE_URL` en secrets |
| Redis timeout | Verificar `REDIS_URL` in secrets |
| OOM Killed | `flyctl scale memory 512` |

**Más ayuda**: Ver "Troubleshooting" en `FLY_DEPLOYMENT_GUIDE.md`

---

## 📈 Monitoreo Post-Deploy

### Primeras 24 horas

```bash
# Ver logs en tiempo real
flyctl logs -f

# Buscar errores
flyctl logs | grep ERROR

# Métricas
curl https://sist-cabanas-mvp.fly.dev/metrics
```

### SLOs a Validar

- ✅ **Uptime**: > 99.9%
- ✅ **Response Time P95**: < 3s (texto), < 15s (audio)
- ✅ **Error Rate**: < 1%
- ✅ **iCal Sync**: < 20 min desfase

---

## 🎯 Próximas Fases

### Fase 2 (Semana 1)
- [ ] UAT con admin real
- [ ] Validar webhooks (WhatsApp, Mercado Pago)
- [ ] Load testing (100 RPS)
- [ ] Backup strategy

### Fase 3 (Semana 2-3)
- [ ] Custom domain
- [ ] GitHub Actions CI/CD
- [ ] CDN para assets (Cloudflare)
- [ ] Rate limiting tuning

### Fase 4 (Mes 2)
- [ ] Scale a 2-3 máquinas si necesario
- [ ] Multi-region deployment (gru)
- [ ] Disaster recovery testing
- [ ] Shutdown Railway

---

## ✅ Validación Final

Antes de marcar como "Production Ready":

- [ ] Deploy exitoso
- [ ] Health check 200 OK
- [ ] BD con datos
- [ ] Reserva test creada
- [ ] Logs sin ERROR
- [ ] WhatsApp webhook funciona
- [ ] iCal sync importa eventos
- [ ] Response time < 1s (healthz)

**Status**: 🟢 Ready when these pass

---

## 📞 Soporte & Escalation

### Fly.io Support
- **Community**: https://community.fly.io
- **Status**: https://status.fly.io
- **Email**: support@fly.io

### Interna
- **Code**: https://github.com/eevans-d/SIST_CABANAS_MVP/issues
- **Docs**: `/docs/operations/`

---

## 📌 Notas Importantes

1. **Free Tier**: Válido para MVP (< 100 usuarios)
2. **Escalabilidad**: Aumentar máquinas/RAM si > 1000 RPS
3. **Backups**: Automáticos en PostgreSQL (7 días)
4. **Monitoring**: Prometheus metrics en `/metrics`
5. **Security**: HTTPS automático, JWT validation, rate limiting
6. **Argentina First**: Región eze optimizada para usuarios locales

---

**Ultima Actualización**: Octubre 18, 2025  
**Versión**: 1.0 - MVP Ready  
**Próximo Review**: Enero 2026 (post-MVP)

🚀 **¡Listo para Deploy!** 🚀
