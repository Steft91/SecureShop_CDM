# STG-2: Formatos, validación previa y veredicto (R6, R9)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [STG-1](../stefany/STG-1-stego-esqueleto-y-analisis.md) (Stefany) |
| Lo necesitan | [STG-3](../stefany/STG-3-stego-api.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), sección *Task STG-2* |
| Estado | Pendiente |

## Objetivo

El punto de extensión `FORMATS`, la validación previa y la clasificación en `invalida`, `problema`, `revision_manual` o `limpia`.

## Cómo trabajar sin esperar

Depende de tu STG-1 y de `shared.crypto.sha256` (FND-2). `verdict.py` y la tabla de formatos se pueden escribir junto con los módulos de la fase A.

## Criterios de aceptación

- [ ] Contenido que no coincide con la firma, un PNG truncado, una bomba de descompresión, más de 5 MB o más de 20 MP → `invalida` con sus `motivos` (`test_r09_formatos.py`)
- [ ] Anomalía estructural → `problema`; solo estadística → `revision_manual`; si coinciden, gana `problema` (`test_veredicto.py`)
- [ ] RGBA, paleta, escala de grises y 16 bits se analizan sin 500 (`test_modos_de_imagen_no_rgb`)
- [ ] El JSON del veredicto tiene las claves de la spec §12.7 y los NaN salen como `null`

## Entregables

- `services/stego/stego_svc/{formats,verdict}.py`
- Tests `test_r09_formatos.py`, `test_veredicto.py`

## Documentación a actualizar

- Filas R6 y R9 de la trazabilidad

## Verificación

`pytest services/stego -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)


> **Actualización de alcance:** STG-5, STG-6 y STG-7 completan en este parcial los 9 formatos (GIF, WAV, MP3, MP4, PDF, DOCX y TXT), además de PNG y JPEG.
