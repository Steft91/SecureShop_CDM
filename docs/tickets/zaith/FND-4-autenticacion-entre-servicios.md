# FND-4: Autenticación entre servicios, identidad, auditoría y base web (R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Incremento | Primer parcial |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith) |
| Lo necesitan | [AUD-1](../andres/AUD-1-audit-esqueleto.md) (Andrés), [ATH-1](../andres/ATH-1-auth-esqueleto-y-jwt.md) (Andrés), [STG-1](../stefany/STG-1-stego-esqueleto-y-analisis.md) (Stefany), [ROOM-1](../andres/ROOM-1-rooms-crear-y-mis-salas.md) (Andrés), [CHAT-1](../zaith/CHAT-1-chat-almacen-cifrado.md) (Zaith), [MED-1](../stefany/MED-1-media-archivos-cifrados.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-4* |
| Estado | Pendiente |

## Objetivo

Tokens de servicio con allowlist por hash, identidad del gateway (`X-User-*`), `require_perm`, cliente de auditoría con fallback y la app base con errores JSON.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] Los 12 tests de `test_r16_service_auth.py` pasan
- [ ] Sin token → 401; un llamador fuera de la allowlist → 403 y `svc.reject.token`
- [ ] Las cabeceras `X-User-*` sin el token del gateway se ignoran (401)
- [ ] `require_perm` responde `403 "permiso insuficiente"` y audita `perm.denied`
- [ ] `/health` responde sin token; con `engine=None`, sin BD
- [ ] Correlación (RNF-19): el `X-Request-ID` del gateway llega al código, a `ServiceClient` y a `AuditClient`; uno ausente o inválido se reemplaza por uno de 32 hex (`test_observabilidad.py`, 7 tests)
- [ ] Una línea de registro JSON por petición, con `status` y `ms` y **sin query string** (RNF-18)

## Entregables

- `services/shared/shared/{service_auth,identity,audit_client,web,observability,testing}.py`
- `services/shared/tests/test_r16_service_auth.py`, `test_observabilidad.py`

## Documentación a actualizar

- Fila R16 de la trazabilidad (y R3: la correlación llega a audit)

## Verificación

`pytest services/shared -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Andrés y Stefany de que FND-4 ya está cerrado
