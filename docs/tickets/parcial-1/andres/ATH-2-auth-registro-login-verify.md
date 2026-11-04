# ATH-2: Login, JWT, sesión revocable, `authorization/check`, `profile` y `logout` (R4, R5, R16)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés) |
| Lo necesitan | [ATH-3](../andres/ATH-3-auth-admin-por-cli.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../../plans/2026-10-13-03-auth.md), sección *Task ATH-2* |
| Estado | Pendiente |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

Un login con bloqueo que entrega el JWT (sin cookies), sesiones revocables (una cuenta puede tener varias), el `POST /internal/authorization/check` que el gateway llama en cada petición y que decide **por acción** (spec §23.6), y `profile` y `logout`.

**Fuera de este ticket** (lo quitó el enunciado): el registro abierto, el alias, la cookie de dispositivo y la sesión única por cuenta.

## Cómo trabajar sin esperar

Solo depende de tu ATH-1. El plan (Task ATH-2) ya no tiene la cookie de dispositivo; de su código quita además el registro, el alias y la cookie `__Host-session`, y cambia `verify` por `check`.

## Criterios de aceptación

- [ ] `POST /api/auth/login` → `200 {access_token, token_type: "Bearer", expires_in}` sin `Set-Cookie`; `" ANA "` y `ana` son la misma cuenta (`test_usuario_normalizado_al_crear_y_en_login`)
- [ ] Clave mala y usuario inexistente → el mismo `401 "credenciales inválidas"`; 5 fallos en 15 min por usuario o IP → 429 + `Retry-After` (`test_r04_*`); cuenta `inactive` → 403 después de verificar la contraseña
- [ ] `check` sin token, con el JWT alterado o vencido → 401 (`test_jwt_alterado_401`, `test_jwt_vencido_401`); con la sesión terminada o la cuenta inactiva → 401 (`test_jwt_de_sesion_terminada_401`, `test_cuenta_inactiva_401`)
- [ ] `check` traduce `X-Original-URI` a la acción de §23.6 y responde `200 {subject_id, action, allowed: true, reason}` con `X-User-Id`, `X-User-Name`, `X-Session-Id` y `X-User-Perms`, o `403 {allowed: false, …}` y `authz.denied`; la ruta se compara por segmentos completos (`/api/usersx` no es `/api/users`) y una que no está en el mapa → 403 (`test_check_decide_por_accion`)
- [ ] Solo cuentan los roles `active`; el claim `roles` del JWT no autoriza nada
- [ ] `check` solo acepta al gateway (`test_r16_check_solo_para_el_gateway`)
- [ ] `GET /api/auth/profile` → `{id, username, email, status, roles, permissions}`; `POST /api/auth/logout` → 204 y el mismo JWT da 401 después
- [ ] Eventos JSON `auth.login.ok`, `auth.login.fail`, `auth.login.locked`, `auth.login.inactive`, `auth.logout` y `authz.denied`, sin el JWT ni la contraseña

## Entregables

- `services/auth/auth_svc/{accounts,sessions,routes,internal}.py`
- Tests `test_r04_login.py`, `test_sesiones.py`, `test_r16_check.py`

## Documentación a actualizar

- Filas R4, R5 y R16 de la trazabilidad (R13 queda *Fuera del parcial*)

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
