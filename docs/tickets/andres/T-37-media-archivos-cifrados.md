# T-37 · MED-1: Esqueleto de `media`, archivos cifrados y rotación (R2, R11)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Incremento 3 |
| Bloqueado por | [T-36 · FE-3](../zaith/T-36-frontend-chat-y-dueno.md) (Zaith) |
| Desbloquea | [T-38 · MED-2](../stefany/T-38-media-subida-y-clamav.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-07-media.md`](../../plans/2026-10-13-07-media.md), sección *Task MED-1* |
| Estado | Pendiente |

## Objetivo

Guardar cada archivo cifrado con su propia DEK y poder rotar la KEK sin tocar los archivos.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-07-media.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] En disco no aparecen ni los bytes del PNG ni su `IHDR`; `vault.load` devuelve el original
- [ ] Un bit alterado o la DEK de otro archivo → `InvalidTag`
- [ ] `rotate_kek` deja todo en la versión nueva y los archivos intactos
- [ ] `media` en estado `healthy` y en la CI

## Entregables

- `services/media/**` (esqueleto, migración, `vault.py`, `rotate_kek.py`)
- Servicios `media` y `media-migrate` en compose

## Documentación a actualizar

- Filas R2 y R11 de la trazabilidad

## Verificación

`pytest services/media -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-38
