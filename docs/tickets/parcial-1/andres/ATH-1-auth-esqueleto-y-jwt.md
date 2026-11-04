# ATH-1: Esqueleto de `auth`, modelo N:M, roles ADMIN/ANALYST/USER y firma de JWT (R11)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith), [FND-3](../andres/FND-3-argon2-y-limites.md) (Andrés), [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [ATH-2](../andres/ATH-2-auth-registro-login-verify.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../../plans/2026-10-13-03-auth.md), sección *Task ATH-1* |
| Estado | Pendiente |

> El paso de compose necesita además FND-6; los tests no.

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

Servicio `auth` con la migración de la spec §23.3 (`users`, `roles`, `permissions`, `role_permissions`, la N:M `user_roles`, `user_sessions` y `failed_attempts`), el catálogo de permisos y los roles semilla ADMIN, ANALYST y USER, la firma RS256 y el mínimo privilegio en la BD.

## Cómo trabajar sin esperar

`shared` ya está en `feat/zaith-fundaciones` (FND-2, 4, 5 y 6 cerrados); solo falta tu FND-3. Empieza por `0001_cuentas.py` y `tokens.py`: `Signer` solo usa `pyjwt` y `test_tokens.py` corre sin BD. El plan (Task ATH-1) sirve de base: cambia las tablas por las de §23.3.

## Criterios de aceptación

- [ ] Las tablas de §23.3 con sus FK, `UNIQUE (user_id, role_id)`, `username` y `email` únicos, `status` y campos de auditoría (`test_modelo_n_m_con_fk_y_unicidad`)
- [ ] El catálogo (`users.manage`, `roles.manage`, `steganography.analyze`, `steganography.results.read`, `steganography.results.read_any`) y los roles ADMIN (todos), ANALYST (`steganography.analyze`, `steganography.results.read`) y USER (ninguno) quedan como filas, no como constantes del código (`test_catalogo_y_roles_semilla`)
- [ ] `Signer` solo acepta `RS256`: `alg: none` o HS256 con la clave pública se rechazan; `exp = iat + JWT_TTL_MIN` (15 por defecto) (`test_tokens.py`)
- [ ] `auth_app` no puede `CREATE TABLE`, ni `DELETE` en `users` o `roles`, ni editar `permissions`; sí puede `DELETE` en `user_roles` (`test_r11_privilegios.py`)
- [ ] `services/auth/.env.example` con las variables no secretas (`JWT_TTL_MIN`, `ALLOWED_ORIGINS`, límites del login) y la nota de que los secretos los genera `deploy/gen_secrets.py`
- [ ] `auth` y `auth-migrate` en compose, con `auth` en `healthy`

## Entregables

- `services/auth/**` (esqueleto, `migrations/versions/0001_cuentas.py`, `config.py`, `tokens.py`, `main.py`, `.env.example`)
- Servicios `auth` y `auth-migrate` en compose

## Documentación a actualizar

- Fila R11 de la trazabilidad
- `docs/justificacion-criptografica.md` si cambia algo del JWT

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
