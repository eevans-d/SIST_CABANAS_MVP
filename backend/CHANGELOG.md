# 📚 CHANGELOG - Sistema Alojamientos MVP

Todos los cambios notables en este proyecto serán documentados aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-27

### ✨ Agregado - MVP Core
- **Sistema de Reservas Anti-Double-Booking**
  - Lock Redis con TTL de 30 minutos para pre-reservas
  - Constraint PostgreSQL EXCLUDE GIST para prevenir overlaps
  - Pre-reservas ephémeras con expiración automática
  - Códigos únicos de reserva (formato: RES + fecha + secuencial)

- **Integración WhatsApp Business Cloud API**
  - Webhook con validación HMAC SHA-256 obligatoria
  - Procesamiento de mensajes de texto y audio
  - Pipeline STT con Whisper + FFmpeg (OGG → WAV)
  - NLU heurístico para intent detection

- **Integración Mercado Pago**
  - Webhook con validación x-signature v1
  - Procesamiento de notificaciones de pago
  - Estados: pending → paid → confirmed reservation

- **Sincronización iCal**
  - Import/export para Airbnb, Booking.com
  - Deduplicación por external_id
  - Tokens seguros para export público
  - Sync automático cada 15 minutos

### 🔒 Seguridad
- **Validación HMAC** en todos los webhooks
- **JWT** para autenticación admin
- **Enmascaramiento automático** de datos sensibles en logs
- **Rate limiting** por IP en endpoints públicos
- **HTTPS obligatorio** con redirect automático

### 📊 Observabilidad
- **Métricas Prometheus** custom (reservas, locks, overlaps)
- **Health endpoint** completo (DB, Redis, integraciones, iCal sync age)
- **Logging estructurado** con trace-id y masking
- **CLI de management** para tokens, stats, cleanup

### 🚀 Deploy & DevOps
- **Docker Compose** completo con PostgreSQL 16 + Redis 7
- **Nginx** reverse proxy con SSL automático
- **Script de deploy** con backup/rollback automático
- **Health checks** en todos los containers
- **Certificados Let's Encrypt** automáticos

### 🧪 Testing
- **27 tests** pasando (unit + integration)
- **Markers pytest** para tests que requieren servicios externos
- **Fixtures** reutilizables para DB y servicios
- **Load testing** script incluido (20 concurrent requests)

### 📋 Modelos de Datos
- **Accommodations**: id, name, type, capacity, base_price, amenities, location
- **Reservations**: code, guest_data, dates, pricing, status, channel_source
- **Estados**: pre_reserved (30min) → confirmed → checked_in → completed

### 🔧 APIs Implementadas
- `POST /api/reservations/pre-reserve` - Crear pre-reserva con lock
- `GET /health` - Health check completo con métricas
- `POST /webhooks/whatsapp` - Webhook WhatsApp con HMAC
- `POST /webhooks/mercadopago` - Webhook Mercado Pago
- `GET /ical/export/{id}/{token}` - Export calendario público

### 🛠️ Tech Stack Final
- **Backend**: FastAPI 0.104.1 + SQLAlchemy async
- **Database**: PostgreSQL 16 + Redis 7
- **Deploy**: Docker Compose + Nginx + Let's Encrypt
- **Monitoring**: Prometheus metrics + structured logging
- **Security**: HMAC webhooks + JWT + data masking

## [Próximas Versiones]

### 🎯 Post-MVP (v1.1.0)
- [ ] Dashboard web para gestión
- [ ] Notificaciones email automáticas
- [ ] Multi-propietario support
- [ ] Reporting avanzado
- [ ] Integration tests E2E

### 🚀 Escalabilidad (v2.0.0)
- [ ] Horizontal scaling con load balancer
- [ ] Database read replicas
- [ ] Centralized logging (ELK stack)
- [ ] Kubernetes deployment
- [ ] Multi-región support

---

**🎉 MVP COMPLETADO - 27 Sep 2025**  
**🚀 Ready for Production Deployment**