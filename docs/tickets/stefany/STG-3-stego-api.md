# STG-3: API pública e interna con análisis aislado (R5, R9, R10, R16)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Incremento | Primer parcial |
| Necesita | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) (Stefany) |
| Lo necesitan | [STG-4](../stefany/STG-4-stego-demo-y-calibracion.md) (Stefany), [MED-3](../stefany/MED-3-media-politica-y-publicacion.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../plans/2026-10-13-10-stego.md), sección *Task STG-3* |
| Estado | Pendiente |

## Objetivo

`POST /api/stego/analyze` con el permiso `stego:analyze` y las rutas internas que usará `media`, con el análisis en un pool de procesos con timeout.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] Sin identidad del gateway → 401; sin `stego:analyze` → 403 y `perm.denied` (`test_r05_api.py`)
- [ ] Más de 10 análisis por minuto por usuario → 429 y `stego.ratelimited`
- [ ] Si el análisis supera `STEGO_TIMEOUT_S` → `revision_manual`
- [ ] Se audita `stego.analyzed` (info si es `limpia`; warning en los demás casos); `/internal/analyze` y `/internal/sanitize` solo aceptan a `media` (`test_r16_internas.py`)
- [ ] Si el sanitizador deja residuos estructurales, `/internal/sanitize` responde 503 y audita `stego.sanitize.failed` (critical) (A3-RS-36)

## Entregables

- `services/stego/stego_svc/{pipeline,routes}.py`
- Tests `test_r05_api.py`, `test_r16_internas.py`

## Documentación a actualizar

- Filas R5, R9, R10 y R16 de la trazabilidad

## Verificación

`pytest services/stego -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
