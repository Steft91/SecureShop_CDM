# T-15 · STG-1: Esqueleto de `stego` sin BD, estegoanálisis y sanitización (R6)

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Primer parcial |
| Bloqueado por | [T-14 · ATH-4](../stefany/T-14-auth-roles-y-permisos.md) (Stefany) |
| Desbloquea | [T-16 · STG-2](../andres/T-16-stego-formatos-y-veredicto.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../plans/2026-10-13-10-stego.md), sección *Task STG-1* |
| Estado | Pendiente |

## Objetivo

Servicio `stego` sin estado, con chi² (Westfeld), RS (Fridrich), entropía LSB, estructura PNG/JPEG y la sanitización del plano LSB.

## Criterios de aceptación

- [ ] Un PNG con LSB secuencial al 10 % → chi² o RS por encima del umbral; un PNG natural → por debajo (`test_r06_estego.py`)
- [ ] Datos después de `IEND` o `FFD9` → anomalía estructural
- [ ] Después de sanitizar, el plano LSB cambia y se conserva el alfa
- [ ] `stego` en estado `healthy` en compose (sin BD, solo en la red `apps`) y en la matriz de la CI

## Entregables

- `services/stego/**` (esqueleto, `stego.py`, `png.py`, `jpeg.py`, `tools/stego_lab.py`)
- Servicio `stego` en compose

## Documentación a actualizar

- Fila R6 de la trazabilidad
- `.claude/skills/stego-analysis/SKILL.md` si cambia un umbral

## Verificación

`pytest services/stego -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-16
