# PAR-2: Informe del primer parcial (RP-10)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Entrega del parcial |
| Parcial | Primer parcial |
| Fase | C — integración y entrega |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Lo necesitan | [PAR-3](../stefany/PAR-3-demo-y-ensayo.md) (Stefany) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../../plans/2026-10-25-parcial-1.md), sección *Task PAR-2* |
| Estado | Pendiente |

## Objetivo

El informe que pide el docente: descripción, arquitectura, REST, tecnologías, integración con `auth`, controles y evidencias.

## Cómo trabajar sin esperar

Las secciones de descripción, arquitectura, tecnologías y API se redactan desde la spec y los planes en cualquier momento. Las cifras y las evidencias esperan a que todo esté en verde.

## Criterios de aceptación

- [ ] Tiene las 11 secciones del plan
- [ ] Las cifras (tests, umbrales, TPR/FPR) salen de correr `pytest` y de `docs/calibracion-estego.md`, no de memoria
- [ ] Andrés revisó las secciones de `auth` y Zaith las de arquitectura y tecnologías
- [ ] `docs/requisitos.md` y `docs/cumplimiento-normativo.md` quedan con el estado del parcial

## Entregables

- `docs/informe-parcial-1.md`

## Documentación a actualizar

- `docs/requisitos.md`
- `docs/cumplimiento-normativo.md`

## Verificación

Lectura cruzada del equipo

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
