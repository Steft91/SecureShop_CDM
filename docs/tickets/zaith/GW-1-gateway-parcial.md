# GW-1: Gateway Nginx con TLS 1.3, `auth_request` y las rutas del parcial (R5, R7, R10, R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Gateway |
| Incremento | Primer parcial |
| Necesita | [ATH-4](../andres/ATH-4-auth-roles-y-permisos.md) (Andrés), [AUD-3](../andres/AUD-3-audit-consulta.md) (Andrés), [STG-4](../stefany/STG-4-stego-demo-y-calibracion.md) (Stefany) |
| Lo necesitan | [PAR-1](../stefany/PAR-1-postman.md) (Stefany), [PAR-2](../stefany/PAR-2-informe-parcial.md) (Stefany), [GW-2](../zaith/GW-2-gateway-salas-media-ws.md) (Zaith), [FE-1](../stefany/FE-1-frontend-esqueleto-y-cripto.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-04-gateway.md`](../../plans/2026-10-13-04-gateway.md), sección *Task GW-1* |
| Estado | Pendiente |

> `nginx.conf`, los snippets y `nginx -t` se escriben y prueban solos (Steps 1–4); los Steps 5–7 necesitan los tres servicios arriba y FND-6.

## Objetivo

El único punto de entrada: TLS 1.3, cabeceras de seguridad, rate limit y `auth_request` a `auth`, con la identidad imposible de falsificar.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Stefany de que GW-1 ya está cerrado
