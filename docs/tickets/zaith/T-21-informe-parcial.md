# T-21 · PAR-2: Informe del primer parcial (RP-10)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Primer parcial |
| Bloqueado por | [T-20 · PAR-1](../stefany/T-20-postman.md) (Stefany) |
| Desbloquea | [T-22 · PAR-3](../andres/T-22-demo-y-ensayo.md) (Andrés) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../plans/2026-10-25-parcial-1.md), sección *Task PAR-2* |
| Estado | Pendiente |

## Objetivo

El informe que pide el docente: descripción, cómo se construyó, REST, tecnologías, integración con auth y evidencias.

## Criterios de aceptación

- [ ] Tiene las 11 secciones del plan
- [ ] Las cifras (tests, umbrales, TPR/FPR) salen de correr `pytest` y de `docs/calibracion-estego.md`, no de memoria
- [ ] Andrés revisó las secciones 2, 6 y 8, y Stefany la 7
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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-22
