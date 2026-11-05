# STG-3: API de análisis con persistencia, resultados y análisis aislado (R5, R9, R10, R11, R16)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Parcial | Primer parcial |
| Fase | B — servicios sobre `shared` |
| Necesita | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) (Stefany), [FND-3](../andres/FND-3-argon2-y-limites.md) (Andrés) |
| Lo necesitan | [STG-4](../stefany/STG-4-stego-demo-y-calibracion.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), sección *Task STG-3* |
| Estado | Cerrado (2026-11-04; commit pendiente) |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

`POST /api/steganography/analyze` (`steganography.analyze`) y `GET /api/steganography/results/{id}` (`steganography.results.read` y propiedad), sobre `shared`, con BD propia, la cuarentena en un volumen aislado y el análisis en un pool de procesos con timeout (spec §23.7).

## Cómo trabajar sin esperar

Parte de `routes.py` de `feat/stefany-stego` y corrige:
1. Montar la app con `shared.web.create_base_app` y usar `require_perm`. Hoy confía en una cabecera `X-Service-Name: gateway` que cualquiera puede mandar y lee `X-User-*` a mano (R16).
2. Cambiar la lista `_events` por `shared.audit.emit`: hoy los eventos nunca llegan a los registros (T12).
3. Leer los umbrales de `Settings`: hoy `.995` y `.15` están fijos en la ruta.
4. Cambiar `asyncio.to_thread` por `ProcessPoolExecutor`: un hilo que se pasa del tiempo sigue corriendo.

La BD de pruebas sale de `deploy/docker-compose.test.yml` con `testing.prepare_database("stego", …)` (FND-5). La BD `stego` del stack (`init.sh`, `gen_secrets.py` y compose) la agrega Zaith en GW-1.

## Criterios de aceptación

- [x] Sin el token del gateway → 401 (middleware); sin identidad → 401; sin `steganography.analyze` → 403 y `perm.denied` (`test_r05_api.py`)
- [x] Cada análisis queda en `analyses` con id, usuario, `sha256`, técnica, indicadores, fecha, `status` y `action`; `stego_app` solo tiene `SELECT` e `INSERT` (`test_r11_privilegios_stego`)
- [x] La respuesta trae las claves del JSON de spec §23.7
- [x] `GET /api/steganography/results/{id}`: el dueño → 200; otro ANALYST → 403 y `perm.denied` (T11, `test_r05_resultado_ajeno_403`); con `steganography.results.read_any` → 200; inexistente → 404
- [x] Un `sospechoso` deja el archivo en `stego_quarantine/<analysis_id>` (`STEGO_QUARANTINE_DIR=/data`, archivos `0600`), escrito antes del `INSERT`; si falla la escritura o el `INSERT` → 503; los demás no dejan archivo
- [x] `filename` saneado (basename, NFC, sin caracteres de control, ≤ 255) y nunca en los eventos; un nombre de 300 caracteres no da 500 (`test_nombre_largo_se_trunca`)
- [x] El 413 también emite `stego.rejected`
- [x] Más de 10 análisis por minuto por usuario → 429 y `stego.ratelimited`; tiempo excedido → `no_concluyente` (`test_timeout_del_analisis_es_no_concluyente`)
- [x] Eventos con `shared.audit.emit` (`stego.analyzed`, `stego.rejected`, `stego.result.read`), sin el contenido del archivo
- [x] `services/stego/.env.example`, la migración `0001_analisis.py` y `docs/openapi/stego.json` (exportado con `app.openapi()`)

## Entregables

- `services/stego/stego_svc/{pipeline,routes}.py` y `services/stego/migrations/`
- `services/stego/tests/test_r05_api.py`, `services/stego/tests/test_resultados.py`
- `services/stego/.env.example`, `docs/openapi/stego.json`

## Documentación a actualizar

- Filas R5, R9, R10, R11 y R16 de la trazabilidad

## Verificación

`pytest services/stego -q`

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado, con la fecha; el hash se añadirá al cerrar los commits.


> **Alcance (spec §23.1):** PNG con análisis de píxeles y estructura es lo obligatorio; JPEG, GIF y WAV entran con lo que ya tienen. STG-6 y STG-7 no bloquean la entrega.
