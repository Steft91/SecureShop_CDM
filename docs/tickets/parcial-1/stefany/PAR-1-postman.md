# PAR-1: Colección de Postman del flujo del docente (RP-11)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Entrega del parcial |
| Parcial | Primer parcial |
| Fase | C — integración y entrega |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith), [STG-4](../stefany/STG-4-stego-demo-y-calibracion.md) (Stefany) |
| Lo necesitan | [PAR-3](../stefany/PAR-3-demo-y-ensayo.md) (Stefany) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../../plans/2026-10-25-parcial-1.md), sección *Task PAR-1* |
| Estado | Cerrado con evidencia pendiente (2026-11-04) |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

La colección que recorre por el gateway los escenarios **T01–T12** del enunciado (spec §23.9), con un test por petición.

## Cómo trabajar sin esperar

Arma las carpetas y los `pm.test` con las rutas de §23.4 y §23.7 antes de que el gateway esté arriba; solo la corrida espera a GW-1.

## Criterios de aceptación

- [x] El flujo de la sustentación: el ADMIN crea dos cuentas, le da ANALYST y USER a una y ANALYST a las dos (T05), repite una asignación (T06), la cuenta entra y analiza con su JWT
- [x] Negativos: sin token y con JWT alterado → 401 (T03); el JWT vencido está cubierto por `services/auth/tests/test_r16_check.py::test_jwt_vencido_401`; solo USER → 403 (T04); se retira ANALYST y el mismo JWT → 403 (T07); análisis ajeno → 403 (T11)
- [x] `referencia.png` → `sin_indicios` y `lsb.png` → `sospechoso`, con sus métricas (T09); no imagen → 415, truncada → 422, más de 5 MB → 413 (T10)
- [x] T01 y T08 (parar y levantar `auth` o `stego`) quedan como pasos manuales con la petición que se repite
- [x] El admin entra con `admin_username` y `admin_password`, variables de entorno solo locales; la colección no tiene contraseñas reales ni tokens (Step 3)
- [x] Newman en verde (36 peticiones, 57 aserciones, 0 fallas); [ ] captura del Runner en `docs/evidencias/parcial-1-runner.png` (la incorpora el equipo en la sustentación).

## Entregables

- `docs/postman/parcial-1.postman_collection.json`
- `docs/postman/README.md`
- `docs/evidencias/parcial-1-runner.png`

## Documentación a actualizar

- *Verificación manual* de la trazabilidad

## Verificación

El Runner de Postman contra `https://localhost` (Step 2 del plan)

## Al cerrar

- [x] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [x] La trazabilidad y los documentos de arriba están actualizados
- [x] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [x] *Estado* = Cerrado con evidencia pendiente, con la fecha; el hash se añadirá al cerrar los commits.
