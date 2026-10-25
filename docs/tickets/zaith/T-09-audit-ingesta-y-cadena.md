# T-09 · AUD-2: Ingesta de eventos y cadena verificable (R3, R16)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Primer parcial |
| Bloqueado por | [T-08 · AUD-1](../stefany/T-08-audit-esqueleto.md) (Stefany) |
| Desbloquea | [T-10 · AUD-3](../andres/T-10-audit-consulta.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-02-audit.md`](../../plans/2026-10-13-02-audit.md), sección *Task AUD-2* |
| Estado | Pendiente |

## Objetivo

`POST /internal/events` para los cinco servicios, con el `service` sacado del token y una cadena SHA-256 que detecta alteraciones.

## Criterios de aceptación

- [ ] `201 {id}`; el `service` sale del token aunque el payload diga otra cosa
- [ ] Una alteración hecha con el owner la detecta `verify` (`broken_at`)
- [ ] `audit_app` no puede `UPDATE`, `DELETE` ni `TRUNCATE`
- [ ] El gateway u otro llamador fuera de la allowlist → 403 (lo registra `audit` directamente en su BD)
- [ ] `request_id` (`^[A-Za-z0-9-]{8,64}$`, si no 422) se guarda en `details` y el hash de la cadena lo cubre (`test_rnf19_*`)

## Entregables

- `services/audit/audit_svc/routes.py`
- `services/audit/tests/test_r03_cadena.py`, `test_r16_llamadores.py`

## Documentación a actualizar

- Filas R3 y R16 de la trazabilidad

## Verificación

`pytest services/audit -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-10
