# STG-6: MP3 y MP4

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Modulo | Stego |
| Parcial | Primer parcial |
| Fase | B - servicios sobre `shared` |
| Necesita | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) |
| Lo necesitan | [GW-1](../zaith/GW-1-gateway-parcial.md), [PAR-1](../stefany/PAR-1-postman.md) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), *Task STG-6* |
| Estado | Pendiente |

## Objetivo

Agregar MP3 y MP4 sin lecturas ilimitadas, respetando los limites del formato y el tope de 20 MB del gateway para MP4.

## Criterios de aceptacion

- [ ] `mp3.py` y `mp4.py` exponen `STRUCTURAL`, `validate` y `analyze`.
- [ ] Se validan frames/ID3 de MP3 y cajas ISO-BMFF de MP4, con firma y extension coherentes.
- [ ] Tests cubren limpio, sospechoso, corrupto, extension incorrecta y exceso de tamano.
- [ ] `FORMATS` registra ambos formatos y el gateway acepta hasta 20 MB unicamente en analisis.
- [ ] `pytest services/stego -q` y Ruff pasan.

## Verificacion

Tests unitarios, `nginx -t` y coleccion Postman con los casos MP3/MP4.
