# T-16 · STG-2: Formatos, validación previa y veredicto (R6, R9)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Primer parcial |
| Bloqueado por | [T-15 · STG-1](../zaith/T-15-stego-esqueleto-y-analisis.md) (Zaith) |
| Desbloquea | [T-17 · STG-3](../stefany/T-17-stego-api.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../plans/2026-10-13-10-stego.md), sección *Task STG-2* |
| Estado | Pendiente |

## Objetivo

El punto de extensión `FORMATS`, la validación previa y la clasificación en `invalida`, `problema`, `revision_manual` o `limpia`.

## Criterios de aceptación

- [ ] Un `.exe` renombrado, un PNG truncado, una bomba de descompresión, más de 5 MB o más de 20 MP → `invalida` con sus `motivos` (`test_r09_formatos.py`)
- [ ] Anomalía estructural → `problema`; solo estadística → `revision_manual`; si coinciden, gana `problema` (`test_veredicto.py`)
- [ ] RGBA, paleta, escala de grises y 16 bits se analizan y sanitizan sin 500 (`test_modos_de_imagen_no_rgb`)
- [ ] El JSON del veredicto tiene las claves de la spec §12.7 y los NaN salen como `null`

## Entregables

- `services/stego/stego_svc/{formats,verdict}.py`
- Tests `test_r09_formatos.py`, `test_veredicto.py`

## Documentación a actualizar

- Filas R6 y R9 de la trazabilidad

## Verificación

`pytest services/stego -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-17
