# GW-2: Gateway: rutas de salas, media y WebSocket

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Gateway |
| Incremento | Incremento 2 |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith), [ROOM-4](../andres/ROOM-4-rooms-membresia-interna.md) (Andrés), [CHAT-4](../zaith/CHAT-4-chat-avisos-y-latidos.md) (Zaith) |
| Lo necesitan | [FE-3](../stefany/FE-3-frontend-chat-y-dueno.md) (Stefany), [E2E-1](../zaith/E2E-1-e2e-cuentas-y-gateway.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-04-gateway.md`](../../plans/2026-10-13-04-gateway.md), sección *Task GW-2* |
| Estado | Pendiente |

## Objetivo

Agregar al gateway las rutas de `rooms`, `media` y `/ws`, todas con `proxy-user.conf`.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-04-gateway.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `nginx -t` → `test is successful`
- [ ] `http://localhost/ws` → 301; `/api/rooms/mine` sin sesión → 401
- [ ] `POST /api/media/files` de 6 MB → 413 JSON
- [ ] El WebSocket abre con `wss://localhost/ws?room=<id>`

## Entregables

- `gateway/nginx.conf`

## Documentación a actualizar

- *Verificación manual* de la trazabilidad

## Verificación

El Step 2 del plan (curl)

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Stefany de que GW-2 ya está cerrado
