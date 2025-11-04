---
name: Pull Request
about: Template para pull requests
title: ''
labels: ''
assignees: ''
---

## 📝 Descripción

Descripción clara y concisa de los cambios implementados.

## 🔗 Issue Relacionado

Closes #[número]
Relates to #[número]

## 🎯 Tipo de Cambio

- [ ] 🐛 Bug fix (cambio que corrige un issue)
- [ ] ✨ Nueva funcionalidad (cambio que añade funcionalidad)
- [ ] 💥 Breaking change (cambio que rompe compatibilidad)
- [ ] 📚 Documentación
- [ ] ♻️ Refactorización (sin cambio funcional)
- [ ] ⚡ Performance
- [ ] 🧪 Tests

## 🧪 ¿Cómo se Probó?

Descripción detallada de cómo se probaron los cambios:

- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Tests manuales
- [ ] Smoke tests

**Comandos ejecutados:**
```bash
pytest tests/test_nueva_feature.py -v
```

**Resultado:** [descripción de resultados]

## 📸 Screenshots / Logs

Si aplica, agregar screenshots o logs que demuestren el cambio.

## ✅ Checklist Pre-Merge

### Code Quality
- [ ] Tests añadidos/actualizados (coverage > 80%)
- [ ] Todos los tests pasan (`pytest tests/ -v`)
- [ ] CI "CI - Tests" pasando en GitHub Actions
- [ ] CI "CI - Lint & Types" pasando en GitHub Actions
- [ ] Linting ok (`flake8 app/ tests/`)
- [ ] Format ok (`black app/ tests/ --check`)
- [ ] Type checking ok (`mypy app/`) [si aplica]

### Commits
- [ ] Commits siguen convención (feat/fix/docs/etc)
- [ ] Mensajes de commit descriptivos
- [ ] Branch actualizado con `main`

### Documentation
- [ ] Documentación actualizada (README, CHANGELOG, etc)
- [ ] Docstrings añadidos/actualizados
- [ ] CHANGELOG.md actualizado [si aplica]
- [ ] ADR creado [si decisión arquitectónica]

### Security
- [ ] Sin secretos hardcoded
- [ ] Sin logs de información sensible
- [ ] Validaciones de entrada implementadas
- [ ] Manejo de errores apropiado
- [ ] Webhooks con firma HMAC validados y tests pasando (WhatsApp/MercadoPago)
- [ ] Constraint anti doble-booking activo (PostgreSQL EXCLUDE gist) y no alterado
- [ ] Locks Redis presentes en operaciones críticas (reservas)

### Performance
- [ ] No hay regresiones de performance
- [ ] Queries optimizadas [si aplica DB]
- [ ] N+1 queries evitados [si aplica]

## 📊 Métricas de Coverage

```
Coverage: XX% (antes: YY%)
```

## 🚨 Breaking Changes

Si este PR incluye breaking changes, describirlos aquí:

- **Cambio 1:** [descripción + cómo migrar]
- **Cambio 2:** [descripción + cómo migrar]

## 🔍 Revisión Sugerida

Áreas específicas donde necesitas feedback:

- [ ] Arquitectura/diseño
- [ ] Lógica de negocio
- [ ] Performance
- [ ] Seguridad
- [ ] UX/DX

## 📋 Deploy Checklist [si aplica]

- [ ] Migraciones DB creadas y probadas
- [ ] Variables de entorno documentadas en `.env.template`
- [ ] Cambios en nginx/docker-compose documentados
- [ ] Plan de rollback definido
- [ ] (`btree_gist`) habilitado en Postgres para entornos nuevos

## 🛡️ Guardas de Costo y Política (si aplica a deploy)

- [ ] Ejecuté `./ops/deploy-check.sh` y obtuve: CHECKS OK
- [ ] App única en Fly: `sist-cabanas-mvp`, región `gru`, usando `--ha=false`
- [ ] Exporté `DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"`
- [ ] Confirmo NO modificar constraint anti doble-booking ni locks Redis sin aprobación
- [ ] Leí `CONTRIBUTING.md` (política de rama única y convenciones)

## 🎓 Notas para Reviewers

Información adicional relevante para quienes revisan:

- Decisiones técnicas importantes
- Trade-offs considerados
- Áreas de incertidumbre

## 🔗 Referencias

Links a documentación, tickets, discusiones, etc.

---

**Antes de marcar como "Ready for review":**
- [ ] He revisado mi propio código
- [ ] He probado los cambios localmente
- [ ] Los CI checks están pasando
- [ ] He resuelto todos los comentarios pendientes
