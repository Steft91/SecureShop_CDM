# T-26 · ROOM-2: Ingreso, salida y miembros (R8, R15)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Incremento 2 |
| Bloqueado por | [T-25 · ROOM-1](../andres/T-25-rooms-crear-y-mis-salas.md) (Andrés) |
| Desbloquea | [T-27 · ROOM-3](../zaith/T-27-rooms-moderacion.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-05-rooms.md`](../../plans/2026-10-13-05-rooms.md), sección *Task ROOM-2* |
| Estado | Pendiente |

## Objetivo

Ingreso único con código + clave + alias, membresía persistente y salida.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-05-rooms.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Clave mala y sala inexistente dan el mismo `401 "sala o clave inválida"`; rate limit por IP, usuario y sala → 429
- [ ] El veto se revisa **después** de la clave
- [ ] 20 ingresos concurrentes con `max_members=6` → exactamente 5 aceptados
- [ ] El alias de quien salió sigue reservado; el dueño no puede salir sin ceder (409)

## Entregables

- `services/rooms/rooms_svc/rooms.py`
- Tests `test_ingreso.py`, `test_r08_rate_limit.py`, `test_r15_cupo.py`, `test_salida.py`

## Documentación a actualizar

- Filas R8 y R15 de la trazabilidad

## Verificación

`pytest services/rooms -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-27
