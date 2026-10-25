# ROOM-4: Membresía interna y latido (R16)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Rooms |
| Incremento | Incremento 2 |
| Necesita | [ROOM-1](../andres/ROOM-1-rooms-crear-y-mis-salas.md) (Andrés) |
| Lo necesitan | [GW-2](../zaith/GW-2-gateway-salas-media-ws.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-05-rooms.md`](../../plans/2026-10-13-05-rooms.md), sección *Task ROOM-4* |
| Estado | Pendiente |

## Objetivo

Los contratos que usan `chat` y `media` para saber quién es miembro, con qué alias y si está silenciado.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-05-rooms.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `/internal/membership` → `{alias, mode, is_owner, muted_until}` o 404 (salió, fue expulsado o la sala cerró)
- [ ] El admin global sin membresía → 404 (no lee mensajes)
- [ ] Solo `chat` y `media` llaman a `/internal/membership`; solo `chat`, al latido
- [ ] El latido informa `member` y `muted_until` de cada par

## Entregables

- `services/rooms/rooms_svc/internal.py`
- `services/rooms/tests/test_r16_internas.py`

## Documentación a actualizar

- Fila R16 de la trazabilidad
- `CLAUDE.md`: marcar `rooms`

## Verificación

`pytest services/rooms -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Zaith de que ROOM-4 ya está cerrado
