# T-20 · PAR-1: Colección de Postman del flujo del docente (RP-11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Primer parcial |
| Bloqueado por | [T-19 · GW-1](../andres/T-19-gateway-parcial.md) (Andrés) |
| Desbloquea | [T-21 · PAR-2](../zaith/T-21-informe-parcial.md) (Zaith) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../plans/2026-10-25-parcial-1.md), sección *Task PAR-1* |
| Estado | Pendiente |

## Objetivo

La colección que recorre los 5 pasos del docente, con un test por petición, y que corre completa en el Runner.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-21
