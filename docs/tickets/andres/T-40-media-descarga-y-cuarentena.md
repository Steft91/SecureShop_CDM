# T-40 · MED-4: Descarga firmada y cuarentena del admin global (R5, R12)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Incremento 3 |
| Bloqueado por | [T-39 · MED-3](../zaith/T-39-media-politica-y-publicacion.md) (Zaith) |
| Desbloquea | [T-41 · FE-4](../stefany/T-41-frontend-imagenes.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-07-media.md`](../../plans/2026-10-13-07-media.md), sección *Task MED-4* |
| Estado | Pendiente |

## Objetivo

Descargas solo con URL firmada para ese usuario y con su membresía vigente; la revisión de la cuarentena.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-07-media.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Firma de otro usuario, vencida o alterada, quien ya no es miembro o un archivo en cuarentena → 404
- [ ] Archivo alterado en disco → 404 y `file.integrity.failed`, nunca 500
- [ ] La cuarentena exige `quarantine:manage` (con `rooms:manage_any` solamente → 403)
- [ ] Liberar sanitiza, genera una DEK nueva y publica; eliminar borra el archivo

## Entregables

- `services/media/media_svc/{routes,admin}.py`
- Tests `test_r12_descarga.py`, `test_cuarentena.py`

## Documentación a actualizar

- Filas R5 y R12 de la trazabilidad
- `CLAUDE.md`: marcar `media`

## Verificación

`pytest services/media -q -m "not clamav"`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-41
