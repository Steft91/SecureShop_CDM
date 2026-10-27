# FND-1: Higiene del repo y contexto de Claude Code

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Parcial | Primer parcial |
| Fase | A — arranque, sin depender de nadie |
| Necesita | Nada: puedes empezar ya |
| Lo necesitan | Nadie más |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-1* |
| Estado | Pendiente |

## Objetivo

Dejar el repo listo para trabajar: ignorados, lint, reglas de seguridad, hook de protección, skills, agente auditor y la tabla de trazabilidad del parcial.

## Cómo trabajar sin esperar

No depende de nadie: es lo primero que haces. Ciérrala pronto, porque el hook y `ruff.toml` los usan los tres desde su primer commit.

## Criterios de aceptación

- [ ] `.gitignore` excluye `deploy/secrets/`, `deploy/certs/`, `**/.env` y `services/stego/tools/calibracion/`
- [ ] El hook `.claude/hooks/guard.py` bloquea `ws://`, un bloque `PRIVATE KEY` y un secreto literal fuera de `tests/`, `docs/` y `.claude/` (autoprueba del plan)
- [ ] `.claude/settings.json` niega leer `deploy/secrets/**`, `deploy/certs/**` y `**/.env`
- [ ] `docs/trazabilidad-riesgos.md` tiene las filas del parcial (R2, R4, R5, R6, R7, R9, R10, R11, R13 y R16) en *Pendiente*, con su columna ISO
- [ ] `CLAUDE.md` enlaza la spec, el índice, `docs/tickets/` y la trazabilidad, y tiene la lista *Estado actual*
- [ ] `ruff.toml` incluye la regla `C90` con complejidad ≤ 10 por función (RNF-11)
- [ ] `.github/pull_request_template.md` trae la lista de verificación de seguridad

## Entregables

- `.gitignore`, `.gitattributes`, `.dockerignore`, `ruff.toml`
- `.github/pull_request_template.md`
- `CLAUDE.md`, `.claude/**`
- `docs/trazabilidad-riesgos.md`

## Documentación a actualizar

- `CLAUDE.md`
- `docs/trazabilidad-riesgos.md`

## Verificación

La autoprueba de `guard.py` del plan y `ruff check .`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
