# T-14 · ATH-4: Roles, permisos y administración de cuentas (R5)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Primer parcial |
| Bloqueado por | [T-13 · ATH-3](../andres/T-13-auth-totp-y-admin.md) (Andrés) |
| Desbloquea | [T-15 · STG-1](../zaith/T-15-stego-esqueleto-y-analisis.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-4* |
| Estado | Pendiente |

## Objetivo

CRUD de roles con permisos del catálogo, asignación de roles a usuarios y la protección del último admin.

## Criterios de aceptación

- [ ] Crear un rol con `["stego:analyze"]` y asignarlo: vale en la **siguiente** petición sin volver a entrar (`test_r05_rol_asignado_vale_en_la_siguiente_peticion`)
- [ ] Un permiso fuera del catálogo → 422; el rol `admin` no se edita ni se borra; `user` no se borra
- [ ] Quitarle `admin` al último admin activo → 409 y `admin.guard.last_admin` (con `pg_advisory_xact_lock`)
- [ ] Cada cambio se audita como obligatorio (`role.created`, `user.roles.changed`, …)

## Entregables

- `services/auth/auth_svc/admin.py`
- `services/auth/tests/test_r05_roles.py`

## Documentación a actualizar

- Fila R5 de la trazabilidad
- `CLAUDE.md`: marcar `auth` (parcial)

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-15
