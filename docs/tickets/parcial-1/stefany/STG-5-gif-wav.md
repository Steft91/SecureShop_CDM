# STG-5: GIF y WAV

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Modulo | Stego |
| Parcial | Primer parcial |
| Fase | B - servicios sobre `shared` |
| Necesita | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) |
| Lo necesitan | [STG-6](../zaith/STG-6-mp3-mp4.md), [STG-7](../andres/STG-7-pdf-docx-txt.md), [PAR-1](../stefany/PAR-1-postman.md) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), *Task STG-5* |
| Estado | Pendiente |

## Objetivo

Agregar analisis seguro y determinista de GIF y WAV al microservicio `stego`.

## Criterios de aceptacion

- [ ] `gif.py` y `wav.py` exponen `STRUCTURAL`, `validate` y `analyze`.
- [ ] Firmas, extensiones, topes, parsers acotados y veredictos estan cubiertos por tests.
- [ ] GIF cubre paleta/frames y WAV cubre RIFF/WAVE, chunks y LSB en silencio.
- [ ] `FORMATS` registra ambos formatos al final y la documentacion de limites queda actualizada.
- [ ] `pytest services/stego -q` y Ruff pasan.

## Verificacion

Tests unitarios y ejecucion de la coleccion con un archivo limpio y uno sospechoso de cada formato.
