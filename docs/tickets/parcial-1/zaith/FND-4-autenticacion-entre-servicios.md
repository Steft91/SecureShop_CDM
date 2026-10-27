# FND-4: Autenticación entre servicios, identidad, eventos de seguridad y base web (R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Parcial | Primer parcial |
| Fase | A — arranque, sin depender de nadie |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith) |
| Lo necesitan | [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés), [STG-1](../stefany/STG-1-stego-esqueleto-y-analisis.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-4* |
| Estado | Pendiente |

## Objetivo

Token de servicio con allowlist por hash, identidad del gateway (`X-User-*`), `require_perm`, los eventos de seguridad como registros JSON (`shared.audit.emit`) y la app base con errores JSON.

## Cómo trabajar sin esperar

Solo necesita tu FND-2. Es la pieza que más esperan Andrés (ATH-1) y Stefany (STG-1): prioriza `service_auth`, `identity`, `audit`, `web` y `testing` antes que FND-5 y FND-6.

## Criterios de aceptación

- [ ] `test_r16_service_auth.py` (9 tests) y `test_observabilidad.py` (6 tests) pasan
- [ ] Sin token → 401; un llamador fuera de la allowlist → 403 y el evento `svc.reject.token`
- [ ] Las cabeceras `X-User-*` sin el token del gateway se ignoran (401)
- [ ] `require_perm` responde `403 "permiso insuficiente"` y emite `perm.denied`
- [ ] `audit.emit` escribe una línea JSON con `"msg": <acción>` y el resto en `event`; `testing.events(caplog, acción)` la encuentra
- [ ] `/health` responde sin token; con `engine=None`, sin BD
- [ ] Correlación (RNF-19): el `X-Request-ID` del gateway llega al código y a los eventos; uno ausente o inválido se reemplaza por uno de 32 hex
- [ ] Una línea de registro JSON por petición, con `status` y `ms` y **sin query string** (RNF-18)

## Entregables

- `services/shared/shared/{service_auth,identity,audit,web,observability,testing}.py`
- `services/shared/tests/test_r16_service_auth.py`, `test_observabilidad.py`

## Documentación a actualizar

- Fila R16 de la trazabilidad

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
