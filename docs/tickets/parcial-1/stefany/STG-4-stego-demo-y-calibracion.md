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
| Estado | Pendiente |

## Objetivo

Generar las 4 imágenes de la demo y fijar los umbrales con al menos 15 fotos reales.

## Cómo trabajar sin esperar

Junta las fotos reales para la calibración desde el primer día (en `services/stego/tools/calibracion/`, que está en `.gitignore`). Al cerrar, avisa a Zaith: GW-1 usa estas imágenes.

## Criterios de aceptación

- [ ] `stego_lab.py demo docs/demo-imagenes` escribe las 4 imágenes y cada una da su veredicto esperado (`test_demo.py`)
- [ ] `docs/calibracion-estego.md` tiene la tabla TPR/FPR con ≥ 15 fotos reales y los umbrales elegidos
- [ ] Si los umbrales cambian, quedan en compose y en la skill, y `pytest services/stego` sigue en verde
- [ ] Fila R6 en *Implementado*

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

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
