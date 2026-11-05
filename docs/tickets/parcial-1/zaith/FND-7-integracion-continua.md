# FND-7: Integración continua

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Módulo | Fundaciones |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [FND-3](../andres/FND-3-argon2-y-limites.md) (Andrés), [FND-6](../zaith/FND-6-docker-secretos-postgres.md) (Zaith) |
| Lo necesitan | Nadie más |
| Plan | [`docs/plans/2026-10-13-01-fundaciones.md`](../../../plans/2026-10-13-01-fundaciones.md), sección *Task FND-7* |
| Estado | Cerrado en local (2026-11-04, `d8bb1e2`); faltan el run en GitHub (push autorizado) y la regla de `main` (quien administra el repo) |

## Objetivo

Workflow de GitHub Actions con la matriz de servicios, SAST (CodeQL) y detección de secretos (gitleaks).

## Cómo trabajar sin esperar

Puedes escribir `ci.yml` y `.coveragerc` desde la fase A; para el Step 2 (todo en verde en local) necesitas FND-3 de Andrés dentro de `shared`. Andrés y Stefany suman `auth` y `stego` a la matriz en ATH-1 y STG-1.

## Criterios de aceptación

- [x] `.github/workflows/ci.yml` tiene los jobs `services` (matriz `[shared, auth]`; `stego` entra con STG-1), `codeql` y `secrets`
- [x] El job `services` corre ruff, pytest, bandit y pip-audit
- [x] El job falla si un servicio baja del 80 % de cobertura de líneas (RNF-10) o si una función supera la complejidad 10 (RNF-11) (2026-11-04 en local: `shared` 92 %, `auth` 96 %; ruff con `C90` limpio; bandit y pip-audit sin hallazgos)
- [x] gitleaks sin falsos positivos y sin eximir carpetas: `.gitleaksignore` lista por huella los 21 hallazgos ya commiteados (ejemplos de `docs/plans/` y la contraseña de prueba de `services/auth/tests/conftest.py`); gitleaks 8.30.1, el mismo que fija la CI, no encuentra nada en los 66 commits de ramas y remotos
- [x] Auditoría (`security-auditor`, 2026-11-04) aplicada: acciones fijadas por SHA, `persist-credentials: false`, CodeQL publica en Code scanning, revisión completa semanal y a pedido, pip-audit también sobre el `requirements.lock` y `gitleaks-action@v3` (v2 usa Node 20, ya retirado de los runners)
- [ ] Cuando el equipo autorice el primer `push`, la CI queda en verde (no se hace `push` sin autorización)
- [ ] Quien administra el repositorio protege `main`: PR con 1 aprobación, los jobs en verde y "Code scanning results" de CodeQL (Step 4; anotar la fecha en la trazabilidad)

## Entregables

- `.github/workflows/ci.yml`, `.coveragerc`, `.gitleaksignore`

## Documentación a actualizar

- `docs/cumplimiento-normativo.md` (Shift Left: evidencia de la CI)

## Verificación

`python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` y, cuando se autorice el push, el run en verde

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
