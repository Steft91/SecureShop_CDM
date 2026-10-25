# MED-1: Esqueleto de `media`, archivos cifrados y rotación (R2, R11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Media |
| Incremento | Incremento 3 |
| Necesita | [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [MED-2](../stefany/MED-2-media-subida-y-clamav.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-07-media.md`](../../plans/2026-10-13-07-media.md), sección *Task MED-1* |
| Estado | Pendiente |

## Objetivo

Guardar cada archivo cifrado con su propia DEK y poder rotar la KEK sin tocar los archivos.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
