# T-23 · ATH-5: Suspensión, reactivación, cambio de contraseña y latido de sesiones (R5, R13)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Incremento 2 |
| Bloqueado por | [T-22 · PAR-3](../andres/T-22-demo-y-ensayo.md) (Andrés) |
| Desbloquea | [T-24 · ATH-6](../zaith/T-24-auth-rotacion-kek.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-5* |
| Estado | Pendiente |

## Objetivo

Revocación inmediata de cuentas y el latido que usa `chat` para saber qué sesiones siguen vivas.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-24
