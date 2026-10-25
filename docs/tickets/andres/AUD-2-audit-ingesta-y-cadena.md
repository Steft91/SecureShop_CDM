# AUD-2: Ingesta de eventos y cadena verificable (R3, R16)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Audit |
| Incremento | Primer parcial |
| Necesita | [AUD-1](../andres/AUD-1-audit-esqueleto.md) (Andrés) |
| Lo necesitan | [AUD-3](../andres/AUD-3-audit-consulta.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-02-audit.md`](../../plans/2026-10-13-02-audit.md), sección *Task AUD-2* |
| Estado | Pendiente |

## Objetivo

`POST /internal/events` para los cinco servicios, con el `service` sacado del token y una cadena SHA-256 que detecta alteraciones.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
