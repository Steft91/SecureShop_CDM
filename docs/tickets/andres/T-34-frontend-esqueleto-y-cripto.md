# T-34 · FE-1: Frontend: esqueleto, criptografía con vectores y SPA en el gateway

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Incremento 2 |
| Bloqueado por | [T-33 · GW-2](../zaith/T-33-gateway-salas-media-ws.md) (Zaith) |
| Desbloquea | [T-35 · FE-2](../stefany/T-35-frontend-cuenta-y-salas.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-1* |
| Estado | Pendiente |

## Objetivo

La SPA base con toda la WebCrypto verificada contra los mismos vectores que Python, servida por el gateway.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-35
