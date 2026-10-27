# STG-3: API de análisis aislado en otro proceso (R5, R9, R10, R16)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) (Stefany), [FND-3](../andres/FND-3-argon2-y-limites.md) (Andrés) |
| Lo necesitan | [STG-4](../stefany/STG-4-stego-demo-y-calibracion.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), sección *Task STG-3* |
| Estado | Pendiente |

## Objetivo

`POST /api/stego/analyze` con el permiso `stego:analyze`, con el análisis en un pool de procesos con timeout.

## Cómo trabajar sin esperar

Depende de tu STG-2, de `require_perm` y del registro JSON local del servicio (sin `audit`) y de `TokenBucket` (FND-3 de Andrés). La identidad del gateway se simula con las cabeceras de `shared.testing`: no esperas a `auth` ni al gateway.

## Criterios de aceptación

- [ ] Sin identidad del gateway → 401; sin `stego:analyze` → 403 y `perm.denied`; solo acepta el token del gateway (`test_r05_api.py`)
- [ ] Más de 10 análisis por minuto por usuario → 429 y `stego.ratelimited`; el límite es por usuario
- [ ] Si el análisis supera `STEGO_TIMEOUT_S` → `revision_manual`
- [ ] Se emite `stego.analyzed` (info si es `limpia`; warning en los demás casos)

## Entregables

- `services/stego/stego_svc/{pipeline,routes}.py`
- `services/stego/tests/test_r05_api.py`

## Documentación a actualizar

- Filas R5, R9, R10 y R16 de la trazabilidad

## Verificación

`pytest services/stego -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)


> **Actualización de alcance:** STG-5, STG-6 y STG-7 completan en este parcial los 9 formatos (GIF, WAV, MP3, MP4, PDF, DOCX y TXT), además de PNG y JPEG.
