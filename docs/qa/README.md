# 📚 Biblioteca de Prompts QA - Sistema MVP

Este directorio contiene la **Biblioteca Esencial de Prompts para QA de Sistemas** aplicada al Sistema MVP de Automatización de Reservas.

## 🎯 Estructura de la Biblioteca

La biblioteca consta de **20 prompts organizados en 5 fases**:

### 🔍 FASE 1: ANÁLISIS INICIAL (4 Prompts)
- **P001:** Auditoría Completa del Sistema ✅ **COMPLETADO**
- **P002:** Inventario de Dependencias y Vulnerabilidades
- **P003:** Matriz de Cobertura de Testing
- **P004:** Setup de Infraestructura de QA

### ⚡ FASE 2: TESTING CORE (6 Prompts)
- **P101:** Suite de Tests E2E Críticos
- **P102:** Tests de Consistencia del Agente IA
- **P103:** Detector de Loops Infinitos
- **P104:** Tests de Memory Leaks
- **P105:** Suite de Prompt Injection
- **P106:** Load Testing con k6

### 🛡️ FASE 3: SEGURIDAD (4 Prompts)
- **P301:** Threat Modeling LLM + OWASP LLM Top 10
- **P302:** DAST/API Security con OWASP ZAP
- **P303:** Secrets Scanning + SBOM
- **P304:** Guardrails en Runtime (Policy-as-Code)

### 📊 FASE 4: PERFORMANCE (3 Prompts)
- **P401:** Profiling y Flamegraphs (CPU/Mem/IO)
- **P402:** Eficiencia de Tokens y Costos
- **P403:** Observabilidad de Agentes (Métricas + Trazas)

### 🔧 FASE 5: OPERACIONES (3 Prompts)
- **P501:** Monitoring y Alertas Base
- **P502:** Chaos Engineering (Resiliencia)
- **P503:** Disaster Recovery + Backups

## 📋 Estado Actual

### ✅ Completado
- **P001: Auditoría Completa del Sistema**
  - Archivo: `P001_AUDITORIA_SISTEMA_COMPLETA.md`
  - Fecha: 14 Octubre 2025
  - Hallazgos: 5 riesgos críticos identificados
  - Roadmap: 4 semanas de mejoras planificadas
  - Scripts generados:
    - `../../tools/audit.sh` - Script de auditoría automatizada
    - `../../tools/summarize_vulns.py` - Consolidador de reportes de seguridad

### 🔄 En Progreso
- Ninguno actualmente

### ⏳ Pendiente
- P002 a P503 (19 prompts restantes)

## 🚀 Cómo Usar Esta Biblioteca

### Ejecución Individual
Para ejecutar un prompt específico:

1. Abrir el documento del prompt (ej: `P002_DEPENDENCIAS_Y_VULNERABILIDADES.md`)
2. Leer la sección "Prompt:" completa
3. Copiar el prompt a GitHub Copilot Chat
4. Completar placeholders si es necesario: `{PROYECTO}`, `{STACK}`, etc.
5. Ejecutar y validar outputs generados

### Ejecución Secuencial (Recomendado)
Para máxima cobertura, ejecutar en orden:

```bash
# Fase 1 - Análisis
P001 ✅ → P002 → P003 → P004

# Fase 2 - Testing Core
P101 → P102 → P103 → P104 → P105 → P106

# Fase 3 - Seguridad
P301 → P302 → P303 → P304

# Fase 4 - Performance
P401 → P402 → P403

# Fase 5 - Operaciones
P501 → P502 → P503
```

### Ejecución por Necesidad
Atajos según necesidad específica:

**"Necesito empezar QA desde cero"**
→ P001, P004, P003

**"Tengo vulnerabilidades de seguridad"**
→ P002, P105, P301–P304

**"El sistema es lento o caro"**
→ P106, P401–P403, P104

**"Quiero automatizar todo"**
→ P101–P103 + CI/CD en P004, P106

## 📊 Métricas de Progreso

| Fase | Prompts | Completados | % Completitud |
|------|---------|-------------|---------------|
| Fase 1 | 4 | 1 | 25% |
| Fase 2 | 6 | 0 | 0% |
| Fase 3 | 4 | 0 | 0% |
| Fase 4 | 3 | 0 | 0% |
| Fase 5 | 3 | 0 | 0% |
| **TOTAL** | **20** | **1** | **5%** |

## 🛠️ Scripts Generados

### `../../tools/audit.sh`
Script de auditoría completa del sistema.

**Uso:**
```bash
# Auditoría completa
./tools/audit.sh

# Auditoría rápida (omite tests)
./tools/audit.sh --quick

# Solo seguridad
./tools/audit.sh --security-only

# Solo performance
./tools/audit.sh --performance-only
```

**Genera:**
- `reports/audit_TIMESTAMP_system_info.txt`
- `reports/audit_TIMESTAMP_structure.txt`
- `reports/audit_TIMESTAMP_pip_audit.json`
- `reports/audit_TIMESTAMP_safety.json`
- `reports/audit_TIMESTAMP_trivy_fs.json`
- `reports/audit_TIMESTAMP_gitleaks.json`
- `reports/audit_TIMESTAMP_coverage.json`
- `reports/audit_TIMESTAMP_SUMMARY.txt`

### `../../tools/summarize_vulns.py`
Consolida reportes JSON de seguridad en Markdown ejecutivo.

**Uso:**
```bash
# Después de ejecutar audit.sh
python3 tools/summarize_vulns.py reports/
```

**Genera:**
- `reports/audit_TIMESTAMP_CONSOLIDATED_REPORT.md`
  - Resumen ejecutivo con métricas
  - Vulnerabilidades críticas priorizadas
  - Recomendaciones accionables

## 📈 Roadmap de Implementación

### Semana 1 (14-21 Oct 2025)
- ✅ P001: Auditoría completa
- ⏳ P002: Dependencias y vulnerabilidades
- ⏳ P003: Matriz de cobertura de testing
- ⏳ P004: Setup infraestructura QA

### Semana 2 (21-28 Oct 2025)
- ⏳ P101: Tests E2E críticos
- ⏳ P105: Suite prompt injection
- ⏳ P106: Load testing k6
- ⏳ P301: Threat modeling

### Semana 3 (28 Oct - 4 Nov 2025)
- ⏳ P102: Consistencia del agente
- ⏳ P104: Memory leaks
- ⏳ P302: DAST con ZAP
- ⏳ P303: Secrets + SBOM

### Semana 4 (4-11 Nov 2025)
- ⏳ P103: Detector de loops
- ⏳ P401-P403: Performance suite
- ⏳ P501-P503: Operaciones
- ⏳ P304: Guardrails runtime

## 🎯 Criterios de Éxito

Al completar todos los prompts, el sistema debe cumplir:

- ✅ **Cobertura de tests ≥70%**
- ✅ **0 vulnerabilidades críticas conocidas**
- ✅ **E2E tests en CI ejecutándose**
- ✅ **Load testing baseline establecido**
- ✅ **Threat model documentado y aprobado**
- ✅ **Distributed tracing operativo**
- ✅ **≥5 ADRs documentados**
- ✅ **Dashboards observabilidad completos**
- ✅ **Runbooks DR probados**
- ✅ **SBOM generándose en cada release**

## 📞 Contacto y Soporte

**Tech Lead:** Ver CODEOWNERS
**QA Manager:** Ver CONTRIBUTING.md
**Security Champion:** Ver docs/security/README.md

## 🔗 Referencias

- **Documentación principal:** `../../README.md`
- **Arquitectura técnica:** `../architecture/TECHNICAL_ARCHITECTURE.md`
- **Security audit:** `../../SECURITY_AUDIT_v1.0.0.md`
- **Performance benchmarks:** `../../PERFORMANCE_BENCHMARKS_v1.0.0.md`

---

**Última actualización:** 14 Octubre 2025
**Versión biblioteca:** 1.0
**Próxima revisión:** Al completar Fase 1 (4 prompts)
