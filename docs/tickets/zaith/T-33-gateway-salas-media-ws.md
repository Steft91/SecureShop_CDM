# T-33 · GW-2: Gateway: rutas de salas, media y WebSocket

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Incremento 2 |
| Bloqueado por | [T-32 · CHAT-4](../stefany/T-32-chat-avisos-y-latidos.md) (Stefany) |
| Desbloquea | [T-34 · FE-1](../andres/T-34-frontend-esqueleto-y-cripto.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-04-gateway.md`](../../plans/2026-10-13-04-gateway.md), sección *Task GW-2* |
| Estado | Pendiente |

## Objetivo

Agregar al gateway las rutas de `rooms`, `media` y `/ws`, todas con `proxy-user.conf`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-34
