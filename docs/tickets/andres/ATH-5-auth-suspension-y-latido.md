# ATH-5: Suspensión, reactivación, cambio de contraseña y latido de sesiones (R5, R13)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Incremento | Incremento 2 |
| Necesita | [ATH-4](../andres/ATH-4-auth-roles-y-permisos.md) (Andrés) |
| Lo necesitan | [FE-5](../andres/FE-5-frontend-panel-admin.md) (Andrés), [E2E-1](../zaith/E2E-1-e2e-cuentas-y-gateway.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-5* |
| Estado | Pendiente |

## Objetivo

Revocación inmediata de cuentas y el latido que usa `chat` para saber qué sesiones siguen vivas.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] Suspender termina las sesiones, pide a `chat` cerrar sus WebSockets y la siguiente petición da 401; el login → `403 "cuenta suspendida"`
- [ ] Nadie se suspende a sí mismo; no se suspende al último admin (409)
- [ ] Cambiar la contraseña exige la actual, aplica la política y termina la sesión
- [ ] `/internal/sessions/heartbeat` (solo `chat`) devuelve las sesiones `ended`

## Entregables

- `services/auth/auth_svc/{sessions,admin,routes,internal}.py`
- Tests `test_r05_suspension.py`, `test_cuenta.py`

## Documentación a actualizar

- Filas R5 y R13 de la trazabilidad

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Zaith de que ATH-5 ya está cerrado
