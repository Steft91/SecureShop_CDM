# T-39 · MED-3: Política con `stego`, sanitización y publicación (R6, R9)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Incremento 3 |
| Bloqueado por | [T-38 · MED-2](../stefany/T-38-media-subida-y-clamav.md) (Stefany) |
| Desbloquea | [T-40 · MED-4](../andres/T-40-media-descarga-y-cuarentena.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-07-media.md`](../../plans/2026-10-13-07-media.md), sección *Task MED-3* |
| Estado | Pendiente |

## Objetivo

Aplicar el veredicto de `stego`: cuarentena, rechazo o sanitización, cifrado y publicación en la sala.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-07-media.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `limpia` → sanitizada, cifrada y publicada en `chat`; `problema` o `revision_manual` → cuarentena, sin publicar
- [ ] `stego` responde 422 → rechazo; `stego` caído → 503
- [ ] Volver a subir los bytes sanitizados no pasa por la cuarentena (`test_reenvio_de_imagen_sanitizada_no_va_a_cuarentena`)
- [ ] `chat` caído → 503 y archivo huérfano; el borrado interno es idempotente y solo lo pide `chat`

## Entregables

- `services/media/media_svc/{pipeline,routes}.py`
- Tests `test_r06_politica.py`, `test_publicacion.py`, `test_r16_internas.py`

## Documentación a actualizar

- Filas R6 y R9 de la trazabilidad

## Verificación

`pytest services/media -q -m "not clamav"`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-40
