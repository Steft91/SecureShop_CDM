# ATH-6: Rotación de la KEK de auth (R2)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Incremento | Incremento 2 |
| Necesita | [ATH-4](../andres/ATH-4-auth-roles-y-permisos.md) (Andrés) |
| Lo necesitan | Nadie más |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-6* |
| Estado | Pendiente |

## Objetivo

Re-envolver los secretos TOTP con una KEK nueva sin que nadie pierda el acceso.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] Con `kek_auth_v2` montada y `CURRENT_KEK_VERSION=2`, `python -m auth_svc.rotate_kek` re-envuelve todo
- [ ] El admin sigue entrando con su TOTP después de rotar
- [ ] Se audita `key.rotate.auth` con `{"to": 2, "users": n}`

## Entregables

- `services/auth/auth_svc/rotate_kek.py`
- `services/auth/tests/test_r02_rotacion.py`

## Documentación a actualizar

- Fila R2 de la trazabilidad
- `docs/justificacion-criptografica.md` (ciclo de vida de la KEK)

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
