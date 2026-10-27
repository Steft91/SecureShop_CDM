# Spec: Salas de Chat Seguras — Diseño de arquitectura (microservicios)

| | |
|---|---|
| **Fecha** | 2026-10-12 · **Revisión 2:** 2026-10-13 (arquitectura de microservicios; reemplaza el monolito modular de la revisión 1) · **Revisión 3:** 2026-10-13 (cumplimiento del resumen del docente: normas, enfoques y cifrado de archivos en reposo; §21) · **Revisión 4:** 2026-10-25 (clase del 22/10: cuentas con RBAC y JWT, salas con dueño, servicio `stego` y primer parcial; §22) |
| **Autores** | Zaith Alejandro Manangón Vinueza, Stefany Maricela Díaz Antun, Andrés Isaias Cedeño Cuenca |
| **Asignatura** | Software Seguro — Proyecto Integrador |
| **Estado** | Revisión 4. Planes del primer parcial en `docs/plans/` y tickets en `docs/tickets/parcial-1/` |
| **Fuente de requisitos** | `Documentación/Tarea 2/Actividad2_SGSI_Proyecto_Integrador.md` (enunciado + Tablas 1–4 de riesgos), `PROYECTO INTEGRADOR - RESUMEN.docx` (resumen del docente) y la clase del 22/10/2026 (alcance del primer parcial). Los requisitos con ID están en `docs/requisitos.md` |
| **Plazo** | **Primer parcial:** corte definitivo con el gateway, `auth` y `stego`, probado con Postman (meta de demo: 30 oct; fecha de la defensa por confirmar). **Después:** lo que el docente pida para los parciales 2 y 3 |

> **Alcance del primer parcial.** Solo se construyen el gateway, `auth` (cuentas, RBAC y JWT, con el admin global creado por CLI) y `stego`. No entran el servicio `audit`, el TOTP de los admins, la rotación de la KEK, `rooms`, `chat`, `media` ni el frontend: los eventos de seguridad son registros JSON en la salida de cada servicio. Las secciones de esta spec que describen esas piezas son el diseño de referencia para después. Donde la spec y los planes de `docs/plans/` difieren, mandan los planes.

---

## 1. Propósito y criterios de éxito

Construir la aplicación de **salas de chat seguras** del proyecto integrador con **arquitectura de microservicios**, igual que en SecureShop (Tarea 1): un punto de entrada común, un servicio por dominio y una base de datos por servicio. Desde la revisión 4, las personas tienen **cuenta con roles (RBAC)** y cualquiera puede crear salas y administrarlas, como en Discord. El sistema debe implementar y **demostrar con pruebas** los 15 tratamientos de riesgo de la Tarea 2 (Tabla 3), más el riesgo R16 que introduce la propia arquitectura (§16.3).

**Criterios de éxito (definición de "terminado"):**
1. **Cuentas y RBAC:** cualquiera se registra. Los permisos se asignan a roles que el admin global crea y edita, y cada operación se autoriza en el servidor con los permisos **actuales** del usuario, no con los que tenía al iniciar sesión. El login entrega un JWT. Quien tiene un permiso de admin entra además con TOTP.
2. **Salas con dueño:** un usuario con `rooms:create` crea hasta 2 salas activas con ID único, clave, cupo y tipo (texto / multimedia / ambos), y las administra: las edita, las cierra, las cede, expulsa, silencia y borra mensajes.
3. Dos o más navegadores intercambian mensajes cifrados en una sala. Una cuenta no puede estar activa desde dos dispositivos.
4. **Esteganografía:** `POST /api/stego/analyze` responde *inválida*, *limpia*, *problema* o *revisión manual* a quien tenga el permiso `stego:analyze`. En las salas, una imagen con LSB embebido termina en **cuarentena**, genera una alerta y queda en auditoría; una imagen limpia se entrega sanitizada.
5. **Microservicios:** un gateway como único punto de entrada y 6 servicios (`auth`, `rooms`, `chat`, `media`, `stego`, `audit`). Cada servicio con datos tiene su propia BD (`stego` no guarda estado), su propia imagen y su propio job de migración, y se despliega por separado (`docker compose up -d --build <servicio>`).
6. Los **16 riesgos** (R1–R15 de la Tarea 2 + R16) tienen al menos un test automatizado en verde, mapeado en `docs/trazabilidad-riesgos.md`.
7. Todo el sistema corre con un comando en local y en un VPS con certificado válido.
8. Cada requisito funcional y de seguridad del documento del docente (`docs/requisitos.md`, RF-xx y RS-xx) tiene un test o una evidencia manual.
9. Existe la documentación que evidencia ISO/IEC 27001, ISO/IEC 27034, Zero Trust, Secure by Design y Shift Left (`docs/cumplimiento-normativo.md`) y la justificación de la criptografía (`docs/justificacion-criptografica.md`).
10. **Primer parcial:** el flujo del docente funciona de punta a punta desde Postman: crear un usuario, crear un rol con sus permisos, asignarlo, iniciar sesión, recibir el JWT y analizar una imagen con él (§18.1).

---

## 2. Requisitos del enunciado → decisiones

| Requisito | Decisión |
|---|---|
| *(Docente, 22/10)* Usuarios, roles y control de acceso basado en roles; el login devuelve un token válido (JWT) | Servicio `auth`: registro abierto (el registro solo da el rol `user`), Argon2id, roles dinámicos con permisos de un catálogo fijo (§9.1) y un **JWT RS256 que apunta a una sesión revocable**. El gateway lo verifica con `auth` en **cada** request y pasa los permisos actuales (§4.3) |
| *(Docente, 22/10)* API de esteganografía a la que se entra con el token que emite `auth` | Servicio `stego`, sin estado: `POST /api/stego/analyze` exige `stego:analyze` y responde inválida / limpia / problema / revisión manual (§9.9, §12.7) |
| Administrador autenticado que gestiona las salas | Dos niveles. El **dueño** administra su sala (§9.3). El **admin global** (como el personal de Discord) gestiona cuentas, roles y cualquier sala, pero **no lee conversaciones**. TOTP obligatorio para todo permiso de admin; el primer admin se crea por CLI, sin credenciales por defecto |
| Sala: ID único, clave, cupo máximo, tipo | Tabla `rooms` (BD `rooms`): `code` UNIQUE (normalizado a minúsculas), `key_hash` Argon2id, `max_members`, `mode` y `owner_id`. Máximo **2 salas activas por dueño** |
| Un usuario se conecta desde un único dispositivo | Una sesión `full` activa por cuenta (índice único parcial en `user_sessions`), ligada a la cookie de dispositivo y verificada en **cada** request. **Política: se rechaza el login desde otro dispositivo** mientras la sesión siga viva; desde el mismo dispositivo, la reemplaza |
| Acceso condicionado a ID + clave | El **primer** ingreso exige ID + clave (Argon2id, límite de intentos por IP, usuario y sala, error genérico) y crea la membresía. Después, la sala se abre desde *Mis salas* sin volver a pedir la clave |
| Confidencialidad, integridad y autenticidad; justificar algoritmos, protocolos y gestión de claves | TLS 1.3 hasta el gateway + **cifrado por conexión en capa de aplicación** entre navegador y `chat` (ECDH P-256 con *hello* firmado → HKDF-SHA256 → AES-256-GCM con AAD) + envelope encryption en reposo (DEK por sala, KEK propia de `chat`) |
| Análisis de archivos y estegoanálisis con alertas, auditoría y política | `media` (tope de tamaño, ClamAV, política, cifrado) + `stego` (firma, validación, estegoanálisis, sanitización) → **cuarentena** / rechazo / sanitización. Alertas en el servicio `audit` |
| *(Docente)* Microservicios como en SecureShop | Gateway Nginx + 6 servicios por dominio + 5 BD (una por servicio con datos, roles aislados) |
| Toda la información de las salas protegida con criptografía | Mensajes **y archivos** cifrados en tránsito (TLS 1.3 y AES-256-GCM por conexión) y en reposo (envelope: DEK por sala y DEK por archivo) |
| Cierre de salas, modificación y consulta | `PATCH /api/rooms/{id}` (clave, cupo, tipo), `DELETE /api/rooms/{id}` = **cerrar sala** (`active=false`, cierra las conexiones y no admite ingresos). *Mis salas* para el usuario y `GET /api/admin/rooms` (solo metadatos) para el admin global |
| Moderación dentro de la sala | El dueño expulsa (con veto opcional), silencia y borra mensajes; cada miembro borra los suyos. El admin global puede hacer lo mismo que el dueño, salvo leer o borrar mensajes y cambiar la clave |
| Alertas visibles | Eventos `warning`/`critical` en `audit` y aviso con contador en el panel del admin (§14.3) |
| ISO/IEC 27001 y 27034 relacionadas con riesgos y mecanismos | `docs/cumplimiento-normativo.md` y columna ISO en `docs/trazabilidad-riesgos.md` |
| Zero Trust, Secure by Design, Shift Left | Matrices con evidencia en `docs/cumplimiento-normativo.md`; CI con SAST (CodeQL, bandit), SCA y detección de secretos (§16.5) |
| Justificar algoritmos, protocolos y gestión de claves | `docs/justificacion-criptografica.md` (se mantiene alineado con §10–§11) |

**Decisiones de contexto tomadas con el equipo:**
- Backend **Python 3.13 + FastAPI** en todos los servicios. Cliente **web SPA (React + TypeScript)**; en el primer parcial, **Postman**.
- Despliegue: **Docker Compose local** y el **mismo Compose en un VPS** (Let's Encrypt).
- Multimedia: **solo PNG y JPEG** por ahora, con un **punto de extensión** para agregar formatos (§12.1).
- Comunicación interna: **REST síncrono + un token por servicio** (sin broker).
- BD: **un contenedor PostgreSQL, una base de datos y un par de roles por cada servicio con datos** (`stego` no tiene BD).
- Gateway: **Nginx con `auth_request` hacia `auth`**, que verifica el JWT **y** la sesión a la que apunta en cada request (revocación inmediata). Se descartaron: verificar el JWT solo en cada servicio (no se puede revocar al instante), un gateway propio en FastAPI (habría que reimplementar el proxy de WebSocket) y Traefik/Kong (otra herramienta que aprender).
- **Token: JWT RS256**, porque lo pide el docente. Es una referencia firmada a una sesión del servidor: la revocación, la inactividad y el dispositivo los decide la sesión, no el `exp` del token.
- Modelo criptográfico **B** (cifrado en capa de aplicación sobre TLS). Se descartaron A (solo TLS) y C (E2E puro, que impide el estegoanálisis en el servidor).
- *(Rev. 4)* **Salas estilo Discord:** cualquiera crea salas y queda como dueño; la membresía es persistente; hay un solo dueño por sala y puede cederla; no hay moderadores ni reportes.
- *(Rev. 4)* **`stego` es un servicio propio:** nace en el primer parcial y luego `media` lo usa por la red interna.
- *(Rev. 4)* **El primer parcial es un corte definitivo:** fundaciones, `audit`, gateway, `auth` y `stego` tal como quedan en el sistema final; no se escribe código provisional.

---

## 3. Alcance, fuera de alcance y limitaciones conocidas

**Dentro:** todo lo de la sección 2: cuentas y roles, salas con dueño y moderación, mensajería cifrada, imágenes analizadas, API de esteganografía, el panel del admin global (usuarios, roles, salas, cuarentena y auditoría), los controles del dueño en la sala, las pruebas por servicio y e2e, la colección de Postman, CI, el despliegue local y en el VPS, y el contexto para Claude Code.

**Fuera (YAGNI, con el disparador que justificaría agregarlo):**
| Omitido | Agregar cuando |
|---|---|
| Broker de mensajes (RabbitMQ/NATS) | Haya consumidores asíncronos reales o más de una instancia por servicio |
| mTLS / service mesh entre servicios | El sistema salga de una sola máquina o lo exija el docente (ver limitación 3) |
| Varias réplicas por servicio | Haga falta escalar `chat` (requiere pub/sub y un almacén compartido de claves) |
| HashiCorp Vault | Haya más de un servidor o se requiera rotación automática |
| Formatos distintos de PNG/JPEG | El docente los especifique (§12.6) |
| Reportes de usuarios | El docente los pida |
| Edición de mensajes | El docente la pida (exige guardar versiones para la auditoría) |
| Moderadores y roles dentro de la sala | Haga falta repartir la moderación |
| Correo, recuperación de contraseña y foto de perfil | El docente los pida (agregan datos personales y otro canal de imágenes) |
| Notificaciones, estadísticas, búsqueda y paginación | Haya más usuarios o salas de los que caben en una lista |
| `.mcp.json` | Usen GitHub Issues/Projects u otra integración externa |

**Limitaciones conocidas (se declaran en el informe):**
1. `chat` ve el texto plano de los mensajes por diseño (para validar, persistir y auditar), y `media` y `stego` ven los archivos (para analizarlos). La confianza en esos servicios es un supuesto explícito.
2. **No hay verificación de identidad real.** Una persona puede crear varias cuentas; el cupo, el veto y el límite de 2 salas actúan por cuenta. Quien conoce la clave de una sala puede unirse con su propia cuenta; el dueño la ve en la lista de miembros y puede expulsarla.
3. **Tramo interno en HTTP plano.** TLS termina en el gateway; las llamadas gateway→servicio y servicio→servicio viajan en HTTP dentro de redes Docker internas.
   - Los **mensajes** siguen protegidos en ese tramo por el cifrado de aplicación, y el *hello* firmado impide un MITM activo (§10.1).
   - Los **tokens de servicio, los JWT y los archivos subidos** viajan en claro dentro de la red interna (en reposo los archivos están cifrados, §11.2). El gateway no reenvía el JWT a los servicios (§13).
   - Mitigaciones: redes segmentadas, `cap_drop: ALL` (sin `NET_RAW` no hay ARP spoofing ni sniffing desde un contenedor comprometido) y tokens rotables. Mejora futura: mTLS.
4. Una instancia por servicio: las claves de conexión viven en memoria de `chat` y la difusión ocurre dentro de ese proceso.
5. El estegoanálisis es estadístico. Esquemas adaptativos o LSB-matching (±1) pueden evadir chi²; la **sanitización** (§12.5) destruye payloads LSB aunque no se detecten.
6. `audit` es un punto único de falla para las operaciones que otorgan acceso (fallan cerradas con 503 si `audit` no responde, §14.4). Es una decisión deliberada a favor de la trazabilidad. Las operaciones que **quitan** acceso nunca se bloquean por la auditoría.
7. **El "único dispositivo" es una cookie.** La sesión queda ligada a la cookie `__Host-device` (`HttpOnly`); no es un identificador de hardware. Quien copie las dos cookies de un navegador puede usarlas desde otro equipo mientras la sesión esté viva. Borrar las cookies equivale a cambiar de dispositivo: el login se rechaza hasta que la sesión anterior venza por inactividad (30 min).
8. **El admin global no lee conversaciones.** Puede cerrar, ceder o moderar una sala por sus miembros, pero no ve ni borra mensajes, y no puede cambiar la clave de una sala ajena (le permitiría entrar a leerla). La moderación del contenido es del dueño.
9. Una conexión WebSocket ya abierta conserva el alias y el modo de sala que obtuvo al conectarse. La expulsión, el silencio, la salida, el cierre de la sala, el logout y la suspensión se le notifican al instante y, si esa notificación se pierde, se reconcilian en el siguiente latido (30 s).

---

## 4. Arquitectura

### 4.1 Vista general
```
Navegador (React SPA + WebCrypto) · Postman (primer parcial)
   │  HTTPS / WSS — solo TLS 1.3
   ▼
┌─ gateway (Nginx) ── redes: public, apps ───────────────────────────────────┐
│ TLS · HSTS · CSP · rate limit · SPA estática · /chat-key.json               │
│ auth_request → auth /internal/verify (JWT + sesión + permisos actuales)     │
│ Sobrescribe X-User-* · inyecta su X-Service-Token                           │
└───┬─────────┬──────────┬──────────┬──────────┬──────────┬───────────────────┘
    ▼         ▼          ▼          ▼          ▼          ▼
  auth      rooms      chat       media      stego      audit
            (las llamadas internas entre servicios están en §4.4)
  media ──► clamav (red scan)          todos ──► audit (POST /internal/events)
                        ▼  (red data)
  PostgreSQL 17: BD auth · rooms · chat · media · audit   (stego no tiene BD)
```

### 4.2 Servicios
| Servicio | Responsabilidad | BD (tablas) | Riesgos |
|---|---|---|---|
| **gateway** | Único punto de entrada: TLS, cabeceras de seguridad, rate limit perimetral, enrutamiento, autenticación delegada (`auth_request` a `auth`), SPA estática | — | 7, 10, 16 |
| **auth** | Registro, login, TOTP para permisos de admin, JWT y sesiones (un dispositivo por cuenta), roles y permisos, suspensión; `verify`; CLI `create_admin`; rotación de su KEK | `auth`: `users`, `permissions`, `roles`, `role_permissions`, `user_roles`, `user_sessions`, `failed_attempts` | 4, 5, 13 |
| **rooms** | Salas con dueño (máximo 2 activas), ingreso con clave, membresía y alias por sala, cupo atómico, expulsión con veto, silencio, cesión y cierre; membresía para chat y media | `rooms`: `rooms`, `room_members`, `failed_attempts` | 1, 5, 8, 15 |
| **chat** | WebSocket, handshake ECDH firmado, cifrado de tramas, mensajes cifrados en reposo (DEK por sala), historial, borrado de mensajes, silencio, inactividad y latidos de sesión y membresía | `chat`: `room_keys`, `messages` | 2, 7, 10, 14 |
| **media** | Subida, tope de tamaño, ClamAV, política (cuarentena, rechazo o publicación), cifrado de archivos en reposo, descarga con URL firmada, panel de cuarentena | `media`: `files` + volumen de archivos cifrados | 2, 6, 9, 12 |
| **stego** | Firma real, validación con Pillow, estegoanálisis (estructura, chi², RS) y sanitización; API pública de análisis | — (sin estado) | 6, 9 |
| **audit** | Recepción de eventos de todos los servicios, cadena de hash, consulta y verificación para el admin | `audit`: `audit_log` | 3 |

Cada servicio es un proyecto Python independiente (`services/<svc>/`, paquete `<svc>_svc`) que comparte una librería común (`services/shared/`, paquete `shared`) y una única plantilla de `Dockerfile` (argumento `SERVICE`).

### 4.3 Modelo de confianza
1. **Autenticación centralizada en el gateway.** Antes de enrutar una ruta protegida, Nginx hace un `auth_request` a `auth /internal/verify`. `auth` valida el JWT (firma RS256, `iss`, `aud`, `exp`), la sesión a la que apunta (`sid` activa, etapa `full`, sin vencer y con la misma cookie de dispositivo) y la cuenta (no suspendida). Si responde 2xx, el gateway copia la identidad que devolvió (`X-User-Id`, `X-User-Name`, `X-Session-Id`, `X-User-Perms`) a la petición hacia el servicio.
   - **Los permisos salen de la BD en ese momento, no del token**, así que un rol quitado deja de valer en la siguiente petición.
   - **Toda cabecera de identidad que mande el cliente se sobrescribe o se vacía** en todas las rutas, y el JWT no se reenvía a los servicios.
2. **Autorización en cada servicio.** El servicio decide si esa identidad puede hacer la operación: permiso del catálogo (`require_perm`), dueño o miembro de la sala (rooms), modo de la sala y silencio (chat y media, que se lo consultan a rooms).
3. **Autenticación servicio a servicio (R16).**
   - Cada llamador (gateway, auth, rooms, chat, media, stego) tiene un token aleatorio de 256 bits y lo envía en `X-Service-Token`.
   - El receptor guarda **solo el SHA-256** de los tokens de quienes pueden llamarlo, así que un servicio comprometido no puede usar lo que tiene montado para hacerse pasar por otro.
   - **Todas** las rutas de un servicio exigen un token válido; solo `/health` está exento (lo usa el healthcheck de Docker).
   - Rutas públicas: el llamador debe ser `gateway`. Rutas `/internal/*`: el llamador debe estar en la allowlist de esa ruta.
   - Las cabeceras de identidad solo se leen si el llamador es `gateway`.
4. **Allowlist de llamadores:**
   | Servicio | Acepta llamadas de |
   |---|---|
   | auth | gateway, chat |
   | rooms | gateway, chat, media |
   | chat | gateway, auth, rooms, media |
   | media | gateway, chat |
   | stego | gateway, media |
   | audit | gateway, auth, rooms, chat, media, stego |
5. **Red:** los servicios no publican puertos y el gateway nunca enruta `/internal/*`.
6. **Claves aisladas:** `jwt_signing_key` y `kek_auth` (TOTP) solo en `auth`; `kek_chat` (DEK de salas) y `chat_sign_key` solo en `chat`; `kek_media` solo en `media`; `url_signing_key` solo en `chat` (firma) y `media` (verifica).

### 4.4 Comunicación interna (REST síncrono, timeout 3 s)
| Llamador → receptor | Endpoint | Cuándo | Si el receptor no responde |
|---|---|---|---|
| gateway → auth | `GET /internal/verify` | cada ruta protegida y cada `/ws` | 401 al cliente |
| auth → chat | `POST /internal/users/{id}/disconnect` | logout, suspensión, cambio de contraseña | Se registra y se continúa: la sesión ya terminó en `auth` y el latido cierra el WS |
| chat → auth | `POST /internal/sessions/heartbeat` | cada 30 s con las sesiones conectadas | Se reintenta en el siguiente ciclo |
| chat, media → rooms | `POST /internal/membership` | al abrir el WS, al borrar un mensaje ajeno, en cada subida y descarga | WS: 4403 · borrado: se rechaza · media: 503 |
| chat → rooms | `POST /internal/membership/heartbeat` | cada 30 s con los pares (sala, usuario) conectados | Se reintenta en el siguiente ciclo |
| rooms → chat | `POST /internal/rooms/{id}/kick`, `/mute`, `/close` | salida, expulsión, silencio, cierre de sala | Se registra y se continúa: la decisión ya está en `rooms` y el latido la reconcilia |
| media → chat | `POST /internal/rooms/{room_id}/files` | archivo aceptado o liberado | 503 al que subió el archivo; el archivo queda huérfano e inaccesible (§9.7) |
| chat → media | `POST /internal/files/{id}/delete` | se borra un mensaje con imagen | Se registra; el archivo ya es inaccesible porque `chat` no firma URLs de mensajes borrados |
| media → stego | `POST /internal/analyze`, `POST /internal/sanitize` | cada subida; cada publicación y cada liberación | 503 (falla cerrado) |
| auth, rooms, chat, media, stego → audit | `POST /internal/events` | cada evento auditable | §14.4 (fallo cerrado para otorgamientos) |
| media → clamav | clamd INSTREAM :3310 | cada subida | 503 (fallo cerrado) |

### 4.5 Redes y endurecimiento de contenedores
| Red | `internal` | Miembros | Para qué |
|---|---|---|---|
| `public` | no | gateway | Publicar 80/443 |
| `apps` | sí | gateway, auth, rooms, chat, media, stego, audit | Tráfico HTTP entre gateway y servicios y entre servicios |
| `data` | sí | db, auth, rooms, chat, media, audit, los 5 jobs de migración | Acceso a PostgreSQL (ni el gateway ni `stego` llegan a la BD) |
| `scan` | sí | media, clamav | Solo `media` llega a ClamAV |
| `clamav-egress` | no | clamav | Actualización de firmas (freshclam) |

Servicios Python: usuario no-root (uid 10001), `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, `read_only: true` con `tmpfs: /tmp`. `media` monta además el volumen `media_data` en `/data`.

### 4.6 Límites de escala
Una réplica por servicio. Escalar `chat` exige mover la difusión a pub/sub (Redis/NATS) y enrutar las conexiones por usuario. `stego` no tiene estado y escalaría sin cambios. Las demás piezas (`auth`, `rooms`, `media`, `audit`) no tienen estado en memoria salvo cachés triviales.

---

## 5. Estructura del repositorio

```
SecureShop_CDM/
├── CLAUDE.md                        contexto principal para Claude Code (§17)
├── .claude/                         reglas, comando, skills, agente, hook (§17)
├── services/
│   ├── Dockerfile                   plantilla única (ARG SERVICE)
│   ├── lock.sh                      genera services/<svc>/requirements.lock en un contenedor
│   ├── shared/                      librería común (paquete `shared`)
│   │   └── shared/
│   │       ├── secrets.py           lectura de /run/secrets (falla si falta)
│   │       ├── crypto.py            b64, AES-GCM, ECDH/HKDF, ECDSA (hello), tramas, URLs firmadas
│   │       ├── passwords.py         Argon2id (con tope de concurrencia) y política de claves
│   │       ├── service_auth.py      verificación de X-Service-Token, allowlist, ServiceClient
│   │       ├── identity.py          require_gateway / require_user / require_perm
│   │       ├── audit_client.py      emisión de eventos con fallback a stdout
│   │       ├── web.py               create_base_app: errores JSON, /health, Origin/CSRF
│   │       └── testing.py           utilidades de prueba (BD de prueba, migraciones, clientes, imágenes)
│   ├── auth/    auth_svc/  migrations/  tests/  pyproject.toml  requirements.lock  alembic.ini
│   ├── rooms/   rooms_svc/ …
│   ├── chat/    chat_svc/  …
│   ├── media/   media_svc/ …
│   ├── stego/   stego_svc/ tests/ tools/stego_lab.py  pyproject.toml  requirements.lock   (sin BD)
│   └── audit/   audit_svc/ …
├── gateway/
│   ├── Dockerfile                   build multi-stage de la SPA + nginx
│   ├── nginx.conf
│   └── snippets/                    proxy-base.conf, proxy-public.conf, proxy-user.conf
├── frontend/                        Vite + React + TS (src/pages, src/lib)
├── e2e/                             pytest contra el stack completo vía https://localhost
├── deploy/
│   ├── docker-compose.yml
│   ├── docker-compose.test.yml      Postgres (y ClamAV opcional) para las pruebas por servicio
│   ├── postgres/init.sh             crea BDs y roles leyendo /run/secrets
│   ├── gen_secrets.py               genera deploy/secrets/* y deploy/public/chat-key.json
│   ├── secrets/   (gitignored)
│   ├── public/    (gitignored)      chat-key.json (clave pública, se monta en el gateway)
│   └── certs/     (gitignored)      certificados (mkcert en local, Let's Encrypt en el VPS)
├── docs/
│   ├── specs/  plans/  tickets/     diseño, planes por subsistema y un ticket por archivo y persona
│   ├── postman/                     colección del primer parcial (`parcial-1.postman_collection.json`)
│   ├── crypto-vectors.json          vectores compartidos Python ↔ TypeScript
│   ├── trazabilidad-riesgos.md      riesgo → control (ISO 27001) → servicio/archivo → test → estado
│   ├── requisitos.md                RF-xx / RS-xx / RP-xx del documento del docente + brechas
│   ├── cumplimiento-normativo.md    ISO 27001, ISO 27034, Zero Trust, Secure by Design, Shift Left
│   ├── justificacion-criptografica.md  algoritmos, protocolo y gestión de claves justificados
│   ├── informe-pruebas.md           resultados por servicio, e2e y calibración (se genera en E2E-3)
│   └── despliegue-vps.md
├── .github/workflows/ci.yml
└── Documentación/                   entregables académicos (ya existe)
```

---

## 6. Stack

| Capa | Tecnología | Por qué |
|---|---|---|
| Servicios | Python 3.13, FastAPI, uvicorn | WebSockets nativos; estegoanálisis y cripto en el mismo lenguaje |
| HTTP interno | httpx (`AsyncClient`) | Cliente async con `MockTransport` para pruebas |
| BD | PostgreSQL 17, SQLAlchemy 2 (async, consultas `text()` con binds) + asyncpg, Alembic por servicio | Constraints, índices parciales y transacciones |
| Contraseñas | `argon2-cffi` (Argon2id, RFC 9106: t=3, m=64 MiB, p=4) | Riesgos 1 y 4 |
| Tokens | `PyJWT` con `cryptography` (RS256) | JWT pedido por el docente; solo `auth` firma |
| Cripto | `cryptography` (ECDH y ECDSA P-256, HKDF, AESGCM, RSA) | Primitivas auditadas, interoperan con WebCrypto |
| MFA | `pyotp` + `qrcode` | TOTP RFC 6238 |
| Imágenes | Pillow, numpy, scipy (`chi2.sf`) | Decodificación y estadística (solo `stego`) |
| Antimalware | ClamAV (`clamav/clamav`, o `clamav/clamav-debian` en ARM) vía INSTREAM | Riesgo 9 |
| Gateway | Nginx 1.27 (`auth_request`) | TLS 1.3, rate limit, autenticación delegada |
| Front | React 19, Vite, TypeScript estricto, react-router, CSS plano | Sin librería de UI: menos superficie |
| Cripto en el front | WebCrypto (`crypto.subtle`) | Nativo, claves no extraíbles |
| Pruebas | pytest, httpx, pytest-timeout; vitest; e2e con httpx + `websockets`; colección de Postman para el parcial | |
| CI | GitHub Actions: ruff, pytest (matriz por servicio), bandit, pip-audit, npm audit, CodeQL, gitleaks | Shift Left: SAST, SCA y secretos desde el primer push |

Las versiones exactas quedan en `services/<svc>/requirements.lock` (generado en el plan) y en `frontend/package-lock.json`.

---

## 7. Datos por servicio

Un contenedor PostgreSQL con 5 bases de datos (`stego` no tiene). **No hay claves foráneas entre bases**: las referencias cruzadas (`user_id`, `room_id`, `file_id`) son UUID opacos validados por el servicio dueño.

### 7.1 BD `auth`
```sql
CREATE TABLE users (
  id                uuid PRIMARY KEY,
  username          text UNIQUE NOT NULL CHECK (username ~ '^[a-z0-9_.-]{3,32}$'),  -- normalizado a minúsculas
  password_hash     text NOT NULL,                 -- $argon2id$...
  totp_secret       bytea,                         -- nonce||ct, AES-GCM con kek_auth, AAD "totp|<id>"; NULL sin TOTP
  totp_confirmed_at timestamptz,                   -- NULL hasta que el primer código valida la configuración
  totp_last_step    bigint NOT NULL DEFAULT 0,     -- anti-reuso del código TOTP
  kek_version       int,                           -- versión de la KEK que envolvió totp_secret
  suspended_until   timestamptz,                   -- NULL: activa · 'infinity': suspensión indefinida
  suspended_reason  text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CHECK ((totp_secret IS NULL) = (kek_version IS NULL))
);
CREATE TABLE permissions (                          -- catálogo fijo (§9.1); lo carga la migración
  code         text PRIMARY KEY,
  description  text NOT NULL,
  requires_mfa boolean NOT NULL                     -- permiso de admin: solo vale en una sesión que pasó por TOTP
);
CREATE TABLE roles (
  id          uuid PRIMARY KEY,
  name        text UNIQUE NOT NULL CHECK (name ~ '^[a-z0-9_-]{3,32}$'),
  description text NOT NULL DEFAULT '',
  builtin     boolean NOT NULL DEFAULT false,       -- 'user' y 'admin': no se borran
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE role_permissions (
  role_id    uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission text NOT NULL REFERENCES permissions(code),
  PRIMARY KEY (role_id, permission)
);
CREATE TABLE user_roles (
  user_id uuid NOT NULL REFERENCES users(id),
  role_id uuid NOT NULL REFERENCES roles(id),
  PRIMARY KEY (user_id, role_id)
);
CREATE TABLE user_sessions (
  id          uuid PRIMARY KEY,                     -- claim `sid` del JWT
  user_id     uuid NOT NULL REFERENCES users(id),
  stage       text NOT NULL CHECK (stage IN ('preauth','full')),
  mfa         boolean NOT NULL,                     -- la sesión pasó por TOTP
  device_hash bytea NOT NULL,                       -- SHA-256 de la cookie de dispositivo
  last_seen   timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz NOT NULL,                 -- preauth: 5 min; full: 8 h absolutas
  ended_at    timestamptz,
  end_reason  text                                  -- logout | replaced | expired | suspended | password_changed | mfa_passed
);
CREATE UNIQUE INDEX one_full_session_per_user
  ON user_sessions (user_id) WHERE stage = 'full' AND ended_at IS NULL;      -- riesgo 13
CREATE TABLE failed_attempts (
  id         bigserial PRIMARY KEY,
  key        text NOT NULL,                       -- 'user:<u>' | 'ip:<ip>' | 'register:<ip>'
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON failed_attempts (key, created_at);
```
- La migración carga el catálogo de permisos y los roles semilla `user` (`rooms:create`) y `admin` (todos los permisos).
- Una sesión vencida que todavía no tiene `ended_at` bloquearía el índice único: el login primero marca como `expired` las sesiones del usuario que ya vencieron.

### 7.2 BD `rooms`
```sql
CREATE TABLE rooms (
  id           uuid PRIMARY KEY,
  code         text UNIQUE NOT NULL CHECK (code ~ '^[a-z0-9_-]{3,32}$'),  -- normalizado a minúsculas
  key_hash     text NOT NULL,                     -- $argon2id$...
  mode         text NOT NULL CHECK (mode IN ('text','media','both')),
  max_members  int  NOT NULL CHECK (max_members BETWEEN 2 AND 50),
  member_count int  NOT NULL DEFAULT 0,
  owner_id     uuid NOT NULL,                     -- usuario dueño (vive en la BD auth)
  created_by   uuid NOT NULL,
  active       boolean NOT NULL DEFAULT true,
  created_at   timestamptz NOT NULL DEFAULT now(),
  closed_at    timestamptz,
  CHECK (member_count BETWEEN 0 AND max_members)  -- respaldo del riesgo 15
);
CREATE INDEX rooms_by_owner ON rooms (owner_id) WHERE active;
CREATE TABLE room_members (
  room_id      uuid NOT NULL REFERENCES rooms(id),
  user_id      uuid NOT NULL,
  alias        text NOT NULL,                     -- NFKC, 2–24 caracteres
  joined_at    timestamptz NOT NULL DEFAULT now(),
  left_at      timestamptz,                       -- NULL = miembro actual
  left_reason  text CHECK (left_reason IN ('left','kicked')),
  banned_until timestamptz,                       -- veto de reingreso
  muted_until  timestamptz,                       -- silencio
  PRIMARY KEY (room_id, user_id)
);
CREATE UNIQUE INDEX alias_per_room ON room_members (room_id, lower(alias));  -- el alias sigue reservado aunque su dueño salga
CREATE TABLE failed_attempts (
  id         bigserial PRIMARY KEY,
  key        text NOT NULL,                     -- 'ip:<ip>' | 'user:<id>' | 'room:<id>'
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON failed_attempts (key, created_at);
```
`member_count` cuenta las filas con `left_at IS NULL` y se actualiza en la misma transacción que cada alta o baja.

### 7.3 BD `chat`
```sql
CREATE TABLE room_keys (
  room_id     uuid PRIMARY KEY,                 -- id de la sala (vive en rooms); se crea con el primer mensaje
  dek_wrapped bytea NOT NULL,                   -- nonce||ct, AES-GCM con kek_chat, AAD "dek|<room_id>"
  kek_version int NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE messages (
  id         bigserial PRIMARY KEY,
  room_id    uuid NOT NULL REFERENCES room_keys(room_id),
  user_id    uuid NOT NULL,                     -- autor (cuenta)
  kind       text NOT NULL CHECK (kind IN ('text','file')),
  file_id    uuid,                              -- solo kind='file' (identificador opaco)
  payload    bytea,                             -- nonce||ct con la DEK, AAD "msg|<room_id>|<user_id>"; NULL si se borró
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  deleted_by uuid,                              -- el autor o el dueño de la sala
  CHECK ((kind = 'file') = (file_id IS NOT NULL)),
  CHECK ((deleted_at IS NULL) = (payload IS NOT NULL))
);
CREATE INDEX ON messages (room_id, id);
CREATE INDEX ON messages (file_id) WHERE file_id IS NOT NULL;
```
Payload en claro antes de cifrar: `{"from","body","ts"}` (texto) o `{"from","file_id","ts"}` (archivo). Borrar un mensaje destruye su contenido; la fila queda como evidencia de que existió.

### 7.4 BD `media`
```sql
CREATE TABLE files (
  id           uuid PRIMARY KEY,
  room_id      uuid NOT NULL,
  user_id      uuid NOT NULL,
  alias        text NOT NULL,
  storage_name text UNIQUE,                     -- uuid4 hex sin extensión; NULL si fue rechazado
  dek_wrapped  bytea,                           -- DEK del archivo envuelta con kek_media (nonce||ct, AAD "filedek|<id>"); NULL si fue rechazado
  kek_version  int,                             -- versión de la KEK que envolvió la DEK
  mime         text NOT NULL,                   -- 'unknown' si la firma no coincidió
  size         int  NOT NULL,
  sha256       bytea NOT NULL,                  -- del archivo original
  clean_sha256 bytea,                           -- de los bytes sanitizados que se publican (§9.6, paso 3)
  status       text NOT NULL CHECK (status IN ('clean','quarantined','rejected','released','deleted')),
  verdict      jsonb NOT NULL,                  -- veredicto de stego (§12.7) y motivo
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON files (user_id, created_at);
CREATE INDEX ON files (clean_sha256) WHERE clean_sha256 IS NOT NULL;
```

### 7.5 BD `audit`
```sql
CREATE TABLE audit_log (
  id        bigserial PRIMARY KEY,
  ts        timestamptz NOT NULL,
  service   text NOT NULL,                      -- deducido del token del llamador, nunca del payload
  severity  text NOT NULL CHECK (severity IN ('info','warning','critical')),
  actor     text NOT NULL,                      -- 'user:<username>' | 'ip:<ip>' | 'svc:<nombre>' | 'system'
  action    text NOT NULL,
  target    text,
  ip        inet,
  details   jsonb NOT NULL DEFAULT '{}',
  prev_hash bytea NOT NULL,
  hash      bytea NOT NULL
);
```

### 7.6 Roles (riesgos 11 y 16)
Para cada servicio con BD `<svc>` ∈ {auth, rooms, chat, media, audit}:

| Rol | Permisos | Uso |
|---|---|---|
| `<svc>_owner` | Dueño de la BD `<svc>`; DDL. `ALTER ROLE … SET log_statement = 'all'` | Solo el job `<svc>-migrate` (Alembic) |
| `<svc>_app` | `CONNECT` **solo** a la BD `<svc>`; DML sobre sus tablas (en `audit_log`: solo `SELECT, INSERT`); `USAGE` en sus secuencias. Sin DDL ni `TRUNCATE` | El servicio en ejecución |

- `deploy/postgres/init.sh` (se ejecuta una vez como superusuario) crea los 10 roles con contraseñas leídas de `/run/secrets` y las 5 BD. Luego ejecuta `REVOKE ALL ON DATABASE <svc> FROM PUBLIC` y `GRANT CONNECT ON DATABASE <svc> TO <svc>_app`.
- La primera migración de cada servicio hace `REVOKE ALL ON SCHEMA public FROM PUBLIC`, `GRANT USAGE ON SCHEMA public TO <svc>_app` y los `GRANT` explícitos por tabla.

---

## 8. Contratos HTTP

### 8.1 API pública (vía gateway)
**Identidad:** "—" = pública; "usuario" = JWT válido verificado por el gateway; un permiso (`stego:analyze`) = además ese permiso; "dueño" = dueño de la sala o `rooms:manage_any`; "miembro" = miembro actual de la sala.

| Método | Ruta | Servicio | Identidad | Descripción |
|---|---|---|---|---|
| POST | `/api/auth/register` | auth | — | `{username, password}` → `201 {id, username}`. Siempre con el rol `user` |
| POST | `/api/auth/login` | auth | — | `{username, password}` → `200 {access_token, token_type: "Bearer", expires_in}` + cookies `__Host-session` (y `__Host-device` si faltaba). Con un permiso de admin → `200 {mfa: "required" \| "setup"}` + cookie de etapa `preauth` |
| POST | `/api/auth/totp/setup` | auth | cookie `preauth`, sin TOTP confirmado | → `{otpauth_uri}` |
| POST | `/api/auth/totp` | auth | cookie `preauth` | `{code}` → sesión `full` con id nuevo; mismo cuerpo y cookies que el login |
| POST | `/api/auth/logout` | auth | usuario | Termina la sesión y cierra sus WebSockets (204) |
| GET | `/api/auth/me` | auth | usuario | `{id, username, roles, permissions}` |
| POST | `/api/auth/password` | auth | usuario | `{current, new}` → 204. Termina la sesión: hay que volver a entrar |
| GET | `/api/admin/users` | auth | `users:manage` | `[{id, username, roles, suspended_until, created_at}]` (hasta 200) |
| POST | `/api/admin/users/{id}/suspend` | auth | `users:manage` | `{reason, minutes?}` (sin `minutes` = indefinida) → termina sus sesiones y cierra sus WebSockets |
| POST | `/api/admin/users/{id}/reactivate` | auth | `users:manage` | `{reason?}` |
| PUT | `/api/admin/users/{id}/roles` | auth | `roles:manage` | `{roles: [role_id…]}` |
| GET | `/api/admin/permissions` | auth | `roles:manage` | Catálogo con `requires_mfa` |
| GET / POST | `/api/admin/roles` | auth | `roles:manage` | Listar / crear `{name, description?, permissions: [...]}` |
| PUT | `/api/admin/roles/{id}/permissions` | auth | `roles:manage` | `{permissions: [...]}`. El rol `admin` no se edita |
| DELETE | `/api/admin/roles/{id}` | auth | `roles:manage` | Solo roles no semilla y sin usuarios asignados |
| GET | `/api/rooms/mine` | rooms | usuario | Salas activas donde es miembro: `[{id, code, mode, alias, is_owner, member_count, max_members}]` |
| POST | `/api/rooms` | rooms | `rooms:create` | `{code, key, max_members, mode, alias}` → crea la sala y la membresía del dueño. 409 si ya tiene 2 salas activas |
| POST | `/api/rooms/join` | rooms | usuario | `{code, key, alias}` → membresía + `{room: {id, code, mode}}` |
| POST | `/api/rooms/{id}/leave` | rooms | miembro | 204. El dueño recibe 409 hasta que ceda la sala |
| GET | `/api/rooms/{id}/members` | rooms | miembro o dueño | `[{user_id, alias, is_owner, muted}]` |
| PATCH | `/api/rooms/{id}` | rooms | dueño | `{key?, max_members?, mode?}`: cupo ≥ miembros actuales; la clave solo la cambia el dueño |
| DELETE | `/api/rooms/{id}` | rooms | dueño | **Cierra la sala**: `active=false` y cierra sus conexiones; no admite ingresos y el código no se reutiliza |
| POST | `/api/rooms/{id}/owner` | rooms | dueño | `{user_id}` → cede la sala a un miembro actual que tenga menos de 2 salas activas |
| POST | `/api/rooms/{id}/members/{user_id}/kick` | rooms | dueño | `{reason, ban_minutes}` (0 = sin veto; máximo 525600) |
| GET | `/api/rooms/{id}/bans` | rooms | dueño | `[{user_id, alias, banned_until}]` |
| DELETE | `/api/rooms/{id}/bans/{user_id}` | rooms | dueño | Levanta el veto |
| POST / DELETE | `/api/rooms/{id}/members/{user_id}/mute` | rooms | dueño | `{reason, minutes}` (1–10080) / quita el silencio |
| GET | `/api/admin/rooms` | rooms | `rooms:manage_any` | Todas las salas, solo metadatos: `[{id, code, mode, owner_id, owner_alias, member_count, max_members, active, created_at}]` |
| POST | `/api/media/files` | media | miembro | multipart `room_id`, `file` → `{file_id, status}` |
| GET | `/api/media/files/{id}?exp=&sig=` | media | miembro | Descarga de un archivo `clean` o `released` |
| GET | `/api/admin/quarantine` | media | `quarantine:manage` | Archivos en cuarentena con su `verdict` |
| POST | `/api/admin/quarantine/{id}/release` | media | `quarantine:manage` | Sanitiza, publica en la sala y marca `released` |
| DELETE | `/api/admin/quarantine/{id}` | media | `quarantine:manage` | Borra el archivo físico y marca `deleted` |
| POST | `/api/stego/analyze` | stego | `stego:analyze` | multipart `file` → veredicto (§12.7) |
| GET | `/api/admin/audit?min_severity=&after_id=&limit=` | audit | `audit:read` | Eventos con `id > after_id`, del más nuevo al más viejo |
| GET | `/api/admin/audit/verify` | audit | `audit:read` | Recorre la cadena → `{ok, broken_at}` |
| WS | `/ws?room=<id>` | chat | miembro | Canal de chat (§9.5, §10) |
| GET | `/chat-key.json` | gateway (estático) | — | `{"kid": "v1", "pub": "<b64url 65 B>"}` clave pública ECDSA del chat |

**JWT:** RS256 firmado con `jwt_signing_key`. Claims: `iss` (`auth`), `aud` (`secure-chat`), `sub` (id del usuario), `sid` (id de la sesión), `name` (username), `stage` (`preauth` o `full`), `roles` (nombres, solo informativo), `iat` y `exp` (el vencimiento absoluto de la sesión). La autorización nunca usa los roles del token: usa los permisos que `auth` lee de la BD en cada request.

**Cookies:** `__Host-session` (el JWT) y `__Host-device` (128 bits aleatorios, sin fingerprinting), las dos con prefijo `__Host-` (Secure, Path=/, sin Domain), `HttpOnly` y `SameSite=Strict`. Ningún token es accesible desde JavaScript; la SPA no lee el `access_token` del cuerpo. Los clientes de API (Postman) mandan el token en `Authorization: Bearer` y conservan `__Host-device` en su almacén de cookies.

**CSRF:** además de SameSite=Strict, la dependencia `require_gateway` de la librería compartida rechaza con 403 (y audita `http.reject.origin`) los `POST/PUT/PATCH/DELETE` públicos cuyo `Origin` no esté en `ALLOWED_ORIGINS`. La colección de Postman manda `Origin: https://localhost`; la protección es para navegadores, que no permiten falsificar esa cabecera.

**Validaciones de entrada:**
- **Todos los cuerpos** usan modelos Pydantic con `extra="forbid"`: un campo de más (`role`, `roles`, `owner_id`, `suspended_until`…) → 422. Así no hay asignación masiva.
- `username`: se normaliza a minúsculas; `^[a-z0-9_.-]{3,32}$`. Contraseña: ≥ 12 caracteres, al menos 3 de 4 clases (minúsculas, mayúsculas, dígitos, símbolos) y distinta del `username`.
- Nombre de rol: `^[a-z0-9_-]{3,32}$`; permisos solo del catálogo.
- `code`: se normaliza a minúsculas; `^[a-z0-9_-]{3,32}$`. Clave de sala: la misma política que la contraseña y distinta del `code`.
- `alias`: NFKC y `strip`; 2–24 caracteres de letras, dígitos, espacio, `_` y `-`.
- Mensaje: 1–2000 caracteres y sin caracteres de control salvo `\n` y `\t`.
- `max_members`: 2–50. `reason`: 1–200 caracteres sin controles.

### 8.2 API interna (nunca enrutada por el gateway)
| Servicio | Método y ruta | Llamadores | Contrato |
|---|---|---|---|
| auth | `GET /internal/verify` | gateway | Lee `Authorization: Bearer` o la cookie `__Host-session`, más `__Host-device` → `204` + `X-User-Id`, `X-User-Name`, `X-Session-Id`, `X-User-Perms` (separados por comas; sin los `requires_mfa` si la sesión no pasó por TOTP; ausente si no hay permisos). Desliza `last_seen` · `401` |
| auth | `POST /internal/sessions/heartbeat` | chat | `{session_ids: [...]}` → `last_seen = now()` en las activas · `200 {ended: [...]}` con las que ya no lo están |
| rooms | `POST /internal/membership` | chat, media | `{room_id, user_id}` → `200 {alias, mode, is_owner, muted_until}` si la sala está activa y es miembro actual · `404` |
| rooms | `POST /internal/membership/heartbeat` | chat | `{members: [{room_id, user_id}]}` → `200 {states: [{room_id, user_id, member, muted_until}]}` |
| chat | `POST /internal/users/{id}/disconnect` | auth | `{code}` → cierra todos los WS de ese usuario · `204` |
| chat | `POST /internal/rooms/{room_id}/kick` | rooms | `{user_id, code}` → cierra su WS en la sala y avisa `leave` · `204` |
| chat | `POST /internal/rooms/{room_id}/mute` | rooms | `{user_id, until}` (`null` quita el silencio) · `204` |
| chat | `POST /internal/rooms/{room_id}/close` | rooms | Cierra todas las conexiones de la sala con 4401 · `204` |
| chat | `POST /internal/rooms/{room_id}/files` | media | `{file_id, user_id, alias}` → guarda el evento cifrado y lo difunde · `204` |
| media | `POST /internal/files/{id}/delete` | chat | Borra el archivo del disco y marca `deleted` (idempotente) · `204` |
| stego | `POST /internal/analyze` | media | Cuerpo: los bytes de la imagen (`application/octet-stream`) → `200` veredicto (§12.7) · `422 {error, motivos}` |
| stego | `POST /internal/sanitize` | media | Bytes → `200` bytes sanitizados (`image/png` o `image/jpeg`) · `422` · `503` si la salida conserva residuos (§12.5) |
| audit | `POST /internal/events` | auth, rooms, chat, media, stego | `{severity, action, actor, target?, ip?, details?}` → `201 {id}`; `service` sale del token |

Todos los servicios exponen además `GET /health` sin token (`{"status": "ok"}` si su BD responde; `stego` responde sin BD), usado solo por el healthcheck de Docker.

---

## 9. Flujos

### 9.1 Cuentas, roles y permisos (riesgos 4, 5 y 13)
**Catálogo de permisos** (fijo; lo carga la migración y lo usa `require_perm`):
| Permiso | Qué permite | Exige TOTP |
|---|---|---|
| `rooms:create` | Crear salas (máximo 2 activas) | No |
| `stego:analyze` | Usar `POST /api/stego/analyze` | No |
| `users:manage` | Listar, suspender y reactivar cuentas | Sí |
| `roles:manage` | Crear y editar roles; asignar roles a usuarios | Sí |
| `rooms:manage_any` | Ver todas las salas y hacer en cualquiera lo que hace su dueño, sin leer mensajes ni cambiar la clave | Sí |
| `quarantine:manage` | Revisar la cuarentena de imágenes | Sí |
| `audit:read` | Ver y verificar la auditoría | Sí |

**Roles semilla:** `user` (`rooms:create`; se puede editar, no se borra) y `admin` (todos los permisos; no se edita ni se borra). El registro asigna siempre `user`.

**Registro** (`POST /api/auth/register`): como máximo 10 registros por IP por hora (clave `register:<ip>`; si se excede → 429 y `auth.register.ratelimited`). Se normaliza el username, se aplica la política de contraseña y se guarda el hash Argon2id. Si el usuario ya existe → `409 "usuario no disponible"`. Auditoría `user.registered` (obligatoria).

**Login** (`POST /api/auth/login`):
1. Si hay ≥ 5 fallos en 15 min con clave `user:<u>` **o** `ip:<ip>` → `429` + `Retry-After` y auditoría `auth.login.locked`.
2. Argon2id verify. Si el usuario no existe se verifica contra un hash dummy, para no revelar por tiempo qué usuarios existen.
3. Si falla: se registra el fallo, retraso progresivo `min(0.25·2^(n−1), 4)` s y `401 "credenciales inválidas"` (`auth.login.fail`).
4. Cuenta suspendida (`suspended_until > now()`) → `403 "cuenta suspendida"` y `auth.login.suspended`. Se comprueba **después** de la contraseña.
5. **Dispositivo:** si no llega `__Host-device`, se genera uno y se pone en la respuesta.
6. **Una sesión por cuenta (R13):** se marcan como `expired` las sesiones vencidas del usuario. Si queda una sesión `full` activa con **otro** `device_hash` → `409 "ya hay una sesión activa en otro dispositivo"` y `auth.login.second_device` (warning). Si es del mismo dispositivo, se termina (`replaced`).
7. Si el usuario tiene algún permiso `requires_mfa` → sesión `preauth` (5 min), JWT de etapa `preauth` en la cookie y `200 {mfa: "required"}`, o `{mfa: "setup"}` si todavía no confirmó su TOTP. Si no → sesión `full` (`mfa=false`), JWT y `auth.login.ok` (obligatoria).
8. **TOTP** (`POST /api/auth/totp`): aplica el mismo bloqueo; descifra el secreto con `kek_auth` y verifica con `pyotp` (ventana ±1), rechazando si `step <= totp_last_step`. Si falla → se registra el fallo (`auth.totp.fail`). Si es válido → termina la sesión `preauth` (`mfa_passed`) y crea una sesión `full` **con un id nuevo** (contra la fijación de sesión) y `mfa=true`; 30 min de inactividad y 8 h absolutas. Auditoría `auth.login.ok`.
9. **Configurar TOTP** (`POST /api/auth/totp/setup`, solo en `preauth` y sin TOTP confirmado): genera un secreto nuevo, lo guarda cifrado y responde el `otpauth_uri`. El primer código válido en `/api/auth/totp` fija `totp_confirmed_at` (`auth.totp.enrolled`). Con TOTP ya confirmado → 409.
10. **Bootstrap:** `docker compose exec auth python -m auth_svc.create_admin <usuario>` pide la contraseña (o la lee con `--password-stdin`), crea la cuenta con el rol `admin` y el TOTP ya confirmado, e imprime el QR y el secreto.

**Verify** (`GET /internal/verify`, en cada request que pasa por el gateway):
1. JWT válido: firma RS256 con la clave pública de `jwt_signing_key`, `iss`, `aud`, `exp` y `stage = full`.
2. Sesión `sid`: etapa `full`, sin `ended_at`, `expires_at > now()`, `last_seen > now() − 30 min` y `device_hash` igual al SHA-256 de `__Host-device`. Si el dispositivo no coincide → 401 y `auth.verify.device_mismatch` (warning).
3. Cuenta no suspendida.
4. Permisos: la unión de los permisos de sus roles; si la sesión no pasó por TOTP, sin los `requires_mfa`. Así, quien recibe un rol de admin a mitad de una sesión necesita volver a entrar con TOTP para usarlo.
5. Desliza `last_seen` y responde 204 con las cabeceras de identidad. Cualquier otro caso → 401.

**Roles y permisos:** los cambios valen desde la siguiente request, porque `verify` lee la BD. Auditoría `role.created`, `role.permissions.changed`, `role.deleted` y `user.roles.changed` (obligatorias; `actor` = el admin).

**Nunca sin admin:** "admin activo" = cuenta no suspendida con el rol `admin`. Se rechaza con `409` y `admin.guard.last_admin` quitarle el rol `admin` al último admin activo o suspenderlo. Nadie puede suspenderse a sí mismo. La comprobación y el cambio van en una transacción con `pg_advisory_xact_lock`, para que dos admins no se quiten el rol a la vez.

**Suspensión y reactivación:** `suspended_until = now() + minutes` (o `infinity`) y `suspended_reason`. Terminan sus sesiones (`suspended`) y `auth` pide a `chat` cerrar sus WebSockets. La suspensión con fecha vence sola, porque `login` y `verify` comparan con `now()`. Reactivar = `suspended_until = NULL`. Auditoría `user.suspended` (warning) y `user.reactivated` (obligatoria).

**Logout y cambio de contraseña:** terminan la sesión (`logout` / `password_changed`), borran la cookie y piden a `chat` cerrar los WebSockets del usuario. El cambio de contraseña exige la actual y aplica la política.

### 9.2 Salas y membresía (riesgos 1, 8 y 15)
**Crear** (`POST /api/rooms`, permiso `rooms:create`):
1. Política de clave, código normalizado y alias válido.
2. Transacción con `pg_advisory_xact_lock` sobre el `owner_id`: si ya tiene 2 salas activas → `409 "ya tienes 2 salas activas"` y `room.limit.reached`. Si no, inserta la sala (`member_count = 1`) y la membresía del dueño. Código repetido → `409 "código no disponible"`. Auditoría `room.created` (obligatoria).

**Primer ingreso** (`POST /api/rooms/join {code, key, alias}`):
1. Rate limit: ≥ 5 fallos en 10 min por `ip`, ≥ 10 por `user` o ≥ 20 por `room` → `429` y auditoría.
2. Busca la sala activa por `code` y hace Argon2id verify (dummy si no existe). Si falla → registra el fallo en las tres claves y responde `401 "sala o clave inválida"`.
3. Veto vigente (`banned_until > now()`) → `403 "no puedes entrar a esta sala"` y `room.join.banned`. Se comprueba **después** de la clave, para no revelar el veto a quien no la conoce.
4. Si ya es miembro actual → 200 con la sala (idempotente; el alias no cambia).
5. **Transacción única:**
   ```sql
   UPDATE rooms SET member_count = member_count + 1
    WHERE id = :room AND active AND member_count < max_members
   RETURNING id;                        -- 0 filas → 409 "sala llena"
   INSERT INTO room_members (room_id, user_id, alias) VALUES (:room, :user, :alias)
   ON CONFLICT (room_id, user_id) DO UPDATE
      SET alias = EXCLUDED.alias, joined_at = now(), left_at = NULL, left_reason = NULL;
                                        -- choque con alias_per_room → rollback → 409 "alias en uso"
   ```
   En la misma transacción se emite `room.member.joined` (obligatorio; si `audit` falla, el ingreso falla con 503).

**Volver:** *Mis salas* (`GET /api/rooms/mine`); abrir la sala es conectar el WebSocket (§9.5). La clave no se vuelve a pedir. Si el dueño cambia la clave, los miembros actuales siguen dentro.

**Salir** (`POST /api/rooms/{id}/leave`): el dueño recibe `409 "cede la sala antes de salir"`. Para los demás: `left_at = now()`, `left_reason = 'left'` y `member_count − 1` en la misma transacción; `rooms` pide a `chat` cerrar su conexión (4401). Auditoría `room.member.left`.

### 9.3 Administración de la sala (riesgo 5)
`puede_administrar(sala, quien) = sala.owner_id == quien.user_id o "rooms:manage_any" ∈ quien.perms`. Cada acción se audita con el actor; si la hace el admin global sobre una sala ajena, con `details.as_admin = true`. Un intento sin permiso → 403 y `room.forbidden`.

| Acción | Reglas | Efecto | Evento |
|---|---|---|---|
| Editar | Cupo ≥ `member_count`; clave con la política. **La clave solo la cambia el dueño** | Actualiza la sala | `room.updated` (obligatorio) |
| Cerrar | — | `active = false`, `closed_at`; `chat` cierra todas sus conexiones (4401). Los datos se conservan y el código no se reutiliza | `room.closed` |
| Ceder | El destino es miembro actual, sin veto y con menos de 2 salas activas (con `pg_advisory_xact_lock` sobre el destino) | Cambia `owner_id` | `room.owner.transferred` (obligatorio) |
| Expulsar | Nunca al dueño; `ban_minutes` entre 0 y 525600 | `left_at`, `left_reason = 'kicked'`, `banned_until` si `ban_minutes > 0`, `member_count − 1`; `chat` cierra su conexión con 4411 | `room.member.kicked` (warning) |
| Levantar veto | — | `banned_until = NULL` | `room.member.unbanned` |
| Silenciar / quitar silencio | Nunca al dueño; de 1 a 10080 min | `muted_until`; `chat` actualiza la conexión abierta | `room.member.muted` / `room.member.unmuted` |

El admin global no necesita ser miembro para administrar una sala. Para leer mensajes sí, y para ser miembro necesita la clave, que no puede cambiar en una sala ajena.

Si suspenden al dueño, sus salas siguen funcionando para los demás miembros; el admin global puede cederlas a otro miembro.

### 9.4 Ciclo de vida de una conexión
| Evento | Quién lo detecta | Qué ocurre |
|---|---|---|
| Cerrar o recargar la pestaña (WS 1000/1001) | chat | Cierra la conexión y avisa `leave` (presencia) a la sala; la membresía sigue |
| Violación de protocolo (4400/4403/4408/4413/4429) | chat | Cierra el WS y audita |
| Inactividad: 15 min sin mensajes del usuario | chat (en memoria) | Cierra con 4410; la membresía sigue |
| Expulsión | rooms → chat | Cierra con 4411; la sala desaparece de *Mis salas* |
| Silencio | rooms → chat | La conexión sigue; `chat` responde a cada `msg` con una trama `error` (`muted`) y `media` rechaza las subidas |
| Salida voluntaria | rooms → chat | Cierra con 4401 |
| Sala cerrada | rooms → chat | Cierra todas sus conexiones con 4401 |
| Logout, suspensión o cambio de contraseña | auth → chat | Cierra todas las conexiones del usuario con 4401 |
| Sesión vencida (8 h, o 30 min sin actividad) | latido chat → auth | La respuesta `ended` la incluye y `chat` cierra con 4401 |
| `chat` se reinicia | clientes | Reconectan y hacen un handshake nuevo |
| `auth` o `rooms` se reinician | — | Nada: el estado vive en su BD; el latido reconcilia |

**Reconciliación:** cada 30 s, `chat` manda a `auth` las sesiones conectadas (`ended` le dice cuáles cerrar) y a `rooms` los pares (sala, usuario) conectados (`states` le dice quién dejó de ser miembro y quién está silenciado). Así se corrige cualquier aviso perdido. Mientras alguien chatea, ese latido también mantiene viva su sesión.

### 9.5 Chat por WebSocket (riesgos 7, 10 y 14)
1. El gateway hace el `auth_request` de usuario. `chat` lee `room` de la query, pide a `rooms` la membresía (si no es miembro de una sala activa: acepta, cierra con 4403 y audita `ws.reject.membership`) y valida `Origin` contra `ALLOWED_ORIGINS` (si no coincide: acepta, cierra con 4403 y audita).
2. **Handshake** (§10.1) con `session_id` = `X-Session-Id` (la sesión de la cuenta). El cliente tiene 10 s para enviar `hello`. Si no lo hace o es inválido → 4400.
3. Si el mismo usuario ya tenía un WS abierto en esa sala, el anterior se cierra con **4409** (la nueva conexión gana).
4. Tras el handshake, `chat` envía el historial (últimos 50 eventos de la sala: mensajes, archivos y borrados, re-cifrados para esta conexión) y difunde un evento `join` (presencia).
5. Por cada trama: tamaño ≤ `WS_MAX_FRAME` (16 KB; si no → 4413), token bucket de 5/s con ráfaga 10 (si no → 4429), `seq` mayor que el último recibido (si no → 4408), descifrado AES-GCM (si el tag falla → 4400 y auditoría **critical** `ws.tamper`).
6. Payload `msg`: el modo de la sala debe permitir texto (si no → 4403); si el usuario está silenciado, `chat` responde `{"t":"error","code":"muted","until":…}` y la conexión sigue (`ws.muted`); el cuerpo debe ser válido según §8.1 (si no → 4400). **El remitente sale de `X-User-Id` y del alias que devolvió `rooms`, nunca del payload.**
7. Se persiste en `messages`, cifrado con la DEK de la sala (creada en la primera escritura), y se difunde a cada conexión de la sala cifrado con **su** clave y **su** contador `s2c`.
8. Payload `del` (`{"t":"del","id":…}`): el mensaje debe ser de la sala. Si el usuario es el autor, se borra. Si no, `chat` pregunta a `rooms` si es el dueño; si tampoco lo es → 4403 y auditoría. Borrar = `payload = NULL`, `deleted_at` y `deleted_by`, y se difunde `{"t":"deleted","id":…}`. Si era una imagen, `chat` pide a `media` borrar el archivo. Auditoría `message.deleted` (`details`: `message_id`, `by_owner`).
9. Payload `file_url`: si existe un mensaje `kind='file'` no borrado con ese `file_id` **en la sala de la conexión**, responde con una URL firmada nueva. Si no → 4403 y auditoría.
10. Cada 30 s una tarea de fondo envía los latidos a `auth` y a `rooms` (§9.4) y cierra por inactividad las conexiones con `last_activity` vencido.
11. uvicorn hace ping cada 30 s y cierra si no hay pong en otros 30 s (`--ws-ping-interval 30 --ws-ping-timeout 30`).

### 9.6 Subida de imágenes (riesgos 6 y 9)
`POST /api/media/files` (multipart `room_id`, `file`). `media` pide a `rooms` la membresía: si no es miembro → 403; si el modo de la sala no admite multimedia → 403 y `file.rejected.forbidden`; si está silenciado → `403 "estás silenciado"` y `file.rejected.muted`. Como máximo 5 subidas por minuto por usuario (si no → 429).
1. Tope de 5 MB (Nginx `client_max_body_size 5m` solo en esta ruta, más el control de la app). Si se excede → `rejected (size)`.
2. **ClamAV** INSTREAM. Si encuentra algo → `rejected (malware)` y auditoría **critical**. Si no responde → **falla cerrado**: 503 y `clamav.unavailable`.
3. **Excepción:** si el `sha256` del archivo coincide con el `clean_sha256` de un archivo ya publicado, se publica sin volver a analizar. Son bytes que generó el propio sistema; por ejemplo, una imagen descargada del chat y vuelta a subir. La sanitización aleatoriza el plano LSB, así que el chi² la marcaría como sospechosa. Cualquier modificación cambia el hash y fuerza el análisis completo.
4. **`stego /internal/analyze`** (§12): `422` → `rejected (type | invalid)`; veredicto `problema` o `revision_manual` → cuarentena; `limpia` → sanitización. Si `stego` no responde → 503 y `stego.unavailable` (falla cerrado).
5. **Política:**
   - Sospechoso → se guarda **cifrado** (§11.2) en `/data/quarantine/<uuid>`, `status=quarantined`, auditoría warning `file.quarantined` con el veredicto. El usuario recibe "archivo retenido para revisión" y **el archivo no se publica**.
   - Rechazado → no se guarda el archivo; se registran `sha256`, `mime` y motivo en `files` y en auditoría.
   - Limpio → **`stego /internal/sanitize`** (§12.5) → se guarda **cifrado** en `/data/media/<uuid>`, `status=clean` → publicación (§9.7).
6. Archivos con permisos `0640`, dueño uid 10001. Solo `media` monta el volumen. Lo que queda en disco es `nonce‖ct‖tag` de AES-256-GCM: sin la KEK no hay imagen, y cualquier alteración del archivo falla en la descarga.

### 9.7 Publicación y descarga (riesgo 12)
- **Publicación:** `media` llama a `chat POST /internal/rooms/{room_id}/files {file_id, user_id, alias}`. `chat` guarda un mensaje `kind='file'` cifrado y difunde a cada conexión `{"t":"file","id":<id del mensaje>,"file_id":…,"from":alias,"url":…,"ts":…}`, con una **URL firmada por destinatario**:
  `url = /api/media/files/{file_id}?exp={exp}&sig={b64url(HMAC-SHA256(url_signing_key, "{file_id}|{user_id}|{exp}"))}`, con `exp = now + 60 s`.
  Si `chat` no responde, `media` devuelve 503. El archivo queda `clean` pero no aparece en ninguna sala, así que nadie puede obtener una URL firmada para él.
- **Descarga:** `GET /api/media/files/{id}?exp&sig`. El gateway verifica al usuario; `media` exige firma válida contra `X-User-Id` (`hmac.compare_digest`), `exp` no vencido, `status` ∈ {`clean`, `released`} y que el usuario siga siendo miembro de `files.room_id` (`rooms /internal/membership`). Si algo falla → `404` (no revela si el archivo existe) y auditoría `file.download.denied`. Si pasa, `media` descifra el archivo con su DEK en memoria; un tag GCM inválido (archivo alterado o ausente en disco) responde 404 y audita `file.integrity.failed`.
- **Cabeceras de respuesta:** `Content-Type` del allowlist, `X-Content-Type-Options: nosniff`, `Content-Disposition: inline; filename="image.<ext>"`, `Cache-Control: private, no-store`.
- **Renovación:** cuando una imagen expira en pantalla, la SPA envía `{"t":"file_url","file_id":…}` por el WS.

### 9.8 Cuarentena (admin global con `quarantine:manage`)
- `GET /api/admin/quarantine` → lista con `room_id`, `alias`, `mime`, `size`, `sha256` y `verdict`.
- **Liberar:** lee y descifra el original de `/data/quarantine`, lo **sanitiza** con `stego`, lo guarda cifrado con una DEK nueva en `/data/media`, borra el original, `status=released`, auditoría `file.released` (obligatoria) y publicación (§9.7).
- **Eliminar:** borra el archivo, `status=deleted`, auditoría `file.deleted`.
- La cuarentena es solo del admin global: un dueño podría liberar un payload en su propia sala.

### 9.9 API de esteganografía (primer parcial)
`POST /api/stego/analyze` (multipart `file`, permiso `stego:analyze`):
1. Tope de 5 MB (Nginx y la app).
2. Como máximo 10 análisis por minuto por usuario (token bucket en memoria por `X-User-Id`; si no → 429 y `stego.ratelimited`).
3. El mismo análisis que `/internal/analyze` (§12), en un `ProcessPoolExecutor` con timeout de `STEGO_TIMEOUT_S`.
4. No guarda nada. Auditoría `stego.analyzed` con `sha256`, veredicto y motivos: `info` si es `limpia`, `warning` en los demás casos.
5. Responde el veredicto (§12.7).

---

## 10. Protocolo criptográfico (fuente de verdad para Python y TypeScript)

### 10.1 Handshake por conexión WebSocket (*hello* firmado)
| Paso | Valor |
|---|---|
| 1. Cliente | Genera un par **ECDH P-256 efímero** (WebCrypto, privada no extraíble) y envía como **primera trama**: `{"t":"hello","pub":"<b64url del punto sin comprimir, 65 B>"}` |
| 2. chat | Valida que el punto esté en la curva y genera su propio par efímero y un `salt` de 32 bytes aleatorios. `shared` = ECDH (32 bytes). `K` = **HKDF-SHA256**(`shared`, `salt`, `info` = `"secure-chat/v1|{room_id}|{session_id}"`, 32 bytes) |
| 3. chat | Firma la transcripción `T` = UTF-8 de `"secure-chat/v1/hello|{room_id}|{session_id}|{client_pub}|{server_pub}|{salt}"` (los tres últimos en b64url) con **ECDSA P-256 + SHA-256** usando `chat_sign_key` (clave de largo plazo). Firma en formato **IEEE P1363** (`r‖s`, 64 bytes) |
| 4. chat → cliente | `{"t":"hello","pub":"<b64url>","salt":"<b64url>","sig":"<b64url>"}` |
| 5. Cliente | Verifica `sig` sobre `T`, reconstruida con **su propia** `client_pub` y con la clave pública de `/chat-key.json`, que sirve el propio gateway (sin pasar por la red interna). Si falla → cierra con 4400 y muestra "conexión no segura" |
| Resultado | `K` es exclusiva de esta conexión. En el navegador es un `CryptoKey` no extraíble y solo vive en memoria |

Desde la revisión 4, `session_id` es el id de la sesión de la cuenta (`sid`). Cada conexión sigue teniendo su propia `K`, porque las claves efímeras y el `salt` cambian en cada handshake.

**Por qué se firma:** TLS termina en el gateway y el tramo gateway→chat es HTTP interno. La firma impide que alguien con presencia en la red interna reemplace las claves efímeras (MITM activo). Como la firma cubre la `client_pub` que recibió el servidor, también se detecta una sustitución de la clave del cliente.

### 10.2 Tramas
- **Cifrado:** AES-256-GCM, nonce aleatorio de 12 bytes por trama, tag de 16 bytes concatenado al ciphertext (formato por defecto de WebCrypto y de `AESGCM`).
- **AAD** = UTF-8 de `"v1|{room_id}|{session_id}|{seq}|{dir}"`, con `dir ∈ {c2s, s2c}`. En `s2c`, `session_id` es el del **destinatario**.
- **En el cable:** `{"seq": <int>, "n": "<b64url nonce>", "c": "<b64url ct||tag>"}`.
- `seq` empieza en 1 **por conexión y por dirección** y debe ser estrictamente creciente; el receptor rechaza `seq <= último`. El sufijo `dir` impide reflejar tramas hacia su emisor. Como cada conexión tiene su propia `K`, una trama de una conexión anterior no descifra en la nueva.
- **Payload en claro** (JSON UTF-8, serializado sin espacios):
  - `c2s`: `{"t":"msg","body":"…"}` · `{"t":"file_url","file_id":"…"}` · `{"t":"del","id":123}`
  - `s2c`: `{"t":"msg","id":123,"from":"alias","body":"…","ts":"ISO-8601"}` · `{"t":"file","id":124,"file_id":"<uuid>","from":"alias","url":"…","ts":"…"}` · `{"t":"file_url","file_id":"…","url":"…"}` · `{"t":"deleted","id":123}` · `{"t":"error","code":"muted","until":"ISO-8601"}` · `{"t":"system","event":"join|leave","alias":"…"}` · `{"t":"history","items":[…eventos msg/file/deleted…]}`
  - En todos los eventos, `id` es el id del mensaje. En el historial, un mensaje borrado aparece como `{"t":"deleted","id":123,"ts":"…"}`.
- **Límite práctico:** 2^32 tramas por clave con nonces aleatorios. Una conexión nunca se acerca a ese número.

### 10.3 Códigos de cierre del WS
| Código | Motivo |
|---|---|
| 4400 | Trama malformada, tag GCM inválido, o handshake inválido o vencido |
| 4401 | Sesión o membresía terminada (logout, suspensión, salida, sala cerrada, reconciliación) |
| 4403 | Origin no permitido, no es miembro, tipo de contenido no permitido en la sala, archivo ajeno o borrado no autorizado |
| 4408 | Replay (`seq` no creciente) |
| 4409 | Reemplazada por otra conexión del mismo usuario en la sala |
| 4410 | Expiración por inactividad |
| 4411 | Expulsado de la sala |
| 4413 | Trama demasiado grande |
| 4429 | Rate limit |

### 10.4 Vectores de prueba
`docs/crypto-vectors.json` contiene casos fijos: claves ECDH de prueba en JWK, `salt`, ids, nonces, tramas `c2s`/`s2c` esperadas, y una clave ECDSA de prueba con una transcripción y una firma generada en Python. pytest **y** vitest verifican lo mismo: misma `K` (por el ciphertext resultante), mismas tramas y firma válida. Si cambia el protocolo, cambian los vectores.

---

## 11. Gestión de claves y secretos (riesgos 2 y 16)

### 11.1 Inventario
`python deploy/gen_secrets.py` los crea en `deploy/secrets/` (gitignored, directorio `0700`, archivos `0644` para que el uid del contenedor pueda leerlos) y **nunca sobrescribe**. `--rotate <nombre>` regenera uno.

| Secreto | Contenido | Montado en |
|---|---|---|
| `svc_token_{gateway,auth,rooms,chat,media,stego}` | 32 bytes b64url | Solo su dueño (el del gateway va dentro de `gateway_token.conf`) |
| `svc_hash_{gateway,auth,rooms,chat,media,stego}` | SHA-256 hex del token | Los receptores según la allowlist (§4.3) |
| `gateway_token.conf` | `proxy_set_header X-Service-Token "<token>";` | gateway |
| `jwt_signing_key` | RSA de 3072 bits en PKCS#8 PEM | auth |
| `kek_auth_v1` | 32 bytes b64url | auth |
| `kek_chat_v1` | 32 bytes b64url | chat |
| `kek_media_v1` | 32 bytes b64url | media |
| `chat_sign_key` | ECDSA P-256 en PKCS#8 PEM | chat (además se genera `deploy/public/chat-key.json` con la pública, montado en el gateway) |
| `url_signing_key` | 32 bytes b64url | chat, media |
| `db_<svc>_owner`, `db_<svc>_app` | 32 bytes b64url | `<svc>-migrate` / `<svc>` y `db` |
| `postgres_password` | 32 bytes b64url | db |

- Cada servicio lee sus secretos desde `/run/secrets/*` al arrancar y **no arranca si falta alguno**. Ningún secreto va en el código, en variables de entorno ni en un `.env` versionado.
- El JWT no se guarda en ninguna parte: la BD solo tiene el id de la sesión a la que apunta, y sin `jwt_signing_key` nadie puede fabricar uno. La cookie de dispositivo se guarda como SHA-256.
- Argon2id para las contraseñas y las claves de sala, con un **tope de 4 verificaciones concurrentes** por proceso (4 × 64 MiB) para que un ataque de logins o ingresos masivos no agote la memoria.

### 11.2 Envelope encryption
- **auth:** el secreto TOTP se cifra con `kek_auth_v{n}` (AAD `totp|<user_id>`) y se guarda junto con `kek_version`.
- **chat:** cada sala tiene una DEK de 32 bytes, creada con su primer mensaje y envuelta con `kek_chat_v{n}` (AAD `dek|<room_id>`). Los mensajes se cifran con la DEK (AAD `msg|<room_id>|<user_id>`).
- **media:** cada archivo aceptado o en cuarentena tiene su propia DEK de 32 bytes, envuelta con `kek_media_v{n}` (AAD `filedek|<file_id>`) y guardada en `files.dek_wrapped`. El contenido se cifra con AES-256-GCM (AAD `file|<file_id>`), de modo que un archivo no se puede intercambiar por otro. Al liberar de la cuarentena se genera una DEK nueva.

### 11.3 Rotación
| Qué | Cómo |
|---|---|
| KEK de auth | Montar `kek_auth_v2`, `CURRENT_KEK_VERSION=2`, reiniciar `auth`, ejecutar `python -m auth_svc.rotate_kek` (re-envuelve los secretos TOTP) y luego retirar la v1 |
| Clave de firma de JWT | `gen_secrets.py --rotate jwt_signing_key` y reiniciar `auth`: los JWT anteriores dejan de verificar y todos vuelven a iniciar sesión |
| KEK de chat | Igual con `kek_chat_v2` y `python -m chat_svc.rotate kek` (re-envuelve las DEK; los mensajes no se tocan) |
| DEK de una sala comprometida | `python -m chat_svc.rotate room <room_id>`: DEK nueva y re-cifrado de los mensajes de la sala en una transacción. La escritura de mensajes toma `FOR SHARE` sobre `room_keys`, así que espera a que termine la rotación |
| KEK de media | Igual con `kek_media_v2` y `python -m media_svc.rotate_kek` (re-envuelve las DEK; los archivos no se tocan) |
| Token de servicio | `gen_secrets.py --rotate svc_token_<x>` (regenera token y hash) y reiniciar `<x>` y sus receptores |
| Clave de firma del chat | `gen_secrets.py --rotate chat_sign_key` (regenera `chat-key.json`), reiniciar `chat` y recargar el gateway |
| TLS | `mkcert` en local; Let's Encrypt en el VPS con hooks de renovación (`docs/despliegue-vps.md`) |

---

## 12. Análisis de archivos y estegoanálisis (riesgos 6 y 9) — servicio `stego`

`stego` hace el análisis y la sanitización; `media` decide la política (§9.6). La API pública (§9.9) usa el mismo análisis.

### 12.1 Punto de extensión
```python
# stego_svc/formats.py
FORMATS = {
    "image/png":  Format(mime="image/png",  ext="png", signature=b"\x89PNG\r\n\x1a\n", pil_format="PNG",
                         analyze=png.analyze,  sanitize=png.sanitize,  residual=png.residual),
    "image/jpeg": Format(mime="image/jpeg", ext="jpg", signature=b"\xff\xd8\xff",      pil_format="JPEG",
                         analyze=jpeg.analyze, sanitize=jpeg.sanitize, residual=jpeg.residual),
}
```
Para agregar un formato basta con una entrada nueva, su módulo y sus tests. `analyze` y `sanitize` son funciones de módulo (las ejecuta un `ProcessPoolExecutor`). `residual(data)` devuelve solo los motivos **estructurales** (los mismos de `problema`) y reanaliza la salida de `sanitize` (§12.5).

**Validación previa** (igual para la API pública y la interna): tope de 5 MB, firma (*magic bytes*) contra `FORMATS` ignorando la extensión y el `Content-Type`, `MAX_IMAGE_PIXELS` = 20 MP, formato decodificado igual al de la firma, `verify()` y luego `load()`.

### 12.2 PNG (dominio de píxeles, canales RGB)
- **Chi² de Westfeld–Pfitzmann** por canal: para los pares `(2k, 2k+1)` se calcula `E = (h[2k] + h[2k+1]) / 2` y `χ² = Σ (h[2k] − E)² / E` (solo pares con `E > 4`), con `p = 1 − CDF_χ²(χ², gl = pares − 1)`. Se evalúa sobre los prefijos de 10 %, 25 %, 50 % y 100 % de los píxeles en orden de escaneo (prefijos de al menos 1000 píxeles), porque el embedding secuencial deja el prefijo con p ≈ 1. **Sospechoso si algún p ≥ `STEGO_CHI2_P`.**
- **Análisis RS** (Fridrich, Goljan, Du 2001): grupos de 2×2 píxeles en zigzag, función de variación `Σ|xᵢ₊₁ − xᵢ|`, máscara `[0,1,1,0]`, estimación de la tasa `p̂` por canal resolviendo `2(d₁+d₀)x² + (d₋₀−d₋₁−d₁−3d₀)x + d₀−d₋₀ = 0` (la raíz de menor módulo) con `p̂ = x/(x−½)`. **Sospechoso si `p̂ ≥ STEGO_RS_RATE`.**
- **Entropía del plano LSB** en bloques de 64×64: se reportan la media y la fracción de bloques con entropía ≥ 0.999 bits. Es una métrica de **apoyo**; solo se vuelve disparador si la calibración muestra que separa bien (`STEGO_ENTROPY_TRIGGER`, desactivado por defecto).
- **Estructura:** cualquier dato después de `IEND` es sospechoso; también lo son los chunks `tEXt/zTXt/iTXt` que sumen más de 1 KB y los chunks desconocidos o privados.
- Las métricas que no se pueden calcular (por ejemplo, NaN) se guardan como `null`: el veredicto debe poder serializarse en JSON.

### 12.3 JPEG
- Más de 16 bytes después del marcador `FFD9` final → sospechoso.
- Segmentos `APPn` + `COM` que sumen más de 64 KB → sospechoso.
- El recorrido salta los segmentos por su longitud; así una miniatura EXIF con su propio `FFD9` no confunde al análisis.
- *Stretch:* chi² sobre el histograma de coeficientes DCT (detector de JSteg) con `jpegio`, solo si instala sin problemas.

### 12.4 Calibración
`services/stego/tools/stego_lab.py`:
- `embed <in> <out> --rate 0.1 --mode seq|random`: LSB replacement con bits aleatorios.
- `calibrate <dir_limpias>`: genera variantes al 5, 10, 25, 50 y 100 % y reporta TPR/FPR por detector.

Se necesitan ≥ 30 imágenes limpias reales (fotos de celular y capturas de pantalla); para el primer parcial alcanzan 15. El chi² tiende a dar falsos positivos con histogramas muy suaves; los umbrales finales se fijan con esta herramienta y se documentan en el informe con la tabla TPR/FPR.

### 12.5 Sanitización (CDR) de todo archivo aceptado o liberado
- **PNG:** se decodifica (se conserva el canal alfa si existe), se **reemplaza el plano LSB por bits aleatorios** (imperceptible; destruye payloads LSB-1 aunque no se detecten) y se recodifica sin chunks auxiliares. Recodificar sin tocar los píxeles **no** basta, porque PNG es sin pérdida.
- **JPEG:** se aplica la orientación EXIF y se recodifica a RGB con calidad 90, sin EXIF, ICC ni comentarios.
- **Reanálisis estructural de la salida:** antes de entregarla, `stego` revisa la estructura de lo que produjo el sanitizador (`residual`: datos pegados, chunks de texto o desconocidos, metadatos excesivos). Si queda algo, no la entrega: responde 503 y audita `stego.sanitize.failed` (critical), y `media` no publica ni libera nada. Solo se revisa la estructura: el plano LSB aleatorio dispararía chi² por diseño (A3-RS-36).
- `media` guarda el `clean_sha256` de la salida. Una imagen con el plano LSB aleatorio es estadísticamente idéntica a una con LSB embebido al 100 %, así que el sistema reconoce sus propias salidas por hash (§9.6, paso 3) y no las vuelve a analizar. El prototipo del 2026-10-13 lo confirmó: también fallan las alternativas de poner el LSB en cero (lo marca RS), recodificar como JPEG o redimensionar (lo marca chi²).

### 12.6 Agregar formatos en el futuro
Audio WAV: LSB sobre las muestras PCM (chi² y RS se adaptan a 16 bits); sanitización aleatorizando el LSB de las muestras. PDF y video: firma + ClamAV + política de rechazo hasta definir un análisis específico.

### 12.7 Veredicto
| Veredicto | Cuándo | Respuesta |
|---|---|---|
| `invalida` | La validación previa (§12.1) falla: firma que no coincide o formato no admitido, más de 5 MB, más de 20 MP, decodificación fallida o formato decodificado distinto de la firma | `422 {"error": "archivo no permitido", "motivos": [...]}` |
| `problema` | Anomalía **estructural** determinista (§12.2 *Estructura*, §12.3) | `200` |
| `revision_manual` | Algún detector **estadístico** supera su umbral (chi², RS; entropía si se activa) o el análisis superó `STEGO_TIMEOUT_S` | `200` |
| `limpia` | Ninguna de las anteriores | `200` |

```json
{
  "verdict": "limpia | problema | revision_manual",
  "format": "image/png",
  "sha256": "…",
  "checks": {
    "trailing_bytes": 0, "text_bytes": 312, "unknown_chunks": [],
    "chi2_p": 0.37, "rs_rate": 0.01,
    "lsb_entropy_mean": 0.98, "lsb_entropy_high_fraction": 0.02
  },
  "motivos": []
}
```
En JPEG, `checks` trae `trailing_bytes` y `metadata_bytes`. `chi2_p` y `rs_rate` son el máximo sobre canales (y prefijos, en el caso de chi²). Si una anomalía estructural y un detector estadístico coinciden, gana `problema`.
`problema` es determinista (un archivo pegado al final está ahí o no está); `revision_manual` puede ser un falso positivo y lo revisa una persona. En las salas, los dos van a cuarentena.

---

## 13. Gateway (Nginx) — riesgos 7, 10 y 16

- **TLS:** `listen 443 ssl; http2 on; ssl_protocols TLSv1.3; ssl_session_tickets off;`. El puerto 80 solo responde `301` a https, así que **`ws://` nunca llega a ningún servicio**.
- **Cabeceras** (nivel `server`, con `always`; ninguna `location` declara `add_header`):
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'` (en CSP3, `'self'` cubre `wss:` del mismo host)
  - `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`, `server_tokens off`
- **Rutas:**
  | Ruta | Upstream | `auth_request` | Límite |
  |---|---|---|---|
  | `= /api/auth/register`, `= /api/auth/login`, `= /api/auth/totp`, `= /api/auth/totp/setup` | auth | — (la etapa `preauth` la valida `auth`) | zona `login` 1 r/s, ráfaga 5 |
  | `/api/auth/` | auth | usuario | zona `api` 10 r/s, ráfaga 20 |
  | `/api/admin/rooms` | rooms | usuario | `api` |
  | `/api/admin/quarantine` | media | usuario | `api` |
  | `/api/admin/audit` | audit | usuario | `api` |
  | `/api/admin/` | auth | usuario | `api` |
  | `= /api/rooms/join` | rooms | usuario | `login` |
  | `/api/rooms` | rooms | usuario | `api` |
  | `= /api/media/files` | media | usuario | `api`, `client_max_body_size 5m` |
  | `/api/media/` | media | usuario | `api` |
  | `= /api/stego/analyze` | stego | usuario | `api`, `client_max_body_size 5m` |
  | `= /ws` | chat | usuario | `limit_conn` 20 por IP, `proxy_read_timeout 75s` |
  | `= /chat-key.json` | archivo estático montado | — | — |
  | `/` | SPA (`try_files $uri /index.html`) | — | — |
  | cualquier otra `/api/…` o `/internal/…` | — | — | `404` JSON |
- **`auth_request`:** una sola ubicación `internal` (`/_auth/user` → `auth /internal/verify`) que incluye solo `proxy-base.conf`, con `proxy_pass_request_body off`, `Content-Length ""` y `X-Original-URI`. Así las cookies y el `Authorization` originales llegan a `auth`. La identidad se toma con `auth_request_set $x $upstream_http_x_…`.
- **Snippets de proxy** (en cada `location` se incluye exactamente uno, porque `proxy_set_header` no se hereda cuando una `location` declara los suyos):
  - `proxy-base.conf`: `Host`, `X-Real-IP $remote_addr`, `X-Forwarded-For $remote_addr` (sobrescribe, no concatena), `X-Forwarded-Proto https` y el token del gateway (`include /run/secrets/gateway_token_conf`, el secreto que se genera en `deploy/secrets/gateway_token.conf`).
  - `proxy-public.conf`: base + **vacía** las 4 cabeceras `X-User-*` y `Authorization`. Las cookies sí pasan, porque `auth` las necesita en el login (dispositivo) y en el TOTP (etapa `preauth`).
  - `proxy-user.conf`: base + `X-User-*` desde `auth_request` + `Authorization ""` y `Cookie ""`: ni el JWT ni las cookies viajan a los servicios.
- **Correlación (RNF-19):** el gateway genera `X-Request-ID` (`$request_id`), sobrescribe el del cliente y lo manda en `proxy-base.conf`, tanto a los servicios como al `auth_request` (la subpetición comparte variables con la petición, así que es el mismo id). Vuelve **una sola vez** al cliente (`add_header` a nivel `server`; los servicios no lo devuelven). Cada servicio toma el id (si cumple `^[A-Za-z0-9-]{8,64}$`, o crea uno), lo pone en sus registros, lo reenvía en `ServiceClient` y lo manda a `audit`, que lo guarda en `details.request_id` dentro del hash de la cadena.
- **Registros (RNF-18):** una línea JSON por petición en el gateway y en cada servicio (`ts`, `service`, `level`, `request_id`, `logger`, `msg`, y `method`, `path`, `status`, `ms`), **sin query string**. uvicorn corre con `--no-access-log` y `LOG_FORMAT=json`.
- **Errores en JSON:** `error_page 401 403 404 413 429 502 503` → `{"error":"…"}` con `default_type application/json`.
- `client_max_body_size` es 16k por defecto y 5m solo en las rutas de subida y análisis. `client_body_timeout 10s`.
- **Verificación manual** (evidencia para el informe): `curl --tlsv1.2 --tls-max 1.2 https://localhost/` debe fallar; `curl -I http://localhost/ws` → 301; `curl https://localhost/internal/verify` → 404.

---

## 14. Auditoría — servicio `audit` (riesgo 3)

### 14.1 Escritura
- `POST /internal/events`: valida el token, deduce `service` del token y normaliza `ip` (si no es una IP válida → `null`).
- Toma `pg_advisory_xact_lock(42)`, lee el último `hash` e inserta. *Límite conocido: las escrituras quedan serializadas; a esta escala no importa.*
- `hash = SHA256(prev_hash || json canónico de {ts, service, severity, actor, action, target, ip, details})`, con claves ordenadas, sin espacios y `ensure_ascii=False`. El primer `prev_hash` son 32 bytes en cero.
- `audit_app` no puede `UPDATE`, `DELETE` ni `TRUNCATE`. `GET /api/admin/audit/verify` recorre la cadena; si se rompe, devuelve `{ok:false, broken_at:id}` y registra `audit.chain.broken` (critical).
- `POST /internal/events` acepta un `request_id` opcional (el `X-Request-ID` del gateway; si no cumple `^[A-Za-z0-9-]{8,64}$` → 422) y lo guarda dentro de `details`, así que el hash lo cubre. `audit` agrega el id también a sus propios eventos. Con él, una petición se sigue del gateway a los registros de cada servicio y a la cadena.
- **Nunca** se registran contraseñas, claves de sala, tokens (JWT incluidos), cuerpos de mensajes ni secretos TOTP.

### 14.2 Eventos
| Servicio | info | warning | critical |
|---|---|---|---|
| auth | `user.registered`, `auth.login.ok`, `auth.logout`, `auth.password.changed`, `auth.totp.enrolled`, `user.reactivated`, `user.roles.changed`, `role.created`, `role.permissions.changed`, `role.deleted`, `admin.create`, `key.rotate.auth` | `auth.login.fail`, `auth.login.locked`, `auth.login.suspended`, `auth.login.second_device`, `auth.totp.fail`, `auth.verify.device_mismatch`, `auth.register.ratelimited`, `user.suspended`, `admin.guard.last_admin` | — |
| rooms | `room.created`, `room.updated`, `room.closed`, `room.owner.transferred`, `room.member.joined`, `room.member.left`, `room.member.unbanned`, `room.member.unmuted` | `room.join.fail`, `room.join.ratelimited`, `room.join.full`, `room.join.alias_taken`, `room.join.banned`, `room.limit.reached`, `room.member.kicked`, `room.member.muted`, `room.forbidden` | — |
| chat | `message.deleted`, `key.rotate.chat` | `ws.reject.{origin,handshake,replay,rate,size,forbidden,malformed,membership}`, `ws.muted` | `ws.tamper` |
| media | `file.accepted`, `file.released`, `file.deleted`, `key.rotate.media` | `file.quarantined`, `file.rejected.{type,invalid,size,forbidden,muted}`, `file.download.denied`, `file.integrity.failed`, `clamav.unavailable`, `stego.unavailable` | `file.rejected.malware` |
| stego | `stego.analyzed` (limpia) | `stego.analyzed` (problema, revisión manual o inválida), `stego.ratelimited` | `stego.sanitize.failed` |
| todos | — | `http.reject.origin`, `svc.reject.token` (token ausente o inválido, o llamador fuera de la allowlist), `perm.denied` (falta el permiso) | — |
| audit | — | — | `audit.chain.broken` |

`audit` registra sus propios `svc.reject.token` escribiendo directamente en su BD.

### 14.3 Consulta
El panel del admin global (permiso `audit:read`) pide `GET /api/admin/audit?min_severity=warning&after_id=<último>` cada 10 s (alertas) y la vista completa con `min_severity=info`. En el primer parcial se consulta desde Postman.

**Alertas visibles:** el dashboard cuenta los eventos `warning`/`critical` posteriores al más reciente que existía al abrirlo (o a la última vez que el admin miró la pestaña *Auditoría*) y muestra una insignia en la pestaña y una banda con la acción del último (p. ej. `file.quarantined`). Abrir *Auditoría* lo pone en cero. El contador vive en memoria del navegador (la regla de frontend prohíbe `localStorage`); la fuente de verdad sigue siendo `audit`.

### 14.4 Si `audit` no responde
`AuditClient.emit(..., required=…)` usa un timeout de 2 s y un reintento:
- **`required=True`** (eventos que **otorgan** algo: `user.registered`, `auth.login.ok`, `user.reactivated`, `user.roles.changed`, `role.created`, `role.permissions.changed`, `room.created`, `room.updated`, `room.owner.transferred`, `room.member.joined`, `file.accepted`, `file.released`, `key.rotate.*`): se emite **dentro** de la transacción, antes del commit. Si falla, la operación se revierte y responde 503.
- **Resto** (rechazos, avisos y todo lo que **quita** acceso: logout, suspensión, expulsión, silencio, cierre, borrado): se escribe en stdout con la marca `AUDIT_FALLBACK` y el JSON del evento, y la operación continúa. Una revocación nunca espera a la auditoría.

---

## 15. Manejo de errores
- El cliente siempre recibe mensajes **genéricos** en JSON `{"error": "…"}` ("credenciales inválidas", "sala o clave inválida", "permiso insuficiente", "cuenta suspendida", "ya hay una sesión activa en otro dispositivo", "usuario no disponible", "no puedes entrar a esta sala", "estás silenciado", "archivo no permitido", "archivo retenido para revisión", 404 en descargas negadas). El detalle va a auditoría.
- El login no revela si un usuario existe (hash dummy y el mismo mensaje). El registro sí lo revela con `409`, porque es inevitable; lo limita el tope de 10 registros por IP por hora.
- Excepciones no controladas: handler global → `500 {"error":"error interno"}` + log en stdout sin datos sensibles. FastAPI sin docs ni OpenAPI públicos (`docs_url=None`, `openapi_url=None`).
- Errores de validación: `422 {"error":"datos inválidos"}`, sin repetir la entrada.
- **Fallar cerrado:** secreto ausente → el servicio no arranca; ClamAV, `stego`, BD o `audit` (en otorgamientos) caídos → 503; el `auth_request` del gateway rechaza → 401, y si `auth` no responde → 503.

---

## 16. Pruebas y trazabilidad

### 16.1 Por servicio
- pytest contra **PostgreSQL real** (`deploy/docker-compose.test.yml`, puerto 5433). Cada servicio con BD crea su BD `<svc>_test` con roles reales y migraciones aplicadas; sin mocks de BD. `stego` no tiene BD: sus pruebas usan imágenes sintéticas (`shared.testing.natural_image`, `embed_lsb`).
- Los servicios vecinos (audit, chat, rooms, auth, media, stego) se simulan con `httpx.MockTransport` inyectado en `ServiceClient`. Las pruebas verifican qué se llamó, con qué token y con qué cuerpo.
- Las peticiones del "gateway" en las pruebas se construyen con el token de prueba del gateway y las cabeceras `X-User-*` (`shared.testing.user_headers`).
- Los WebSocket se prueban con el `TestClient` de Starlette dentro de un bloque `with` (un solo event loop).
- `@pytest.mark.clamav` marca los tests que necesitan clamd (`docker compose -f deploy/docker-compose.test.yml --profile clamav up`); se omiten en CI.
- **Frontend:** vitest para `lib/crypto.ts` contra `docs/crypto-vectors.json`.
- **Primer parcial:** la colección `docs/postman/parcial-1.postman_collection.json` recorre el flujo del docente con un test por petición y corre completa en el Runner de Postman contra `https://localhost`.

### 16.2 End-to-end (`e2e/`)
pytest + httpx + `websockets` contra el stack completo vía `https://localhost`, verificando TLS con la CA de mkcert. Crea su admin con `create_admin --password-stdin` (y calcula el TOTP con el secreto que imprime). Cubre lo que cruza servicios:
- **Cuentas:** registro → login → un segundo dispositivo se rechaza; un usuario sin `stego:analyze` → 403, con el rol asignado → 200, sin volver a iniciar sesión; suspensión → 401 en la siguiente petición y el WS se cierra.
- Chat entre dos clientes con *hello* firmado verificado; expulsión → 4411 y reingreso vetado → 403.
- Imagen limpia → publicada y descargable; imagen con LSB → cuarentena y alerta visible en `GET /api/admin/audit`.
- Gateway: `/internal/*` → 404; `X-User-*` enviados por el cliente se ignoran; `http://` → 301.

Se ejecuta en local antes de cada hito.

### 16.3 Riesgo nuevo R16
"Suplantación entre microservicios": un proceso con presencia en la red interna (o un servicio comprometido) invoca endpoints internos o inyecta cabeceras de identidad haciéndose pasar por el gateway u otro servicio. La vulnerabilidad que habría sin tratamiento es que los servicios confíen en cualquier petición de la red interna. Valoración propuesta: **P=3, I=5 → 15 (Alto)**; residual estimado 5 (Medio). Tratamiento: §4.3–4.5 y §13. Recomendación: agregarlo al documento SGSI de la Tarea 2.

### 16.4 Tests mínimos por riesgo
| R | Servicio | Tests |
|---|---|---|
| 01 | rooms | `key_hash` empieza con `$argon2id$`; la clave en claro no aparece en ninguna columna |
| 02 | shared, auth, chat, media | El servicio no arranca sin secretos; `rotate_kek` (auth, media) y `rotate kek/room` (chat) mantienen todo legible; los mensajes en BD y los archivos en disco no contienen el contenido en claro |
| 03 | audit | `audit_app` no puede `UPDATE/DELETE/TRUNCATE`; una alteración hecha con el owner la detecta `verify`; `service` sale del token aunque el payload diga otra cosa |
| 04 | auth | Bloqueo tras 5 fallos; un permiso de admin no vale sin TOTP; código TOTP reusado rechazado; el `sid` cambia al pasar a `full` |
| 05 | auth, rooms, media, stego, audit (+e2e) | Sin el permiso → 403 y `perm.denied`; el registro nunca da `admin` y un cuerpo con `role` → 422; un permiso quitado deja de valer en la siguiente petición; no se puede quitar el último admin; quien no es dueño no administra la sala; el admin global no cambia la clave de una sala ajena |
| 06 | stego, media | PNG con LSB secuencial al 10 % → `revision_manual` y cuarentena; datos después de `IEND` → `problema`; PNG limpio → `limpia`; tras sanitizar, el plano LSB cambia |
| 07 | chat (+e2e) | WS con `Origin` ajeno → 4403; trama alterada → 4400 + auditoría critical; *hello* firmado verificable; vectores; e2e: 301 en http |
| 08 | rooms | Rate limit de ingreso por IP, usuario y sala; clave débil rechazada al crear la sala; el veto se revisa después de la clave |
| 09 | stego, media | Firma que no coincide, más de 5 MB o decompression bomb → `invalida` y rechazo; ClamAV o `stego` caídos → 503; EICAR → rechazo (`clamav`) |
| 10 | chat, stego | Rate de mensajes → 4429; trama mayor a 16 KB → 4413; sin `hello` en 10 s → 4400; más de 10 análisis por minuto → 429 |
| 11 | todos los servicios con BD | `<svc>_app` no puede `CREATE TABLE`/`DROP` ni conectarse a otra BD |
| 12 | media | Firma inválida, vencida, de otro usuario o de alguien que ya no es miembro → 404; archivo en cuarentena no descargable |
| 13 | auth (+e2e) | Login desde otro dispositivo con la sesión viva → 409; el JWT con otra cookie de dispositivo → 401; tras logout o vencimiento, el otro dispositivo entra; el índice único impide dos sesiones `full` |
| 14 | chat | El `from` del payload se ignora; AAD de otra sala → 4400; `seq` repetido → 4408; borrar un mensaje ajeno sin ser dueño → 4403 |
| 15 | rooms | 20 ingresos concurrentes con cupo 5 → exactamente 5 aceptados; el `CHECK` impide superar el máximo; 3 creaciones concurrentes del mismo dueño → 2 salas |
| 16 | shared y cada servicio (+e2e) | Sin token → 401; token de un llamador fuera de la allowlist → 403; cabeceras de identidad sin el token del gateway → ignoradas (401); e2e: `/internal/*` → 404 y cabeceras falsificadas ignoradas |

`docs/trazabilidad-riesgos.md` tiene la tabla `Riesgo | Control | Servicio/Archivo(s) | Test(s) | Estado`. Se actualiza con cada cambio de seguridad (comando `/risk-check`) y se copia al informe final.

### 16.5 CI (`.github/workflows/ci.yml`)
- Job `services`, en matriz `[shared, auth, rooms, chat, media, stego, audit]` con servicio `postgres:17`: `ruff check` (con complejidad ciclomática ≤ 10 por función, RNF-11), `ruff format --check`, `pytest -m "not clamav"` con **cobertura de líneas ≥ 80 %** por servicio (RNF-10), `bandit -q -r <paquete>` y `pip-audit -r requirements.lock`. Cada servicio entra a la matriz con su tarea `*-1`. `main` exige PR con una aprobación y estos jobs en verde; la plantilla de PR (`.github/pull_request_template.md`) trae la lista de verificación de seguridad.
- Job `frontend`: `npm ci`, `npx vitest run`, `npm run build`, `npm audit --audit-level=high`.
- Job `codeql`: análisis estático de CodeQL para Python y JavaScript/TypeScript (inyecciones, flujos de datos no confiables, uso inseguro de APIs).
- Job `secrets`: gitleaks sobre todo el historial del repositorio.
- El e2e no corre en CI (ClamAV es demasiado pesado).

---

## 17. Contexto para Claude Code
| Archivo | Contenido |
|---|---|
| `CLAUDE.md` | (~120 líneas) qué es, la arquitectura en 10 líneas, comandos (compose, pruebas por servicio, e2e, migraciones, `create_admin`, `gen_secrets`), mapa del repo, invariantes de seguridad, enlaces al spec, al plan, a los tickets y a la trazabilidad, y una sección **"Estado actual"** que se actualiza al cerrar cada fase |
| `CLAUDE.local.md` | (gitignored) cada integrante anota sus tickets, sus servicios y sus preferencias |
| `.claude/settings.json` | Allow: pytest, ruff, alembic, `docker compose`, npm/npx, git (lectura). Deny: `Read(deploy/secrets/**)`, `Read(deploy/certs/**)`, `Read(**/.env)`. Registra el hook |
| `.claude/rules/security.md` | Invariantes globales: nunca `ws://` ni HTTP en claro hacia el cliente; nunca secretos en el código; la identidad sale de `X-User-*` verificado por el gateway y la pertenencia a la sala, de `rooms`; la autorización usa permisos, nunca el rol del token; queries parametrizadas; modelos con `extra="forbid"`; errores genéricos y detalle a auditoría; auditar todo rechazo; Argon2id; no registrar datos sensibles; fallar cerrado |
| `.claude/rules/microservices.md` | Nunca leer cabeceras de identidad sin verificar el token del gateway (usar `shared.identity`: `require_user`, `require_perm`); `/internal/*` siempre con `allow(...)` y allowlist; cada servicio toca **solo su BD**; las llamadas entre servicios pasan por `ServiceClient`; un servicio nuevo necesita red, secretos, rol de BD (si tiene datos) y entrada en la allowlist |
| `.claude/rules/backend.md` | `paths: services/**`: FastAPI async, paquete `<svc>_svc`, `create_app(settings, …)` inyectable, migraciones con GRANT explícito, dependencias de `shared` |
| `.claude/rules/frontend.md` | `paths: frontend/**`: TS estricto, nunca `dangerouslySetInnerHTML`, toda la cripto en `lib/crypto.ts`, `CryptoKey` no extraíbles y solo en memoria, nada en `localStorage`/`sessionStorage` (ni el JWT), sin estilos ni scripts inline, sin `StrictMode` (abre y cierra el WS dos veces); los botones se muestran según `/api/auth/me`, pero la autorización es del servidor |
| `.claude/rules/testing.md` | `paths: **/tests/**, e2e/**`: Postgres real, `test_rNN_*` por riesgo, vecinos con `MockTransport`, actualizar la trazabilidad |
| `.claude/commands/risk-check.md` | `/risk-check`: contrasta el diff con R1–R16 y las reglas; señala controles rotos o sin test; actualiza la trazabilidad |
| `.claude/skills/stego-analysis/SKILL.md` | Algoritmos (§12), veredicto, umbrales, calibración y cómo agregar un formato (servicio `stego`) |
| `.claude/skills/crypto-protocol/SKILL.md` | Protocolo (§10–11): handshake firmado, tramas, AAD, códigos, vectores, rotación |
| `.claude/agents/security-auditor.md` | Subagente de solo lectura: revisa cambios contra la Tabla 3, R16, OWASP Top 10 y el modelo de confianza (§4.3) |
| `.claude/hooks/guard.py` | `PreToolUse` sobre `Edit\|Write`: bloquea `ws://`, bloques `PRIVATE KEY` y secretos literales de ≥ 16 caracteres fuera de `tests/`, `docs/`, `.claude/` y `CLAUDE.md`. En Python, multiplataforma |

---

## 18. Fases y reparto

Los tickets de cada persona (Zaith, Andrés y Stefany), uno por archivo, están en `docs/tickets/`. Los planes por subsistema están en `docs/plans/`.

### 18.1 Primer parcial: corte definitivo
**Contenido:** fundaciones (FND), `audit` (AUD), `auth` con RBAC, JWT, sesiones y TOTP (ATH), `stego` (STG), el gateway con las rutas de esos servicios (GW-1), la colección de Postman y el informe. Todo queda como en el sistema final.

**Demo en vivo** (los 5 pasos del docente, desde Postman contra `https://localhost`):
1. Crear un usuario nuevo con `POST /api/auth/register`.
2. El admin inicia sesión (contraseña + TOTP), crea un rol nuevo con sus permisos (`POST /api/admin/roles` con `stego:analyze`) y se lo asigna al usuario (`PUT /api/admin/users/{id}/roles`).
3. El usuario inicia sesión y recibe el JWT.
4. Con ese token, `POST /api/stego/analyze` con cuatro imágenes preparadas: inválida (un archivo que no es imagen), limpia, problema (un ZIP pegado al final) y revisión manual (LSB embebido).
5. Casos negativos: sin token → 401; el mismo usuario antes de recibir el rol → 403; `GET /api/admin/audit` muestra todo lo anterior.

### 18.2 Incremento 2: salas y chat
`rooms` completo, `chat` completo, `auth` con suspensión, cambio de contraseña y latido de sesiones, rutas de salas y WS en el gateway (GW-2) y la SPA con login, registro, *Mis salas*, chat y controles del dueño (FE-1…FE-3).

### 18.3 Incremento 3: imágenes en las salas y cierre
`media` completo, imágenes en el chat y panel del admin global (usuarios, roles, salas, cuarentena y auditoría) (FE-4, FE-5), e2e, calibración con fotos reales, VPS y trazabilidad final.

**Orden de recorte si hay atraso:** chi² DCT de JPEG → análisis RS (quedan chi² + entropía + estructura) → historial → `rotate room` → lista de vetos en la UI → UI de verificación de la cadena → e2e reducido al camino feliz + reglas del gateway.
**No se recorta nunca:** RBAC en el servidor, MFA para permisos de admin, una sesión por cuenta, solo TLS 1.3, *hello* firmado, tokens de servicio, Argon2id, cuarentena, sanitización, cifrado de archivos en reposo, auditoría encadenada, los tests por riesgo ni los documentos de cumplimiento (`docs/requisitos.md`, `docs/cumplimiento-normativo.md`, `docs/justificacion-criptografica.md`).

---

## 19. Configuración (variables no secretas)
| Variable | Servicios | Valor por defecto |
|---|---|---|
| `ALLOWED_ORIGINS` | todos | `https://localhost` (en dev se agrega `https://localhost:5173`) |
| `DB_HOST` / `DB_PORT` | todos los que tienen BD | `db` / `5432` |
| `AUDIT_URL` · `AUTH_URL` · `ROOMS_URL` · `CHAT_URL` · `MEDIA_URL` · `STEGO_URL` | según §4.4 | `http://<servicio>:8000` |
| `CURRENT_KEK_VERSION` | auth, chat, media | `1` |
| `JWT_ISSUER` / `JWT_AUDIENCE` | auth | `auth` / `secure-chat` |
| `SESSION_IDLE_MIN` / `SESSION_ABS_HOURS` / `PREAUTH_MIN` | auth | `30` / `8` / `5` |
| `LOGIN_MAX_FAILS` / `LOGIN_WINDOW_MIN` / `LOGIN_DELAY_BASE` | auth | `5` / `15` / `0.25` |
| `REGISTER_MAX_PER_HOUR` | auth | `10` |
| `JOIN_MAX_FAILS_IP` / `_USER` / `_ROOM` / `JOIN_WINDOW_MIN` | rooms | `5` / `10` / `20` / `10` |
| `MAX_ROOMS_PER_OWNER` | rooms | `2` |
| `CONN_IDLE_MIN` / `HEARTBEAT_INTERVAL_S` / `HANDSHAKE_TIMEOUT_S` | chat | `15` / `30` / `10` |
| `WS_RATE_PER_S` / `WS_BURST` / `WS_MAX_FRAME` | chat | `5` / `10` / `16384` |
| `HISTORY_SIZE` / `SIGNED_URL_TTL_S` | chat | `50` / `60` |
| `UPLOAD_MAX_BYTES` / `UPLOAD_PER_MIN` | media | `5242880` / `5` |
| `CLAMAV_HOST` / `CLAMAV_PORT` / `MEDIA_DIR` | media | `clamav` / `3310` / `/data` |
| `UPLOAD_MAX_BYTES` / `MAX_IMAGE_PIXELS` / `ANALYZE_PER_MIN` | stego | `5242880` / `20000000` / `10` |
| `STEGO_CHI2_P` / `STEGO_RS_RATE` / `STEGO_ENTROPY_TRIGGER` / `STEGO_TIMEOUT_S` | stego | `0.95` / `0.08` / `off` / `10` |
| `LOG_FORMAT` | todos los servicios Python | `json` en los contenedores (la imagen lo fija); vacío en las pruebas |

**Desarrollo del frontend:** `npm run dev` (Vite en `https://localhost:5173` con los certificados de mkcert) con `server.proxy` de `/api`, `/ws` y `/chat-key.json` hacia `https://localhost` (el gateway). Las cookies `__Host-` exigen https también en desarrollo.

---

## 20. Riesgos del proyecto y preguntas abiertas
| Tema | Mitigación / decisión pendiente |
|---|---|
| El alcance crece por incrementos y el docente lo cambia en clase | `Dockerfile` único, librería compartida, compose con anclas YAML. Los planes de rooms, chat, media, frontend y e2e quedan a nivel de tareas; su código detallado se escribe justo antes de cada incremento |
| Fecha de la defensa del parcial y rúbrica desconocidas | Meta de demo: 30 oct. Preguntar en clase; el orden de los tickets deja primero lo que pide el docente |
| El docente construye en clase su propio microservicio de usuarios | Si exige usar el suyo, se adapta `auth` manteniendo los contratos de §8 |
| Postman no envía `Origin` | La colección fija `Origin: https://localhost` (la protección CSRF es para navegadores) |
| Postman podría no conservar la cookie `__Host-device` y entonces `verify` respondería 401 | Probarlo en el primer día de GW-1; si falla, la colección guarda la cookie del login en una variable y la manda en la cabecera `Cookie` |
| El docente puede pedir más formatos | Punto de extensión `FORMATS` (§12.1, §12.6) |
| ClamAV usa ~1.5–3 GB de RAM y tarda minutos en cargar firmas | VPS con ≥ 4 GB; healthcheck de clamd con `start_period`; en ARM usar `clamav/clamav-debian` (variable `CLAMAV_IMAGE`). En el primer parcial no se levanta |
| `jpegio` puede no tener wheels para Python 3.13 | Es *stretch*; JPEG queda cubierto por estructura + recodificación |
| Falsos positivos del estegoanálisis en fotos reales | Calibración con imágenes reales; la cuarentena (no el rechazo) permite que el admin libere |
| R16 no está en el documento SGSI | El equipo lo agrega a las Tablas 1–4 de la Tarea 2 |
| Proveedor del VPS sin definir | Oracle Cloud Free (ARM, 24 GB) o DigitalOcean/AWS; el Compose es idéntico |

---

## 21. Cumplimiento del resumen del docente (revisión 3)

El resumen del docente (`PROYECTO INTEGRADOR - RESUMEN.docx`) repite el enunciado de la Tarea 2 y agrega: las **funcionalidades mínimas esperadas**, los enfoques **Zero Trust, Secure by Design y Shift Left**, las normas **ISO/IEC 27001 y 27034** y el **resultado esperado** (aplicación funcional más documentación que lo evidencie). El análisis completo, con IDs, está en `docs/requisitos.md`.

| Brecha | Cambio |
|---|---|
| B-01 · Normas ISO sin relación con riesgos y mecanismos | `docs/cumplimiento-normativo.md` (declaración de aplicabilidad y marco de 27034); columna ISO en `docs/trazabilidad-riesgos.md` |
| B-02 · Algoritmos y claves sin justificación formal | `docs/justificacion-criptografica.md` |
| B-03 · Zero Trust, Secure by Design y Shift Left sin evidencia propia; sin SAST ni detección de secretos | Matrices en `docs/cumplimiento-normativo.md`; CodeQL y gitleaks en la CI (§16.5) |
| B-04 · Archivos sin cifrar en reposo | Envelope por archivo con `kek_media_v{n}` (§7.4, §9.6–§9.8, §11); sale de "fuera de alcance" |
| B-05 · El panel no permitía modificar salas | Formulario *Editar* (dueño y admin global) |
| B-06 · "Cierre" de sala nombrado "eliminar" | §8.1 y §9.3; botón *Cerrar sala* |
| B-07 · Alertas solo como filas de una tabla | Contador de alertas nuevas en el dashboard (§14.3) |
| B-08 · Sin informe de pruebas | `docs/informe-pruebas.md` en E2E-3 |
| B-09 · "Único dispositivo" por cookie sin declarar | Limitación 7 (§3) |

La pregunta abierta de esta revisión (¿cuentas registradas o alias + dispositivo?) quedó respondida en la clase del 22/10: el docente pidió usuarios con roles (§22).

---

## 22. Revisión 4: clase del 22/10/2026

El docente redujo el primer parcial a **dos microservicios integrados, sin interfaz gráfica, probados con Postman**: uno de usuarios y autenticación con RBAC, cuyo login entrega un JWT, y una API de esteganografía a la que se entra con ese token. Pidió además un informe final y una demostración en vivo. Esto respondió la pregunta abierta de la revisión 3 y llevó a los siguientes cambios. Antes de aplicarlos, el equipo comparó el diseño con una propuesta externa de roles USER/ADMIN y tomó de ella lo que faltaba.

| Cambio | Motivo | Secciones |
|---|---|---|
| Cuentas con registro, roles dinámicos con permisos (RBAC) y JWT RS256 | Pedido del docente para el parcial; "crear un rol nuevo y agregarle propiedades" = permisos del catálogo | §2, §7.1, §8, §9.1 |
| Salas con dueño, membresía persistente, máximo 2 salas activas por persona, cesión de la sala | Decisión del equipo: modelo de Discord | §7.2, §9.2, §9.3 |
| Admin global sin acceso a las conversaciones ni a la clave de salas ajenas | Privacidad de las salas (ISO 27001 A.5.34) | §3 (limitación 8), §9.3 |
| Moderación: expulsión con veto, silencio y borrado de mensajes (propios y, para el dueño, ajenos) | La propuesta de roles mostró que el diseño solo permitía cerrar la sala entera | §9.3–§9.5, §10.2 |
| Una sesión por cuenta (R13 pasa de `rooms` a `auth`); desaparecen la cookie de sala, `verify-session` y el barrido de sesiones | La cuenta reemplaza al alias como identidad | §4.3, §7.1, §9.1, §9.4 |
| Revocación inmediata: el gateway verifica el JWT y su sesión en cada request y pasa los permisos actuales | El spec había descartado JWT por no poder revocarse; con la sesión en el servidor sí se puede | §2, §4.3, §9.1 |
| Nunca sin admin; el registro nunca da `admin`; cuerpos con `extra="forbid"` | Controles de escalamiento de privilegios que faltaban | §8.1, §9.1 |
| Servicio `stego` separado de `media` | La API de esteganografía del parcial se reutiliza en las salas | §4, §9.6, §9.9, §12 |
| Primer parcial como corte definitivo (fundaciones, audit, gateway, auth y stego) | Las fundaciones exigen el gateway y `audit`; así no hay código provisional | §2, §18.1 |
| Fuera de alcance: reportes, edición de mensajes, moderadores, correo, notificaciones y estadísticas | YAGNI; se agregan si el docente los pide | §3 |

### 22.1 Requisitos de la Actividad 3 que se adoptan

El 20/10 una rama paralela del equipo transcribió los requisitos de la Actividad 3 (21 RF, 19 RNF y 39 RS) sobre otro diseño (correo verificado, canal general, 9 formatos). Se revisaron contra esta revisión y se adoptó lo siguiente. El documento original no está en el repositorio, así que los IDs son los de esa transcripción.

| Requisito | Qué se hace | Dónde | Cuándo |
|---|---|---|---|
| RNF-11 · complejidad ≤ 10 | Regla `C90` de ruff; `jpeg.structure` se parte | §16.5; FND-1, STG-1 | Parcial |
| RNF-10 · cobertura ≥ 80 % | `--cov-fail-under=80` en la CI | §16.5; FND-7 | Parcial |
| A3-RS-32 · cambios controlados | Plantilla de PR y protección de `main` (1 aprobación y la CI en verde) | §16.5; FND-1, FND-7 | Parcial |
| RNF-18, RNF-19 · correlación y registros | `X-Request-ID`, registros JSON y `request_id` en la cadena de auditoría | §13, §14.1; FND-4, AUD-2, GW-1 | Parcial |
| RNF-07 · consulta de auditoría con 100 000 eventos ≤ 2 s | Una prueba (el índice `(severity, id)` ya existe) | §14.3; AUD-3 | Parcial |
| A3-RS-36 · reanálisis de lo sanitizado | `residual` estructural sobre la salida de `sanitize` | §12.5; STG-3 | Parcial |
| RNF-14 · orden de mensajes por sala | Candado por sala al difundir: el orden en vivo coincide con el historial | §9.5; CHAT-3 | Incremento 2 |
| RNF-18 · métricas y alerta de consumo | `GET /api/admin/metrics`, `resource.high` (CPU y memoria > 80 % durante 5 min) y pestaña *Estado* | FE-5 | Incremento 3 |
| RNF-15…17 · recuperación | Respaldos cifrados con `age` (diarios, 14 días), restauración y simulacro | E2E-3 | Incremento 3 |
| RNF-08, 09, 13 · usabilidad | Prueba de contraste y Lighthouse ≥ 90 | FE-5 | Incremento 3 |

No se adoptan, salvo que el docente los pida: la prueba de 500 conexiones con 25 contenedores (RNF-06; si hace falta, una versión de 20 a 50 participantes con p95), `bench_formats` (solo hay dos formatos), la prueba con 5 personas y todo lo del otro diseño (correo, Mailpit, canal general, 9 formatos).
