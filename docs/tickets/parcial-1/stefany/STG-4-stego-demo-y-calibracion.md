# STG-4: Imágenes de la demo y calibración rápida

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [STG-3](../stefany/STG-3-stego-api.md) (Stefany) |
| Lo necesitan | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith), [PAR-1](../stefany/PAR-1-postman.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), sección *Task STG-4* |
| Estado | Cerrado (2026-11-04) |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

Las imágenes de la demo (T09 y T10) y la justificación del método con la calibración.

## Cómo trabajar sin esperar

La calibración con 39 fotos ya está en `docs/calibracion-estego.md` (rama `feat/stefany-stego`). Al cerrar, avisa a Zaith: GW-1 usa estas imágenes.

## Criterios de aceptación

- [x] `stego_lab.py demo docs/demo-imagenes` escribe `referencia.png` (`sin_indicios`), `lsb.png` (la misma con LSB embebido, `sospechoso`), `zip-al-final.png` (`sospechoso` por estructura), `no-es-imagen.png` (415) y `truncada.png` (422), y cada una da lo esperado (`test_demo.py`)
- [x] El archivo de más de 5 MB para T10 se genera en la demo y no se versiona
- [x] `docs/calibracion-estego.md` tiene la tabla TPR/FPR, los umbrales elegidos y la justificación de chi², RS y entropía (procedimiento, parámetros y limitaciones) que usa el informe
- [x] Si los umbrales cambian, quedan en compose y en la skill, y `pytest services/stego` sigue en verde
- [x] Fila R6 en *Implementado*

## Entregables

- `services/stego/tools/stego_lab.py` (subcomando `demo`)
- `docs/demo-imagenes/`
- `docs/calibracion-estego.md`

## Documentación a actualizar

- `docs/calibracion-estego.md`
- `CLAUDE.md`: marcar `stego`

## Verificación

`pytest services/stego -q`

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado, con la fecha; el hash se añadirá al cerrar los commits.
