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
| Estado | Pendiente |

## Objetivo

Workflow de GitHub Actions con la matriz de servicios, SAST (CodeQL) y detección de secretos (gitleaks).

## Cómo trabajar sin esperar

Puedes escribir `ci.yml` y `.coveragerc` desde la fase A; para el Step 2 (todo en verde en local) necesitas FND-3 de Andrés dentro de `shared`. Andrés y Stefany suman `auth` y `stego` a la matriz en ATH-1 y STG-1.

## Criterios de aceptación

- [ ] `.github/workflows/ci.yml` tiene los jobs `services` (matriz `[shared]`), `codeql` y `secrets`
- [ ] El job `services` corre ruff, pytest, bandit y pip-audit
- [ ] El job falla si un servicio baja del 80 % de cobertura de líneas (RNF-10) o si una función supera la complejidad 10 (RNF-11)
- [ ] Cuando el equipo autorice el primer `push`, la CI queda en verde (no se hace `push` sin autorización)
- [ ] Quien administra el repositorio protege `main`: PR con 1 aprobación y los jobs en verde (Step 4; anotar la fecha en la trazabilidad)

## Entregables

- `.github/workflows/ci.yml`, `.coveragerc`

## Documentación a actualizar

- `docs/cumplimiento-normativo.md` (Shift Left: evidencia de la CI)

## Verificación

`python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` y, cuando se autorice el push, el run en verde

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
