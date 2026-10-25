# FE-1: Frontend: esqueleto, criptografía con vectores y SPA en el gateway

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Frontend |
| Incremento | Incremento 2 |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Lo necesitan | [FE-2](../stefany/FE-2-frontend-cuenta-y-salas.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-1* |
| Estado | Pendiente |

> Los vectores de `docs/crypto-vectors.json` los genera FND-2.

## Objetivo

La SPA base con toda la WebCrypto verificada contra los mismos vectores que Python, servida por el gateway.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-08-frontend.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `npx vitest run`: `crypto.test.ts` reproduce los vectores (misma `K`, tramas y firma)
- [ ] `npm run build` sin errores; `https://localhost/` sirve la SPA con la CSP
- [ ] Job `frontend` en la CI (vitest, build, `npm audit --audit-level=high`)

## Entregables

- `frontend/**` (esqueleto, `lib/crypto.ts`, `lib/api.ts`)
- `gateway/Dockerfile` y `gateway/nginx.conf` (SPA)
- Job `frontend` en la CI

## Documentación a actualizar

- Fila R7 de la trazabilidad (vectores en el navegador)

## Verificación

`npx vitest run` y `npm run build` en `frontend/`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
