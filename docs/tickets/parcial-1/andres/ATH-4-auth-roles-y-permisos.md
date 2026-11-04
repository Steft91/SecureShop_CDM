# ATH-4: Usuarios, roles y asignaciones N:M (R5)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [ATH-3](../andres/ATH-3-auth-admin-por-cli.md) (Andrés) |
| Lo necesitan | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../../plans/2026-10-13-03-auth.md), sección *Task ATH-4* |
| Estado | Cerrado (2026-11-04, `b48a710`) |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

Las rutas de administración de la spec §23.4 (`/api/users`, `/api/roles` y `/api/user-roles`), la protección del último ADMIN y el OpenAPI de `auth`.

## Cómo trabajar sin esperar

Solo depende de tu ATH-3. Al cerrarla, avisa a Zaith: es lo que GW-1 espera de ti. El plan (Task ATH-4) sirve de base: sus rutas `/api/admin/*` pasan a las de §23.4.

## Criterios de aceptación

- [x] `POST` y `GET /api/users` y `PATCH /api/users/{id}` con `users.manage`: la cuenta nace sin roles; usuario o correo repetido → 409 (`test_admin_crea_cuenta_sin_roles`, `test_usuario_o_correo_duplicado_409`); `status = inactive` termina sus sesiones
- [x] `POST` y `GET /api/roles` y `PATCH /api/roles/{id}` con `roles.manage`: permiso fuera del catálogo → 422; ADMIN no se edita (409); un rol `inactive` no da permisos
- [x] `POST /api/user-roles`: una cuenta con dos roles y un rol en dos cuentas (T05, `test_n_m_dos_roles_y_dos_usuarios`); repetir la asignación → 409 sin fila nueva (T06, `test_asignacion_repetida_409`)
- [x] `DELETE /api/user-roles/{id}`: el mismo JWT pierde el permiso en la siguiente petición (T07, `test_r05_rol_retirado_deja_de_valer_con_el_mismo_jwt`); asignar vale igual de rápido (`test_r05_rol_asignado_vale_en_la_siguiente_peticion`)
- [x] Retirarle ADMIN o desactivar al último ADMIN activo → 409 y `admin.guard.last_admin` (con `pg_advisory_xact_lock`); nadie se desactiva a sí mismo
- [x] Sin escalada: sin el rol ADMIN no se asigna ni retira ADMIN, ni se crea o edita un rol con `users.manage` o `roles.manage` → 403 y `authz.denied` (`test_r05_sin_admin_no_concede_permisos_de_admin`)
- [x] Sin el permiso → 403; un campo de más en el cuerpo → 422
- [x] Eventos `user.created`, `user.updated`, `role.created`, `role.updated`, `user_role.assigned` y `user_role.revoked` después del commit (`actor` = el admin)
- [x] `docs/openapi/auth.json` exportado con `app.openapi()`, con `/internal/authorization/check` incluido

## Entregables

- `services/auth/auth_svc/admin.py`
- `services/auth/tests/test_r05_roles.py`, `services/auth/tests/test_usuarios.py`
- `docs/openapi/auth.json`

## Documentación a actualizar

- Fila R5 de la trazabilidad
- `CLAUDE.md`: marcar `auth`

## Verificación

`pytest services/auth -q`

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
