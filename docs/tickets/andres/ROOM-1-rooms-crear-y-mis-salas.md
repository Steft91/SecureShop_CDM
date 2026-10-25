# ROOM-1: Esqueleto de `rooms`, crear sala y *Mis salas* (R1, R5, R8, R11, R15)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Rooms |
| Incremento | Incremento 2 |
| Necesita | [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [ROOM-2](../andres/ROOM-2-rooms-ingreso-y-salida.md) (Andrés), [ROOM-4](../andres/ROOM-4-rooms-membresia-interna.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-05-rooms.md`](../../plans/2026-10-13-05-rooms.md), sección *Task ROOM-1* |
| Estado | Pendiente |

> Los contratos de `audit` y `chat` se simulan con `testing.Recorder`.

## Objetivo

Salas con dueño: crear una sala (máximo 2 activas) y listar *Mis salas*.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-05-rooms.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] La clave de sala se guarda con Argon2id y nunca en claro; una clave débil → 422
- [ ] Sin `rooms:create` → 403; un cuerpo con `owner_id` → 422
- [ ] La tercera sala activa → `409 "ya tienes 2 salas activas"`; 3 creaciones concurrentes → exactamente 2
- [ ] El dueño queda como miembro (`member_count = 1`); `rooms` en estado `healthy` y en la CI

## Entregables

- `services/rooms/**` (esqueleto, migración, `schemas.py`, `notify.py`, `rooms.py`)
- Servicios `rooms` y `rooms-migrate` en compose

## Documentación a actualizar

- Filas R1, R11 y R15 de la trazabilidad

## Verificación

`pytest services/rooms -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
