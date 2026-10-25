# E2E-3: Calibración, VPS, trazabilidad final, informe de pruebas y demo

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | E2E y cierre |
| Incremento | Incremento 3 |
| Necesita | [E2E-2](../zaith/E2E-2-e2e-chat-e-imagenes.md) (Zaith), [FE-5](../andres/FE-5-frontend-panel-admin.md) (Andrés) |
| Lo necesitan | Nadie más |
| Plan | [`docs/plans/2026-10-13-09-e2e-cierre.md`](../../plans/2026-10-13-09-e2e-cierre.md), sección *Task E2E-3* |
| Estado | Pendiente |

## Objetivo

Cerrar el proyecto: calibración con fotos reales, despliegue en un VPS, documentos finales y la demo.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-09-e2e-cierre.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `docs/calibracion-estego.md` con ≥ 30 fotos reales y los umbrales finales
- [ ] El VPS responde por https con un certificado válido y rechaza TLS 1.2
- [ ] `docs/informe-pruebas.md` y la trazabilidad con R1–R16 en *Implementado*
- [ ] Respaldo cifrado con `age` y simulacro de restauración: `audit/verify` da `ok` y el historial se descifra (Step 2b)
- [ ] `docs/demo.md` ensayada una vez completa; `CLAUDE.md` con todo marcado

## Entregables

- `docs/despliegue-vps.md`, `docs/informe-pruebas.md`, `docs/demo.md`

## Documentación a actualizar

- `docs/trazabilidad-riesgos.md`, `docs/requisitos.md`, `docs/cumplimiento-normativo.md`, `docs/justificacion-criptografica.md`, `CLAUDE.md`

## Verificación

Los Steps 1–5 del plan

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
