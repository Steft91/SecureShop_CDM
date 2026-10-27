# ATH-2: Registro con alias, login, JWT y sesión de dispositivo único, `verify`, `me` y `logout` (R4, R5, R10, R13, R16)

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

## Objetivo

Cuentas con registro abierto (usuario, contraseña y alias visible) y sin roles, un login con bloqueo que entrega el JWT, una sesión por cuenta ligada al dispositivo, y el `verify` que el gateway llama en cada petición.

## Cómo trabajar sin esperar

Solo depende de tu ATH-1.

## Criterios de aceptación

- [ ] El registro pide `alias` (RF-20) y no asigna roles; un cuerpo con `role` → 422; `" ANA "` y `ana` son la misma cuenta (`test_usuario_normalizado_en_registro_y_login`)
- [ ] El alias se normaliza, es único sin distinguir mayúsculas y rechaza caracteres de control y `<>` (`test_alias_duplicado_sin_distinguir_mayusculas_409`, `test_alias_invalido_422`); `me` y la lista de cuentas lo devuelven
- [ ] Tope de registros por IP (`test_r10_tope_de_registros_por_ip`)
- [ ] 5 fallos en 15 min → 429 + `Retry-After`; el mismo mensaje si el usuario no existe
- [ ] El login devuelve `{access_token, token_type: "Bearer", expires_in}`
- [ ] Login desde otro dispositivo con la sesión viva → 409; el JWT con otra cookie de dispositivo → 401
- [ ] `verify` acepta la cookie o `Authorization: Bearer` y devuelve `X-User-Id/Name`, `X-Session-Id` y `X-User-Perms`; sin cookie de dispositivo → 401, nunca 500; solo lo llama el gateway
- [ ] Los eventos (`auth.login.ok`, `auth.login.fail`, `auth.login.locked`, …) salen como registros JSON

## Entregables

- `services/auth/auth_svc/{accounts,sessions,routes,internal}.py`
- Tests `test_registro.py`, `test_r04_login.py`, `test_r13_sesiones.py`, `test_r16_verify.py`

## Documentación a actualizar

- Filas R4, R5, R10, R13 y R16 de la trazabilidad

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
