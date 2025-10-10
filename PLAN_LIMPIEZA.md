# 🧹 Plan de Limpieza y Consolidación del Repositorio

**Fecha:** 2025-10-10
**Objetivo:** Eliminar duplicados, archivos obsoletos y consolidar documentación

---

## 📋 ANÁLISIS DE DUPLICADOS Y OBSOLETOS

### ❌ ARCHIVOS A ELIMINAR (Raíz del proyecto)

#### 1. **Archivos de sesión antiguos (consolidados en ESTADO_ACTUAL_2025-10-10.md)**
- [ ] `SESSION_SUMMARY_2025-10-09.md` → Información ya en ESTADO_ACTUAL
- [ ] `CIERRE_JORNADA_2025-10-09.md` → Información ya en ESTADO_ACTUAL
- [ ] `FASE_4_1_COMPLETADA.md` → Información ya en ESTADO_ACTUAL

**Razón:** Toda la información histórica está consolidada en `ESTADO_ACTUAL_2025-10-10.md`

#### 2. **Archivos desconocidos en workspace raíz** (fuera del repositorio)
- [ ] `alojamientos_partes_3_4.md`
- [ ] `alojamientos_partes_3_4.md:Zone.Identifier`
- [ ] `sistema_agentes_alojamientos_parte1.md`
- [ ] `sistema_agentes_alojamientos_parte1.md:Zone.Identifier`
- [ ] `Sistema_Agentico_MVP_Documentacion.markdown`
- [ ] `Sistema_Agentico_MVP_Documentacion.markdown:Zone.Identifier`

**Razón:** Archivos externos al proyecto, parecen ser documentación descargada

---

### 📁 DUPLICADOS EN /docs vs /backend

#### ADRs Duplicados
- [ ] `docs/adr/001-no-pms-externo.md` (más completo)
- [ ] `docs/adr/ADR-001-no-pms-mvp.md` (parece duplicado)
- [ ] `backend/docs/adr/ADR-0001-daterange-back-to-back.md` (único, mover a docs/adr/)

**Acción:** Consolidar en `docs/adr/` y eliminar de backend

#### Auditorías Duplicadas
- [ ] `backend/docs/AUDITORIA_2025-09-27.md` (antigua, 27 sept)
- [x] `AUDITORIA_TECNICA_COMPLETA.md` (actual, 10 oct) ← MANTENER

**Acción:** Archivar la antigua

#### Roadmaps Múltiples
- [x] `ROADMAP_MVP_PRIORIDAD_ALTA.md` (1,147 líneas - PRINCIPAL)
- [ ] `backend/ROADMAP_BCD.md` (178 líneas - Post-MVP)

**Acción:** Ambos son útiles, mantener pero referenciar claramente

---

### 🗂️ ESTRUCTURA RECOMENDADA POST-LIMPIEZA

```
/
├── README.md ✅ (PRINCIPAL - corregir terminología)
├── ESTADO_ACTUAL_2025-10-10.md ✅ (CONSOLIDADO)
├── ROADMAP_MVP_PRIORIDAD_ALTA.md ✅ (Fase 4+)
├── IMPLEMENTATION_PLAN_DETAILED.md ✅ (Plan Fase 4.3)
├── AUDITORIA_TECNICA_COMPLETA.md ✅ (Auditoría técnica)
│
├── backend/
│   ├── CHANGELOG.md ✅
│   ├── ROADMAP_BCD.md ✅ (Post-MVP específico)
│   ├── DEPLOY_CHECKLIST.md ✅
│   ├── DEPLOY_TUNING.md ✅
│   └── security_audit.md ✅
│
├── docs/
│   ├── INDEX.md ✅ (Índice de toda la doc)
│   ├── TROUBLESHOOTING.md ✅
│   ├── API_REFERENCE.md ✅
│   │
│   ├── adr/ (Consolidado)
│   │   ├── 000-template.md
│   │   ├── 001-no-pms-externo.md ✅
│   │   └── 002-daterange-back-to-back.md (mover desde backend)
│   │
│   ├── architecture/
│   │   └── TECHNICAL_ARCHITECTURE.md ✅
│   │
│   ├── deployment/
│   │   ├── README.md
│   │   ├── STAGING_DEPLOY_GUIDE.md ✅
│   │   └── ROLLBACK_PLAN.md ✅
│   │
│   ├── monitoring/
│   │   ├── MONITORING_SETUP.md ✅
│   │   └── ALERT_RUNBOOK.md ✅
│   │
│   ├── testing/
│   │   └── BEST_PRACTICES.md ✅
│   │
│   ├── security/
│   │   └── AUDIT_CHECKLIST.md ✅
│   │
│   ├── backup/
│   │   ├── BACKUP_STRATEGY.md ✅
│   │   └── DISASTER_RECOVERY.md ✅
│   │
│   ├── ci-cd/
│   │   └── GITHUB_ACTIONS_GUIDE.md ✅
│   │
│   └── archive/ (NUEVO - para docs antiguas)
│       ├── AUDITORIA_2025-09-27.md
│       ├── DAILY_LOG_2025-09-24.md
│       ├── FASE3_RESUMEN.md
│       ├── SESSION_SUMMARY_2025-10-09.md
│       ├── CIERRE_JORNADA_2025-10-09.md
│       └── FASE_4_1_COMPLETADA.md
│
└── archive/ (NUEVO - raíz)
    └── documentacion_externa/
        ├── alojamientos_partes_3_4.md
        ├── sistema_agentes_alojamientos_parte1.md
        └── Sistema_Agentico_MVP_Documentacion.markdown
```

---

## ✅ ACCIONES A EJECUTAR

### Fase 1: Crear Directorio Archive
```bash
mkdir -p docs/archive
mkdir -p archive/documentacion_externa
```

### Fase 2: Mover Archivos de Sesión Antiguos
```bash
mv SESSION_SUMMARY_2025-10-09.md docs/archive/
mv CIERRE_JORNADA_2025-10-09.md docs/archive/
mv FASE_4_1_COMPLETADA.md docs/archive/
```

### Fase 3: Archivar Docs Antiguas
```bash
mv docs/DAILY_LOG_2025-09-24.md docs/archive/
mv docs/FASE3_RESUMEN.md docs/archive/
mv backend/docs/AUDITORIA_2025-09-27.md docs/archive/
```

### Fase 4: Consolidar ADRs
```bash
# Mover ADR de backend a docs
mv backend/docs/adr/ADR-0001-daterange-back-to-back.md docs/adr/002-daterange-back-to-back.md

# Eliminar duplicado
rm docs/adr/ADR-001-no-pms-mvp.md  # Si es duplicado de 001-no-pms-externo.md
```

### Fase 5: Limpiar Archivos Externos (en workspace, no repo)
```bash
# Si están en el workspace pero fuera del repo
mv ../alojamientos_partes_3_4.md* archive/documentacion_externa/ 2>/dev/null || true
mv ../sistema_agentes_alojamientos_parte1.md* archive/documentacion_externa/ 2>/dev/null || true
mv ../Sistema_Agentico_MVP_Documentacion.markdown* archive/documentacion_externa/ 2>/dev/null || true
```

### Fase 6: Actualizar .gitignore
```bash
echo "
# Archived documentation
docs/archive/
archive/

# Zone.Identifier files from Windows
*.Zone.Identifier
" >> .gitignore
```

---

## 📝 CORRECCIONES DE TERMINOLOGÍA

### Archivos que requieren corrección de "agéntico" → "automatización"

1. **README.md** (CRÍTICO - público)
   - Línea ~8: "Sistema agéntico MVP" → "Sistema de automatización MVP"
   - Actualizar descripción completa

2. **.github/copilot-instructions.md**
   - Título: "Sistema Agéntico MVP" → "Sistema de Automatización MVP"
   - Clarificar que NO es agentes IA reales

3. **docs/architecture/TECHNICAL_ARCHITECTURE.md**
   - Referencias a arquitectura "agéntica"
   - Clarificar como "arquitectura de automatización"

4. **backend/README.md**
   - Actualizar referencias terminológicas

---

## 🎯 DOCUMENTACIÓN CONSOLIDADA FINAL

### Documentos Principales (Orden de lectura)
1. **README.md** - Inicio, quick start, features
2. **ESTADO_ACTUAL_2025-10-10.md** - Estado actual completo
3. **ROADMAP_MVP_PRIORIDAD_ALTA.md** - Plan de desarrollo
4. **IMPLEMENTATION_PLAN_DETAILED.md** - Plan Fase 4.3
5. **AUDITORIA_TECNICA_COMPLETA.md** - Auditoría técnica

### Documentos de Referencia
- **docs/INDEX.md** - Índice completo de documentación
- **docs/TROUBLESHOOTING.md** - Solución de problemas
- **docs/API_REFERENCE.md** - Referencia de API

---

## ⏱️ ESTIMACIÓN DE TIEMPO

- **Fase 1-3:** Mover archivos (15 min)
- **Fase 4:** Consolidar ADRs (10 min)
- **Fase 5:** Limpiar externos (5 min)
- **Fase 6:** Actualizar .gitignore (5 min)
- **Corrección terminología:** 30-45 min
- **Testing post-limpieza:** 15 min

**Total:** ~1.5 horas

---

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] Directorio `docs/archive/` creado
- [ ] Archivos de sesión movidos a archive
- [ ] ADRs consolidados en `docs/adr/`
- [ ] Archivos externos archivados
- [ ] .gitignore actualizado
- [ ] README.md terminología corregida
- [ ] copilot-instructions.md actualizado
- [ ] Git status clean (excepto archive/)
- [ ] Tests siguen pasando
- [ ] Commit de limpieza realizado

---

**Próximos pasos tras limpieza:**
1. ✅ Limpieza y consolidación
2. 🔄 Corrección de terminología
3. 🚀 Fase 4.3: Rate Limiting
4. 📧 Post-MVP: Email notifications
