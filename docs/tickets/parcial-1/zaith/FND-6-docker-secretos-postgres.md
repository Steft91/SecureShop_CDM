# FND-6: Plantilla Docker, generación de secretos y PostgreSQL de `auth`

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Parcial | Primer parcial |
| Fase | A — arranque, sin depender de nadie |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith) |
| Lo necesitan | [FND-7](../zaith/FND-7-integracion-continua.md) (Zaith), [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-6* |
| Estado | Cerrado (2026-11-03, `c090a11`) |

## Objetivo

Dockerfile único por servicio, el generador de secretos (con la clave del JWT) y Postgres con la BD de `auth` y sus dos roles.

## Cómo trabajar sin esperar

Solo necesita tu FND-2. Los demás la usan únicamente en el paso de compose de ATH-1 y STG-1: sus tests no la esperan.

## Criterios de aceptación

- [x] `python deploy/gen_secrets.py` crea los 7 secretos y nunca sobrescribe; `--rotate svc_token_gateway` regenera el token, su hash y `gateway_token.conf` (`test_gen_secrets.py`)
- [x] `jwt_signing_key` es RSA de 3072 bits
- [x] `docker compose up -d db` crea la BD `auth` con `auth_owner` y `auth_app` (Step 5 del plan)
- [x] El `Dockerfile` fija `LOG_FORMAT=json` y arranca uvicorn con `--no-access-log`

## Entregables

- `services/Dockerfile`, `services/lock.sh`
- `deploy/gen_secrets.py`, `deploy/postgres/init.sh`, `deploy/docker-compose.yml`
- `services/shared/tests/test_gen_secrets.py`

## Documentación a actualizar

- Filas R2, R11 y R16 de la trazabilidad

## Verificación

`pytest services/shared -q` y los comandos del Step 5 del plan

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
