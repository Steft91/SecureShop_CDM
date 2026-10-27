# PAR-3: Guion de la demo y ensayo desde un clon limpio (RP-11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Entrega del parcial |
| Parcial | Primer parcial |
| Fase | C — integración y entrega |
| Necesita | [PAR-1](../stefany/PAR-1-postman.md) (Stefany), [PAR-2](../stefany/PAR-2-informe-parcial.md) (Stefany) |
| Lo necesitan | Nadie más |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../../plans/2026-10-25-parcial-1.md), sección *Task PAR-3* |
| Estado | Pendiente |

## Objetivo

El guion de unos 7 minutos con el plan B, y un ensayo completo desde un `git clone` limpio.

## Cómo trabajar sin esperar

El guion (quién habla y qué petición se ejecuta) se escribe con la tabla de PAR-1; el ensayo es lo último del parcial y lo hacen los tres.

## Criterios de aceptación

- [ ] `docs/demo-parcial-1.md` con los 5 pasos, quién habla y qué petición se ejecuta
- [ ] Ensayo desde un clon limpio: Runner 30/30 y demo en ≤ 8 minutos cronometrados
- [ ] `pytest` de `shared`, `auth` y `stego` en verde y la CI de la rama en verde
- [ ] `CLAUDE.md`: primer parcial cerrado

## Entregables

- `docs/demo-parcial-1.md`

## Documentación a actualizar

- `CLAUDE.md`

## Verificación

`pytest services/shared services/auth services/stego -q` y el ensayo del Step 2

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
