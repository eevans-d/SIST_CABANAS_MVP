# 🤝 Contribuciones — Política y Buenas Prácticas

Este repositorio sigue un modelo de rama única para simplicidad operativa y control de costos.

## 🪵 Política de ramas

- Rama única: `main` (canónica).
- PRs son opcionales para cambios pequeños; requeridos para cambios riesgosos (seguridad, schema, deploy).
- No se mantienen ramas largas. Si necesitas una, bórrala al merge (squash recomendado).

## 🧾 Mensajes de commit

- Usa Conventional Commits cuando sea posible: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, etc.
- Commits pequeños y descriptivos; evita “misc”/“updates”.

## ✅ Checks locales antes de subir

- Hooks pre-commit ya configurados (`.pre-commit-config.yaml`).
- Lint/estilo: Black, Flake8, isort (se ejecutan vía hooks).
- Tests: `cd backend && pytest -q` (suite >180 tests). Algunos tests de overlap requieren PostgreSQL real con `btree_gist`.

## 📚 Documentación

- Índice canónico: `DOCUMENTATION_INDEX.md` (única fuente de verdad).
- Docs históricos marcados como “ARCHIVADO”. Evita editar históricos salvo aclaración.

## 🚀 Deploy (Fly.io) — Guardas de costo

- App única: `sist-cabanas-mvp` (región `gru`).
- Antes de desplegar: `./ops/deploy-check.sh` (debe mostrar “CHECKS OK”).
- Requiere `DEPLOY_ACK="I_ACCEPT_SINGLE_APP_COSTS"` y `--ha=false` (una sola instancia).

## 🔐 Seguridad

- Nunca subir secretos. Usa `.env` locales y `fly secrets` en staging/prod.
- Validar firmas webhooks SIEMPRE (WhatsApp `X-Hub-Signature-256`, Mercado Pago `x-signature`).
- No registrar datos sensibles en logs (PII, tokens).

## 🧩 Estilo y arquitectura

- Mantener la filosofía MVP: SHIPPING > PERFECCIÓN.
- No introducir microservicios ni complejidad innecesaria.
- Respetar el constraint anti doble-booking y locks Redis.

Gracias por contribuir con criterio y foco.
