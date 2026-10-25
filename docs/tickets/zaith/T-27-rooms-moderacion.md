# T-27 · ROOM-3: Administración de la sala por el dueño y el admin global (R5)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Incremento 2 |
| Bloqueado por | [T-26 · ROOM-2](../stefany/T-26-rooms-ingreso-y-salida.md) (Stefany) |
| Desbloquea | [T-28 · ROOM-4](../andres/T-28-rooms-membresia-interna.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-05-rooms.md`](../../plans/2026-10-13-05-rooms.md), sección *Task ROOM-3* |
| Estado | Pendiente |

## Objetivo

Editar, cerrar, ceder, expulsar con veto y silenciar, por el dueño o por el admin global con `rooms:manage_any`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-05-rooms.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Quien no es dueño → 403 y `room.forbidden`
- [ ] El admin global administra sin ser miembro (`details.as_admin`), pero no cambia la clave de una sala ajena
- [ ] Cerrar → `chat` cierra la sala, no se admiten ingresos y el código no se reutiliza
- [ ] Expulsar con veto → aviso 4411 y reingreso 403; silenciar → aviso `mute`; nunca al dueño

## Entregables

- `services/rooms/rooms_svc/manage.py`
- Tests `test_r05_dueno.py`, `test_moderacion.py`

## Documentación a actualizar

- Fila R5 de la trazabilidad

## Verificación

`pytest services/rooms -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-28
