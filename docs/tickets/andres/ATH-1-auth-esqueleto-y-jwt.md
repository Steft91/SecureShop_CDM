# ATH-1: Esqueleto de `auth`, catálogo de permisos, roles semilla y firma de JWT (R11)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Incremento | Primer parcial |
| Necesita | [FND-3](../andres/FND-3-argon2-y-limites.md) (Andrés), [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [ATH-2](../andres/ATH-2-auth-registro-login-verify.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-1* |
| Estado | Pendiente |

> El paso de compose necesita además FND-6. El contrato de `audit` se simula con `testing.Recorder`, así que no esperas a AUD-2.

## Objetivo

Servicio `auth` con su migración (catálogo de 7 permisos y roles `user`/`admin`), la firma RS256 y el mínimo privilegio.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] La migración carga los 7 permisos y los roles `user` (`rooms:create`) y `admin` (todos)
- [ ] `Signer` solo acepta `RS256`: un token `alg: none` o firmado con HS256 usando la clave pública se rechaza (`test_tokens.py`)
- [ ] `auth_app` no puede `CREATE TABLE` ni conectarse a otra BD
- [ ] `auth` en estado `healthy` en compose y en la matriz de la CI

## Entregables

- `services/auth/**` (esqueleto, `0001_cuentas.py`, `config.py`, `tokens.py`, `main.py`)
- Servicios `auth` y `auth-migrate` en compose

## Documentación a actualizar

- Fila R11 de la trazabilidad
- `docs/justificacion-criptografica.md` (fila JWT RS256)

## Verificación

`pytest services/auth -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
