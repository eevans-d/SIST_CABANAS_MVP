# 🚀 Deploy Dashboard Admin - Guía Rápida

## Prerequisitos

- Docker 20.10+
- Docker Compose 2.0+
- Puerto 3000 disponible para frontend
- Puerto 8000 disponible para backend

## Deploy Rápido (Staging)

### 1. Deploy Automático

```bash
./deploy-dashboard-staging.sh
```

Este script:
- ✅ Verifica prerequisitos
- ✅ Construye imagen del frontend
- ✅ Detiene contenedores existentes
- ✅ Levanta todos los servicios
- ✅ Verifica health checks

### 2. Deploy Manual

Si prefieres hacerlo paso a paso:

```bash
# 1. Crear .env del frontend (si no existe)
cp frontend/admin-dashboard/.env.example frontend/admin-dashboard/.env

# 2. Build del frontend
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml build admin-dashboard

# 3. Levantar servicios
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml up -d

# 4. Ver logs
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml logs -f
```

## URLs Disponibles

Una vez deployado:

- **Admin Dashboard**: http://localhost:3001 (⚠️ puerto 3001, no 3000)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check Frontend**: http://localhost:3001/health

## Comandos Útiles

### Ver Logs

```bash
# Todos los servicios
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml logs -f

# Solo frontend
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml logs -f admin-dashboard

# Solo backend
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml logs -f api
```

### Detener Servicios

```bash
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml down
```

### Rebuild Frontend

```bash
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml build --no-cache admin-dashboard
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml up -d admin-dashboard
```

### Ver Estado de Servicios

```bash
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml ps
```

## Troubleshooting

### Frontend no carga

```bash
# Ver logs del frontend
docker logs alojamientos_admin_dashboard

# Verificar health check
curl http://localhost:3001/health

# Rebuild sin cache
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml build --no-cache admin-dashboard
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml up -d admin-dashboard
```

### API no responde

```bash
# Ver logs del backend
docker logs alojamientos_api

# Verificar health check
curl http://localhost:8000/api/v1/healthz

# Reiniciar backend
docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml restart api
```

### Error "host not found in upstream"

Este error indica que nginx no puede resolver el hostname del backend.

**Solución:**
1. Verificar que `nginx.conf` use `proxy_pass http://api:8000` (no `backend`)
2. Verificar que el servicio dashboard esté en las redes `frontend` y `backend`
3. Rebuild la imagen:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml build --no-cache admin-dashboard
   docker-compose -f docker-compose.yml -f docker-compose.dashboard.yml up -d
   ```

### Puerto 3001 ocupado

```bash
# Ver qué proceso usa el puerto
sudo lsof -i :3001

# Cambiar puerto en docker-compose.dashboard.yml
# Editar la línea: - "3001:80" → - "3002:80"
```

### Build falla con "tsc: not found"

Este error ocurre si `npm ci --only=production` no instala devDependencies necesarias para el build.

**Solución:** Verificar que `Dockerfile` use `npm ci` (sin `--only=production`) en la etapa builder.

## Variables de Entorno

### Frontend (.env en frontend/admin-dashboard/)

```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME="Sistema de Reservas - Admin"
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEBUG=false
VITE_JWT_STORAGE_KEY=admin_token
VITE_QUERY_STALE_TIME=30000
VITE_QUERY_CACHE_TIME=300000
```

### Backend (.env en raíz del proyecto)

Ver `.env.template` para todas las variables disponibles.

## Checklist Post-Deploy

- [ ] Frontend carga en http://localhost:3000
- [ ] Backend responde en http://localhost:8000/api/v1/healthz
- [ ] Login funciona con credenciales admin
- [ ] KPIs muestran datos reales
- [ ] Tabla de reservas carga
- [ ] Filtros funcionan correctamente
- [ ] Búsqueda funciona con debounce
- [ ] No hay errores en consola del navegador
- [ ] No hay errores críticos en logs de Docker

## Credenciales de Admin

Por defecto (cambiar en producción):

```
Email: admin@example.com
Password: admin123
```

## Notas de Seguridad

⚠️ **IMPORTANTE para Producción:**

1. Cambiar credenciales admin default
2. Usar HTTPS (configurar certificados SSL)
3. Configurar CORS correctamente
4. Usar variables de entorno seguras
5. No exponer puertos innecesarios
6. Habilitar rate limiting
7. Configurar backups automáticos

## Arquitectura del Deploy

```
┌─────────────────────┐
│   Admin Dashboard   │ :3000 (nginx alpine)
│   (React + Vite)    │
└──────────┬──────────┘
           │ /api/* → proxy
           ▼
┌─────────────────────┐
│   Backend API       │ :8000 (FastAPI)
│   (Python)          │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌────────┐
│PostgreSQL│  │ Redis  │
│  :5432   │  │ :6379  │
└─────────┘  └────────┘
```

## Métricas de Rendimiento

- **Build frontend**: ~30-60s
- **Startup time**: ~10-15s
- **Health check**: ~5s
- **Bundle size**: 322KB gzipped

## Próximos Pasos

1. **UAT Testing**: Probar todas las funcionalidades
2. **Performance Testing**: Verificar tiempos de respuesta
3. **Security Audit**: Revisar configuraciones de seguridad
4. **Deploy Producción**: Seguir guía de producción

## Soporte

Para issues o preguntas:
- Ver logs: `docker-compose logs -f`
- Documentación backend: http://localhost:8000/docs
- GitHub Issues: [crear issue]

---

**Última actualización**: Oct 17, 2025
**Versión Dashboard**: 1.0.0
**Status**: ✅ Staging Ready
