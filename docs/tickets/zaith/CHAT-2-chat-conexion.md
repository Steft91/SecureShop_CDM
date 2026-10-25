# CHAT-2: Conexión: identidad, membresía, `Origin`, *hello* firmado y presencia (R7, R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Chat |
| Incremento | Incremento 2 |
| Necesita | [CHAT-1](../zaith/CHAT-1-chat-almacen-cifrado.md) (Zaith) |
| Lo necesitan | [CHAT-3](../zaith/CHAT-3-chat-tramas-y-mensajes.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-06-chat.md`](../../plans/2026-10-13-06-chat.md), sección *Task CHAT-2* |
| Estado | Pendiente |

> La membresía de `rooms` (ROOM-4) se simula con `testing.Recorder`.

## Objetivo

Abrir el WebSocket solo para miembros, desde el origen permitido, con el handshake ECDH firmado.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-06-chat.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Sin la identidad del gateway → 4401; `Origin` ajeno → 4403; quien no es miembro → 4403
- [ ] El *hello* firmado se verifica con la clave pública y falla con otra `client_pub`
- [ ] Sin `hello` en el plazo → 4400; una segunda conexión del mismo usuario reemplaza a la primera (4409)
- [ ] Presencia `join`/`leave` e historial al conectar

## Entregables

- `services/chat/chat_svc/{ws,hub}.py`
- Tests `test_r07_canal.py`, `test_conexion.py`

## Documentación a actualizar

- Filas R7 y R16 de la trazabilidad

## Verificación

`pytest services/chat -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
