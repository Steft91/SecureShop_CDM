# FND-5: Utilidades de BD para pruebas y migraciones comunes

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Parcial | Primer parcial |
| Fase | A — arranque, sin depender de nadie |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith) |
| Lo necesitan | [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-5* |
| Estado | Pendiente |

## Objetivo

Dar a `auth` la BD de pruebas real y la migración común.

## Cómo trabajar sin esperar

Solo necesita tu FND-2. Andrés la usa desde ATH-1; `stego` no tiene BD, así que Stefany no la espera.

## Criterios de aceptación

- [ ] `docker compose -f deploy/docker-compose.test.yml up -d` levanta Postgres en `127.0.0.1:5433`
- [ ] `test_testing.py` pasa: `prepare_database`, `sql`, `truncate_all` y `assert_least_privilege`

## Entregables

- `services/shared/shared/{testing,migrations}.py`
- `deploy/docker-compose.test.yml`
- `services/shared/tests/test_testing.py`

## Documentación a actualizar

- Ninguna (infraestructura de pruebas)

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
