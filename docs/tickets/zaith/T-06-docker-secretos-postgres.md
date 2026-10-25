# T-06 · FND-6: Plantilla Docker, generación de secretos y PostgreSQL con 5 BD

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Primer parcial |
| Bloqueado por | [T-05 · FND-5](../stefany/T-05-utilidades-de-bd-y-pruebas.md) (Stefany) |
| Desbloquea | [T-07 · FND-7](../andres/T-07-integracion-continua.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-6* |
| Estado | Pendiente |

## Objetivo

Dockerfile único por servicio, generador de secretos (con la clave del JWT) y Postgres con una BD y dos roles por servicio.

## Criterios de aceptación

- [ ] `python deploy/gen_secrets.py` crea los 30 secretos y `deploy/public/chat-key.json`, y nunca sobrescribe; `--rotate` regenera uno
- [ ] `jwt_signing_key` es RSA de 3072 bits y el hash de `stego` coincide con su token (`test_gen_secrets.py`)
- [ ] `docker compose up -d db` crea las 5 BD con su `<svc>_owner`, y `rooms_app` **no** puede conectarse a `auth` (`f`)

## Entregables

- `services/Dockerfile`, `services/lock.sh`
- `deploy/gen_secrets.py`, `deploy/postgres/init.sh`, `deploy/docker-compose.yml`
- `services/shared/tests/test_gen_secrets.py`

## Documentación a actualizar

- Filas R2, R11 y R16 de la trazabilidad

## Verificación

`pytest services/shared -q` y los comandos del Step 5 del plan

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-07
