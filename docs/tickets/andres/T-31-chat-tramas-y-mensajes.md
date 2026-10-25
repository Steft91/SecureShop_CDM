# T-31 · CHAT-3: Tramas, mensajes, silencio, borrado y `file_url` (R10, R14)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Incremento 2 |
| Bloqueado por | [T-30 · CHAT-2](../zaith/T-30-chat-conexion.md) (Zaith) |
| Desbloquea | [T-32 · CHAT-4](../stefany/T-32-chat-avisos-y-latidos.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-06-chat.md`](../../plans/2026-10-13-06-chat.md), sección *Task CHAT-3* |
| Estado | Pendiente |

## Objetivo

El bucle de tramas con límites y anti-replay, los mensajes, el silencio, el borrado y la renovación de URLs.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-06-chat.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Trama > 16 KB → 4413; ráfaga → 4429; `seq` repetido → 4408; tag alterado → 4400 y `ws.tamper` critical
- [ ] 2000 emojis no cierran la conexión y 2001 caracteres → 4400 (`test_mensaje_largo_multibyte_no_cierra`)
- [ ] El remitente sale del alias de `rooms`; un campo `from` → 4400
- [ ] Silenciado → trama `error muted` y la conexión sigue; borrar un mensaje ajeno sin ser dueño → 4403
- [ ] Guardar y difundir van bajo un candado por sala: 3 participantes con 90 mensajes ven el mismo orden que el historial (`test_rnf14_*`)

## Entregables

- `services/chat/chat_svc/ws.py`
- Tests `test_r10_limites.py`, `test_r14_integridad.py`, `test_mensajes.py`, `test_borrado.py`

## Documentación a actualizar

- Filas R10 y R14 de la trazabilidad

## Verificación

`pytest services/chat -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-32
