# T-22 · PAR-3: Guion de la demo y ensayo desde un clon limpio (RP-11)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Incremento | Primer parcial |
| Bloqueado por | [T-21 · PAR-2](../zaith/T-21-informe-parcial.md) (Zaith) |
| Desbloquea | [T-23 · ATH-5](../stefany/T-23-auth-suspension-y-latido.md) (Stefany) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../plans/2026-10-25-parcial-1.md), sección *Task PAR-3* |
| Estado | Pendiente |

## Objetivo

El guion de unos 7 minutos con el plan B, y un ensayo completo desde un `git clone` limpio.

## Criterios de aceptación

- [ ] `docs/demo-parcial-1.md` con los 5 pasos, quién habla y qué petición se ejecuta
- [ ] Ensayo desde un clon limpio: Runner 18/18 y demo en ≤ 8 minutos cronometrados
- [ ] `pytest` de `shared`, `audit`, `auth` y `stego` en verde y la CI de la rama en verde
- [ ] `CLAUDE.md`: primer parcial cerrado

## Entregables

- `docs/demo-parcial-1.md`

## Documentación a actualizar

- `CLAUDE.md`

## Verificación

`pytest services/shared services/audit services/auth services/stego -q` y el ensayo del Step 2

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Stefany de que puede empezar T-23
