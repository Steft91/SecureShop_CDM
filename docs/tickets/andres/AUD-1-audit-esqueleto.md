# AUD-1: Esqueleto de `audit`, migración y mínimo privilegio (R11)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Audit |
| Incremento | Primer parcial |
| Necesita | [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [AUD-2](../andres/AUD-2-audit-ingesta-y-cadena.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-02-audit.md`](../../plans/2026-10-13-02-audit.md), sección *Task AUD-1* |
| Estado | Pendiente |

> El paso de compose necesita además FND-6.

## Objetivo

Servicio de auditoría con su tabla `audit_log`, la cadena de hash y un rol de aplicación que no puede modificar ni borrar.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
