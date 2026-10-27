# PAR-1: Colección de Postman del flujo del docente (RP-11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Entrega del parcial |
| Parcial | Primer parcial |
| Fase | C — integración y entrega |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith), [STG-4](../stefany/STG-4-stego-demo-y-calibracion.md) (Stefany) |
| Lo necesitan | [PAR-3](../stefany/PAR-3-demo-y-ensayo.md) (Stefany) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../../plans/2026-10-25-parcial-1.md), sección *Task PAR-1* |
| Estado | Pendiente |

## Objetivo

La colección que recorre el flujo del docente por el gateway, con un test por petición, y que corre completa en el Runner.

## Cómo trabajar sin esperar

Arma las carpetas, las 16 peticiones y sus `pm.test` con la tabla del plan antes de que el gateway esté arriba; solo la corrida del Runner espera a GW-1.

## Criterios de aceptación

- [ ] Las 16 peticiones del plan, con sus `pm.test`, en verde dos veces seguidas en el Runner
- [ ] El admin entra con `admin_username` y `admin_password`, variables de entorno solo locales
- [ ] La colección no contiene contraseñas reales ni tokens (Step 3)
- [ ] Captura del Runner en `docs/evidencias/parcial-1-runner.png`

## Entregables

- `docs/postman/parcial-1.postman_collection.json`
- `docs/postman/README.md`
- `docs/evidencias/parcial-1-runner.png`

## Documentación a actualizar

- *Verificación manual* de la trazabilidad

## Verificación

El Runner de Postman contra `https://localhost` (Step 2 del plan)

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
