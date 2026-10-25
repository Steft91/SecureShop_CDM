# E2E-1: E2E: arnés, cuentas, RBAC y reglas del gateway (R4, R5, R13, R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | E2E y cierre |
| Incremento | Incremento 3 |
| Necesita | [GW-2](../zaith/GW-2-gateway-salas-media-ws.md) (Zaith), [ATH-5](../andres/ATH-5-auth-suspension-y-latido.md) (Andrés) |
| Lo necesitan | [E2E-2](../zaith/E2E-2-e2e-chat-e-imagenes.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-09-e2e-cierre.md`](../../plans/2026-10-13-09-e2e-cierre.md), sección *Task E2E-1* |
| Estado | Pendiente |

## Objetivo

Probar contra el stack real lo que cruza servicios en las cuentas y en el gateway.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-09-e2e-cierre.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Segundo dispositivo → 409; un JWT robado sin la cookie de dispositivo → 401
- [ ] El rol asignado vale sin volver a entrar; un permiso de admin sin TOTP no vale
- [ ] Suspensión → 401 en la siguiente petición
- [ ] `/internal/*` → 404; cabeceras de identidad falsificadas ignoradas; http → 301; TLS 1.2 rechazado

## Entregables

- `e2e/{pytest.ini,conftest.py,requirements.txt}`
- `e2e/test_cuentas.py`, `e2e/test_gateway.py`

## Documentación a actualizar

- Filas R4, R5, R13 y R16 de la trazabilidad

## Verificación

`pytest e2e -q -k "cuentas or gateway"` con el stack levantado

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
