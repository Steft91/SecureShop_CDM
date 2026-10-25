# CHAT-1: Esqueleto de `chat`, almacén cifrado y rotación (R2, R11)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Chat |
| Incremento | Incremento 2 |
| Necesita | [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [CHAT-2](../zaith/CHAT-2-chat-conexion.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-06-chat.md`](../../plans/2026-10-13-06-chat.md), sección *Task CHAT-1* |
| Estado | Pendiente |

## Objetivo

Mensajes cifrados en reposo con una DEK por sala, borrado que destruye el contenido y rotación de claves.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-06-chat.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Ni `payload` ni `dek_wrapped` contienen el texto en claro
- [ ] Un `payload` copiado a otro autor no descifra (AAD con `user_id`)
- [ ] `rotate kek` y `rotate room <id>` mantienen el historial legible
- [ ] `chat` en estado `healthy` y en la CI

## Entregables

- `services/chat/**` (esqueleto, migración, `store.py`, `rotate.py`)
- Servicios `chat` y `chat-migrate` en compose

## Documentación a actualizar

- Filas R2 y R11 de la trazabilidad

## Verificación

`pytest services/chat -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
