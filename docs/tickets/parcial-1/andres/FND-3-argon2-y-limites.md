# FND-3: Contraseñas Argon2id y límites de intentos

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Fundaciones |
| Parcial | Primer parcial |
| Fase | A — arranque, sin depender de nadie |
| Necesita | Nada: puedes empezar ya |
| Lo necesitan | [FND-7](../zaith/FND-7-integracion-continua.md) (Zaith), [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés), [STG-3](../stefany/STG-3-stego-api.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-3* |
| Estado | Pendiente |

## Objetivo

Hash de contraseñas con Argon2id (con tope de concurrencia), la política de claves y el token bucket, dentro de `shared`.

## Cómo trabajar sin esperar

Son dos módulos sueltos (`passwords.py` y `ratelimit.py`) que no importan nada de `shared`. Si el `pyproject.toml` de FND-2 aún no está, pruébalos con `pip install argon2-cffi pytest` y `PYTHONPATH=services/shared pytest services/shared/tests/test_passwords.py services/shared/tests/test_token_bucket.py`.

## Criterios de aceptación

- [ ] El hash empieza con `$argon2id$` y usa `m=64 MiB, t=3, p=4`
- [ ] Nunca hay más de 4 cálculos Argon2id concurrentes por proceso
- [ ] `strong_enough` exige ≥ 12 caracteres, 3 de 4 clases y que la clave sea distinta del valor `forbid`
- [ ] `TokenBucket` deja pasar la ráfaga y después limita al ritmo configurado (reloj inyectable)

## Entregables

- `services/shared/shared/{passwords,ratelimit}.py`
- `services/shared/tests/test_passwords.py`, `test_token_bucket.py`

## Documentación a actualizar

- Fila R4 de la trazabilidad (control compartido)

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
