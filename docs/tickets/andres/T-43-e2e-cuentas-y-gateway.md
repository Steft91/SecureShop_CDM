# T-43 · E2E-1: E2E: arnés, cuentas, RBAC y reglas del gateway (R4, R5, R13, R16)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Incremento 3 |
| Bloqueado por | [T-42 · FE-5](../zaith/T-42-frontend-panel-admin.md) (Zaith) |
| Desbloquea | [T-44 · E2E-2](../stefany/T-44-e2e-chat-e-imagenes.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-09-e2e-cierre.md`](../../plans/2026-10-13-09-e2e-cierre.md), sección *Task E2E-1* |
| Estado | Pendiente |

## Objetivo

Probar contra el stack real lo que cruza servicios en las cuentas y en el gateway.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-44
