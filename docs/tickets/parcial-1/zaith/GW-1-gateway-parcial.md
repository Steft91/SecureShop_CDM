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
| Estado | Pendiente |

> Es el punto donde se juntan los tres: avisa en el grupo cuando `auth` y `stego` estén `healthy` en compose.

## Objetivo

El único punto de entrada, que habla con los dos microservicios: TLS 1.3, cabeceras de seguridad, rate limit, `auth_request` a `auth` y rutas a `auth` y `stego`, con la identidad imposible de falsificar.

## Cómo trabajar sin esperar

Los Steps 1–4 (`nginx.conf`, los snippets, el `Dockerfile` y `nginx -t`) no necesitan ningún servicio: hazlos en cuanto cierres la fase A. Los Steps 5–7 esperan a que `auth` y `stego` estén arriba.

## Criterios de aceptación

- [ ] `nginx -t` → `test is successful`
- [ ] http → 301; TLS 1.2 rechazado; `/internal/verify` → 404; HSTS y CSP presentes
- [ ] `X-User-*` falsificadas sin JWT → 401; `auth` caído → 503
- [ ] El admin creado por CLI entra con su contraseña vía curl, analiza `2-problema-zip-al-final.png` (`problema`) y los eventos `auth.login.ok` y `stego.analyzed` aparecen en `docker compose logs` (Step 6)
- [ ] `X-Request-ID`: una sola cabecera en la respuesta, que sobrescribe la del cliente, y el mismo id en los registros JSON de `gateway` y `auth`
- [ ] Queda anotado si Postman conserva `__Host-device` (Step 7)

## Entregables

- `gateway/nginx.conf`, `gateway/snippets/*.conf`, `gateway/Dockerfile`
- Servicio `gateway` en compose

## Documentación a actualizar

- Filas R7, R10 y R16 y la *Verificación manual* de la trazabilidad
- `CLAUDE.md`: marcar GW-1

## Verificación

Los Steps 4–7 del plan (`nginx -t`, curl y Postman)

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
