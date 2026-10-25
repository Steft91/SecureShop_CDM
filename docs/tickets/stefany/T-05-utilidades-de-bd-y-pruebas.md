# T-05 · FND-5: Utilidades de BD para pruebas, migraciones comunes e imágenes sintéticas

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Primer parcial |
| Bloqueado por | [T-04 · FND-4](../andres/T-04-autenticacion-entre-servicios.md) (Andrés) |
| Desbloquea | [T-06 · FND-6](../zaith/T-06-docker-secretos-postgres.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-5* |
| Estado | Pendiente |

## Objetivo

Dar a todos los servicios la BD de pruebas real, la migración común y las imágenes sintéticas para el estegoanálisis.

## Criterios de aceptación

- [ ] `docker compose -f deploy/docker-compose.test.yml up -d` levanta Postgres en `127.0.0.1:5433`
- [ ] `test_testing.py` pasa: `prepare_database`, `sql`, `truncate_all`, `assert_least_privilege`
- [ ] `natural_image` y `embed_lsb` son deterministas con la misma semilla

## Entregables

- `services/shared/shared/{testing,migrations}.py`
- `deploy/docker-compose.test.yml`
- `services/shared/tests/test_testing.py`

## Documentación a actualizar

- Ninguna (infraestructura de pruebas)

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-06
