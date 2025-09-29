# Consolidación de repositorios

Estado: EN PROCESO (esperando secreto de Actions)

- Repo oficial único: eevans-d/SIST_CABANAS_MVP (este repo)
- Repos a archivar: eevans-d/SIST_CABANAS_DOCS, eevans-d/SIST_CABANAS
- Workflow de archivado manual creado: `.github/workflows/archive-repo.yml`
  - Ejecutado el 2025-09-29 con inputs: `SIST_CABANAS_DOCS,SIST_CABANAS`
  - Resultado: FALLÓ por falta del secreto `REPO_ADMIN_TOKEN`
  - Issue de seguimiento: https://github.com/eevans-d/SIST_CABANAS_MVP/issues/1

Acción pendiente (dueño del repo):
- [ ] Crear secret `REPO_ADMIN_TOKEN` con un PAT que tenga permisos de administración sobre los repos a archivar.
- [ ] Re-ejecutar el workflow desde Actions → "Maintenance - Archive Duplicate Repo".

Notas:
- Alternativamente, archivar manualmente por UI en cada repo (Settings → Danger Zone → Archive this repository).
- Una vez archivados, actualizar este archivo a Estado: COMPLETADO.
