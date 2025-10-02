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
