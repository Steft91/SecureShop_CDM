# T-18 · STG-4: Imágenes de la demo y calibración rápida

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Primer parcial |
| Bloqueado por | [T-17 · STG-3](../stefany/T-17-stego-api.md) (Stefany) |
| Desbloquea | [T-19 · GW-1](../andres/T-19-gateway-parcial.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../plans/2026-10-13-10-stego.md), sección *Task STG-4* |
| Estado | Pendiente |

## Objetivo

Generar las 4 imágenes de la demo y fijar los umbrales con al menos 15 fotos reales.

## Criterios de aceptación

- [ ] `stego_lab.py demo docs/demo-imagenes` escribe las 4 imágenes, y cada una da su veredicto esperado (`test_demo.py`)
- [ ] `docs/calibracion-estego.md` tiene la tabla TPR/FPR con ≥ 15 fotos reales y los umbrales elegidos
- [ ] Si los umbrales cambian, quedan en compose y en la skill, y `pytest services/stego` sigue en verde

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

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-19
