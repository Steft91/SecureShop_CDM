# PAR-1: Colección de Postman del flujo del docente (RP-11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Entrega del parcial |
| Incremento | Primer parcial |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Lo necesitan | [PAR-3](../stefany/PAR-3-demo-y-ensayo.md) (Stefany) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../plans/2026-10-25-parcial-1.md), sección *Task PAR-1* |
| Estado | Pendiente |

> Necesita también las imágenes de STG-4.

## Objetivo

La colección que recorre los 5 pasos del docente, con un test por petición, y que corre completa en el Runner.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] Las 18 peticiones del plan, con sus `pm.test`, en verde dos veces seguidas en el Runner
- [ ] El TOTP lo calcula el *pre-request script* (sin escribir el código a mano)
- [ ] La colección no contiene contraseñas reales, el secreto TOTP ni tokens
- [ ] Captura del Runner en `docs/evidencias/parcial-1-runner.png`

## Entregables

- `docs/postman/parcial-1.postman_collection.json`
- `docs/postman/README.md`
- `docs/evidencias/parcial-1-runner.png`

## Documentación a actualizar

- *Verificación manual* de la trazabilidad

## Verificación

El Runner de Postman contra `https://localhost` (Step 3 del plan)

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
