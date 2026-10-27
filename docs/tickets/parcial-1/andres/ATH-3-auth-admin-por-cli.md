# ATH-3: Alta del admin global por CLI (R4)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [ATH-2](../andres/ATH-2-auth-registro-login-verify.md) (Andrés) |
| Lo necesitan | [ATH-4](../andres/ATH-4-auth-roles-y-permisos.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../../plans/2026-10-13-03-auth.md), sección *Task ATH-3* |
| Estado | Pendiente |

## Objetivo

El primer admin se crea por línea de comandos, sin credenciales por defecto, y entra con su contraseña como cualquier cuenta.

## Cómo trabajar sin esperar

Solo depende de tu ATH-2.

## Criterios de aceptación

- [ ] `python -m auth_svc.create_admin <usuario>` pide la contraseña dos veces (o la lee con `--password-stdin`), aplica la política de claves y crea la cuenta con el rol `admin`
- [ ] Imprime `admin <usuario> creado` y emite `admin.create` después del commit
- [ ] Un usuario duplicado falla sin tocar la cuenta existente
- [ ] El admin entra con su contraseña y `verify` le da los tres permisos (`test_admins.py`, 4 tests)

## Entregables

- `services/auth/auth_svc/create_admin.py`
- `accounts.create_admin` y la fixture `admin`
- `services/auth/tests/test_admins.py`

## Documentación a actualizar

- Fila R4 de la trazabilidad

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
