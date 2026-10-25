# Tickets

Un archivo por ticket, separado por persona (`andres/`, `stefany/` y `zaith/`). Cada ticket es una tarea de los planes de `docs/plans/`.

## Reglas de la cadena

- **Orden estricto, en rueda: Andrés → Stefany → Zaith.** El ticket T-NN empieza solo cuando T-(NN−1) está **cerrado**. Cerrado significa tests en verde, documentos actualizados, commit hecho y aviso al siguiente.
- Cada ticket dice quién lo bloquea y a quién desbloquea.
- Mientras espera su turno, cada integrante puede leer su próximo ticket, la tarea en el plan y las secciones del spec que cita, sin escribir código de esa tarea.
- Al cerrar, el dueño cambia *Estado* en su ticket y en la tabla de abajo.
- Commits en español, sin líneas de atribución, en `feat/arquitectura-chat-seguro`. Nada de `push`, PR ni merge a `main` sin que el equipo lo autorice.
- Si el docente cambia el alcance, se ajustan primero el spec y el plan, y después los tickets.

## Cadena

| Ticket | Tarea | Título | Responsable | Incremento | Estado |
|---|---|---|---|---|---|
| T-01 | [FND-1](andres/T-01-higiene-y-claude-code.md) | Higiene del repo y contexto de Claude Code | Andrés | Primer parcial | Pendiente |
| T-02 | [FND-2](stefany/T-02-shared-cripto-y-secretos.md) | Paquete `shared`: secretos, criptografía y vectores | Stefany | Primer parcial | Pendiente |
| T-03 | [FND-3](zaith/T-03-argon2-y-limites.md) | Contraseñas Argon2id y límites de intentos | Zaith | Primer parcial | Pendiente |
| T-04 | [FND-4](andres/T-04-autenticacion-entre-servicios.md) | Autenticación entre servicios, identidad, auditoría y base web (R16) | Andrés | Primer parcial | Pendiente |
| T-05 | [FND-5](stefany/T-05-utilidades-de-bd-y-pruebas.md) | Utilidades de BD para pruebas, migraciones comunes e imágenes sintéticas | Stefany | Primer parcial | Pendiente |
| T-06 | [FND-6](zaith/T-06-docker-secretos-postgres.md) | Plantilla Docker, generación de secretos y PostgreSQL con 5 BD | Zaith | Primer parcial | Pendiente |
| T-07 | [FND-7](andres/T-07-integracion-continua.md) | Integración continua | Andrés | Primer parcial | Pendiente |
| T-08 | [AUD-1](stefany/T-08-audit-esqueleto.md) | Esqueleto de `audit`, migración y mínimo privilegio (R11) | Stefany | Primer parcial | Pendiente |
| T-09 | [AUD-2](zaith/T-09-audit-ingesta-y-cadena.md) | Ingesta de eventos y cadena verificable (R3, R16) | Zaith | Primer parcial | Pendiente |
| T-10 | [AUD-3](andres/T-10-audit-consulta.md) | Consulta y verificación para el admin global (R5) | Andrés | Primer parcial | Pendiente |
| T-11 | [ATH-1](stefany/T-11-auth-esqueleto-y-jwt.md) | Esqueleto de `auth`, catálogo de permisos, roles semilla y firma de JWT (R11) | Stefany | Primer parcial | Pendiente |
| T-12 | [ATH-2](zaith/T-12-auth-registro-login-verify.md) | Registro, login, JWT y sesión de dispositivo único, `verify`, `me` y `logout` (R4, R5, R13, R16) | Zaith | Primer parcial | Pendiente |
| T-13 | [ATH-3](andres/T-13-auth-totp-y-admin.md) | TOTP para los permisos de admin y alta del admin global por CLI (R4) | Andrés | Primer parcial | Pendiente |
| T-14 | [ATH-4](stefany/T-14-auth-roles-y-permisos.md) | Roles, permisos y administración de cuentas (R5) | Stefany | Primer parcial | Pendiente |
| T-15 | [STG-1](zaith/T-15-stego-esqueleto-y-analisis.md) | Esqueleto de `stego` sin BD, estegoanálisis y sanitización (R6) | Zaith | Primer parcial | Pendiente |
| T-16 | [STG-2](andres/T-16-stego-formatos-y-veredicto.md) | Formatos, validación previa y veredicto (R6, R9) | Andrés | Primer parcial | Pendiente |
| T-17 | [STG-3](stefany/T-17-stego-api.md) | API pública e interna con análisis aislado (R5, R9, R10, R16) | Stefany | Primer parcial | Pendiente |
| T-18 | [STG-4](zaith/T-18-stego-demo-y-calibracion.md) | Imágenes de la demo y calibración rápida | Zaith | Primer parcial | Pendiente |
| T-19 | [GW-1](andres/T-19-gateway-parcial.md) | Gateway Nginx con TLS 1.3, `auth_request` y las rutas del parcial (R5, R7, R10, R16) | Andrés | Primer parcial | Pendiente |
| T-20 | [PAR-1](stefany/T-20-postman.md) | Colección de Postman del flujo del docente (RP-11) | Stefany | Primer parcial | Pendiente |
| T-21 | [PAR-2](zaith/T-21-informe-parcial.md) | Informe del primer parcial (RP-10) | Zaith | Primer parcial | Pendiente |
| T-22 | [PAR-3](andres/T-22-demo-y-ensayo.md) | Guion de la demo y ensayo desde un clon limpio (RP-11) | Andrés | Primer parcial | Pendiente |
| T-23 | [ATH-5](stefany/T-23-auth-suspension-y-latido.md) | Suspensión, reactivación, cambio de contraseña y latido de sesiones (R5, R13) | Stefany | Incremento 2 | Pendiente |
| T-24 | [ATH-6](zaith/T-24-auth-rotacion-kek.md) | Rotación de la KEK de auth (R2) | Zaith | Incremento 2 | Pendiente |
| T-25 | [ROOM-1](andres/T-25-rooms-crear-y-mis-salas.md) | Esqueleto de `rooms`, crear sala y *Mis salas* (R1, R5, R8, R11, R15) | Andrés | Incremento 2 | Pendiente |
| T-26 | [ROOM-2](stefany/T-26-rooms-ingreso-y-salida.md) | Ingreso, salida y miembros (R8, R15) | Stefany | Incremento 2 | Pendiente |
| T-27 | [ROOM-3](zaith/T-27-rooms-moderacion.md) | Administración de la sala por el dueño y el admin global (R5) | Zaith | Incremento 2 | Pendiente |
| T-28 | [ROOM-4](andres/T-28-rooms-membresia-interna.md) | Membresía interna y latido (R16) | Andrés | Incremento 2 | Pendiente |
| T-29 | [CHAT-1](stefany/T-29-chat-almacen-cifrado.md) | Esqueleto de `chat`, almacén cifrado y rotación (R2, R11) | Stefany | Incremento 2 | Pendiente |
| T-30 | [CHAT-2](zaith/T-30-chat-conexion.md) | Conexión: identidad, membresía, `Origin`, *hello* firmado y presencia (R7, R16) | Zaith | Incremento 2 | Pendiente |
| T-31 | [CHAT-3](andres/T-31-chat-tramas-y-mensajes.md) | Tramas, mensajes, silencio, borrado y `file_url` (R10, R14) | Andrés | Incremento 2 | Pendiente |
| T-32 | [CHAT-4](stefany/T-32-chat-avisos-y-latidos.md) | Avisos internos, archivos publicados, latidos e inactividad (R16) | Stefany | Incremento 2 | Pendiente |
| T-33 | [GW-2](zaith/T-33-gateway-salas-media-ws.md) | Gateway: rutas de salas, media y WebSocket | Zaith | Incremento 2 | Pendiente |
| T-34 | [FE-1](andres/T-34-frontend-esqueleto-y-cripto.md) | Frontend: esqueleto, criptografía con vectores y SPA en el gateway | Andrés | Incremento 2 | Pendiente |
| T-35 | [FE-2](stefany/T-35-frontend-cuenta-y-salas.md) | Frontend: cuenta, *Mis salas*, crear sala e ingresar | Stefany | Incremento 2 | Pendiente |
| T-36 | [FE-3](zaith/T-36-frontend-chat-y-dueno.md) | Frontend: chat cifrado y controles del dueño | Zaith | Incremento 2 | Pendiente |
| T-37 | [MED-1](andres/T-37-media-archivos-cifrados.md) | Esqueleto de `media`, archivos cifrados y rotación (R2, R11) | Andrés | Incremento 3 | Pendiente |
| T-38 | [MED-2](stefany/T-38-media-subida-y-clamav.md) | Subida: membresía, límites y ClamAV (R9) | Stefany | Incremento 3 | Pendiente |
| T-39 | [MED-3](zaith/T-39-media-politica-y-publicacion.md) | Política con `stego`, sanitización y publicación (R6, R9) | Zaith | Incremento 3 | Pendiente |
| T-40 | [MED-4](andres/T-40-media-descarga-y-cuarentena.md) | Descarga firmada y cuarentena del admin global (R5, R12) | Andrés | Incremento 3 | Pendiente |
| T-41 | [FE-4](stefany/T-41-frontend-imagenes.md) | Frontend: imágenes en el chat | Stefany | Incremento 3 | Pendiente |
| T-42 | [FE-5](zaith/T-42-frontend-panel-admin.md) | Frontend: panel del admin global | Zaith | Incremento 3 | Pendiente |
| T-43 | [E2E-1](andres/T-43-e2e-cuentas-y-gateway.md) | E2E: arnés, cuentas, RBAC y reglas del gateway (R4, R5, R13, R16) | Andrés | Incremento 3 | Pendiente |
| T-44 | [E2E-2](stefany/T-44-e2e-chat-e-imagenes.md) | E2E: chat, moderación e imágenes (R6, R7, R12, R14) | Stefany | Incremento 3 | Pendiente |
| T-45 | [E2E-3](zaith/T-45-cierre-final.md) | Calibración, VPS, trazabilidad final, informe de pruebas y demo | Zaith | Incremento 3 | Pendiente |

Las tareas 1–22 son el **primer parcial** (corte definitivo); 23–36, el **incremento 2** (salas y chat), y 37–45, el **incremento 3** (imágenes en las salas y cierre).
