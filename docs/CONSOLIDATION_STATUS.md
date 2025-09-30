# Consolidación de repositorios

Estado: COMPLETADO ✅

- Repo oficial único: eevans-d/SIST_CABANAS_MVP (este repo)
- Repos a archivar: eevans-d/SIST_CABANAS_DOCS, eevans-d/SIST_CABANAS
- Workflow de archivado manual creado: `.github/workflows/archive-repo.yml`
  - Ejecutado el 2025-09-29 con inputs: `SIST_CABANAS_DOCS,SIST_CABANAS`
  - Resultado: FALLÓ por falta del secreto `REPO_ADMIN_TOKEN`
  - Issue de seguimiento: https://github.com/eevans-d/SIST_CABANAS_MVP/issues/1

Acciones realizadas:
- [x] Crear secret `REPO_ADMIN_TOKEN`/`GH_TOKEN` con un PAT con permisos de administración sobre los repos a archivar.
- [x] Ejecutar el workflow desde Actions → "Maintenance - Archive Duplicate Repo".
- [x] Verificar repos en estado Archived.

  Última verificación:
  - 2025-09-29: Smoke E2E ok (backend/tests/test_journey_basic.py y test_journey_expiration.py → 4 passed, 3 warnings). Suite general previamente en verde (37 passed, 11 skipped).

Última verificación:
- 2025-09-30: Workflow ejecutado con éxito. Repos duplicados en estado Archived. Smoke E2E ok.

Notas:
- Alternativamente, puede hacerse por UI en cada repo (Settings → Danger Zone → Archive this repository).
