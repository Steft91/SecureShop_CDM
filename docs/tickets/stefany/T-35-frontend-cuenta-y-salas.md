# T-35 · FE-2: Frontend: cuenta, *Mis salas*, crear sala e ingresar

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Incremento 2 |
| Bloqueado por | [T-34 · FE-1](../andres/T-34-frontend-esqueleto-y-cripto.md) (Andrés) |
| Desbloquea | [T-36 · FE-3](../zaith/T-36-frontend-chat-y-dueno.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-2* |
| Estado | Pendiente |

## Objetivo

Registro, login con TOTP cuando hace falta, *Mis salas*, crear sala e ingresar.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-08-frontend.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `session.test.tsx`: `me` se carga de `/api/auth/me` y el navegador no guarda nada (`localStorage` y `sessionStorage` vacíos)
- [ ] El login con `{mfa: "setup"}` muestra el `otpauth_uri` y pide el código
- [ ] Las 5 verificaciones manuales del plan, hechas

## Entregables

- `frontend/src/lib/session.tsx`
- `frontend/src/pages/{Login,Register,Account,MyRooms,CreateRoom,JoinRoom}.tsx`

## Documentación a actualizar

- Ninguna

## Verificación

`npx vitest run` y la verificación manual del Step 3

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-36
