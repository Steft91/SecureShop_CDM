# T-11 · ATH-1: Esqueleto de `auth`, catálogo de permisos, roles semilla y firma de JWT (R11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Primer parcial |
| Bloqueado por | [T-10 · AUD-3](../andres/T-10-audit-consulta.md) (Andrés) |
| Desbloquea | [T-12 · ATH-2](../zaith/T-12-auth-registro-login-verify.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../plans/2026-10-13-03-auth.md), sección *Task ATH-1* |
| Estado | Pendiente |

## Objetivo

Servicio `auth` con su migración (catálogo de 7 permisos y roles `user`/`admin`), la firma RS256 y el mínimo privilegio.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-12
