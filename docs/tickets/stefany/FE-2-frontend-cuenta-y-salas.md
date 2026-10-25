# FE-2: Frontend: cuenta, *Mis salas*, crear sala e ingresar

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Frontend |
| Incremento | Incremento 2 |
| Necesita | [FE-1](../stefany/FE-1-frontend-esqueleto-y-cripto.md) (Stefany), [ATH-4](../andres/ATH-4-auth-roles-y-permisos.md) (Andrés), [ROOM-2](../andres/ROOM-2-rooms-ingreso-y-salida.md) (Andrés) |
| Lo necesitan | [FE-3](../stefany/FE-3-frontend-chat-y-dueno.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-2* |
| Estado | Pendiente |

## Objetivo

Registro, login con TOTP cuando hace falta, *Mis salas*, crear sala e ingresar.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
