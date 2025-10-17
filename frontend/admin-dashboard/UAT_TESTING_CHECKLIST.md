# 🎯 Dashboard Admin - Checklist UAT Testing

## Estado: DEPLOYED ✅ - Ready for Testing

**Entorno**: Staging
**URL**: http://localhost:3001
**Fecha**: 17 de Octubre, 2025

---

## ✅ Pre-requisitos de Testing

Antes de comenzar UAT, verificar:

- [ ] Dashboard accesible en http://localhost:3001
- [ ] API respondiendo en http://localhost:8000
- [ ] Backend health check OK: `curl http://localhost:8000/api/v1/healthz`
- [ ] Frontend health check OK: `curl http://localhost:3001/health`
- [ ] Base de datos tiene datos de testing (al menos 10 reservas)
- [ ] Credenciales admin disponibles (ver `.env` o documentación)

---

## 🔐 Test 1: Autenticación

### Login Flow
- [ ] Abrir http://localhost:3001
- [ ] Ver formulario de login
- [ ] Ingresar credenciales admin
  - Email: `admin@example.com`
  - Password: `admin123` (o las definidas en tu sistema)
- [ ] Click en "Login" button
- [ ] Verificar redirección a dashboard `/dashboard`
- [ ] Verificar que aparece nombre/email del admin en header/navbar

### Error Handling
- [ ] Intentar login con password incorrecta → Ver mensaje de error
- [ ] Intentar login con email no existente → Ver mensaje de error
- [ ] Verificar que los errores NO exponen información sensible

**Status**: ⏳ Pending
**Issues**: [Anotar aquí cualquier problema encontrado]

---

## 📊 Test 2: KPIs Dashboard

### Carga Inicial
- [ ] Abrir dashboard page (`/dashboard`)
- [ ] Ver 5 KPI cards:
  1. Total Reservas
  2. Confirmadas
  3. Pre-Reservadas
  4. Canceladas
  5. Revenue Total
- [ ] Verificar que cada card muestra un número (no "0" si hay datos)
- [ ] Verificar que los números coinciden con datos reales en DB

### Visual Quality
- [ ] Cards tienen íconos apropiados para cada categoría
- [ ] Colores son consistentes (azul, verde, amarillo, rojo, purple)
- [ ] Texto es legible (tamaño de fuente, contraste)
- [ ] Layout se ve bien en desktop (1920x1080)
- [ ] Layout se ve bien en tablet (768x1024)
- [ ] Layout se ve bien en mobile (375x667)

### Auto-Refresh
- [ ] Abrir Network tab en DevTools
- [ ] Esperar 30 segundos
- [ ] Verificar que hace request a `/api/v1/admin/dashboard/stats`
- [ ] Verificar que KPIs se actualizan automáticamente
- [ ] Repetir 2-3 veces para confirmar consistencia

### Loading States
- [ ] Refrescar página (F5)
- [ ] Verificar skeleton loaders mientras carga
- [ ] Verificar transición suave a datos reales

### Error Handling
- [ ] Detener backend: `docker stop alojamientos_api`
- [ ] Refrescar dashboard
- [ ] Verificar mensaje de error claro y amigable
- [ ] Verificar que no se rompe el layout
- [ ] Re-iniciar backend: `docker start alojamientos_api`
- [ ] Verificar que vuelve a cargar automáticamente

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## 📋 Test 3: Tabla de Reservas

### Carga Inicial
- [ ] Ver tabla con 8 columnas:
  1. ID
  2. Code
  3. Guest (nombre + email/teléfono)
  4. Dates (check-in → check-out)
  5. Status (badge de color)
  6. Total ($)
  7. Channel (whatsapp/email)
  8. Actions (botones)
- [ ] Verificar que muestra 10 reservas por página (o las que haya)
- [ ] Verificar que datos son correctos vs DB

### Paginación
- [ ] Ver controles de paginación (< 1 2 3 >)
- [ ] Click en página 2 → Ver siguientes 10 reservas
- [ ] Click en página 1 → Volver a primeras 10
- [ ] Click en "Next" → Avanzar
- [ ] Click en "Previous" → Retroceder
- [ ] Verificar que disabled states funcionan (no se puede ir a página -1 o más allá del total)

### Ordenamiento
- [ ] Click en header "ID" → Ordenar ascendente
- [ ] Click nuevamente → Ordenar descendente
- [ ] Click en "Dates" → Ordenar por fecha check-in
- [ ] Click en "Total" → Ordenar por precio
- [ ] Verificar visual feedback (flecha ↑↓)

### Status Badges
- [ ] Ver badges de diferentes colores según status:
  - `confirmed`: Verde
  - `pre_reserved`: Amarillo
  - `pending_confirmation`: Naranja
  - `cancelled`: Rojo
  - `expired`: Gris
- [ ] Verificar que texto del status es legible en el badge

### Loading States
- [ ] Aplicar un filtro (ver Test 4)
- [ ] Verificar skeleton rows mientras carga
- [ ] Verificar transición suave

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## 🔍 Test 4: Sistema de Filtros

### Filtro por Status

#### UI del Filtro
- [ ] Ver dropdown "Filter by Status"
- [ ] Click en dropdown → Ver 7 opciones con checkboxes:
  1. Confirmed
  2. Pre-Reserved
  3. Pending Confirmation
  4. Pending Payment
  5. Cancelled
  6. Expired
  7. Blocked
- [ ] Verificar visual feedback al hover

#### Funcionalidad Single Select
- [ ] Seleccionar "Confirmed"
- [ ] Verificar que aparece badge azul "Status: Confirmed" debajo del dropdown
- [ ] Verificar que tabla filtra y muestra solo confirmadas
- [ ] Verificar que URL actualiza: `?statuses=confirmed`
- [ ] Refrescar página (F5) → Verificar que filtro persiste

#### Funcionalidad Multi-Select
- [ ] Click en dropdown nuevamente
- [ ] Seleccionar "Pre-Reserved" (ahora hay 2 seleccionados)
- [ ] Verificar badge muestra "Status: Confirmed, Pre-Reserved"
- [ ] Verificar tabla muestra ambos tipos
- [ ] Verificar URL: `?statuses=confirmed,pre_reserved`

#### Clear Individual
- [ ] Click en X del badge de status
- [ ] Verificar que filtro se remueve
- [ ] Verificar que tabla vuelve a mostrar todos
- [ ] Verificar que URL se actualiza

#### Click Outside para Cerrar
- [ ] Abrir dropdown
- [ ] Click fuera del dropdown
- [ ] Verificar que se cierra

### Filtro por Fechas

#### UI del Filtro
- [ ] Ver dos inputs: "Start Date" y "End Date"
- [ ] Verificar placeholders: "YYYY-MM-DD"

#### Funcionalidad Start Date
- [ ] Ingresar fecha start: `2025-10-01`
- [ ] Verificar badge verde "Dates: from 2025-10-01"
- [ ] Verificar tabla filtra reservas con check-in >= 2025-10-01
- [ ] Verificar URL: `?start_date=2025-10-01`

#### Funcionalidad End Date
- [ ] Ingresar fecha end: `2025-10-31`
- [ ] Verificar badge actualiza: "Dates: from 2025-10-01 to 2025-10-31"
- [ ] Verificar tabla filtra reservas en rango
- [ ] Verificar URL: `?start_date=2025-10-01&end_date=2025-10-31`

#### Validación de Fechas
- [ ] Intentar end_date < start_date
- [ ] Verificar auto-corrección o mensaje de error
- [ ] Intentar fecha futura muy lejana (>1 año)
- [ ] Verificar manejo apropiado

#### Clear Individual
- [ ] Click en X del badge de dates
- [ ] Verificar que ambas fechas se limpian
- [ ] Verificar tabla vuelve a mostrar todos

### Filtro Combinado (Status + Dates)
- [ ] Aplicar filtro de status: "Confirmed"
- [ ] Aplicar filtro de fechas: "2025-10-01" a "2025-10-31"
- [ ] Verificar que tabla muestra solo confirmadas en ese rango
- [ ] Verificar que aparecen 2 badges
- [ ] Verificar URL: `?statuses=confirmed&start_date=2025-10-01&end_date=2025-10-31`
- [ ] Refrescar (F5) → Verificar que ambos filtros persisten

### Clear All
- [ ] Con múltiples filtros activos
- [ ] Click en botón "Clear All Filters"
- [ ] Verificar que todos los badges desaparecen
- [ ] Verificar que tabla muestra todas las reservas
- [ ] Verificar que URL se limpia: sin query params

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## 🔎 Test 5: Búsqueda

### UI de Búsqueda
- [ ] Ver input de búsqueda con ícono 🔍
- [ ] Placeholder: "Search by guest name, email, or phone..."
- [ ] Verificar que está en el FilterBar (arriba de la tabla)

### Funcionalidad Básica
- [ ] Escribir nombre de guest existente: "Juan"
- [ ] Ver indicador "Escribiendo..." por 300ms
- [ ] Ver indicador cambiar a "Buscando: Juan"
- [ ] Verificar tabla filtra reservas con nombre "Juan"
- [ ] Verificar URL: `?search=Juan`

### Búsqueda por Email
- [ ] Limpiar búsqueda anterior
- [ ] Escribir email: "juan@example.com"
- [ ] Verificar tabla filtra por email
- [ ] Verificar que encuentra coincidencias parciales (e.g., "juan" encuentra "juan@...")

### Búsqueda por Teléfono
- [ ] Limpiar búsqueda
- [ ] Escribir teléfono: "+549"
- [ ] Verificar tabla filtra por teléfono
- [ ] Verificar coincidencias parciales

### Debounce (300ms)
- [ ] Escribir rápidamente "JuanCarlos" (sin pausas)
- [ ] Verificar que NO hace request por cada letra
- [ ] Verificar que hace 1 solo request al terminar de escribir (después de 300ms)
- [ ] Abrir Network tab para confirmar

### Búsqueda + Filtros Combinados
- [ ] Aplicar filtro de status: "Confirmed"
- [ ] Aplicar búsqueda: "Juan"
- [ ] Verificar que tabla muestra solo confirmadas que matchean "Juan"
- [ ] Verificar badges: status badge + search badge (purple)
- [ ] Verificar URL: `?statuses=confirmed&search=Juan`

### Clear Button
- [ ] Con texto en el input de búsqueda
- [ ] Click en botón X dentro del input
- [ ] Verificar que input se limpia
- [ ] Verificar que badge de búsqueda desaparece
- [ ] Verificar que tabla vuelve a mostrar todos (o filtros activos)

### Sin Resultados
- [ ] Buscar texto que no existe: "ZZZZZZZ"
- [ ] Verificar mensaje apropiado: "No reservations found"
- [ ] Verificar que no se rompe el layout

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## 🎨 Test 6: Responsive Design

### Desktop (1920x1080)
- [ ] Layout se ve espacioso y balanceado
- [ ] KPI cards en 1 fila (5 columnas)
- [ ] FilterBar en 1 fila (3 columnas: status, dates, search)
- [ ] Tabla muestra todas las columnas sin scroll horizontal
- [ ] Botones tienen buen tamaño y espaciado

### Laptop (1366x768)
- [ ] Layout se ajusta correctamente
- [ ] KPI cards pueden wrap a 2 filas (aceptable)
- [ ] FilterBar mantiene 3 columnas o wrap a 2
- [ ] Tabla sigue siendo legible

### Tablet Portrait (768x1024)
- [ ] KPI cards en 2-3 columnas
- [ ] FilterBar wraps a 2 filas:
  - Fila 1: Status + Dates
  - Fila 2: Search (full width)
- [ ] Tabla con scroll horizontal si es necesario
- [ ] Touch targets son de tamaño adecuado (min 44x44px)

### Mobile (375x667)
- [ ] KPI cards en 1-2 columnas (vertical stack aceptable)
- [ ] FilterBar 100% wrapping:
  - Status: full width
  - Dates: full width (stacked)
  - Search: full width
- [ ] Tabla con scroll horizontal
- [ ] Badges wrappean correctamente
- [ ] Texto es legible (min 14px)
- [ ] Botones tienen buen touch target

### Zoom Testing
- [ ] Probar zoom 150% en desktop → Verificar legibilidad
- [ ] Probar zoom 200% → Verificar que no se rompe

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## ⚡ Test 7: Performance

### Initial Load Time
- [ ] Abrir DevTools → Network tab
- [ ] Hard refresh (Ctrl+Shift+R)
- [ ] Medir tiempo total de carga
- [ ] **Target**: < 3s para dashboard completo
- [ ] Verificar bundle size cargado: ~322KB gzipped

### API Response Times
- [ ] En Network tab, filtrar por "XHR"
- [ ] Verificar tiempo de respuesta de:
  - `/api/v1/admin/dashboard/stats`: **Target < 500ms**
  - `/api/v1/admin/reservations`: **Target < 1s**
  - Con filtros aplicados: **Target < 1.5s**
  - Con búsqueda: **Target < 2s**

### Throttling Test (Slow 3G)
- [ ] En DevTools → Network, seleccionar "Slow 3G"
- [ ] Refrescar dashboard
- [ ] Verificar loading states son visibles
- [ ] Verificar que no hay timeout errors
- [ ] Cambiar de vuelta a "No throttling"

### Memory Leaks
- [ ] Abrir DevTools → Performance → Memory
- [ ] Hacer snapshot inicial
- [ ] Interactuar con dashboard por 2-3 minutos:
  - Aplicar/remover filtros múltiples veces
  - Cambiar páginas de tabla
  - Hacer búsquedas
- [ ] Hacer snapshot final
- [ ] Verificar que memoria NO crece indefinidamente (max +20MB aceptable)

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## 🐛 Test 8: Error Handling

### Backend Down
- [ ] Detener API: `docker stop alojamientos_api`
- [ ] Refrescar dashboard
- [ ] Verificar mensaje de error amigable (no stack traces en UI)
- [ ] Verificar que layout no se rompe
- [ ] Re-iniciar API: `docker start alojamientos_api`
- [ ] Verificar recovery automático o manual

### Database Empty
- [ ] En estado con DB vacía (0 reservas)
- [ ] Verificar KPIs muestran 0s (no errores)
- [ ] Verificar tabla muestra mensaje "No reservations found"
- [ ] Verificar que no hay errores en consola

### Network Timeout
- [ ] En DevTools → Network, throttle "Offline"
- [ ] Intentar cargar dashboard
- [ ] Verificar mensaje apropiado: "Connection error" o similar
- [ ] Restaurar "No throttling"
- [ ] Verificar retry o manual reload

### Invalid Filter Values
- [ ] Manualmente editar URL: `?statuses=INVALID_STATUS`
- [ ] Verificar que backend maneja gracefully
- [ ] Verificar que frontend no se rompe
- [ ] Cambiar URL: `?start_date=not-a-date`
- [ ] Verificar validación apropiada

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## 🔒 Test 9: Security

### Authentication
- [ ] Sin login, intentar acceder a `/dashboard` directamente
- [ ] Verificar redirección a login
- [ ] Login → Verificar que se almacena JWT en localStorage/cookies
- [ ] Logout → Verificar que JWT se elimina
- [ ] Intentar acceder a dashboard post-logout → Verificar redirección

### CORS
- [ ] Abrir consola del navegador
- [ ] Verificar que NO hay errores CORS
- [ ] Verificar que requests a `/api/v1/` tienen headers apropiados

### XSS Protection
- [ ] En campo de búsqueda, ingresar: `<script>alert('XSS')</script>`
- [ ] Verificar que NO se ejecuta el script
- [ ] Verificar que se escapa el texto correctamente

### SQL Injection (Backend)
- [ ] En búsqueda, ingresar: `' OR '1'='1`
- [ ] Verificar que backend sanitiza input
- [ ] Verificar que NO retorna todas las reservas (ataque falló)

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## ✅ Test 10: Browser Compatibility

### Chrome (latest)
- [ ] Todas las features funcionan
- [ ] No errores en consola

### Firefox (latest)
- [ ] Todas las features funcionan
- [ ] No errores en consola

### Safari (latest)
- [ ] Todas las features funcionan
- [ ] Verificar date pickers (Safari tiene quirks)
- [ ] No errores en consola

### Edge (latest)
- [ ] Todas las features funcionan
- [ ] No errores en consola

**Status**: ⏳ Pending
**Issues**: [Anotar aquí]

---

## 📊 Resumen de Resultados

### Tests Completados: 0/10

| Test | Status | Issues | Severity |
|------|--------|--------|----------|
| 1. Autenticación | ⏳ Pending | - | - |
| 2. KPIs Dashboard | ⏳ Pending | - | - |
| 3. Tabla Reservas | ⏳ Pending | - | - |
| 4. Filtros | ⏳ Pending | - | - |
| 5. Búsqueda | ⏳ Pending | - | - |
| 6. Responsive | ⏳ Pending | - | - |
| 7. Performance | ⏳ Pending | - | - |
| 8. Error Handling | ⏳ Pending | - | - |
| 9. Security | ⏳ Pending | - | - |
| 10. Browser Compat | ⏳ Pending | - | - |

### Critical Issues Found: 0
### Blockers for Production: 0

---

## 🚀 Sign-off

### Tester Information
- **Nombre**: _________________
- **Fecha**: _________________
- **Firma**: _________________

### Approval
- [ ] Todos los tests críticos pasaron
- [ ] Issues críticos resueltos o documentados
- [ ] Performance cumple con targets
- [ ] Security review aprobado
- [ ] **APPROVED FOR PRODUCTION**: ☐ YES ☐ NO

---

**Última Actualización**: Oct 17, 2025
**Versión Dashboard**: 1.0.0
**Entorno**: Staging
