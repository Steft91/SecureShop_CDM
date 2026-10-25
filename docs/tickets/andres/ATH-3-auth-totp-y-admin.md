# ATH-3: TOTP para los permisos de admin y alta del admin global por CLI (R4)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Incremento | Primer parcial |
| Necesita | [ATH-2](../andres/ATH-2-auth-registro-login-verify.md) (Andrés) |
| Lo necesitan | [ATH-4](../andres/ATH-4-auth-roles-y-permisos.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-3* |
| Estado | Pendiente |

## Objetivo

Los permisos `requires_mfa` exigen una sesión que pasó por TOTP; el primer admin se crea por CLI con su QR.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] El login de un admin → `{mfa: "required"}` (o `"setup"` si no tiene TOTP confirmado); el TOTP correcto da una sesión `full` con un `sid` **nuevo**
- [ ] Un código reusado se rechaza (`totp_last_step`); 5 fallos → bloqueo
- [ ] Un permiso de admin sin TOTP no vale (`test_r04_permiso_de_admin_sin_totp_no_vale`)
- [ ] `python -m auth_svc.create_admin <u>` crea la cuenta con el rol `admin` e imprime el QR y `TOTP_SECRET`

## Entregables

- `services/auth/auth_svc/{totp,create_admin}.py`
- Tests `test_admins.py`, `test_r04_totp.py`

## Documentación a actualizar

- Fila R4 de la trazabilidad

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
