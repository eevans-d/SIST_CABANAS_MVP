# 📖 ADMIN PLAYBOOK - Guía Operativa Diaria

**Fecha:** Octubre 16, 2025
**Versión:** 1.0 - Durante implementación Dashboard
**Duración:** Temporal (hasta Oct 28)
**Propósito:** Permitir operación independiente del administrador sin dashboard UI

---

## 🎯 INTRODUCCIÓN

Este playbook te permitirá **operar el sistema completamente** durante los próximos 12 días mientras se implementa el dashboard visual.

**¿Por qué necesitas esto?**
- El backend está 100% funcional pero sin interfaz visual
- Necesitas realizar operaciones diarias sin esperar al dashboard
- Te dará independencia operativa inmediata

**Tiempo estimado de aprendizaje:** 30 minutos
**Tiempo por operación:** 2-5 minutos (vs 15-20 sin esta guía)

---

## 🚀 SETUP INICIAL (Solo una vez)

### 1. Verificar que el sistema esté corriendo:

```bash
# Ir al directorio del proyecto
cd /home/eevan/ProyectosIA/SIST_CABAÑAS

# Verificar que los servicios estén up
docker-compose ps

# Deberías ver:
# - backend: running
# - postgres: running
# - redis: running

# Si no están corriendo:
make up
```

### 2. Obtener token de acceso (válido 24h):

```bash
# Generar token JWT para admin
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password_admin"}'

# Guardar el token que devuelve, lo necesitarás para todas las operaciones
```

**⚠️ IMPORTANTE:** Reemplaza `tu_password_admin` con la contraseña real.

---

## 📊 OPERACIONES DIARIAS MÁS COMUNES

### ✅ OPERACIÓN 1: "¿Cuántas reservas tengo hoy?"

**Tiempo:** ~30 segundos

```bash
# Con curl (reemplaza TOKEN por tu token real):
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations?date_from=$(date +%Y-%m-%d)&date_to=$(date +%Y-%m-%d)"

# Cuenta las reservas en el resultado JSON
```

**Alternativa SQL directa:**
```bash
# Conectar a PostgreSQL
docker exec -it sist_cabanas_postgres psql -U postgres -d cabanas_db

# Query:
SELECT COUNT(*) as reservas_hoy
FROM reservations
WHERE DATE(check_in) = CURRENT_DATE;
```

**Resultado esperado:** Número de reservas para hoy

---

### ✅ OPERACIÓN 2: "¿Qué reservas llegan hoy?" (Check-ins)

**Tiempo:** ~45 segundos

```bash
# API call:
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations?check_in_date=$(date +%Y-%m-%d)" | jq '.[] | {guest_name, check_in, accommodation_id, guests_count}'

# O en PostgreSQL:
SELECT guest_name, accommodation_id, guests_count, check_in, guest_phone
FROM reservations
WHERE DATE(check_in) = CURRENT_DATE
AND reservation_status IN ('confirmed', 'pre_reserved');
```

**Resultado esperado:** Lista de huéspedes que llegan hoy con sus datos

---

### ✅ OPERACIÓN 3: "¿Qué reservas salen hoy?" (Check-outs)

**Tiempo:** ~45 segundos

```bash
# API call:
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations?check_out_date=$(date +%Y-%m-%d)" | jq '.[] | {guest_name, check_out, accommodation_id}'

# O en PostgreSQL:
SELECT guest_name, accommodation_id, check_out, guest_phone
FROM reservations
WHERE DATE(check_out) = CURRENT_DATE
AND reservation_status = 'confirmed';
```

**Resultado esperado:** Lista de huéspedes que se van hoy

---

### ✅ OPERACIÓN 4: "¿Cuáles cabañas están libres este fin de semana?"

**Tiempo:** ~1 minuto

```bash
# Calcular fechas de fin de semana
SATURDAY=$(date -d "next saturday" +%Y-%m-%d)
SUNDAY=$(date -d "next sunday" +%Y-%m-%d)

# Query disponibilidad
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/accommodations/availability?check_in=$SATURDAY&check_out=$SUNDAY"
```

**SQL alternativo:**
```sql
-- Ver qué cabañas NO tienen reservas en el período
SELECT a.id, a.name
FROM accommodations a
WHERE a.id NOT IN (
  SELECT DISTINCT accommodation_id
  FROM reservations
  WHERE check_in <= 'DOMINGO' AND check_out >= 'SABADO'
  AND reservation_status IN ('confirmed', 'pre_reserved')
);
```

---

### ✅ OPERACIÓN 5: "¿Cuánto ingreso tengo este mes?"

**Tiempo:** ~30 segundos

```bash
# Query ingresos del mes
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/reports/monthly?month=$(date +%Y-%m)"

# O en PostgreSQL:
SELECT
  SUM(total_price) as ingresos_mes,
  COUNT(*) as num_reservas
FROM reservations
WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
  AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND reservation_status = 'confirmed';
```

**Resultado esperado:** Total de ingresos y número de reservas del mes

---

### ✅ OPERACIÓN 6: "Ver reserva específica" (por código o teléfono)

**Tiempo:** ~30 segundos

```bash
# Por código de reserva:
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations/search?code=ABC123"

# Por teléfono:
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations/search?phone=5491234567890"
```

**SQL alternativo:**
```sql
-- Por código:
SELECT * FROM reservations WHERE code = 'ABC123';

-- Por teléfono:
SELECT * FROM reservations WHERE guest_phone LIKE '%1234567890%';
```

---

### ✅ OPERACIÓN 7: "Crear reserva manual" (casos especiales)

**Tiempo:** ~2 minutos

```bash
# Datos de ejemplo - REEMPLAZAR con datos reales:
curl -X POST "http://localhost:8000/api/v1/admin/reservations" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "accommodation_id": 1,
    "guest_name": "Juan Pérez",
    "guest_phone": "5491234567890",
    "guest_email": "juan@example.com",
    "check_in": "2025-10-20",
    "check_out": "2025-10-22",
    "guests_count": 2,
    "channel_source": "manual_admin",
    "notes": "Reserva telefónica directa"
  }'
```

**Verificar que no hay conflictos antes de crear!**

---

## 🚨 TROUBLESHOOTING COMÚN

### ❌ Error: "Token expired" o "401 Unauthorized"

**Solución:** Generar nuevo token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password_admin"}'
```

### ❌ Error: "Connection refused" al hacer curl

**Solución:** Verificar que el backend esté corriendo
```bash
# Verificar status
docker-compose ps

# Si está down, levantar:
make up

# Verificar logs si hay problemas:
make logs
```

### ❌ Error: "Accommodation not available" al crear reserva

**Solución:** Verificar disponibilidad primero
```bash
# Buscar conflictos en fechas:
SELECT * FROM reservations
WHERE accommodation_id = TU_CABAÑA_ID
  AND check_in <= 'TU_CHECK_OUT'
  AND check_out >= 'TU_CHECK_IN'
  AND reservation_status IN ('confirmed', 'pre_reserved');
```

### ❌ PostgreSQL no responde

**Solución:** Restart de BD
```bash
docker-compose restart postgres
# Esperar 30 segundos
docker-compose logs postgres
```

---

## 📱 CASOS DE USO ESPECÍFICOS

### 📞 "Llamada telefónica: ¿Tienen disponible para este finde?"

**Flujo rápido (2 minutos):**

1. **Calcular fechas:**
   ```bash
   echo "Sábado: $(date -d 'next saturday' +%Y-%m-%d)"
   echo "Domingo: $(date -d 'next sunday' +%Y-%m-%d)"
   ```

2. **Verificar disponibilidad:**
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/api/v1/admin/accommodations/availability?check_in=SABADO&check_out=DOMINGO"
   ```

3. **Responder al cliente:** "Sí, tenemos la cabaña X disponible" o "No, todo ocupado"

### 💰 "¿Cuánto cobrar por 3 noches en cabaña premium?"

**Flujo rápido (1 minuto):**

1. **Ver precios:**
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/api/v1/admin/accommodations/1" | jq '.base_price, .weekend_multiplier'
   ```

2. **Calcular:**
   - Precio base × noches de semana
   - Precio base × multiplicador × noches de finde
   - Sumar ambos

### 🔍 "Cliente dice que pagó pero no veo la reserva"

**Flujo diagnóstico (2 minutos):**

1. **Buscar por teléfono:**
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/api/v1/admin/reservations/search?phone=TELEFONO_CLIENTE"
   ```

2. **Buscar por email:**
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/api/v1/admin/reservations/search?email=EMAIL_CLIENTE"
   ```

3. **Verificar logs de pagos:**
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/api/v1/admin/payments/search?amount=MONTO&date=HOY"
   ```

---

## 📊 QUERIES SQL ÚTILES PREDEFINIDAS

### Estado General del Sistema

```sql
-- Dashboard resumen
SELECT
  (SELECT COUNT(*) FROM reservations WHERE reservation_status = 'confirmed') as reservas_confirmadas,
  (SELECT COUNT(*) FROM reservations WHERE reservation_status = 'pre_reserved') as pre_reservas,
  (SELECT COUNT(*) FROM reservations WHERE DATE(check_in) = CURRENT_DATE) as check_ins_hoy,
  (SELECT COUNT(*) FROM reservations WHERE DATE(check_out) = CURRENT_DATE) as check_outs_hoy,
  (SELECT SUM(total_price) FROM reservations WHERE reservation_status = 'confirmed' AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)) as ingresos_mes;
```

### Reservas del Día

```sql
-- Check-ins de hoy
SELECT
  guest_name as "Huésped",
  accommodations.name as "Cabaña",
  guests_count as "Personas",
  guest_phone as "Teléfono",
  check_in as "Llegada"
FROM reservations
JOIN accommodations ON reservations.accommodation_id = accommodations.id
WHERE DATE(check_in) = CURRENT_DATE
  AND reservation_status = 'confirmed'
ORDER BY check_in;

-- Check-outs de hoy
SELECT
  guest_name as "Huésped",
  accommodations.name as "Cabaña",
  guest_phone as "Teléfono",
  check_out as "Salida"
FROM reservations
JOIN accommodations ON reservations.accommodation_id = accommodations.id
WHERE DATE(check_out) = CURRENT_DATE
  AND reservation_status = 'confirmed'
ORDER BY check_out;
```

### Disponibilidad

```sql
-- Cabañas disponibles para un período
SELECT
  a.id,
  a.name as "Cabaña",
  a.capacity as "Capacidad",
  a.base_price as "Precio Base"
FROM accommodations a
WHERE a.active = true
  AND a.id NOT IN (
    SELECT DISTINCT accommodation_id
    FROM reservations
    WHERE check_in <= 'TU_FECHA_CHECKOUT'
      AND check_out >= 'TU_FECHA_CHECKIN'
      AND reservation_status IN ('confirmed', 'pre_reserved')
  );
```

---

## ⏰ RUTINA DIARIA SUGERIDA

### 🌅 Mañana (9:00 AM - 5 minutos)

```bash
# 1. Ver check-ins del día
echo "=== CHECK-INS HOY ==="
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations?check_in_date=$(date +%Y-%m-%d)"

# 2. Ver check-outs del día
echo "=== CHECK-OUTS HOY ==="
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations?check_out_date=$(date +%Y-%m-%d)"

# 3. Verificar salud del sistema
curl "http://localhost:8000/api/v1/healthz"
```

### 🌆 Tarde (6:00 PM - 3 minutos)

```bash
# 1. Resumen del día
echo "=== RESUMEN DEL DÍA ==="
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/admin/reports/daily?date=$(date +%Y-%m-%d)"

# 2. Pre-reservas pendientes de confirmación
echo "=== PRE-RESERVAS PENDIENTES ==="
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/admin/reservations?status=pre_reserved"
```

---

## 🆘 CONTACTOS DE EMERGENCIA

### Si algo no funciona:

1. **Problema técnico del sistema:**
   - Revisar logs: `make logs`
   - Restart: `make restart`
   - Si persiste: Contactar soporte técnico

2. **Duda operativa:**
   - Consultar este playbook
   - Buscar en documentación: INDEX.md
   - Consultar con equipo de producto

3. **Error de datos/reservas:**
   - NO modificar BD directamente
   - Usar siempre API endpoints
   - Documentar el problema para análisis

---

## 📈 MÉTRICAS DE ÉXITO

**Con este playbook deberías lograr:**

- ⏱️ **Operaciones básicas en <5 minutos** (vs 15-20 sin guía)
- 🎯 **95% de consultas resueltas sin ayuda técnica**
- 📊 **Visibilidad completa del estado diario del negocio**
- 🔄 **Independencia operativa total**

**Indicadores de que funciona bien:**
- ✅ Puedes responder "¿tengo disponibilidad?" en <2 minutos
- ✅ Generas reportes diarios sin problemas
- ✅ Resuelves consultas de clientes rápidamente
- ✅ No necesitas escalación técnica para operaciones rutinarias

---

## 🚀 MIGRACIÓN AL DASHBOARD

**Cuando el dashboard esté listo (Oct 28):**

1. **Todo esto se vuelve visual** → Clicks en vez de comandos
2. **Tiempo de respuesta:** 5 segundos vs 2-5 minutos actuales
3. **Alertas automáticas** → No más verificación manual
4. **Este playbook queda como backup** → Para casos especiales

**Este esfuerzo de aprendizaje NO se pierde** - te dará:
- ✅ Comprensión profunda del sistema
- ✅ Capacidad de troubleshooting avanzado
- ✅ Independencia total en operaciones críticas

---

## 📋 CHECKLIST DE DOMINIO

Marca cuando domines cada operación:

- [ ] Generar token JWT
- [ ] Ver reservas del día (check-ins/check-outs)
- [ ] Verificar disponibilidad de cabañas
- [ ] Calcular ingresos del mes
- [ ] Buscar reserva específica
- [ ] Crear reserva manual
- [ ] Resolver "token expired"
- [ ] Diagnosticar problemas de conectividad
- [ ] Ejecutar rutina diaria completa
- [ ] Responder consulta telefónica en <3 minutos

**Meta:** 8/10 operaciones dominadas en 2 días de práctica.

---

## 🎯 CONCLUSIÓN

Este playbook te da **independencia operativa completa** durante la implementación del dashboard.

**Tiempo de implementación del dashboard:** 12 días
**Tiempo para dominar este playbook:** 2 días de práctica
**ROI inmediato:** De 15-20 min por consulta → 2-5 minutos

**¡En 48 horas serás autónomo operativamente!** 💪

---

*Playbook v1.0 - Octubre 16, 2025*
*Válido hasta: Oct 28 (lanzamiento dashboard)*
*Actualización prevista: No necesaria (será reemplazado por UI)*
