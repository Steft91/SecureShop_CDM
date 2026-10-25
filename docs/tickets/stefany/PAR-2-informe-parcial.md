# PAR-2: Informe del primer parcial (RP-10)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Entrega del parcial |
| Incremento | Primer parcial |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Lo necesitan | [PAR-3](../stefany/PAR-3-demo-y-ensayo.md) (Stefany) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../plans/2026-10-25-parcial-1.md), sección *Task PAR-2* |
| Estado | Pendiente |

> Las cifras salen de las pruebas de todos los servicios del parcial.

## Objetivo

El informe que pide el docente: descripción, cómo se construyó, REST, tecnologías, integración con auth y evidencias.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] Tiene las 11 secciones del plan
- [ ] Las cifras (tests, umbrales, TPR/FPR) salen de correr `pytest` y de `docs/calibracion-estego.md`, no de memoria
- [ ] Andrés revisó las secciones 6 y 8 (auth) y Zaith la 2 y la 5 (arquitectura y tecnologías)
- [ ] `docs/requisitos.md` y `docs/cumplimiento-normativo.md` quedan con el estado del parcial

## Entregables

- `docs/informe-parcial-1.md`

## Documentación a actualizar

- `docs/requisitos.md`
- `docs/cumplimiento-normativo.md`

## Verificación

Lectura cruzada del equipo

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
