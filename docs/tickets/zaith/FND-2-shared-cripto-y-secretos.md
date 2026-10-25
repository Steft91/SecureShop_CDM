# FND-2: Paquete `shared`: secretos, criptografía y vectores

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Incremento | Primer parcial |
| Necesita | Nada: puedes empezar ya |
| Lo necesitan | [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith), [FND-6](../zaith/FND-6-docker-secretos-postgres.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-2* |
| Estado | Pendiente |

## Objetivo

Crear la librería común con la lectura de secretos y toda la criptografía del protocolo, y generar los vectores que comparten Python y TypeScript.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] `pip install -e "services/shared[dev]"` instala sin errores
- [ ] `test_crypto.py`, `test_r02_secretos.py` y `test_vectors.py` pasan
- [ ] Sin un secreto, `read_secret` falla: el servicio no arranca (R2)
- [ ] `docs/crypto-vectors.json` se genera con `tools/gen_crypto_vectors.py`, y volver a generarlo no lo cambia

## Entregables

- `services/shared/pyproject.toml`
- `services/shared/shared/{crypto,secrets}.py`
- `services/shared/tools/gen_crypto_vectors.py`
- `docs/crypto-vectors.json`

## Documentación a actualizar

- Fila R2 de la trazabilidad
- `docs/justificacion-criptografica.md` si cambia algún parámetro

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
