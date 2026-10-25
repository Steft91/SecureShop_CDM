# ATH-4: Roles, permisos y administración de cuentas (R5)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Incremento | Primer parcial |
| Necesita | [ATH-3](../andres/ATH-3-auth-totp-y-admin.md) (Andrés) |
| Lo necesitan | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith), [ATH-5](../andres/ATH-5-auth-suspension-y-latido.md) (Andrés), [ATH-6](../andres/ATH-6-auth-rotacion-kek.md) (Andrés), [FE-2](../stefany/FE-2-frontend-cuenta-y-salas.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-4* |
| Estado | Pendiente |

## Objetivo

CRUD de roles con permisos del catálogo, asignación de roles a usuarios y la protección del último admin.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Stefany y Zaith de que ATH-4 ya está cerrado
