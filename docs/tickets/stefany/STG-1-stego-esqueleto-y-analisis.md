# STG-1: Esqueleto de `stego` sin BD, estegoanálisis y sanitización (R6)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Incremento | Primer parcial |
| Necesita | [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith), [FND-5](../zaith/FND-5-utilidades-de-bd-y-pruebas.md) (Zaith) |
| Lo necesitan | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../plans/2026-10-13-10-stego.md), sección *Task STG-1* |
| Estado | Pendiente |

> El paso de compose necesita además FND-6.

## Objetivo

Servicio `stego` sin estado, con chi² (Westfeld), RS (Fridrich), entropía LSB, estructura PNG/JPEG y la sanitización del plano LSB.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] Un PNG con LSB secuencial al 10 % → chi² o RS por encima del umbral; un PNG natural → por debajo (`test_r06_estego.py`)
- [ ] Datos después de `IEND` o `FFD9` → anomalía estructural
- [ ] Después de sanitizar, el plano LSB cambia y se conserva el alfa
- [ ] Ninguna función pasa de complejidad 10: `jpeg.structure` se parte con `skip_entropy` (RNF-11)
- [ ] La salida de `sanitize` no tiene residuos estructurales (`png.residual` y `jpeg.residual` vacíos)
- [ ] `stego` en estado `healthy` en compose (sin BD, solo en la red `apps`) y en la matriz de la CI

## Entregables

- `services/stego/**` (esqueleto, `stego.py`, `png.py`, `jpeg.py`, `tools/stego_lab.py`)
- Servicio `stego` en compose

## Documentación a actualizar

- Fila R6 de la trazabilidad
- `.claude/skills/stego-analysis/SKILL.md` si cambia un umbral

## Verificación

`pytest services/stego -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
