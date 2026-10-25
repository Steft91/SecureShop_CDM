# T-19 · GW-1: Gateway Nginx con TLS 1.3, `auth_request` y las rutas del parcial (R5, R7, R10, R16)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Primer parcial |
| Bloqueado por | [T-18 · STG-4](../zaith/T-18-stego-demo-y-calibracion.md) (Zaith) |
| Desbloquea | [T-20 · PAR-1](../stefany/T-20-postman.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-04-gateway.md`](../../plans/2026-10-13-04-gateway.md), sección *Task GW-1* |
| Estado | Pendiente |

## Objetivo

El único punto de entrada: TLS 1.3, cabeceras de seguridad, rate limit y `auth_request` a `auth`, con la identidad imposible de falsificar.

## Criterios de aceptación

- [ ] `nginx -t` → `test is successful`
- [ ] http → 301; TLS 1.2 rechazado; `/internal/verify` → 404; HSTS y CSP presentes
- [ ] `X-User-*` falsificadas sin JWT → 401; `auth` caído → 503
- [ ] El admin entra con contraseña + TOTP vía curl, analiza `2-problema-zip-al-final.png` (`problema`) y ve los eventos en `/api/admin/audit`
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

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-20
