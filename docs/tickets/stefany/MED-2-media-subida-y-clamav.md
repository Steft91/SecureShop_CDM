# MED-2: Subida: membresía, límites y ClamAV (R9)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Media |
| Incremento | Incremento 3 |
| Necesita | [MED-1](../stefany/MED-1-media-archivos-cifrados.md) (Stefany) |
| Lo necesitan | [MED-3](../stefany/MED-3-media-politica-y-publicacion.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-07-media.md`](../../plans/2026-10-13-07-media.md), sección *Task MED-2* |
| Estado | Pendiente |

> La membresía de `rooms` (ROOM-4) se simula con `testing.Recorder`.

## Objetivo

La primera mitad de la subida: membresía, modo de la sala, silencio, tamaño, ritmo y ClamAV, que falla cerrado.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-07-media.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] Quien no es miembro → 403; sala solo de texto → 403; silenciado → `403 "estás silenciado"`
- [ ] Más de 5 MB → 413; la sexta subida en un minuto → 429
- [ ] Malware → 422 y `file.rejected.malware` (critical), sin escribir nada en disco; ClamAV caído → 503
- [ ] Con el perfil `clamav`, la cadena EICAR se detecta

## Entregables

- `services/media/media_svc/{clamav,pipeline,routes}.py`
- Servicio `clamav` en compose y perfil en `docker-compose.test.yml`

## Documentación a actualizar

- Fila R9 de la trazabilidad

## Verificación

`pytest services/media -q -m "not clamav"` y `-m clamav` con el perfil levantado

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
