# Tickets

Un ticket por tarea de los planes de `docs/plans/`. El plan manda: el ticket resume el objetivo, los criterios de aceptación y qué se puede adelantar sin esperar a nadie.

Solo existe el **primer parcial** (gateway, `auth` y `stego`, probados con Postman). Las carpetas `parcial-2/` y `parcial-3/` se crean cuando el docente diga qué se entrega en cada uno.

## Cómo se trabaja

- Cada persona tiene su carpeta y sus tickets van en orden de fase. Dentro de una fase, el orden es el de la tabla.
- **Fase A**: nadie espera a nadie. Zaith deja `shared` lista, Andrés hace FND-3 y Stefany los algoritmos de `stego`.
- **Fase B**: cada servicio sobre `shared`. Lo único que cruza personas es `shared` (FND-2/3/4/5) y está al principio a propósito.
- **Fase C**: el gateway junta `auth` y `stego`, y luego vienen Postman, el informe y la demo.
- Si te falta algo de la fila *Necesita*, sigue con lo de *Cómo trabajar sin esperar*: las *Interfaces* de cada tarea en el plan fijan las firmas exactas.
- Al cerrar un ticket, actualiza su *Estado* aquí y en el ticket.

## Zaith

| Fase | Ticket | Necesita | Estado |
|---|---|---|---|
| A | [FND-1: Higiene del repo y contexto de Claude Code](parcial-1/zaith/FND-1-higiene-y-claude-code.md) | — | Pendiente |
| A | [FND-2: Paquete `shared`: secretos y utilidades criptográficas](parcial-1/zaith/FND-2-shared-cripto-y-secretos.md) | — | Pendiente |
| A | [FND-4: Autenticación entre servicios, identidad, eventos de seguridad y base web (R16)](parcial-1/zaith/FND-4-autenticacion-entre-servicios.md) | FND-2 | Pendiente |
| A | [FND-5: Utilidades de BD para pruebas y migraciones comunes](parcial-1/zaith/FND-5-utilidades-de-bd-y-pruebas.md) | FND-2 | Pendiente |
| A | [FND-6: Plantilla Docker, generación de secretos y PostgreSQL de `auth`](parcial-1/zaith/FND-6-docker-secretos-postgres.md) | FND-2 | Pendiente |
| B | [FND-7: Integración continua](parcial-1/zaith/FND-7-integracion-continua.md) | FND-3, FND-6 | Pendiente |
| C | [GW-1: Gateway Nginx con TLS 1.3, `auth_request` y las rutas del parcial (R5, R7, R10, R16)](parcial-1/zaith/GW-1-gateway-parcial.md) | FND-6, ATH-4, STG-4 | Pendiente |

## Andrés

| Fase | Ticket | Necesita | Estado |
|---|---|---|---|
| A | [FND-3: Contraseñas Argon2id y límites de intentos](parcial-1/andres/FND-3-argon2-y-limites.md) | — | Pendiente |
| B | [ATH-1: Esqueleto de `auth`, catálogo de permisos, rol `admin` y firma de JWT (R11)](parcial-1/andres/ATH-1-auth-esqueleto-y-jwt.md) | FND-2, FND-3, FND-4, FND-5 | Pendiente |
| B | [ATH-2: Registro, login, JWT y sesión de dispositivo único, `verify`, `me` y `logout` (R4, R5, R10, R13, R16)](parcial-1/andres/ATH-2-auth-registro-login-verify.md) | ATH-1 | Pendiente |
| B | [ATH-3: Alta del admin global por CLI (R4)](parcial-1/andres/ATH-3-auth-admin-por-cli.md) | ATH-2 | Pendiente |
| B | [ATH-4: Roles, permisos y administración de cuentas (R5)](parcial-1/andres/ATH-4-auth-roles-y-permisos.md) | ATH-3 | Pendiente |

## Stefany

| Fase | Ticket | Necesita | Estado |
|---|---|---|---|
| A | [STG-1: Esqueleto de `stego` sin BD, imágenes sintéticas y estegoanálisis (R6)](parcial-1/stefany/STG-1-stego-esqueleto-y-analisis.md) | FND-2, FND-4 | Pendiente |
| B | [STG-2: Formatos, validación previa y veredicto (R6, R9)](parcial-1/stefany/STG-2-stego-formatos-y-veredicto.md) | STG-1 | Pendiente |
| B | [STG-3: API de análisis aislado en otro proceso (R5, R9, R10, R16)](parcial-1/stefany/STG-3-stego-api.md) | STG-2, FND-3 | Pendiente |
| B | [STG-4: Imágenes de la demo y calibración rápida](parcial-1/stefany/STG-4-stego-demo-y-calibracion.md) | STG-3 | Pendiente |
| C | [PAR-1: Colección de Postman del flujo del docente (RP-11)](parcial-1/stefany/PAR-1-postman.md) | GW-1, STG-4 | Pendiente |
| C | [PAR-2: Informe del primer parcial (RP-10)](parcial-1/stefany/PAR-2-informe-parcial.md) | GW-1 | Pendiente |
| C | [PAR-3: Guion de la demo y ensayo desde un clon limpio (RP-11)](parcial-1/stefany/PAR-3-demo-y-ensayo.md) | PAR-1, PAR-2 | Pendiente |

## Cruces entre personas

| Quién espera | Qué | De quién | Mientras tanto |
|---|---|---|---|
| Andrés (ATH-1) | FND-2, FND-4, FND-5 | Zaith | Migración y `tokens.py` (sin `shared`) |
| Stefany (STG-1) | FND-2, FND-4 | Zaith | `stego.py`, `png.py`, `jpeg.py`, `synthetic.py` |
| Stefany (STG-3) | FND-3 | Andrés | STG-2 |
| Zaith (FND-7) | FND-3 | Andrés | `ci.yml` y `.coveragerc` |
| Zaith (GW-1) | ATH-4, STG-4 | Andrés, Stefany | Steps 1–4 (`nginx -t`) |
| Stefany (PAR-1, PAR-2) | GW-1 | Zaith | Peticiones de la colección y secciones del informe |
