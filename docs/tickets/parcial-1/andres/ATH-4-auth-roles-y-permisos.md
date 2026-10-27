# ATH-4: Roles, permisos y administración de cuentas (R5)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [ATH-3](../andres/ATH-3-auth-admin-por-cli.md) (Andrés) |
| Lo necesitan | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../../plans/2026-10-13-03-auth.md), sección *Task ATH-4* |
| Estado | Pendiente |

## Objetivo

CRUD de roles con permisos del catálogo, asignación de roles a usuarios y la protección del último admin.

## Cómo trabajar sin esperar

Solo depende de tu ATH-3. Al cerrarla, avisa a Zaith: es lo que GW-1 espera de ti.

## Criterios de aceptación

- [ ] Crear un rol con `["stego:analyze"]` y asignarlo: vale en la **siguiente** petición sin volver a entrar (`test_r05_rol_asignado_vale_en_la_siguiente_peticion`)
- [ ] Un permiso fuera del catálogo → 422; el rol `admin` no se edita ni se borra; un rol con usuarios no se borra
- [ ] Quitarle `admin` al último admin → 409 y `admin.guard.last_admin` (con `pg_advisory_xact_lock`)
- [ ] Sin `roles:manage` o `users:manage` → 403
- [ ] Cada cambio emite su evento después del commit (`role.created`, `role.permissions.changed`, `role.deleted`, `user.roles.changed`)

## Entregables

- `services/auth/auth_svc/admin.py`
- `services/auth/tests/test_r05_roles.py`

## Documentación a actualizar

- Fila R5 de la trazabilidad
- `CLAUDE.md`: marcar `auth`

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
