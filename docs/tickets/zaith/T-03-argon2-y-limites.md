# T-03 · FND-3: Contraseñas Argon2id y límites de intentos

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Primer parcial |
| Bloqueado por | [T-02 · FND-2](../stefany/T-02-shared-cripto-y-secretos.md) (Stefany) |
| Desbloquea | [T-04 · FND-4](../andres/T-04-autenticacion-entre-servicios.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-3* |
| Estado | Pendiente |

## Objetivo

Hash de contraseñas y claves con Argon2id (con tope de concurrencia), la política de claves y el token bucket.

## Criterios de aceptación

- [ ] El hash empieza con `$argon2id$` y usa `m=64 MiB, t=3, p=4`
- [ ] Nunca hay más de 4 cálculos Argon2id concurrentes por proceso
- [ ] `strong_enough` exige ≥ 12 caracteres, 3 de 4 clases y que la clave sea distinta del valor `forbid`
- [ ] `TokenBucket` deja pasar la ráfaga y después limita al ritmo configurado (reloj inyectable)

## Entregables

- `services/shared/shared/{passwords,ratelimit}.py`
- `services/shared/tests/test_passwords.py`, `test_token_bucket.py`

## Documentación a actualizar

- Filas R1 y R4 de la trazabilidad (control compartido)

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-04
