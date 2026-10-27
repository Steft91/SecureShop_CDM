# STG-1: Esqueleto de `stego` sin BD, imágenes sintéticas y estegoanálisis (R6)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Stego |
| Parcial | Primer parcial |
| Fase | A — arranque, sin depender de nadie |
| Necesita | [FND-2](../zaith/FND-2-shared-cripto-y-secretos.md) (Zaith), [FND-4](../zaith/FND-4-autenticacion-entre-servicios.md) (Zaith) |
| Lo necesitan | [STG-2](../stefany/STG-2-stego-formatos-y-veredicto.md) (Stefany) |
| Plan | [`docs/plans/2026-10-13-10-stego.md`](../../../plans/2026-10-13-10-stego.md), sección *Task STG-1* |
| Estado | Pendiente |

> El paso de compose necesita además FND-6.

## Objetivo

Servicio `stego` sin estado, con chi² (Westfeld), RS (Fridrich), entropía LSB, estructura PNG/JPEG y las imágenes sintéticas de las pruebas.

## Cómo trabajar sin esperar

Empieza ya por los módulos de algoritmo: `stego.py`, `png.py`, `jpeg.py` y `synthetic.py` solo usan numpy, Pillow y scipy, no `shared`. Sus tests de `test_r06_estego.py` corren con `PYTHONPATH=services/stego pytest …`. `config.py`, `main.py` y `conftest.py` esperan a FND-2 y FND-4 de Zaith.

## Criterios de aceptación

- [ ] Un PNG con LSB secuencial al 10 % dispara chi²; LSB aleatorio al 50 % dispara RS; imágenes limpias y capturas con colores planos no disparan (`test_r06_estego.py`)
- [ ] Datos después de `IEND` o `FFD9` → anomalía estructural; un JPEG progresivo no confunde al parser
- [ ] `natural_image` y `embed_lsb` son deterministas con la misma semilla
- [ ] Ninguna función pasa de complejidad 10: `jpeg.structure` se parte con `skip_entropy` (RNF-11)
- [ ] `stego` en estado `healthy` en compose (sin BD, solo en la red `apps`) y en la matriz de la CI

## Entregables

- `services/stego/**` (esqueleto, `stego.py`, `png.py`, `jpeg.py`, `synthetic.py`, `tools/stego_lab.py`)
- Servicio `stego` en compose

## Documentación a actualizar

- Fila R6 de la trazabilidad
- `.claude/skills/stego-analysis/SKILL.md` si cambia un umbral

## Verificación

`pytest services/stego -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)


> **Actualización de alcance:** STG-5, STG-6 y STG-7 completan en este parcial los 9 formatos (GIF, WAV, MP3, MP4, PDF, DOCX y TXT), además de PNG y JPEG.
