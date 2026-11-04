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

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

El `README.md` del repositorio, el guion de la sustentación con su plan B y un ensayo completo desde un `git clone` limpio.

## Cómo trabajar sin esperar

El README y el guion se escriben con la spec §23 y la colección de PAR-1; el ensayo es lo último del parcial y lo hacen los tres.

## Criterios de aceptación

- [ ] `README.md` en la raíz: clonar, `python deploy/gen_secrets.py`, mkcert, `docker compose up -d --build`, crear el admin, importar la colección y correr `pytest`
- [ ] `docs/demo-parcial-1.md` sigue el orden que pide el enunciado: los dos servicios por separado (T01), usuario con dos roles y un rol en dos usuarios, login y análisis, los negativos, la revocación con el mismo JWT, AUTH caído y las dos imágenes con sus limitaciones
- [ ] Plan B: captura del Runner y salida de `pytest`
- [ ] `docs/evidencias/eventos-demo.log`: los registros de la demo sin JWT, contraseñas ni secretos (T12)
- [ ] Ensayo desde un clon limpio, con la demo cronometrada
- [ ] `CLAUDE.md`: primer parcial cerrado

## Entregables

- `README.md`, `docs/demo-parcial-1.md`, `docs/evidencias/eventos-demo.log`

## Documentación a actualizar

- `CLAUDE.md`

## Verificación

`pytest services/shared services/auth services/stego -q` y el ensayo del Step 2

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
