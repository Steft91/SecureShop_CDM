# CHAT-4: Avisos internos, archivos publicados, latidos e inactividad (R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Chat |
| Incremento | Incremento 2 |
| Necesita | [CHAT-3](../zaith/CHAT-3-chat-tramas-y-mensajes.md) (Zaith) |
| Lo necesitan | [GW-2](../zaith/GW-2-gateway-salas-media-ws.md) (Zaith), [E2E-2](../zaith/E2E-2-e2e-chat-e-imagenes.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-06-chat.md`](../../plans/2026-10-13-06-chat.md), sección *Task CHAT-4* |
| Estado | Pendiente |

> Los latidos de `auth` (ATH-5) y `rooms` (ROOM-4) se simulan con `testing.Recorder`.

## Objetivo

Obedecer a `auth`, `rooms` y `media` al instante, y reconciliar cada 30 s cualquier aviso perdido.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-06-chat.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Cada ruta interna acepta solo a su llamador (`auth`, `rooms` o `media`)
- [ ] `disconnect` → 4401 en todas las salas; `kick` → 4411 solo en esa sala; `close` → 4401 a toda la sala
- [ ] Un archivo publicado llega con una URL firmada distinta para cada destinatario
- [ ] Latidos: `ended` de `auth` y `member: false` de `rooms` cierran la conexión; 15 min sin actividad → 4410

## Entregables

- `services/chat/chat_svc/{internal,tasks}.py`
- Tests `test_r16_internas.py`, `test_avisos.py`, `test_latidos.py`

## Documentación a actualizar

- Fila R16 de la trazabilidad
- `CLAUDE.md`: marcar `chat`

## Verificación

`pytest services/chat -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
