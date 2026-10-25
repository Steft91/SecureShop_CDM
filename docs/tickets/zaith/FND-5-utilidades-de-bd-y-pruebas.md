# FND-5: Utilidades de BD para pruebas, migraciones comunes e imágenes sintéticas

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Incremento | Primer parcial |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith) |
| Lo necesitan | [AUD-1](../andres/AUD-1-audit-esqueleto.md) (Andrés), [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés), [STG-1](../stefany/STG-1-stego-esqueleto-y-analisis.md) (Stefany), [ROOM-1](../andres/ROOM-1-rooms-crear-y-mis-salas.md) (Andrés), [CHAT-1](../zaith/CHAT-1-chat-almacen-cifrado.md) (Zaith), [MED-1](../stefany/MED-1-media-archivos-cifrados.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-5* |
| Estado | Pendiente |

## Objetivo

Dar a todos los servicios la BD de pruebas real, la migración común y las imágenes sintéticas para el estegoanálisis.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Andrés y Stefany de que FND-5 ya está cerrado
