# STG-7: PDF, DOCX y TXT

| Campo | Valor |
|---|---|
| Responsable | Andres |
| Modulo | Stego |
| Parcial | Primer parcial |
| Fase | B - servicios sobre `shared` |
| Necesita | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) |
| Lo necesitan | [PAR-1](../stefany/PAR-1-postman.md), [PAR-3](../stefany/PAR-3-demo-y-ensayo.md) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), *Task STG-7* |
| Estado | Pendiente |

## Objetivo

Completar el analisis seguro de documentos PDF, DOCX y TXT exigido por la Actividad 3.

## Criterios de aceptacion

- [ ] `pdf.py`, `docx.py` y `txt.py` exponen `STRUCTURAL`, `validate` y `analyze`.
- [ ] PDF valida `%PDF` y estructura acotada; DOCX valida OOXML sin extraer de forma ilimitada.
- [ ] TXT solo se acepta con `.txt` declarado y detecta controles, invisibles y entropia sospechosa.
- [ ] Tests cubren archivo limpio, corrupto, extension incorrecta, limites y contenido sospechoso.
- [ ] `FORMATS` registra los tres formatos y la coleccion tiene casos limpios y sospechosos.

## Verificacion

`pytest services/stego -q` y Runner de Postman con 30 peticiones.
