# ATH-1: Esqueleto de `auth`, catálogo de permisos, rol `admin` y firma de JWT (R11)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Auth |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith), [FND-3](../andres/FND-3-argon2-y-limites.md) (Andrés), [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [ATH-2](../andres/ATH-2-auth-registro-login-verify.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-03-auth.md`](../../../plans/2026-10-13-03-auth.md), sección *Task ATH-1* |
| Estado | Pendiente |

> El paso de compose necesita además FND-6; los tests no.

## Objetivo

Servicio `auth` con su migración (catálogo de 3 permisos y el rol `admin`), la firma RS256 y el mínimo privilegio en la BD.

## Cómo trabajar sin esperar

Mientras Zaith cierra FND-4 y FND-5: escribe la migración `0001_cuentas.py` y `tokens.py` (`Signer` solo usa `pyjwt`, y `test_tokens.py` corre sin BD ni `shared`). Las firmas de `shared` que vas a usar están en las *Interfaces* de FND-4 en el plan de fundaciones.

## Criterios de aceptación

- [ ] La migración carga los permisos `users:manage`, `roles:manage` y `stego:analyze`, y el rol `admin` con los tres (`test_catalogo_y_rol_semilla`)
- [ ] `Signer` solo acepta `RS256`: un token `alg: none` o firmado con HS256 usando la clave pública se rechaza (`test_tokens.py`)
- [ ] `auth_app` no puede `CREATE TABLE`, ni borrar cuentas, ni editar el catálogo (`test_r11_privilegios.py`)
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

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
