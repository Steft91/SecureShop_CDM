# E2E-2: E2E: chat, moderación e imágenes (R6, R7, R12, R14)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | E2E y cierre |
| Incremento | Incremento 3 |
| Necesita | [E2E-1](../zaith/E2E-1-e2e-cuentas-y-gateway.md) (Zaith), [MED-4](../stefany/MED-4-media-descarga-y-cuarentena.md) (Stefany), [CHAT-4](../zaith/CHAT-4-chat-avisos-y-latidos.md) (Zaith) |
| Lo necesitan | [E2E-3](../zaith/E2E-3-cierre-final.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-09-e2e-cierre.md`](../../plans/2026-10-13-09-e2e-cierre.md), sección *Task E2E-2* |
| Estado | Pendiente |

## Objetivo

Probar de punta a punta el chat entre dos cuentas, la moderación y las imágenes.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-09-e2e-cierre.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] El *hello* firmado se verifica en los dos clientes; el mensaje llega con el alias correcto
- [ ] Expulsión → 4411 y reingreso vetado → 403; logout → el WS se cierra con 4401
- [ ] Una imagen limpia se publica y cada uno la descarga solo con **su** URL; reenviar la descargada no va a cuarentena
- [ ] Una imagen con LSB va a cuarentena con su alerta y el admin la libera

## Entregables

- `e2e/test_chat.py`, `e2e/test_media.py`

## Documentación a actualizar

- Filas R6, R7, R12 y R14 de la trazabilidad

## Verificación

`pytest e2e -q` con el stack completo (incluido ClamAV)

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
