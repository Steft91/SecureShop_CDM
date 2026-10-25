# T-08 · AUD-1: Esqueleto de `audit`, migración y mínimo privilegio (R11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Primer parcial |
| Bloqueado por | [T-07 · FND-7](../andres/T-07-integracion-continua.md) (Andrés) |
| Desbloquea | [T-09 · AUD-2](../zaith/T-09-audit-ingesta-y-cadena.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-02-audit.md`](../../plans/2026-10-13-02-audit.md), sección *Task AUD-1* |
| Estado | Pendiente |

## Objetivo

Servicio de auditoría con su tabla `audit_log`, la cadena de hash y un rol de aplicación que no puede modificar ni borrar.

## Criterios de aceptación

- [ ] `audit_app` solo tiene `SELECT, INSERT` sobre `audit_log` (`test_r11_privilegios.py`)
- [ ] La migración corre con `audit_owner`
- [ ] `docker compose up -d --build audit` → `audit` en estado `healthy`; `audit` entra a la matriz de la CI

## Entregables

- `services/audit/**` (esqueleto, migración, `chain.py`, `local.py`)
- Servicios `audit` y `audit-migrate` en compose

## Documentación a actualizar

- Fila R11 de la trazabilidad

## Verificación

`pytest services/audit -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-09
