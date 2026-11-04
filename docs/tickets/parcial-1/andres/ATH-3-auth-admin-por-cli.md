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
| Estado | Cerrado (2026-11-04, `75fbf19`) |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

El primer ADMIN se crea por línea de comandos, sin credenciales por defecto, y entra con su contraseña como cualquier cuenta.

## Cómo trabajar sin esperar

Solo depende de tu ATH-2.

## Criterios de aceptación

- [x] `python -m auth_svc.create_admin <usuario> --email <correo>` pide la contraseña dos veces (o la lee con `--password-stdin`), aplica la política de claves y crea la cuenta con el rol ADMIN
- [x] Imprime `admin <usuario> creado` y emite `admin.create` después del commit
- [x] Un usuario o correo duplicado falla sin tocar la cuenta existente
- [x] El admin entra con su contraseña y `check` le da todos los permisos del catálogo (`test_admins.py`)

## Entregables

- `services/auth/auth_svc/create_admin.py`
- `accounts.create_admin` y la fixture `admin`
- `services/auth/tests/test_admins.py`

## Documentación a actualizar

- Fila R4 de la trazabilidad

## Verificación

`pytest services/auth -q`

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
