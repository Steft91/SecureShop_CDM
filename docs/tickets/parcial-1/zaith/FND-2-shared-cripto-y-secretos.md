# FND-2: Paquete `shared`: secretos y utilidades criptográficas

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Parcial | Primer parcial |
| Fase | A — arranque, sin depender de nadie |
| Necesita | Nada: puedes empezar ya |
| Lo necesitan | [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith), [FND-6](../zaith/FND-6-docker-secretos-postgres.md) (Zaith), [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés), [STG-1](../stefany/STG-1-stego-esqueleto-y-analisis.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-2* |
| Estado | Pendiente |

## Objetivo

Crear la librería común `shared` con la lectura de secretos y las utilidades criptográficas que usan `auth` y `stego`.

## Cómo trabajar sin esperar

No depende de nadie. Hazla justo después de FND-1: el `pyproject.toml` de `shared` es lo que Andrés y Stefany instalan para pasar a la fase B.

## Criterios de aceptación

- [ ] `pip install -e "services/shared[dev]"` instala sin errores
- [ ] `test_crypto.py` y `test_r02_secretos.py` pasan
- [ ] Sin un secreto, `read_secret` falla y el servicio no arranca (R2)

## Entregables

- `services/shared/pyproject.toml`
- `services/shared/shared/{__init__,crypto,secrets}.py`
- `services/shared/tests/test_crypto.py`, `test_r02_secretos.py`

## Documentación a actualizar

- Fila R2 de la trazabilidad
- `docs/justificacion-criptografica.md` si cambia algún parámetro

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
