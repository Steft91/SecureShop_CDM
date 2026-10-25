# T-10 · AUD-3: Consulta y verificación para el admin global (R5)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Primer parcial |
| Bloqueado por | [T-09 · AUD-2](../zaith/T-09-audit-ingesta-y-cadena.md) (Zaith) |
| Desbloquea | [T-11 · ATH-1](../stefany/T-11-auth-esqueleto-y-jwt.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-02-audit.md`](../../plans/2026-10-13-02-audit.md), sección *Task AUD-3* |
| Estado | Pendiente |

## Objetivo

Consulta paginada y verificación de la cadena, solo con el permiso `audit:read`.

## Criterios de aceptación

- [ ] `GET /api/admin/audit` con `audit:read` → eventos con `id > after_id`, del más nuevo al más viejo
- [ ] Sin el permiso → 403, y el intento queda registrado
- [ ] `GET /api/admin/audit/verify` → `{ok, broken_at}`; si la cadena está rota, registra `audit.chain.broken` (critical)

## Entregables

- `services/audit/audit_svc/routes.py`
- `services/audit/tests/test_r05_admin.py`

## Documentación a actualizar

- Fila R5 de la trazabilidad
- `CLAUDE.md`: marcar `audit`

## Verificación

`pytest services/audit -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-11
