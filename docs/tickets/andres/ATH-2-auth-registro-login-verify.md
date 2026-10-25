# ATH-2: Registro, login, JWT y sesión de dispositivo único, `verify`, `me` y `logout` (R4, R5, R13, R16)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Incremento | Primer parcial |
| Necesita | [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés) |
| Lo necesitan | [ATH-3](../andres/ATH-3-auth-totp-y-admin.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-2* |
| Estado | Pendiente |

## Objetivo

Cuentas con registro abierto, un login con bloqueo y una sesión por cuenta ligada al dispositivo, y el `verify` que el gateway llama en cada petición.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] El registro siempre da el rol `user`; un cuerpo con `role` → 422; `" ANA "` y `ana` son la misma cuenta (`test_usuario_normalizado_en_registro_y_login`)
- [ ] 5 fallos en 15 min → 429 + `Retry-After`; mismo mensaje si el usuario no existe
- [ ] Login desde otro dispositivo con la sesión viva → 409; el JWT con otra cookie de dispositivo → 401
- [ ] `verify` devuelve `X-User-Id/Name`, `X-Session-Id` y `X-User-Perms`; sin cookie de dispositivo → 401, nunca 500; solo lo llama el gateway

## Entregables

- `services/auth/auth_svc/{accounts,sessions,routes,internal}.py`
- Tests `test_registro.py`, `test_r04_login.py`, `test_r13_sesiones.py`, `test_r16_verify.py`

## Documentación a actualizar

- Filas R4, R5, R13 y R16 de la trazabilidad

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
