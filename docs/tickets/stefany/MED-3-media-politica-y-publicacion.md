# MED-3: Política con `stego`, sanitización y publicación (R6, R9)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Media |
| Incremento | Incremento 3 |
| Necesita | [MED-2](../stefany/MED-2-media-subida-y-clamav.md) (Stefany), [STG-3](../stefany/STG-3-stego-api.md) (Stefany) |
| Lo necesitan | [MED-4](../stefany/MED-4-media-descarga-y-cuarentena.md) (Stefany), [FE-4](../stefany/FE-4-frontend-imagenes.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-07-media.md`](../../plans/2026-10-13-07-media.md), sección *Task MED-3* |
| Estado | Pendiente |

> `stego` (STG-3) se simula con `testing.Recorder`; la verificación contra el servicio real necesita STG-3.

## Objetivo

Aplicar el veredicto de `stego`: cuarentena, rechazo o sanitización, cifrado y publicación en la sala.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
