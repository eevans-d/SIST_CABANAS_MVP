# 🏠 Integración con "Para Irnos"

## Descripción General

**Para Irnos** es una plataforma argentina de alojamiento similar a Airbnb y Booking.com. Este documento describe cómo integrar **Para Irnos** con el sistema de automatización de reservas para sincronización bidireccional de calendarios.

- **Plataforma**: Para Irnos (https://parairnos.com)
- **Región**: Argentina (con enfoque en turismo nacional)
- **Tipo de integración**: iCal (RFC 5545) - sincronización de disponibilidad

## 🎯 Objetivos de la Integración

1. ✅ **Importar reservas** desde Para Irnos al sistema local
2. ✅ **Exportar disponibilidad** desde el sistema local a Para Irnos
3. ✅ **Evitar doble-booking** sincronizando automáticamente cada 5 minutos
4. ✅ **Deduplicación inteligente** por UID de eventos

## 📋 Requisitos Previos

- Cuenta activa en Para Irnos como propietario de alojamiento
- Acceso a la configuración de calendario de tu propiedad
- Sistema de alojamientos ya configurado (base de datos, backend activo)

## 🔧 Configuración en Para Irnos

### Paso 1: Acceder a Configuración de Calendario

1. Inicia sesión en Para Irnos: https://parairnos.com
2. Ve a tu panel de propietario/gerente de alojamientos
3. Selecciona la propiedad que deseas sincronizar
4. Busca la sección "Calendario" o "Disponibilidad"
5. Dentro de configuración, busca "Sincronización iCal" o "Integración de terceros"

### Paso 2: Obtener URL iCal de Para Irnos

En la sección de sincronización de Para Irnos:

1. Busca una opción como "Exportar calendario" o "URL de sincronización"
2. Selecciona "Formato iCal" o ".ics"
3. Copia la URL que termina con `.ics` o similar:
   ```
   https://parairnos.com/api/properties/{property_id}/calendar.ics
   https://parairnos.com/calendars/{token}.ics
   ```

4. **Nota importante**: Guarda esta URL en un lugar seguro (será privada/requiere token)

### Paso 3: Importar URL en el Sistema Local

#### Opción A: Vía API (Recomendado)

```bash
# Llamar endpoint de admin para configurar importación
curl -X POST http://localhost:8000/api/v1/admin/accommodations/{accommodation_id}/ical-urls \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "para_irnos",
    "ical_url": "https://parairnos.com/api/properties/12345/calendar.ics",
    "enabled": true
  }'
```

#### Opción B: Script de Configuración

```bash
cd backend
python3 scripts/configure_ical.py --source para_irnos --url "https://parairnos.com/api/properties/12345/calendar.ics"
```

#### Opción C: Base de datos (SQL directo)

```sql
-- Conectarse a PostgreSQL
UPDATE accommodations
SET ical_import_urls = jsonb_set(
  COALESCE(ical_import_urls, '{}'::jsonb),
  '{para_irnos}',
  '"https://parairnos.com/api/properties/12345/calendar.ics"'
)
WHERE id = 1;  -- Reemplazar con ID de alojamiento real
```

## 🔄 Configurar Exportación (Sistema Local → Para Irnos)

### Paso 1: Obtener Token de Exportación

El token de exportación se genera automáticamente por alojamiento:

```bash
# Ver token de exportación
curl -X GET http://localhost:8000/api/v1/admin/accommodations/{accommodation_id} \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq '.ical_export_token'
```

### Paso 2: URL de Exportación

La URL de exportación tiene el siguiente formato:

```
https://tu-dominio.com/api/v1/ical/export/{accommodation_id}/{export_token}
```

**Ejemplo**:
```
https://miresrvadora.com/api/v1/ical/export/1/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Paso 3: Configurar en Para Irnos

1. Ve a Configuración → Calendario → Sincronización iCal
2. Busca opción "Importar disponibilidad externa" o "Sincronización inversa"
3. Pega la URL de exportación:
   ```
   https://miresrvadora.com/api/v1/ical/export/1/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```
4. Selecciona intervalo de sincronización (recomendado: 1-2 horas)
5. Guarda configuración

## 📤 Formato de Eventos iCal

### Importación (De Para Irnos)

El sistema reconoce eventos de Para Irnos con este formato:

```
BEGIN:VEVENT
UID:para_irnos_event_12345@parairnos.com
DTSTART;VALUE=DATE:20251120
DTEND;VALUE=DATE:20251123
SUMMARY:Reserva Para Irnos - María García
DESCRIPTION:Reserva en Para Irnos
X-SOURCE:para_irnos
X-CODE:PRNOS-ABC123
STATUS:CONFIRMED
END:VEVENT
```

**Campos críticos**:
- `UID`: Identificador único del evento (DEBE ser único para deduplicación)
- `DTSTART`, `DTEND`: Fechas de check-in y check-out (formato DATE)
- `X-SOURCE`: Debe ser `para_irnos` (para identificación)
- `X-CODE`: Código de reserva (ej: PRNOS-ABC123)

### Exportación (Del Sistema Local)

El sistema exporta eventos locales en formato:

```
BEGIN:VEVENT
UID:local_reservation_1@tu-dominio.com
DTSTART;VALUE=DATE:20251201
DTEND;VALUE=DATE:20251205
SUMMARY:Reserva Local - Juan Pérez
DESCRIPTION:Reserva interna - Pre-reservada
X-SOURCE:internal
X-CODE:RES-001
STATUS:CONFIRMED
END:VEVENT
```

## 🔀 Sincronización Automática

### Background Job

El sistema sincroniza automáticamente cada 5 minutos (configurable):

- **Intervalo**: 300 segundos (5 minutos)
- **Configuración**: `JOB_ICAL_INTERVAL_SECONDS` en `.env`
- **Logs**: Ver en `docker logs api | grep ical_sync`

### Monitoreo

```bash
# Ver métricas de sincronización
curl http://localhost:8000/metrics | grep ical_

# Verificar salud de sincronización
curl http://localhost:8000/api/v1/healthz | jq '.checks.ical_sync'
```

### Deduplicación

El sistema evita crear duplicados:

1. **Por UID**: Verifica si el UID ya existe en `internal_notes`
2. **Por rango de fechas**: Comprueba overlaps con constraint de base de datos
3. **Por fuente**: Distingue entre airbnb, booking, para_irnos, internal

**Ejemplo de deduplicación**:
- Evento viene 5 veces → Solo se crea UNA reserva
- Si el evento ya existe → Se salta sin actualizar

## 🚨 Manejo de Conflictos

### Escenario 1: Doble Booking Detectado

Si hay conflicto de fechas:

```
Status: 409 Conflict
Error: "date_overlap_detected"
Message: "Ya existe una reserva en esas fechas"
```

**Solución**:
1. Revisar que no haya reserva real en esas fechas
2. Si hay error en Para Irnos, sincronizar manualmente desde allí
3. Ejecutar reconciliación: `POST /api/v1/ical/sync`

### Escenario 2: Evento No Sincroniza

Si un evento de Para Irnos no aparece:

```bash
# 1. Ver logs
docker logs api | grep "para_irnos"

# 2. Verificar URL
curl -I "https://parairnos.com/api/properties/12345/calendar.ics"

# 3. Forzar sincronización
curl -X POST http://localhost:8000/api/v1/ical/sync \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

## 📊 Estructura de Base de Datos

### Campo `ical_import_urls` en Accommodations

```json
{
  "airbnb": "https://www.airbnb.com/api/calendars/...",
  "booking": "https://www.booking.com/calendars/...",
  "para_irnos": "https://parairnos.com/api/properties/12345/calendar.ics"
}
```

### Tabla de Reservas (Importadas)

```sql
SELECT * FROM reservations
WHERE channel_source = 'para_irnos'
AND accommodation_id = 1;
```

**Campos generados**:
- `code`: `BLKHASH` (ej: BLK7a9c2f1e)
- `channel_source`: `para_irnos`
- `reservation_status`: `pre_reserved`
- `internal_notes`: Contiene `UID:para_irnos_event_12345@parairnos.com`

## 🔒 Seguridad

### Protección de URLs

- ✅ URLs iCal son **privadas** (contienen token)
- ✅ No expongas URL de exportación públicamente
- ✅ Regenera tokens periódicamente
- ✅ Usa HTTPS en producción

### Validación de Eventos

- ✅ Verifica `X-SOURCE: para_irnos`
- ✅ Valida formato RFC 5545
- ✅ Rechaza eventos sin UID válido
- ✅ Cierra solicitudes HTTP con timeout

## 📈 Monitoreo y Troubleshooting

### Métricas Prometheus

```
# Eventos importados desde Para Irnos
ical_events_imported_total{accommodation_id="1", source="para_irnos"}

# Errores de sincronización
ical_sync_errors_total{accommodation_id="1", error_type="fetch_failed"}

# Edad última sincronización (en minutos)
ical_sync_age_minutes{accommodation_id="1"}
```

### Comandos Útiles

```bash
# Ver todos los alojamientos con Para Irnos configurado
sqlite3 alojamientos_db.db "SELECT id, name, ical_import_urls FROM accommodations WHERE ical_import_urls LIKE '%para_irnos%';"

# Contar eventos importados hoy
docker exec api sqlite3 /app/alojamientos_db.db "SELECT COUNT(*) FROM reservations WHERE channel_source='para_irnos' AND DATE(created_at)=DATE('now');"

# Ver último error de sincronización
docker logs api 2>&1 | grep -i "para_irnos" | tail -20
```

## ✅ Checklist de Validación

- [ ] Obtuve URL iCal de Para Irnos
- [ ] Configuré URL de importación en sistema local
- [ ] Ejecuté sincronización manual (POST /api/v1/ical/sync)
- [ ] Verifiqué que eventos aparecen en reservations table
- [ ] Configuré exportación en Para Irnos
- [ ] Probé que mi reserva local aparece en Para Irnos (después de 1-2h)
- [ ] Revisé logs para errores: `docker logs api | grep ical`
- [ ] Validé métricas Prometheus en /metrics
- [ ] Probé doble-booking protection (intenté reservar fechas ocupadas)

## 🆘 Soporte

### Contacto Para Irnos

- **Email**: support@parairnos.com
- **Chat**: https://parairnos.com/help
- **Documentación**: https://parairnos.com/docs/api

### Contacto Sistema Local

Si encuentras bugs en la sincronización:

1. Recopila logs: `docker logs api > ical_logs.txt`
2. Captura sección relevante de `/metrics`
3. Reporta issue con:
   - Accommodation ID
   - Fuente (para_irnos)
   - Rango de fechas con problema
   - UID del evento problemático

---

**Última actualización**: Octubre 2025
**Versión**: 1.0 - MVP
**Status**: ✅ Production Ready
