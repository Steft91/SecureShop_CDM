# Tickets

Un archivo por ticket, separado por persona (`andres/`, `stefany/` y `zaith/`). Cada ticket es una tarea de los planes de `docs/plans/` y se llama como ella (`FND-2`, `ATH-3`…).

## Cómo se trabaja

- **Cada persona tiene su módulo y su ruta.** Sigue sus tickets en el orden de abajo, sin esperar turno a los demás.
- **Solo hay tres dependencias entre personas que de verdad bloquean:** la librería `shared` (FND-2, FND-4 y FND-5, de Zaith; FND-3, de Andrés) para correr `pytest`; FND-6 para levantar contenedores; y los servicios ya hechos para integrar (GW-1, PAR, FE y E2E). Todo lo demás se acuerda por contrato.
- **El contrato** es el bloque *Interfaces* de la tarea en el plan: nombres, firmas, rutas y cuerpos exactos. Se escribe contra él y los servicios vecinos se simulan con `testing.Recorder`.
- Cada ticket dice qué **necesita** y quién lo **necesita**. Al cerrarlo, avisa a esas personas.
- **Al arrancar:** Zaith cierra primero FND-2, FND-4 y FND-5 (la librería). Mientras tanto, Andrés escribe FND-3 y deja leídos sus planes (AUD y ATH), y Stefany deja leído el de STG; los tres pueden adelantar el código de sus servicios contra las *Interfaces*.
- Commits en español, sin líneas de atribución, en `feat/arquitectura-chat-seguro`. Nada de `push`, PR ni merge a `main` sin que el equipo lo autorice.
- Si el docente cambia el alcance, se ajustan primero el spec y el plan, y después los tickets.

## Reparto

| Persona | Módulos | Parcial | Incr. 2 | Incr. 3 | Total |
|---|---|---|---|---|---|
| Zaith · Plataforma, chat e integración | Fundaciones, Gateway, Chat, E2E y cierre | 7 | 5 | 3 | 15 |
| Andrés · Identidad y salas | Fundaciones, Audit, Auth, Rooms, Frontend | 8 | 6 | 1 | 15 |
| Stefany · Contenido, cliente y entrega | Stego, Entrega del parcial, Frontend, Media | 7 | 3 | 5 | 15 |

## Ruta de cada persona

### Zaith · Plataforma, chat e integración

| Ticket | Título | Incremento | Necesita | Estado |
|---|---|---|---|---|
| [FND-1](zaith/FND-1-higiene-y-claude-code.md) | Higiene del repo y contexto de Claude Code | Primer parcial | — | Pendiente |
| [FND-2](zaith/FND-2-shared-cripto-y-secretos.md) | Paquete `shared`: secretos, criptografía y vectores | Primer parcial | — | Pendiente |
| [FND-4](zaith/FND-4-autenticacion-entre-servicios.md) | Autenticación entre servicios, identidad, auditoría y base web (R16) | Primer parcial | [FND-2](zaith/FND-2-shared-cripto-y-secretos.md) | Pendiente |
| [FND-5](zaith/FND-5-utilidades-de-bd-y-pruebas.md) | Utilidades de BD para pruebas, migraciones comunes e imágenes sintéticas | Primer parcial | [FND-2](zaith/FND-2-shared-cripto-y-secretos.md) | Pendiente |
| [FND-6](zaith/FND-6-docker-secretos-postgres.md) | Plantilla Docker, generación de secretos y PostgreSQL con 5 BD | Primer parcial | [FND-2](zaith/FND-2-shared-cripto-y-secretos.md) | Pendiente |
| [FND-7](zaith/FND-7-integracion-continua.md) | Integración continua | Primer parcial | [FND-3](andres/FND-3-argon2-y-limites.md), [FND-6](zaith/FND-6-docker-secretos-postgres.md) | Pendiente |
| [GW-1](zaith/GW-1-gateway-parcial.md) | Gateway Nginx con TLS 1.3, `auth_request` y las rutas del parcial (R5, R7, R10, R16) | Primer parcial | [ATH-4](andres/ATH-4-auth-roles-y-permisos.md), [AUD-3](andres/AUD-3-audit-consulta.md), [STG-4](stefany/STG-4-stego-demo-y-calibracion.md) | Pendiente |
| [CHAT-1](zaith/CHAT-1-chat-almacen-cifrado.md) | Esqueleto de `chat`, almacén cifrado y rotación (R2, R11) | Incremento 2 | [FND-4](zaith/FND-4-autenticacion-entre-servicios.md), [FND-5](zaith/FND-5-utilidades-de-bd-y-pruebas.md) | Pendiente |
| [CHAT-2](zaith/CHAT-2-chat-conexion.md) | Conexión: identidad, membresía, `Origin`, *hello* firmado y presencia (R7, R16) | Incremento 2 | [CHAT-1](zaith/CHAT-1-chat-almacen-cifrado.md) | Pendiente |
| [CHAT-3](zaith/CHAT-3-chat-tramas-y-mensajes.md) | Tramas, mensajes, silencio, borrado y `file_url` (R10, R14) | Incremento 2 | [CHAT-2](zaith/CHAT-2-chat-conexion.md) | Pendiente |
| [CHAT-4](zaith/CHAT-4-chat-avisos-y-latidos.md) | Avisos internos, archivos publicados, latidos e inactividad (R16) | Incremento 2 | [CHAT-3](zaith/CHAT-3-chat-tramas-y-mensajes.md) | Pendiente |
| [GW-2](zaith/GW-2-gateway-salas-media-ws.md) | Gateway: rutas de salas, media y WebSocket | Incremento 2 | [GW-1](zaith/GW-1-gateway-parcial.md), [ROOM-4](andres/ROOM-4-rooms-membresia-interna.md), [CHAT-4](zaith/CHAT-4-chat-avisos-y-latidos.md) | Pendiente |
| [E2E-1](zaith/E2E-1-e2e-cuentas-y-gateway.md) | E2E: arnés, cuentas, RBAC y reglas del gateway (R4, R5, R13, R16) | Incremento 3 | [GW-2](zaith/GW-2-gateway-salas-media-ws.md), [ATH-5](andres/ATH-5-auth-suspension-y-latido.md) | Pendiente |
| [E2E-2](zaith/E2E-2-e2e-chat-e-imagenes.md) | E2E: chat, moderación e imágenes (R6, R7, R12, R14) | Incremento 3 | [E2E-1](zaith/E2E-1-e2e-cuentas-y-gateway.md), [MED-4](stefany/MED-4-media-descarga-y-cuarentena.md), [CHAT-4](zaith/CHAT-4-chat-avisos-y-latidos.md) | Pendiente |
| [E2E-3](zaith/E2E-3-cierre-final.md) | Calibración, VPS, trazabilidad final, informe de pruebas y demo | Incremento 3 | [E2E-2](zaith/E2E-2-e2e-chat-e-imagenes.md), [FE-5](andres/FE-5-frontend-panel-admin.md) | Pendiente |

### Andrés · Identidad y salas

| Ticket | Título | Incremento | Necesita | Estado |
|---|---|---|---|---|
| [FND-3](andres/FND-3-argon2-y-limites.md) | Contraseñas Argon2id y límites de intentos | Primer parcial | — | Pendiente |
| [AUD-1](andres/AUD-1-audit-esqueleto.md) | Esqueleto de `audit`, migración y mínimo privilegio (R11) | Primer parcial | [FND-4](zaith/FND-4-autenticacion-entre-servicios.md), [FND-5](zaith/FND-5-utilidades-de-bd-y-pruebas.md) | Pendiente |
| [AUD-2](andres/AUD-2-audit-ingesta-y-cadena.md) | Ingesta de eventos y cadena verificable (R3, R16) | Primer parcial | [AUD-1](andres/AUD-1-audit-esqueleto.md) | Pendiente |
| [AUD-3](andres/AUD-3-audit-consulta.md) | Consulta y verificación para el admin global (R5) | Primer parcial | [AUD-2](andres/AUD-2-audit-ingesta-y-cadena.md) | Pendiente |
| [ATH-1](andres/ATH-1-auth-esqueleto-y-jwt.md) | Esqueleto de `auth`, catálogo de permisos, roles semilla y firma de JWT (R11) | Primer parcial | [FND-3](andres/FND-3-argon2-y-limites.md), [FND-4](zaith/FND-4-autenticacion-entre-servicios.md), [FND-5](zaith/FND-5-utilidades-de-bd-y-pruebas.md) | Pendiente |
| [ATH-2](andres/ATH-2-auth-registro-login-verify.md) | Registro, login, JWT y sesión de dispositivo único, `verify`, `me` y `logout` (R4, R5, R13, R16) | Primer parcial | [ATH-1](andres/ATH-1-auth-esqueleto-y-jwt.md) | Pendiente |
| [ATH-3](andres/ATH-3-auth-totp-y-admin.md) | TOTP para los permisos de admin y alta del admin global por CLI (R4) | Primer parcial | [ATH-2](andres/ATH-2-auth-registro-login-verify.md) | Pendiente |
| [ATH-4](andres/ATH-4-auth-roles-y-permisos.md) | Roles, permisos y administración de cuentas (R5) | Primer parcial | [ATH-3](andres/ATH-3-auth-totp-y-admin.md) | Pendiente |
| [ATH-5](andres/ATH-5-auth-suspension-y-latido.md) | Suspensión, reactivación, cambio de contraseña y latido de sesiones (R5, R13) | Incremento 2 | [ATH-4](andres/ATH-4-auth-roles-y-permisos.md) | Pendiente |
| [ATH-6](andres/ATH-6-auth-rotacion-kek.md) | Rotación de la KEK de auth (R2) | Incremento 2 | [ATH-4](andres/ATH-4-auth-roles-y-permisos.md) | Pendiente |
| [ROOM-1](andres/ROOM-1-rooms-crear-y-mis-salas.md) | Esqueleto de `rooms`, crear sala y *Mis salas* (R1, R5, R8, R11, R15) | Incremento 2 | [FND-4](zaith/FND-4-autenticacion-entre-servicios.md), [FND-5](zaith/FND-5-utilidades-de-bd-y-pruebas.md) | Pendiente |
| [ROOM-2](andres/ROOM-2-rooms-ingreso-y-salida.md) | Ingreso, salida y miembros (R8, R15) | Incremento 2 | [ROOM-1](andres/ROOM-1-rooms-crear-y-mis-salas.md) | Pendiente |
| [ROOM-3](andres/ROOM-3-rooms-moderacion.md) | Administración de la sala por el dueño y el admin global (R5) | Incremento 2 | [ROOM-2](andres/ROOM-2-rooms-ingreso-y-salida.md) | Pendiente |
| [ROOM-4](andres/ROOM-4-rooms-membresia-interna.md) | Membresía interna y latido (R16) | Incremento 2 | [ROOM-1](andres/ROOM-1-rooms-crear-y-mis-salas.md) | Pendiente |
| [FE-5](andres/FE-5-frontend-panel-admin.md) | Frontend: panel del admin global | Incremento 3 | [FE-3](stefany/FE-3-frontend-chat-y-dueno.md), [ATH-5](andres/ATH-5-auth-suspension-y-latido.md), [MED-4](stefany/MED-4-media-descarga-y-cuarentena.md) | Pendiente |

### Stefany · Contenido, cliente y entrega

| Ticket | Título | Incremento | Necesita | Estado |
|---|---|---|---|---|
| [STG-1](stefany/STG-1-stego-esqueleto-y-analisis.md) | Esqueleto de `stego` sin BD, estegoanálisis y sanitización (R6) | Primer parcial | [FND-4](zaith/FND-4-autenticacion-entre-servicios.md), [FND-5](zaith/FND-5-utilidades-de-bd-y-pruebas.md) | Pendiente |
| [STG-2](stefany/STG-2-stego-formatos-y-veredicto.md) | Formatos, validación previa y veredicto (R6, R9) | Primer parcial | [STG-1](stefany/STG-1-stego-esqueleto-y-analisis.md) | Pendiente |
| [STG-3](stefany/STG-3-stego-api.md) | API pública e interna con análisis aislado (R5, R9, R10, R16) | Primer parcial | [STG-2](stefany/STG-2-stego-formatos-y-veredicto.md) | Pendiente |
| [STG-4](stefany/STG-4-stego-demo-y-calibracion.md) | Imágenes de la demo y calibración rápida | Primer parcial | [STG-3](stefany/STG-3-stego-api.md) | Pendiente |
| [PAR-1](stefany/PAR-1-postman.md) | Colección de Postman del flujo del docente (RP-11) | Primer parcial | [GW-1](zaith/GW-1-gateway-parcial.md) | Pendiente |
| [PAR-2](stefany/PAR-2-informe-parcial.md) | Informe del primer parcial (RP-10) | Primer parcial | [GW-1](zaith/GW-1-gateway-parcial.md) | Pendiente |
| [PAR-3](stefany/PAR-3-demo-y-ensayo.md) | Guion de la demo y ensayo desde un clon limpio (RP-11) | Primer parcial | [PAR-1](stefany/PAR-1-postman.md), [PAR-2](stefany/PAR-2-informe-parcial.md) | Pendiente |
| [FE-1](stefany/FE-1-frontend-esqueleto-y-cripto.md) | Frontend: esqueleto, criptografía con vectores y SPA en el gateway | Incremento 2 | [GW-1](zaith/GW-1-gateway-parcial.md) | Pendiente |
| [FE-2](stefany/FE-2-frontend-cuenta-y-salas.md) | Frontend: cuenta, *Mis salas*, crear sala e ingresar | Incremento 2 | [FE-1](stefany/FE-1-frontend-esqueleto-y-cripto.md), [ATH-4](andres/ATH-4-auth-roles-y-permisos.md), [ROOM-2](andres/ROOM-2-rooms-ingreso-y-salida.md) | Pendiente |
| [FE-3](stefany/FE-3-frontend-chat-y-dueno.md) | Frontend: chat cifrado y controles del dueño | Incremento 2 | [FE-2](stefany/FE-2-frontend-cuenta-y-salas.md), [ROOM-3](andres/ROOM-3-rooms-moderacion.md), [CHAT-3](zaith/CHAT-3-chat-tramas-y-mensajes.md), [GW-2](zaith/GW-2-gateway-salas-media-ws.md) | Pendiente |
| [MED-1](stefany/MED-1-media-archivos-cifrados.md) | Esqueleto de `media`, archivos cifrados y rotación (R2, R11) | Incremento 3 | [FND-4](zaith/FND-4-autenticacion-entre-servicios.md), [FND-5](zaith/FND-5-utilidades-de-bd-y-pruebas.md) | Pendiente |
| [MED-2](stefany/MED-2-media-subida-y-clamav.md) | Subida: membresía, límites y ClamAV (R9) | Incremento 3 | [MED-1](stefany/MED-1-media-archivos-cifrados.md) | Pendiente |
| [MED-3](stefany/MED-3-media-politica-y-publicacion.md) | Política con `stego`, sanitización y publicación (R6, R9) | Incremento 3 | [MED-2](stefany/MED-2-media-subida-y-clamav.md), [STG-3](stefany/STG-3-stego-api.md) | Pendiente |
| [MED-4](stefany/MED-4-media-descarga-y-cuarentena.md) | Descarga firmada y cuarentena del admin global (R5, R12) | Incremento 3 | [MED-3](stefany/MED-3-media-politica-y-publicacion.md) | Pendiente |
| [FE-4](stefany/FE-4-frontend-imagenes.md) | Frontend: imágenes en el chat | Incremento 3 | [FE-3](stefany/FE-3-frontend-chat-y-dueno.md), [MED-3](stefany/MED-3-media-politica-y-publicacion.md) | Pendiente |

Las tareas del *Primer parcial* son el corte definitivo; las del *Incremento 2*, salas y chat, y las del *Incremento 3*, imágenes en las salas y cierre.
