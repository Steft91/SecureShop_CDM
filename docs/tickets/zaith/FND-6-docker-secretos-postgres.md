# FND-6: Plantilla Docker, generación de secretos y PostgreSQL con 5 BD

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Incremento | Primer parcial |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith) |
| Lo necesitan | [FND-7](../zaith/FND-7-integracion-continua.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-6* |
| Estado | Pendiente |

## Objetivo

Dockerfile único por servicio, generador de secretos (con la clave del JWT) y Postgres con una BD y dos roles por servicio.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] `python deploy/gen_secrets.py` crea los 30 secretos y `deploy/public/chat-key.json`, y nunca sobrescribe; `--rotate` regenera uno
- [ ] `jwt_signing_key` es RSA de 3072 bits y el hash de `stego` coincide con su token (`test_gen_secrets.py`)
- [ ] `docker compose up -d db` crea las 5 BD con su `<svc>_owner`, y `rooms_app` **no** puede conectarse a `auth` (`f`)
- [ ] El `Dockerfile` fija `LOG_FORMAT=json` y arranca uvicorn con `--no-access-log`

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
