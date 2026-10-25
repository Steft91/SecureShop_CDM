# T-38 · MED-2: Subida: membresía, límites y ClamAV (R9)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Incremento 3 |
| Bloqueado por | [T-37 · MED-1](../andres/T-37-media-archivos-cifrados.md) (Andrés) |
| Desbloquea | [T-39 · MED-3](../zaith/T-39-media-politica-y-publicacion.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-07-media.md`](../../plans/2026-10-13-07-media.md), sección *Task MED-2* |
| Estado | Pendiente |

## Objetivo

La primera mitad de la subida: membresía, modo de la sala, silencio, tamaño, ritmo y ClamAV, que falla cerrado.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-39
