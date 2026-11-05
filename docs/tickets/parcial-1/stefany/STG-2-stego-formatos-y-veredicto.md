# STG-2: Formatos, validación previa, veredicto y política (R6, R9)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [STG-1](../stefany/STG-1-stego-esqueleto-y-analisis.md) (Stefany) |
| Lo necesitan | [STG-3](../stefany/STG-3-stego-api.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), sección *Task STG-2* |
| Estado | Cerrado (2026-11-04; commit pendiente) |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

El punto de extensión `FORMATS`, la validación previa (extensión, `Content-Type`, firma, tamaño y píxeles) y la clasificación de la spec §23.7: `sin_indicios`, `sospechoso`, `no_concluyente` o `error`, cada una con su política.

## Cómo trabajar sin esperar

`formats.py` y `verdict.py` ya existen en `feat/stefany-stego`: hay que cambiar los nombres de los veredictos, agregar la política y validar también la extensión y el `Content-Type`.

## Criterios de aceptación

- [x] Más de 5 MB → 413; extensión, `Content-Type` o firma no admitidos → 415; corrupto, truncado, bomba de descompresión o más de 20 MP → 422; los 415 y 422 quedan como `error` con `action = rechazo` (`test_r09_formatos.py`)
- [x] Anomalía estructural o detector estadístico ≥ umbral → `sospechoso` y `cuarentena`; tiempo excedido o menos de 1000 píxeles → `no_concluyente` y `advertencia` (nunca `sin_indicios`); nada → `sin_indicios` y `ninguna` (`test_veredicto.py`)
- [x] RGBA, paleta, escala de grises y 16 bits se analizan sin 500 (`test_modos_de_imagen_no_rgb`)
- [x] `indicators` trae cada métrica con su umbral (`chi2_p_threshold`, `rs_rate_threshold`), los NaN salen como `null`, y la respuesta trae `technique` según el formato y `limitations`

## Entregables

- `services/stego/stego_svc/{formats,verdict}.py`
- Tests `test_r09_formatos.py`, `test_veredicto.py`

## Documentación a actualizar

- Filas R6 y R9 de la trazabilidad

## Verificación

`pytest services/stego -q`

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado, con la fecha; el hash se añadirá al cerrar los commits.


> **Alcance (spec §23.1):** PNG con análisis de píxeles y estructura es lo obligatorio; JPEG, GIF y WAV entran con lo que ya tienen. STG-6 y STG-7 no bloquean la entrega.
