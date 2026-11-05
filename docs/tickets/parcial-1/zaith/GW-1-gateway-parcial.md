# GW-1: Gateway Nginx con TLS 1.3, `auth_request` y las rutas del parcial (R5, R7, R10, R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Gateway |
| Parcial | Primer parcial |
| Fase | C — integración y entrega |
| Necesita | [FND-6](../zaith/FND-6-docker-secretos-postgres.md) (Zaith), [ATH-4](../andres/ATH-4-auth-roles-y-permisos.md) (Andrés), [STG-4](../stefany/STG-4-stego-demo-y-calibracion.md) (Stefany) |
| Lo necesitan | [PAR-1](../stefany/PAR-1-postman.md) (Stefany), [PAR-2](../stefany/PAR-2-informe-parcial.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-04-gateway.md`](../../../plans/2026-10-13-04-gateway.md), sección *Task GW-1* |
| Estado | Cerrado con evidencia pendiente (2026-11-04; pasos 1–6 y 8 verificados; paso 7 requiere CA de mkcert; commit pendiente) |

> Es el punto donde se juntan los tres: avisa en el grupo cuando `auth` y `stego` estén `healthy` en compose.

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

El único punto de entrada, que habla con los dos microservicios: TLS 1.3, cabeceras de seguridad, rate limit, `auth_request` a `POST /internal/authorization/check` y las rutas de la spec §23.5, con la identidad imposible de falsificar. Suma la infraestructura de la BD de `stego`.

## Cómo trabajar sin esperar

Los Steps 1–4 ya están (`b48ed79`). Antes de los Steps 5–7: rutas de §23.5, `proxy_method POST` en `/_auth/user`, cookies vaciadas en todas las rutas (hecho en los snippets) y la BD de `stego`. Lo que falta espera a que `auth` y `stego` estén arriba.

## Criterios de aceptación

- [x] `nginx -t` → `test is successful`
- [x] Rutas de §23.5: `= /api/auth/login`, `/api/auth/`, `/api/users`, `/api/roles`, `/api/user-roles`, `= /api/steganography/analyze` (6m) y `/api/steganography/results/`; sin `/api/auth/register` ni `/api/admin/`; ningún servicio recibe cookies (2026-11-04: `nginx -t` correcto; sin backends, `/internal/authorization/check` y `/api/admin/roles` → 404, `analyze`, `results`, `/api/users` y `login` → 503, TLS 1.2 rechazado)
- [x] BD de `stego`: `init.sh` (`for svc in auth stego`), `gen_secrets.py` (`SERVICES`), compose (`stego`, `stego-migrate`, volumen `stego_quarantine` en `/data` y secretos `db_stego_*`) y `.claude/rules/microservices.md` (2026-11-04; `stego` arranca cuando STG-3 agregue su `requirements.lock`, `alembic.ini` y su migración: hasta entonces `up --build` falla en `stego`. `init.sh` solo corre al crear `pgdata`: quien ya tenía el volumen hace `docker compose -f deploy/docker-compose.yml down -v`)
- [x] http → 301; TLS 1.2 rechazado; `/internal/authorization/check` → 404 desde afuera; HSTS y CSP presentes
- [x] `X-User-*` falsificadas sin JWT → 401; token de USER con `X-User-Perms: steganography.analyze` falsificada → 403
- [x] `auth` caído → 503 y ningún `stego.analyzed` (T08); `stego` caído → 503 en su ruta mientras `auth` sigue respondiendo (T01); más de 5 MB → 413
- [x] El admin del CLI entra vía curl, analiza `lsb.png` (`sospechoso`) y los eventos `auth.login.ok` y `stego.analyzed` aparecen en `docker compose logs` (Step 6)
- [x] `X-Request-ID`: una sola cabecera en la respuesta, que sobrescribe la del cliente, y el mismo id en los registros JSON de `gateway` y `auth`
- [ ] Postman con la CA de mkcert y 200 en `/api/auth/profile` (Step 7): pendiente de generar e instalar la CA en la máquina de entrega.

## Entregables

- `gateway/nginx.conf`, `gateway/snippets/*.conf`, `gateway/Dockerfile`
- `deploy/docker-compose.yml`, `deploy/postgres/init.sh`, `deploy/gen_secrets.py`

## Documentación a actualizar

- Filas R7, R10, R11 y R16 y la *Verificación manual* de la trazabilidad
- `CLAUDE.md`: marcar GW-1

## Verificación

Los Steps 4–7 del plan (`nginx -t`, curl y Postman)

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado con evidencia pendiente, con la fecha; el hash se añadirá al cerrar los commits.
