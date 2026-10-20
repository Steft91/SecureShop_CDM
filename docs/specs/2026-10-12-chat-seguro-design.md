# Spec: Salas de Chat Seguras — Diseño de arquitectura (microservicios)

| | |
|---|---|
| **Fecha** | 2026-10-12 · **Revisión 2:** 2026-10-13 (arquitectura de microservicios; reemplaza el monolito modular de la revisión 1) · **Revisión 3:** 2026-10-19 (cuenta de usuario obligatoria; archivos de cualquier categoría con estegoanálisis por formato) · **Revisión 4:** 2026-10-20 (cuenta con correo verificado y alias; canal general y membresías; reanálisis de la versión sanitizada; requisitos de la Actividad 3) |
| **Autores** | Zaith Alejandro Manangón Vinueza, Stefany Maricela Díaz Antun, Andrés Isaias Cedeño Cuenca |
| **Asignatura** | Software Seguro — Proyecto Integrador |
| **Estado** | Aprobado (diseño, rev. 2). Las rev. 3 y 4 incorporan indicaciones del docente, decisiones del equipo y los requisitos de la Actividad 3; los planes de `docs/plans/` ya están actualizados a la rev. 4 (cada archivo del plan abre con una nota de qué cambió) |
| **Fuente de requisitos** | `Documentación/Tarea 2/Actividad2_SGSI_Proyecto_Integrador.md` (enunciado + Tablas 1–4 de riesgos) + indicaciones posteriores del docente (rev. 3) + Actividad 3 (requisitos RF-01…RF-21, RNF-01…RNF-19 y RS-01…RS-39; rev. 4, §21) |
| **Plazo** | ~3 semanas: 13 oct – 2 nov 2026 |

---

## 1. Propósito y criterios de éxito

Construir la aplicación de **salas de chat seguras** del proyecto integrador con **arquitectura de microservicios**, igual que en SecureShop (Tarea 1): un punto de entrada común, un servicio por dominio y una base de datos por servicio. El sistema debe implementar y **demostrar con pruebas** los 15 tratamientos de riesgo de la Tarea 2 (Tabla 3), más los riesgos que introduce este diseño: R16 (arquitectura) y R17 (cuentas de usuario) (§16.3).

**Criterios de éxito (definición de "terminado"):**
1. Un admin con usuario + contraseña + TOTP crea salas con ID único, clave, cupo y tipo (texto / multimedia / ambos).
2. Para participar es **obligatorio crear una cuenta** con correo y contraseña, activarla con el código que llega por correo y elegir un **alias** en el primer ingreso: sin sesión de usuario no se entra a ninguna sala. Todas las cuentas ven el **canal general**; a las salas del admin se unen una sola vez con código y clave. Dos o más usuarios intercambian mensajes cifrados desde sus navegadores. Una cuenta no puede estar activa desde dos dispositivos.
3. Las salas multimedia aceptan imágenes, audio, video, documentos y texto de la lista blanca (§12.1). Un archivo con información oculta (LSB en una imagen o en un WAV, datos anexados o segmentos ocultos en MP3, MP4, PDF o DOCX, caracteres invisibles en un TXT) termina en **cuarentena**, genera una alerta y queda en auditoría. Un archivo limpio se entrega sanitizado, y solo si la versión sanitizada supera una segunda inspección estructural.
4. **Microservicios:** un gateway como único punto de entrada y 5 servicios (`auth`, `rooms`, `chat`, `media`, `audit`). Cada servicio tiene su propia BD, su propia imagen y su propio job de migración, y se despliega por separado (`docker compose up -d --build <servicio>`).
5. Los **17 riesgos** (R1–R15 de la Tarea 2 + R16 y R17) tienen al menos un test automatizado en verde, mapeado en `docs/trazabilidad-riesgos.md`.
6. Todo el sistema corre con un comando en local y en un VPS con certificado válido.
7. Los requisitos no funcionales y de desarrollo seguro de la Actividad 3 tienen su prueba o su evidencia (§21, `docs/evidencias-rnf.md`).

---

## 2. Requisitos del enunciado → decisiones

| Requisito | Decisión |
|---|---|
| Admin autenticado con usuario/contraseña gestiona salas | Servicio `auth`: Argon2id + TOTP obligatorio; primer admin por CLI; sin credenciales por defecto. CRUD de salas en `rooms` |
| Sala: ID único, clave, cupo máximo, tipo | Tabla `rooms` (BD `rooms`): `code` UNIQUE (normalizado a minúsculas), `key_hash` Argon2id, `max_participants`, `mode` |
| Un usuario se conecta desde un único dispositivo | **Cuenta obligatoria** (§9.2). Una sola sesión activa por cuenta y una sola sesión de sala activa por usuario (índices únicos parciales). Ambas quedan atadas a la cookie de dispositivo, y la de sala se verifica en el gateway en **cada** request. **Política: se rechaza el nuevo ingreso desde otro dispositivo**; desde el mismo dispositivo, la sesión nueva reemplaza a la anterior (recarga, cambio de sala) |
| Acceso condicionado a ID + clave | Además de la cuenta: Argon2id, rate limit por usuario/IP/dispositivo/sala, error genérico |
| Confidencialidad, integridad y autenticidad; justificar algoritmos, protocolos y gestión de claves | TLS 1.3 hasta el gateway + **cifrado por conexión en capa de aplicación** entre navegador y `chat` (ECDH P-256 con *hello* firmado → HKDF-SHA256 → AES-256-GCM con AAD) + envelope encryption en reposo (DEK por sala, KEK propia de `chat`) |
| Análisis de archivos y estegoanálisis con alertas, auditoría y política | Servicio `media`: firma → validación → ClamAV → estegoanálisis **por formato** → **cuarentena** / rechazo / sanitización (CDR). Alertas en el servicio `audit` |
| *(Docente)* Microservicios como en SecureShop | Gateway Nginx + 5 servicios por dominio + 5 BD (una por servicio, roles aislados) |
| *(Docente)* Crear una cuenta es obligatorio | Registro con **correo + contraseña** (Argon2id); la cuenta se activa con un código de 6 dígitos enviado por correo; en el primer ingreso se elige un **alias** visible, único y del alfabeto latino. Cuentas de usuario y de admin en tablas, cookies y verificaciones distintas (§7.1, §9.2) |
| *(Equipo, rev. 4)* Canal general y salas por invitación | Toda cuenta entra al **canal general** (sin clave). El admin crea salas y reparte código + clave; unirse crea una **membresía permanente**, así que después se entra sin la clave. La sala persiste hasta que el admin la elimina; la cuenta puede abandonarla (§9.3) |
| *(Actividad 3)* Requisitos funcionales, no funcionales y de seguridad | Correlación, registros JSON, métricas y alertas de consumo; reanálisis de la versión sanitizada; cierre de sesión que corta la sala; cobertura ≥ 80 %, complejidad ≤ 10, detección de secretos y rama protegida; modelo de amenazas; respaldos cifrados; pruebas de carga y de tiempo por formato (§21) |
| *(Docente)* Estegoanálisis para cualquier tipo de archivo (mp3, mp4, documentos, texto, imagen) | Lista blanca de 9 formatos en 5 categorías (§12.1), cada uno con validación, estegoanálisis y sanitización propios |

**Decisiones de contexto tomadas con el equipo:**
- Backend **Python 3.13 + FastAPI** en todos los servicios. Cliente **web SPA (React + TypeScript)**.
- Despliegue: **Docker Compose local** y el **mismo Compose en un VPS** (Let's Encrypt).
- Archivos: **lista blanca de 9 formatos**: imagen (PNG, JPEG, GIF), audio (MP3, WAV), video (MP4), documento (PDF, DOCX) y texto (TXT). El registro `FORMATS` sigue siendo el punto de extensión (§12.1–12.2).
- Comunicación interna: **REST síncrono + un token por servicio** (sin broker).
- BD: **un contenedor PostgreSQL, una base de datos y un par de roles por servicio**.
- Gateway: **Nginx con `auth_request`**. Se descartaron: JWT verificado en cada servicio (no hay revocación inmediata), gateway propio en FastAPI (habría que reimplementar el proxy de WebSocket) y Traefik/Kong (otra herramienta que aprender).
- Modelo criptográfico **B** (cifrado en capa de aplicación sobre TLS). Se descartaron A (solo TLS) y C (E2E puro, que impide el estegoanálisis en el servidor).

---

## 3. Alcance, fuera de alcance y limitaciones conocidas

**Dentro:** todo lo de la sección 2, las cuentas de usuario (registro con correo verificado, alias, login, sesión única por dispositivo), el canal general y las membresías, el panel de admin (salas, cuarentena, auditoría, estado), las pruebas por servicio y e2e, CI, el despliegue local y en el VPS, los respaldos, las pruebas de carga y el contexto para Claude Code.

**Fuera (YAGNI, con el disparador que justificaría agregarlo):**
| Omitido | Agregar cuando |
|---|---|
| Broker de mensajes (RabbitMQ/NATS) | Haya consumidores asíncronos reales o más de una instancia por servicio |
| mTLS / service mesh entre servicios | El sistema salga de una sola máquina o lo exija el docente (ver limitación 3) |
| Varias réplicas por servicio | Haga falta escalar `chat` (requiere pub/sub y un almacén compartido de claves) |
| HashiCorp Vault | Haya más de un servidor o se requiera rotación automática |
| Cifrado en reposo de archivos | Lo pida el docente (los archivos están fuera del webroot y se sirven autenticados) |
| Formatos fuera de la lista blanca (WebP, HEIC, MOV, WebM, FLAC, OGG, XLSX, PPTX, ODT, ZIP…) | El docente los pida (§12.11) |
| Recodificar el video (H.264) al sanitizar | Haya procesamiento en segundo plano: recodificar tarda más que el timeout de una subida. Hoy el MP4 se remultiplexa (§12.9) |
| MFA para cuentas de usuario | Lo pida el docente (el admin sí tiene TOTP obligatorio) |
| Cambio y recuperación de contraseña, cambio de correo o de alias | Lo pida el docente: el correo ya está verificado, así que la recuperación sería un código más (§9.2) |
| Gestión de cuentas y de miembros desde el panel (listar, desactivar, expulsar de una sala) | Haya abuso real o lo pida el docente; hoy el admin corta el acceso eliminando la sala |
| Métricas con Prometheus/Grafana | Haya más de una réplica o un equipo de operación; hoy cada servicio expone sus métricas al panel (§21.1) |
| `.mcp.json` | Usen GitHub Issues/Projects u otra integración externa |

**Limitaciones conocidas (se declaran en el informe):**
1. `chat` ve el texto plano de los mensajes por diseño (para validar, persistir y auditar) y `media` ve los archivos (para analizarlos). La confianza en esos servicios es un supuesto explícito.
2. **Registro abierto:** cualquiera con un correo puede crear cuentas (con rate limit por dispositivo e IP). Quien conoce la clave de una sala puede unirse con **otra cuenta**; para el sistema es otro participante, limitado por el cupo. Cada cuenta, en cambio, está en un solo dispositivo a la vez. Cambiar la clave de una sala no expulsa a quienes ya son miembros: para cortar el acceso, el admin elimina la sala.
3. **Tramo interno en HTTP plano.** TLS termina en el gateway; las llamadas gateway→servicio y servicio→servicio viajan en HTTP dentro de redes Docker internas.
   - Los **mensajes** siguen protegidos en ese tramo por el cifrado de aplicación, y el *hello* firmado impide un MITM activo (§10.1).
   - Los **tokens de servicio y los archivos subidos** viajan en claro dentro de la red interna.
   - Mitigaciones: 4 redes segmentadas, `cap_drop: ALL` (sin `NET_RAW` no hay ARP spoofing ni sniffing desde un contenedor comprometido) y tokens rotables. Mejora futura: mTLS.
4. Una instancia por servicio: las claves de conexión viven en memoria de `chat` y la difusión ocurre dentro de ese proceso.
5. El estegoanálisis combina estadística (PNG, WAV) y estructura (todos los formatos, §12.3). **No detecta:**
   - esquemas adaptativos o LSB-matching (±1) en imágenes y audio, que pueden evadir chi², RS y SPA;
   - MP3Stego, que oculta bits en la paridad de `part2_3_length` mientras codifica (detector *stretch*, §12.5);
   - datos ocultos en coeficientes o vectores de movimiento del video;
   - texto oculto por formato en documentos (blanco sobre blanco, modo de render invisible en PDF).

   La **sanitización** (§12.9) destruye igual la mayoría de esos canales: aleatoriza los LSB (PNG, WAV), recodifica (JPEG, GIF, MP3) y reconstruye los contenedores (MP4, PDF, DOCX, TXT). Sobreviven a ella los payloads dentro del flujo de video (el MP4 se remultiplexa, no se recodifica), los homoglifos de un TXT (se detectan, pero no se corrigen) y el contenido visible de un documento.
6. `audit` es un punto único de falla para las operaciones que otorgan acceso (fallan cerradas con 503 si `audit` no responde, §14.4). Es una decisión deliberada a favor de la trazabilidad.
7. Si alguien cierra el navegador sin cerrar sesión, su cuenta no puede iniciar sesión desde **otro** dispositivo hasta que esa sesión venza por inactividad (≤ 15 min, §9.2). Es el costo de rechazar el nuevo ingreso: así, quien robe una contraseña no puede desplazar al dueño de una sesión activa.
8. **Correo:** si el proveedor SMTP no entrega, nadie puede activar su cuenta (el registro responde igual y queda `mail.unavailable` en auditoría). En local, Mailpit guarda los correos sin enviarlos.

---

## 4. Arquitectura

### 4.1 Vista general
```
Navegador (React SPA + WebCrypto)
   │  HTTPS / WSS — solo TLS 1.3
   ▼
┌─ gateway (Nginx) ── redes: public, apps ──────────────────────────────────────┐
│ TLS · HSTS · CSP · rate limit · SPA estática · /chat-key.json                 │
│ auth_request → auth /internal/verify-admin · auth /internal/verify-user       │
│                rooms /internal/verify-session                                 │
│ Sobrescribe X-Admin-* / X-User-* / X-Session-* · inyecta su X-Service-Token   │
└───┬───────────┬────────────┬─────────────┬──────────────┬─────────────────────┘
    ▼           ▼            ▼             ▼              ▼
  auth        rooms ◄─────► chat ◄─────── media ─────► clamav (red scan)
    │           │            │             │
    └───────────┴─────┬──────┴─────────────┴──── POST /internal/events ──► audit
    │                 ▼  (red data)
    │     PostgreSQL 17: BD auth · rooms · chat · media · audit
    └── SMTP (red mail) ──► mailer (Mailpit; en el VPS reenvía al proveedor)
```

### 4.2 Servicios
| Servicio | Responsabilidad | BD (tablas) | Riesgos |
|---|---|---|---|
| **gateway** | Único punto de entrada: TLS, cabeceras de seguridad, rate limit perimetral, enrutamiento, autenticación delegada (`auth_request`), SPA estática | — | 7, 10, 16 |
| **auth** | **Cuentas de usuario** (registro con correo y código, alias, login, sesión única por cuenta atada al dispositivo, logout que corta la sala, `verify-user`) y **admins** (login, TOTP, sesiones, `verify-admin`, CLI `create_admin`); bloqueo; rotación de su KEK | `auth`: `admins`, `admin_sessions`, `users`, `user_sessions`, `failed_attempts` | 4, 5, 13, 17 |
| **rooms** | CRUD de salas, **canal general**, **membresías**, cookie de dispositivo, unirse (código + clave), entrar (cupo atómico, una sesión de sala activa por usuario), ciclo de vida de sesiones (salida, barrido, fin por logout); `verify-session` | `rooms`: `rooms`, `room_members`, `room_sessions`, `failed_attempts` | 1, 5, 8, 13, 15 |
| **chat** | WebSocket, handshake ECDH firmado, cifrado de tramas, limpieza de caracteres invisibles en los mensajes, mensajes cifrados en reposo (DEK por sala), historial, eventos de archivo, inactividad, heartbeat de sesiones | `chat`: `room_keys`, `messages` | 2, 6, 7, 10, 14 |
| **media** | Subida, firma, validación y estegoanálisis **por formato** (9 formatos, §12), ClamAV, sanitización (CDR) con **reanálisis estructural** de la salida, cuarentena, descarga con URL firmada, panel de cuarentena | `media`: `files` + volumen de archivos | 6, 9, 12 |
| **audit** | Recepción de eventos de todos los servicios, cadena de hash, consulta y verificación para el admin | `audit`: `audit_log` | 3 |

Cada servicio es un proyecto Python independiente (`services/<svc>/`, paquete `<svc>_svc`) que comparte una librería común (`services/shared/`, paquete `shared`) y una única plantilla de `Dockerfile` (argumento `SERVICE`). Todos exponen además `GET /api/admin/metrics` (§21.1). El contenedor `mailer` (Mailpit) no es un servicio propio: solo recibe el SMTP de auth.

### 4.3 Modelo de confianza
1. **Autenticación centralizada en el gateway.** Antes de enrutar, Nginx hace un `auth_request`:
   - rutas de admin → `auth /internal/verify-admin` → `X-Admin-Id`, `X-Admin-User`;
   - salas de la cuenta (listar, unirse, entrar, abandonar) → `auth /internal/verify-user` → `X-User-Id`, `X-User-Name` (alias);
   - rutas de sesión de sala → `rooms /internal/verify-session` → `X-Session-Id`, `X-Room-Id`, `X-User-Id`, `X-Alias`, `X-Room-Mode`.

   Si responde 2xx, el gateway copia esa identidad a la petición hacia el servicio. **Toda cabecera de identidad que mande el cliente se sobrescribe o se vacía** en todas las rutas.
2. **Autorización en cada servicio.** El servicio decide si esa identidad puede hacer la operación: rol de admin, cuenta de usuario, pertenencia a la sala, modo de la sala.
3. **Autenticación servicio a servicio (R16).**
   - Cada llamador (gateway, auth, rooms, chat, media) tiene un token aleatorio de 256 bits y lo envía en `X-Service-Token`.
   - El receptor guarda **solo el SHA-256** de los tokens de quienes pueden llamarlo, así que un servicio comprometido no puede usar lo que tiene montado para hacerse pasar por otro.
   - **Todas** las rutas de un servicio exigen un token válido; solo `/health` está exento (lo usa el healthcheck de Docker).
   - Rutas públicas: el llamador debe ser `gateway`. Rutas `/internal/*`: el llamador debe estar en la allowlist de esa ruta.
   - Las cabeceras de identidad solo se leen si el llamador es `gateway`.
4. **Allowlist de llamadores:**
   | Servicio | Acepta llamadas de |
   |---|---|
   | auth | gateway |
   | rooms | gateway, chat, auth |
   | chat | gateway, rooms, media |
   | media | gateway |
   | audit | gateway, auth, rooms, chat, media |
5. **Red:** los servicios no publican puertos y el gateway nunca enruta `/internal/*`.
6. **Claves aisladas:** `kek_auth` (TOTP) solo en `auth`; `kek_chat` (DEK de salas) y `chat_sign_key` solo en `chat`; `url_signing_key` solo en `chat` (firma) y `media` (verifica).

### 4.4 Comunicación interna (REST síncrono, timeout 3 s)
| Llamador → receptor | Endpoint | Cuándo | Si el receptor no responde |
|---|---|---|---|
| gateway → auth | `GET /internal/verify-admin` | cada `/api/admin/*` | 401 al cliente |
| gateway → auth | `GET /internal/verify-user` | cada `/api/rooms`, `/api/rooms/join`, `/api/rooms/{id}/enter` y `/api/rooms/{id}/membership` | 401 al cliente |
| gateway → rooms | `GET /internal/verify-session` | cada `/api/rooms/leave`, `/api/media/*`, `/ws` | 401 al cliente |
| auth → rooms | `POST /internal/users/{user_id}/sessions/end` | logout de la cuenta | La cuenta igual se cierra; queda `user.logout.partial` y la SPA ya llamó a `leave` |
| auth → mailer | SMTP :1025 | registro y reenvío de código | El registro responde igual; queda `mail.unavailable` |
| rooms → chat | `POST /internal/sessions/{id}/kick` | salida, barrido, sala eliminada | Se registra y se continúa: la sesión ya terminó en `rooms` y el heartbeat la reconcilia |
| chat → rooms | `POST /internal/sessions/{id}/end` | cierre limpio, violación, inactividad | Se registra; el barrido de `rooms` la termina tras el período de gracia |
| chat → rooms | `POST /internal/sessions/heartbeat` | cada 30 s con las sesiones conectadas | Se reintenta en el siguiente ciclo |
| media → chat | `POST /internal/rooms/{room_id}/files` | archivo aceptado o liberado | 503 al que subió el archivo; el archivo queda huérfano e inaccesible (§9.7) |
| auth, rooms, chat, media → audit | `POST /internal/events` | cada evento auditable | §14.4 (fallo cerrado para otorgamientos) |
| media → clamav | clamd INSTREAM :3310 | cada subida | 503 (fallo cerrado) |

### 4.5 Redes y endurecimiento de contenedores
| Red | `internal` | Miembros | Para qué |
|---|---|---|---|
| `public` | no | gateway | Publicar 80/443 |
| `apps` | sí | gateway, auth, rooms, chat, media, audit | Tráfico HTTP entre gateway y servicios y entre servicios |
| `data` | sí | db, los 5 servicios, los 5 jobs de migración | Acceso a PostgreSQL (el gateway **no** llega a la BD) |
| `scan` | sí | media, clamav | Solo `media` llega a ClamAV |
| `clamav-egress` | no | clamav | Actualización de firmas (freshclam) |
| `mail` | sí | auth, mailer | Solo auth envía correo, y solo al `mailer` |
| `mail-egress` | no | mailer (solo en el VPS, `docker-compose.vps.yml`) | Reenvío al proveedor SMTP; auth nunca sale a internet |

Servicios Python: usuario no-root (uid 10001), `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, `read_only: true` con `tmpfs: /tmp`, `restart: unless-stopped` y límites de recursos (`mem_limit: 512m`, `cpus: 1.0`; el monitor de §21.1 mide contra ellos). `media` monta además el volumen `media_data` en `/data`, lleva ffmpeg en su imagen y su `tmpfs` de `/tmp` tiene 256 MB para los temporales del análisis y la sanitización.

### 4.6 Límites de escala
Una réplica por servicio. Escalar `chat` exige mover la difusión a pub/sub (Redis/NATS) y enrutar las conexiones por sesión. Las demás piezas (`auth`, `rooms`, `media`, `audit`) no tienen estado en memoria salvo cachés triviales.

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
│   │       ├── identity.py          dependencias require_gateway / require_admin / require_user / require_session
│   │       ├── text.py              detección y limpieza de caracteres invisibles (TXT en media, mensajes en chat)
│   │       ├── audit_client.py      emisión de eventos con fallback a stdout
│   │       ├── observability.py     id de correlación, registros JSON, métricas, alerta de consumo
│   │       ├── web.py               create_base_app: errores JSON, /health, Origin/CSRF
│   │       └── testing.py           utilidades de prueba (BD de prueba, migraciones, clientes)
│   ├── auth/    auth_svc/  migrations/  tests/  pyproject.toml  requirements.lock  alembic.ini
│   ├── rooms/   rooms_svc/ …
│   ├── chat/    chat_svc/  …
│   ├── media/   media_svc/ (formats/: un módulo por formato) … (tools/stego_lab.py)
│   └── audit/   audit_svc/ …
├── gateway/
│   ├── Dockerfile                   build multi-stage de la SPA + nginx
│   ├── nginx.conf
│   ├── snippets/                    proxy-base.conf, public.conf, admin.conf, user.conf, session.conf, subrequest.conf
│   └── tests/                       prueba de enrutamiento con servicios falsos (run.sh, check_routes.py)
├── frontend/                        Vite + React + TS (src/pages, src/lib)
├── e2e/                             pytest contra el stack completo vía https://localhost
├── perf/                            carga.py y docker-compose.perf.yml (RNF-01, RNF-02, RNF-06)
├── deploy/
│   ├── docker-compose.yml
│   ├── docker-compose.vps.yml       diferencias del VPS (reenvío de correo)
│   ├── docker-compose.test.yml      Postgres (y ClamAV opcional) para las pruebas por servicio
│   ├── backup.sh  restore.sh        respaldo cifrado con age y restauración (RNF-16)
│   ├── postgres/init.sh             crea BDs y roles leyendo /run/secrets
│   ├── gen_secrets.py               genera deploy/secrets/* y deploy/public/chat-key.json
│   ├── secrets/   (gitignored)
│   ├── public/    (gitignored)      chat-key.json (clave pública, se monta en el gateway)
│   └── certs/     (gitignored)      certificados (mkcert en local, Let's Encrypt en el VPS)
├── docs/
│   ├── specs/  plans/
│   ├── crypto-vectors.json          vectores compartidos Python ↔ TypeScript
│   ├── trazabilidad-riesgos.md      riesgo → control → control ISO 27001 → servicio/archivo → test → estado
│   ├── modelo-amenazas.md           STRIDE por componente (RS-30)
│   ├── evidencias-rnf.md            RNF-01…RNF-19: medición y evidencia
│   └── despliegue-vps.md
├── .github/                         ci.yml y pull_request_template.md (RS-37)
├── .gitleaks.toml                   detección de secretos en la CI (RS-32)
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
| Contraseñas | `argon2-cffi` (Argon2id, RFC 9106: t=3, m=64 MiB, p=4) | Riesgos 1, 4 y 17 |
| Cripto | `cryptography` (ECDH y ECDSA P-256, HKDF, AESGCM) | Primitivas auditadas, interoperan con WebCrypto |
| MFA | `pyotp` + `qrcode` | TOTP RFC 6238 |
| Imágenes y WAV | Pillow, numpy, scipy (`chi2.sf`); `wave` de la librería estándar | Decodificación y estadística (solo `media`) |
| MP3 y MP4 | ffmpeg / ffprobe (paquete de Debian en la imagen de `media`); `mutagen` para etiquetas ID3/APE | Validación, parseo de tramas y cajas, recodificación y remultiplexado |
| PDF y DOCX | `pikepdf` (qpdf); `lxml` con parser endurecido (sin DTD, entidades ni red) | Parseo de objetos y partes, reescritura limpia |
| Antimalware | ClamAV (`clamav/clamav`, o `clamav/clamav-debian` en ARM) vía INSTREAM, con `StreamMaxLength 30M` (cubre los 25 MB del video) | Riesgo 9 |
| Gateway | Nginx 1.27 (`auth_request`) | TLS 1.3, rate limit, autenticación delegada |
| Front | React 19, Vite, TypeScript estricto, react-router, CSS plano | Sin librería de UI: menos superficie |
| Cripto en el front | WebCrypto (`crypto.subtle`) | Nativo, claves no extraíbles |
| Pruebas | pytest, httpx, pytest-timeout; vitest; e2e con httpx + `websockets` | |
| Correo | Mailpit `v1.21.8` (contenedor `mailer`): en local guarda los correos; en el VPS los reenvía al proveedor SMTP | auth no sale a internet |
| Respaldos | `pg_dumpall` + tar del volumen, cifrados con `age` | RNF-16 |
| CI | GitHub Actions: ruff (con complejidad ≤ 10), pytest con `pytest-cov` (≥ 80 %), bandit, pip-audit, gitleaks, npm audit, `nginx -t` y la prueba de enrutamiento del gateway | RNF-10, RNF-11, RS-32 |

Las versiones exactas quedan en `services/<svc>/requirements.lock` (generado en el plan) y en `frontend/package-lock.json`.

---

## 7. Datos por servicio

Un contenedor PostgreSQL con 5 bases de datos. **No hay claves foráneas entre bases**: las referencias cruzadas (`room_id`, `session_id`, `admin_id`) son UUID opacos validados por el servicio dueño.

### 7.1 BD `auth`
```sql
CREATE TABLE admins (
  id             uuid PRIMARY KEY,
  username       text UNIQUE NOT NULL CHECK (username ~ '^[a-z0-9_.-]{3,32}$'),
  password_hash  text NOT NULL,                 -- $argon2id$...
  totp_secret    bytea NOT NULL,                -- nonce||ct, AES-GCM con kek_auth, AAD "totp|<id>"
  totp_last_step bigint NOT NULL DEFAULT 0,     -- anti-reuso del código TOTP
  kek_version    int NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE admin_sessions (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id   uuid NOT NULL REFERENCES admins(id),
  token_hash bytea UNIQUE NOT NULL,             -- SHA-256 del token
  stage      text NOT NULL CHECK (stage IN ('preauth','full')),
  last_seen  timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,              -- preauth: 5 min; full: 8 h absolutas
  ended_at   timestamptz
);
CREATE TABLE users (                            -- cuentas de usuario final (nunca admins)
  id                uuid PRIMARY KEY,
  email             text UNIQUE NOT NULL CHECK (email = lower(email) AND length(email) <= 254),
  password_hash     text NOT NULL,                -- $argon2id$...
  verified_at       timestamptz,                  -- NULL hasta ingresar el código del correo
  verify_code_hash  bytea,                        -- HMAC-SHA256(kek_auth, "verify|<id>|<código>")
  verify_expires_at timestamptz,                  -- 15 min
  verify_attempts   int NOT NULL DEFAULT 0,       -- 5 fallos invalidan el código
  alias             text,                         -- visible en el chat; se elige en el primer ingreso
  alias_key         text UNIQUE,                  -- forma canónica: sin tildes, mayúsculas ni separadores
  created_at        timestamptz NOT NULL DEFAULT now(),
  CHECK ((alias IS NULL) = (alias_key IS NULL))
);
CREATE TABLE user_sessions (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users(id),
  token_hash  bytea UNIQUE NOT NULL,            -- SHA-256 del token
  device_hash bytea NOT NULL,                   -- SHA-256 de la cookie de dispositivo
  last_seen   timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz NOT NULL,             -- 12 h absolutas
  ended_at    timestamptz,
  end_reason  text                              -- 'logout' | 'replaced' | 'expired'
);
CREATE UNIQUE INDEX one_active_session_per_user
  ON user_sessions (user_id) WHERE ended_at IS NULL;                         -- riesgo 13
CREATE TABLE failed_attempts (
  id         bigserial PRIMARY KEY,
  key        text NOT NULL,                     -- 'admin:<u>' | 'admin_ip:<ip>' | 'user:<correo>' | 'user_ip:<ip>'
                                                -- | 'register_device:<hash>' | 'register_ip:<ip>'
                                                -- | 'verify_ip:<ip>' | 'resend:<correo>'
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON failed_attempts (key, created_at);
```
- Admins y usuarios llevan contadores separados: los fallos de un aula entera detrás de una misma IP no bloquean el login del admin.
- Las claves `register_*` y `resend:*` cuentan **cada** intento, exitoso o no (§9.2).
- El correo es el único dato personal que se guarda; en la auditoría, las cuentas aparecen como `user:<id>` y el correo solo como `target` de un intento fallido.

### 7.2 BD `rooms`
```sql
CREATE TABLE rooms (
  id                   uuid PRIMARY KEY,
  code                 text UNIQUE NOT NULL CHECK (code ~ '^[a-z0-9_-]{3,32}$'),  -- normalizado a minúsculas
  key_hash             text,                    -- $argon2id$...; NULL solo en el canal general
  mode                 text NOT NULL CHECK (mode IN ('text','media','both')),
  max_participants     int  NOT NULL CHECK (max_participants BETWEEN 2 AND 50),
  current_participants int  NOT NULL DEFAULT 0, -- conectados ahora (no miembros)
  active               boolean NOT NULL DEFAULT true,
  is_general           boolean NOT NULL DEFAULT false,
  created_by           uuid,                    -- id del admin (vive en la BD auth); NULL en el general
  created_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (current_participants BETWEEN 0 AND max_participants),   -- respaldo del riesgo 15
  CHECK (is_general OR (key_hash IS NOT NULL AND created_by IS NOT NULL)),
  CHECK (NOT is_general OR active)              -- el general no se elimina
);
CREATE UNIQUE INDEX one_general_room ON rooms (is_general) WHERE is_general;
-- la migración inserta el canal general: code 'general', modo 'both', cupo 50, sin clave
CREATE TABLE room_members (                     -- membresía permanente: se crea al unirse con código + clave
  room_id   uuid NOT NULL REFERENCES rooms(id),
  user_id   uuid NOT NULL,                      -- cuenta (vive en la BD auth)
  joined_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (room_id, user_id)
);
CREATE TABLE room_sessions (
  id          uuid PRIMARY KEY,
  room_id     uuid NOT NULL REFERENCES rooms(id),
  user_id     uuid NOT NULL,                    -- cuenta (vive en la BD auth)
  alias       text NOT NULL,                    -- copia del alias de la cuenta al entrar
  device_hash bytea NOT NULL,                   -- SHA-256 de la cookie de dispositivo
  token_hash  bytea UNIQUE NOT NULL,
  last_seen   timestamptz NOT NULL DEFAULT now(),   -- creación o último heartbeat de chat
  created_at  timestamptz NOT NULL DEFAULT now(),
  ended_at    timestamptz,
  end_reason  text                              -- leave | closed | violation | idle | grace | replaced
                                                -- | room_deleted | abandon | logout
);
CREATE UNIQUE INDEX one_active_session_per_user
  ON room_sessions (user_id) WHERE ended_at IS NULL;      -- riesgo 13: una sala a la vez, desde un dispositivo
CREATE TABLE failed_attempts (
  id         bigserial PRIMARY KEY,
  key        text NOT NULL,                     -- 'user:<id>' | 'ip:<ip>' | 'device:<hash>' | 'room:<id>'
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON failed_attempts (key, created_at);
```

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
  session_id uuid NOT NULL,
  kind       text NOT NULL CHECK (kind IN ('text','file')),
  file_id    uuid,                              -- solo kind='file' (identificador opaco)
  payload    bytea NOT NULL,                    -- nonce||ct con la DEK, AAD "msg|<room_id>|<session_id>"
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((kind = 'file') = (file_id IS NOT NULL))
);
CREATE INDEX ON messages (room_id, id);
CREATE INDEX ON messages (file_id) WHERE file_id IS NOT NULL;
```
Payload en claro antes de cifrar: `{"from","body","ts"}` (texto) o `{"from","file_id","mime","size","ts"}` (archivo).

### 7.4 BD `media`
```sql
CREATE TABLE files (
  id           uuid PRIMARY KEY,
  room_id      uuid NOT NULL,
  session_id   uuid NOT NULL,
  user_id      uuid NOT NULL,                   -- cuenta que subió el archivo
  alias        text NOT NULL,
  storage_name text UNIQUE,                     -- uuid4 hex sin extensión; NULL si fue rechazado
  mime         text NOT NULL,                   -- MIME de la lista blanca (§12.1); 'unknown' si ninguna firma coincidió
  size         int  NOT NULL,
  sha256       bytea NOT NULL,                  -- del archivo original
  clean_sha256 bytea,                           -- de los bytes sanitizados que se publican (§9.6, paso 5)
  status       text NOT NULL CHECK (status IN ('clean','quarantined','rejected','released','deleted')),
  verdict      jsonb NOT NULL,                  -- formato, motivos y métricas del análisis (§12.2)
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON files (session_id, created_at);
CREATE INDEX ON files (clean_sha256) WHERE clean_sha256 IS NOT NULL;
```

### 7.5 BD `audit`
```sql
CREATE TABLE audit_log (
  id        bigserial PRIMARY KEY,
  ts        timestamptz NOT NULL,
  service   text NOT NULL,                      -- deducido del token del llamador, nunca del payload
  severity  text NOT NULL CHECK (severity IN ('info','warning','critical')),
  actor     text NOT NULL,                      -- 'admin:<u>' | 'user:<id>' | 'session:<id>' | 'ip:<ip>' | 'system'
  action    text NOT NULL,
  target    text,
  ip        inet,
  details   jsonb NOT NULL DEFAULT '{}',          -- incluye request_id (§21.1): queda dentro del hash
  prev_hash bytea NOT NULL,
  hash      bytea NOT NULL
);
```

### 7.6 Roles (riesgos 11 y 16)
Para cada servicio `<svc>` ∈ {auth, rooms, chat, media, audit}:

| Rol | Permisos | Uso |
|---|---|---|
| `<svc>_owner` | Dueño de la BD `<svc>`; DDL. `ALTER ROLE … SET log_statement = 'all'` | Solo el job `<svc>-migrate` (Alembic) |
| `<svc>_app` | `CONNECT` **solo** a la BD `<svc>`; DML sobre sus tablas (en `audit_log`: solo `SELECT, INSERT`); `USAGE` en sus secuencias. Sin DDL ni `TRUNCATE` | El servicio en ejecución |

- `deploy/postgres/init.sh` (se ejecuta una vez como superusuario) crea los 10 roles con contraseñas leídas de `/run/secrets` y las 5 BD. Luego ejecuta `REVOKE ALL ON DATABASE <svc> FROM PUBLIC` y `GRANT CONNECT ON DATABASE <svc> TO <svc>_app`.
- La primera migración de cada servicio hace `REVOKE ALL ON SCHEMA public FROM PUBLIC`, `GRANT USAGE ON SCHEMA public TO <svc>_app` y los `GRANT` explícitos por tabla.

---

## 8. Contratos HTTP

### 8.1 API pública (vía gateway)
| Método | Ruta | Servicio | Identidad | Descripción |
|---|---|---|---|---|
| POST | `/api/auth/login` | auth | — | Admin: `{username, password}` → cookie `__Host-admin` (etapa `preauth`) |
| POST | `/api/auth/totp` | auth | cookie preauth | Admin: `{code}` → sesión `full`; el token se rota |
| POST | `/api/auth/logout` | auth | cookie admin | Cierra la sesión del admin |
| GET | `/api/auth/me` | auth | cookie admin | `{username}` |
| GET | `/api/device` | rooms | — | Pone la cookie `__Host-device` si no existe (204) |
| POST | `/api/users/register` | auth | cookie de dispositivo | `{email, password}` → **siempre** 202 (no revela si el correo tiene cuenta); envía el código. No abre sesión (§9.2) |
| POST | `/api/users/verify` | auth | — | `{email, code}` → 204 · 400 "código inválido o vencido" |
| POST | `/api/users/verify/resend` | auth | — | `{email}` → 202 (nuevo código si la cuenta está pendiente) |
| POST | `/api/users/login` | auth | cookie de dispositivo | `{email, password}` → cookie `__Host-user` + `{alias}` (`null` si falta elegirlo) · 403 cuenta sin verificar · 409 si la cuenta tiene una sesión activa en otro dispositivo |
| POST | `/api/users/alias` | auth | cookie de usuario | `{alias}` → `{alias}`; una sola vez · 409 ya elegido o no disponible |
| POST | `/api/users/logout` | auth | cookie de usuario | Cierra la sesión de usuario y la de sala (204) |
| GET | `/api/users/me` | auth | cookie de usuario | `{email, alias}`; desliza la inactividad (la SPA lo llama cada 5 min) |
| GET | `/api/rooms` | rooms | usuario (`verify-user`) | `[{id, code, mode, general, connected, max}]`: el general y las salas de la cuenta |
| POST | `/api/rooms/join` | rooms | usuario | `{code, key}` → `{room: {id, code, mode}}`: crea la membresía (idempotente) |
| POST | `/api/rooms/{id}/enter` | rooms | usuario | → cookie `__Host-room` + `{session_id, room}`. Solo miembros (o el general); el alias es el de la cuenta |
| DELETE | `/api/rooms/{id}/membership` | rooms | usuario | Abandona la sala (204); el general no se abandona (409) |
| POST | `/api/rooms/leave` | rooms | sesión | Termina la sesión (204) |
| GET / POST | `/api/admin/rooms` | rooms | admin | Listar / crear `{code, key, max_participants, mode}` |
| PATCH | `/api/admin/rooms/{id}` | rooms | admin | Cambiar `key`, `max_participants` (≥ participantes actuales) o `mode` |
| DELETE | `/api/admin/rooms/{id}` | rooms | admin | `active=false`; termina y expulsa sus sesiones (el general → 409) |
| POST | `/api/media/files` | media | sesión | multipart `file` → `{file_id, status}` |
| GET | `/api/media/files/{id}?exp=&sig=` | media | sesión | Descarga de un archivo `clean` o `released` |
| GET | `/api/admin/quarantine` | media | admin | Archivos en cuarentena con su `verdict` |
| POST | `/api/admin/quarantine/{id}/release` | media | admin | Sanitiza, publica en la sala y marca `released` |
| DELETE | `/api/admin/quarantine/{id}` | media | admin | Borra el archivo físico y marca `deleted` |
| GET | `/api/admin/audit?min_severity=&after_id=&limit=` | audit | admin | Eventos con `id > after_id`, del más nuevo al más viejo |
| GET | `/api/admin/audit/verify` | audit | admin | Recorre la cadena → `{ok, broken_at}` |
| WS | `/ws` | chat | sesión | Canal de chat (§9.5, §10) |
| GET | `/chat-key.json` | gateway (estático) | — | `{"kid": "v1", "pub": "<b64url 65 B>"}` clave pública ECDSA del chat |
| GET | `/api/admin/metrics/{svc}` | cada servicio | admin | Métricas del servicio (§21.1) |
| GET | `/api/status` | chat (`/health`) | — | `{"status":"ok"}` para el monitor de disponibilidad (RNF-04) |

**Cookies:** `__Host-admin`, `__Host-user`, `__Host-room` y `__Host-device`, todas con prefijo `__Host-` (Secure, Path=/, sin Domain), `HttpOnly` y `SameSite=Strict`. Ningún token es accesible desde JavaScript. `__Host-device` es persistente (1 año) para reconocer el mismo dispositivo; las demás son de sesión del navegador.

**CSRF:** además de SameSite=Strict, la dependencia `require_gateway` de la librería compartida rechaza con 403 (y audita `http.reject.origin`) los `POST/PATCH/DELETE` públicos cuyo `Origin` no esté en `ALLOWED_ORIGINS`.

**Validaciones de entrada:**
- `code`: se normaliza a minúsculas; `^[a-z0-9_-]{3,32}$`.
- Clave de sala: ≥ 12 caracteres, al menos 3 de 4 clases (minúsculas, mayúsculas, dígitos, símbolos) y distinta del `code`.
- `username` del admin: se normaliza a minúsculas; `^[a-z0-9_.-]{3,32}$`.
- Correo: se normaliza a minúsculas; ASCII, ≤ 254 caracteres, `local@dominio.tld`.
- Alias: NFC, 3–24 caracteres del alfabeto latino (con tildes y ñ), dígitos, espacios simples, `_`, `.` y `-`. Único por su forma canónica (sin tildes, mayúsculas ni separadores: `Ana.Pérez` = `ana perez`); sin cirílico ni griego no hay homoglifos. Se rechazan los reservados (`admin`, `administrador`, `root`, `system`, `sistema`, `soporte`, `moderador`, `general`).
- Contraseñas de admin y de usuario: misma política que la clave de sala, distintas del `username` (admin) o del correo y su parte local (usuario).
- Mensaje: primero se eliminan los caracteres invisibles (§12.8); luego 1–2000 caracteres y sin caracteres de control salvo `\n` y `\t`.
- `max_participants`: 2–50.
- Archivo: formato, tamaño y contenido según §12.1.

### 8.2 API interna (nunca enrutada por el gateway)
| Servicio | Método y ruta | Llamadores | Contrato |
|---|---|---|---|
| auth | `GET /internal/verify-admin` | gateway | Lee la cookie `__Host-admin` (sesión `full` vigente; desliza `last_seen`) → `204` + `X-Admin-Id`, `X-Admin-User` · `401` |
| auth | `GET /internal/verify-user` | gateway | Lee `__Host-user` + `__Host-device` (sesión vigente y del mismo dispositivo; desliza `last_seen`) → `204` + `X-User-Id`, `X-User-Name` (alias *percent-encoded*) · `401` · `403` si falta elegir el alias |
| rooms | `GET /internal/verify-session` | gateway | Lee `__Host-room` + `__Host-device` → `204` + `X-Session-Id`, `X-Room-Id`, `X-User-Id`, `X-Alias` (UTF-8 *percent-encoded*), `X-Room-Mode` · `401` |
| rooms | `POST /internal/sessions/{id}/end` | chat | `{reason}` → termina la sesión (idempotente) y libera cupo · `204` |
| rooms | `POST /internal/users/{user_id}/sessions/end` | auth | Termina la sesión de sala de la cuenta (`reason='logout'`) y pide `kick(4401)` · `204` |
| rooms | `POST /internal/sessions/heartbeat` | chat | `{session_ids: [...]}` → `last_seen = now()` en las activas · `200 {ended: [...]}` con las de la lista que ya no están activas |
| chat | `POST /internal/sessions/{id}/kick` | rooms | `{code}` → cierra el WS si existe y avisa `leave` a la sala · `204` |
| chat | `POST /internal/rooms/{room_id}/files` | media | `{file_id, session_id, alias, mime, size}` → guarda el evento cifrado y lo difunde · `204` |
| audit | `POST /internal/events` | auth, rooms, chat, media | `{severity, action, actor, target?, ip?, details?}` → `201 {id}`; `service` sale del token |

Todos los servicios exponen además `GET /health` sin token (`{"status": "ok"}` si su BD responde), usado solo por el healthcheck de Docker.

---

## 9. Flujos

### 9.1 Admin (riesgos 4 y 5)
1. `POST /api/auth/login`. Si hay ≥ 5 fallos en 15 min con clave `admin:<u>` **o** `admin_ip:<ip>` → `429` + `Retry-After` y auditoría `admin.login.locked`.
2. Argon2id verify. Si el usuario no existe se verifica contra un hash dummy, para no revelar por tiempo qué usuarios existen.
3. Si falla: se registra el fallo, retraso progresivo `min(0.25·2^(n−1), 4)` s y `401 "credenciales inválidas"`.
4. Si es correcto: `admin_sessions(stage='preauth', expires_at=now+5min)` y cookie `__Host-admin`.
5. `POST /api/auth/totp`: aplica el mismo bloqueo; descifra el secreto con `kek_auth` y verifica con `pyotp` (ventana ±1), rechazando si `step <= totp_last_step`.
   - Si falla → se registra el fallo.
   - Si es válido → `stage='full'`, **token nuevo** (contra la fijación de sesión), 30 min de inactividad y 8 h absolutas. Auditoría `admin.login.ok`.
6. En cada `/api/admin/*`, el gateway llama a `verify-admin`. El servicio de destino aplica `require_admin`, que exige que el llamador sea `gateway` y que venga `X-Admin-Id`.
7. Bootstrap: `docker compose exec auth python -m auth_svc.create_admin <usuario>` pide la contraseña (o la lee con `--password-stdin`) e imprime el QR de TOTP y el secreto.

### 9.2 Cuenta de usuario (riesgos 13 y 17)
Crear una cuenta es **obligatorio**: sin sesión de usuario, ninguna ruta de salas pasa el gateway. Todo el flujo vive en `auth`, separado del de admin.

1. **Registro:** `POST /api/users/register {email, password}`. Exige la cookie de dispositivo.
   1. Rate limit: ≥ 3 registros en 60 min por `register_device` o ≥ 30 por `register_ip` → `429` y auditoría `user.register.ratelimited`. Cuenta cada intento, exitoso o no. El tope por IP es alto porque un aula entera puede salir por la misma IP.
   2. Valida el correo (§8.1) y la política de contraseña (distinta del correo y de su parte local). Si falla → `422`.
   3. Argon2id siempre (mismo tiempo en todos los casos) y, en una transacción:
      - correo nuevo → `INSERT` sin verificar, código nuevo y auditoría `user.register` (obligatoria);
      - correo con cuenta **sin verificar** → se renueva con la contraseña nueva y un código nuevo (`user.register.renewed`, obligatoria). Así nadie bloquea un correo ajeno: solo su dueño recibe el código;
      - correo con cuenta **verificada** → no se toca nada; se le envía el aviso "ya tienes una cuenta" (`user.register.existing`).
   4. Responde **siempre** `202 {status, message}`: el registro no revela qué correos tienen cuenta. Si el correo no sale, la respuesta es la misma y se audita `mail.unavailable`. **No abre sesión.**
2. **Código de verificación:** 6 dígitos de `secrets`, guardado como HMAC-SHA256 con la KEK de auth (una copia de la BD no alcanza para probar los 10⁶ valores), 15 minutos de vigencia y 5 intentos; además, ≥ 20 fallos por IP en 15 min → `429`. `POST /api/users/verify {email, code}` → `204` y `user.verify.ok` (obligatoria), o `400 "código inválido o vencido"` y `user.verify.fail`. `POST /api/users/verify/resend {email}` → `202` siempre (≥ 3 por correo y hora → `429`, exista o no la cuenta); si la cuenta está pendiente, el código anterior deja de servir.
3. **Login:** `POST /api/users/login {email, password}`. Exige la cookie de dispositivo.
   1. Bloqueo: ≥ 5 fallos en 15 min con `user:<correo>` **o** ≥ 20 con `user_ip:<ip>` → `429` + `Retry-After` y auditoría `user.login.locked`.
   2. Argon2id verify, con hash dummy si la cuenta no existe. Si falla → registra el fallo, retraso progresivo `min(0.25·2^(n−1), 4)` s, `401 "credenciales inválidas"` y auditoría `user.login.fail`.
   3. Contraseña correcta pero cuenta sin verificar → `403 "cuenta sin verificar: revisa tu correo"` (`user.login.unverified`). Solo lo sabe quien ya probó la contraseña.
   4. **Transacción única (riesgo 13):**
      ```sql
      UPDATE user_sessions SET ended_at = now(), end_reason = 'expired'
       WHERE user_id = :u AND ended_at IS NULL
         AND (expires_at <= now() OR last_seen <= now() - :idle);
      SELECT id, device_hash FROM user_sessions
       WHERE user_id = :u AND ended_at IS NULL FOR UPDATE;
      INSERT INTO user_sessions (...);   -- índice one_active_session_per_user
      ```
      - Si queda una sesión activa desde **otro** dispositivo → rollback, `409 "la cuenta tiene una sesión activa en otro dispositivo"` y auditoría `user.login.device_conflict`.
      - Si es del **mismo** dispositivo → se termina (`end_reason='replaced'`) y se crea la nueva.
      - Si dos logins compiten, el índice único hace fallar al segundo `INSERT` → 409.
      - En la misma transacción se emite `user.login.ok` (obligatorio).
   5. Responde con la cookie `__Host-user` (token de 256 bits; en BD solo su SHA-256) y `{alias}`. La sesión vence a los 15 min de inactividad (`USER_IDLE_MIN`) o a las 12 h (`USER_ABS_HOURS`).
4. **Alias (primer ingreso):** si `alias` es `null`, la SPA pide elegirlo. `POST /api/users/alias {alias}` valida (§8.1), guarda `alias` y `alias_key` (únicos) y audita `user.alias.set` (obligatoria). Se elige una sola vez; un alias tomado o casi igual a otro → `409 "alias no disponible"`. Mientras no haya alias, `verify-user` responde `403` y no se entra a ninguna sala.
5. **Presencia:** mientras está abierta, la SPA llama `GET /api/users/me` cada 5 min; así, la inactividad mide si el dispositivo sigue presente. Si se cierra el navegador sin cerrar sesión, la cuenta queda libre para otro dispositivo en ≤ 15 min (limitación 7, §3).
6. **Logout:** `POST /api/users/logout` → `end_reason='logout'`, borra la cookie y audita `user.logout`. Además, auth pide a rooms `POST /internal/users/{user_id}/sessions/end`, que termina la sesión de sala y cierra el WebSocket (RS-07), aunque la SPA no haya llamado a `leave`. Si rooms no responde, la cuenta igual queda cerrada y se audita `user.logout.partial`.
7. **`verify-user`** (lo usa el gateway en las rutas de salas de la cuenta): busca la sesión por `token_hash` y exige `ended_at IS NULL`, que no haya vencido (absoluta ni por inactividad) y que `device_hash` coincida con la cookie de dispositivo. Desliza `last_seen`. Si algo falla → `401` y auditoría `gateway.reject.user`; si falta el alias → `403`.
8. **Separación de privilegios:** usuarios y admins viven en tablas distintas, con cookies distintas (`__Host-user` / `__Host-admin`) y verificaciones distintas (`verify-user` / `verify-admin`). Registrarse nunca crea un admin, y una cookie de usuario en `/api/admin/*` → 401.

### 9.3 Salas de la cuenta: canal general, unirse y entrar (riesgos 1, 8, 13 y 15)
1. La SPA llama `GET /api/device` al cargar: cookie de dispositivo de 128 bits aleatorios, **sin fingerprinting**. La necesitan el registro, el login y la entrada a una sala.
2. **Salas de la cuenta:** `GET /api/rooms` devuelve el **canal general** (siempre, sin clave) y las salas activas de las que la cuenta es miembro, con su ocupación.
3. **Unirse** (una vez por sala): `POST /api/rooms/join {code, key}`. El gateway exige una sesión de usuario con alias (`verify-user`) y pasa `X-User-Id` y `X-User-Name`. En `rooms`:
   1. Rate limit: ≥ 5 fallos en 10 min por `user`, ≥ 5 por `ip`, ≥ 10 por `device` o ≥ 20 por `room` → `429` y auditoría.
   2. Busca la sala activa (que no sea el general) por `code` y hace Argon2id verify (dummy si no existe). Si falla → registra el fallo en las cuatro claves y responde `401 "sala o clave inválida"`: la misma respuesta para clave mala, sala inexistente, cerrada o el general (RS-35).
   3. `INSERT INTO room_members … ON CONFLICT DO NOTHING` y, si es nueva, auditoría `room.member.join` (obligatoria). Responde `{room: {id, code, mode}}`. Cambiar la clave después no afecta a quienes ya son miembros (limitación 2).
4. **Entrar a conversar:** `POST /api/rooms/{id}/enter` (también con `verify-user`). Solo miembros activos o el canal general; si no → `404 "sala no encontrada"` (ajena, cerrada o inexistente dan lo mismo). **Transacción única:**
   ```sql
   SELECT id, room_id, device_hash FROM room_sessions
    WHERE user_id = :user AND ended_at IS NULL FOR UPDATE;
   -- otro dispositivo → 409; mismo dispositivo → end_session(reason='replaced')
   UPDATE rooms SET current_participants = current_participants + 1
    WHERE id = :room AND active AND current_participants < max_participants
   RETURNING id;                      -- 0 filas → 409 "sala llena"
   INSERT INTO room_sessions (...);   -- violación del índice único (carrera) → rollback → 409
   ```
   - Si el usuario ya tiene una sesión de sala activa desde **otro** dispositivo → `409 "usuario conectado desde otro dispositivo"` y auditoría `room.enter.device_conflict`. Cubre el caso de una sesión de usuario vencida mientras se chatea (ver §9.4).
   - Si es del **mismo** dispositivo (recarga o cambio de sala), la anterior se termina **antes** del incremento, para que el usuario no ocupe dos cupos. Si es de otra sala, las dos filas de `rooms` se bloquean en orden de `id` (`SELECT … FOR UPDATE ORDER BY id`), para que dos cambios de sala cruzados no se bloqueen mutuamente. Tras el commit, `chat kick(code=4401)` cierra su WS.
   - En la misma transacción se emite `room.enter.ok` (obligatorio; si `audit` falla, la entrada falla con 503).
   - Responde con la cookie `__Host-room` (token de 256 bits; en BD solo su SHA-256) y `{session_id, room: {id, code, mode}}`. El alias de la sesión es el de la cuenta.
5. **Abandonar:** `DELETE /api/rooms/{id}/membership` borra la membresía y, si la cuenta estaba conectada ahí, termina su sesión (`reason='abandon'`) y pide `kick(4401)`. Para volver hace falta otra vez código y clave. El canal general no se abandona (`409`).
6. `verify-session` busca la sesión activa por `token_hash` **y** comprueba que `device_hash` coincida con la cookie de dispositivo. Un token copiado a otro equipo no pasa el gateway.

### 9.4 Ciclo de vida de una sesión de sala
| Evento | Quién lo detecta | Qué ocurre |
|---|---|---|
| Botón "salir" | rooms (`/api/rooms/leave`) | `end_session(reason='leave')` → `chat kick(code=1000)` |
| Nueva entrada del mismo usuario desde el mismo dispositivo | rooms (`/api/rooms/{id}/enter`) | `end_session(reason='replaced')` → `chat kick(code=4401)` |
| Cierre limpio del WS (1000/1001: cerrar o recargar la pestaña) | chat | `rooms end(reason='closed')` + aviso `leave` a la sala |
| Violación de protocolo (4400/4403/4408/4413/4429) | chat | Cierra el WS, `rooms end(reason='violation')` y audita |
| Inactividad: 15 min sin mensajes del usuario | chat (en memoria) | Cierra con 4410 y `rooms end(reason='idle')` |
| Caída anormal del WS | — | `chat` deja de incluir la sesión en el heartbeat. Si no reconecta en 2 min, el barrido de `rooms` la termina (`reason='grace'`) |
| Sala eliminada por el admin | rooms | Termina todas sus sesiones (`reason='room_deleted'`) → `chat kick(code=4401)` por cada una. Las membresías quedan, pero la sala desaparece de las listas |
| La cuenta cierra sesión | auth → rooms (`/internal/users/{id}/sessions/end`) | `end_session(reason='logout')` → `chat kick(code=4401)` (RS-07) |
| La cuenta abandona la sala | rooms (`DELETE …/membership`) | Borra la membresía y `end_session(reason='abandon')` → `chat kick(code=4401)` |
| `chat` se reinicia | clientes | Reconectan y hacen un handshake nuevo; la sesión de `rooms` sigue viva si vuelven dentro del período de gracia |
| `rooms` se reinicia | — | Nada: las sesiones viven en su BD |

- `end_session` es idempotente: `UPDATE … SET ended_at = now() WHERE id = :s AND ended_at IS NULL RETURNING room_id`. Si devuelve una fila, decrementa `current_participants` en la misma transacción.
- **Reconciliación:** la respuesta del heartbeat (`ended`) le dice a `chat` qué conexiones cerrar con 4401, aunque se haya perdido un `kick`.
- Recargar la pestaña equivale a volver a entrar a la sala desde *Tus salas* (sin clave: la membresía es permanente): la SPA no persiste la sesión de sala (la de usuario sigue en su cookie).
- Una vez creada, la sesión de sala no depende de la de usuario. Si la de usuario vence por inactividad mientras se chatea, la de sala sigue viva (la mantiene el heartbeat de `chat`) y su índice único sigue impidiendo un segundo dispositivo.

### 9.5 Chat por WebSocket (riesgos 6, 7, 10 y 14)
1. El gateway hace el `auth_request` de sesión. Si pasa, `chat` recibe las cabeceras de identidad y valida `Origin` contra `ALLOWED_ORIGINS` (si no coincide: acepta, cierra con 4403 y audita).
2. **Handshake** (§10.1): el cliente tiene 10 s para enviar `hello`. Si no lo hace o es inválido → 4400.
3. Si la misma sesión ya tenía un WS abierto, el anterior se cierra con **4409** (la nueva conexión gana; el gateway ya validó el dispositivo).
4. Tras el handshake, `chat` envía el historial (últimos 50 mensajes y eventos de archivo de la sala, re-cifrados para esta conexión) y difunde un evento `join`.
5. Por cada trama: tamaño ≤ `WS_MAX_FRAME` (16 KB; si no → 4413), token bucket de 5/s con ráfaga 10 (si no → 4429), `seq` mayor que el último recibido (si no → 4408), descifrado AES-GCM (si el tag falla → 4400 y auditoría **critical** `ws.tamper`).
6. Payload `msg`: el modo de la sala debe permitir texto (si no → 4403). Se eliminan los caracteres invisibles (§12.8); si se quitó alguno, auditoría `msg.sanitized` solo con los conteos, nunca con el texto. Luego el cuerpo debe ser válido según §8.1 (si no → 4400). **El remitente sale de `X-Alias` / `X-Session-Id`, nunca del payload.**
7. Se persiste en `messages`, cifrado con la DEK de la sala (creada en la primera escritura), y se difunde a cada conexión de la sala cifrado con **su** clave y **su** contador `s2c`.
8. Payload `file_url`: si existe un mensaje `kind='file'` con ese `file_id` **en la sala de la sesión**, responde con una URL firmada nueva. Si no → 4403 y auditoría.
9. Cada 30 s una tarea de fondo envía el heartbeat a `rooms` y cierra por inactividad las conexiones con `last_activity` vencido.
10. uvicorn hace ping cada 30 s y cierra si no hay pong en otros 30 s (`--ws-ping-interval 30 --ws-ping-timeout 30`).

### 9.6 Subida de archivos (riesgos 6 y 9)
`POST /api/media/files`. Requiere sesión, `X-Room-Mode` ∈ {`media`, `both`} (si no → 403 y `file.rejected.forbidden`) y como máximo 5 subidas por minuto por sesión (si no → 429). El selector de archivos de la SPA filtra por extensión solo por comodidad; el control real es la firma.
1. **Tamaño:** Nginx `client_max_body_size 25m` solo en esta ruta y la app corta en `UPLOAD_MAX_BYTES` (25 MB). Tras identificar el formato se aplica el tope de su categoría (§12.1). Si se excede → `rejected (size)`.
2. **Firma (magic bytes)** contra `FORMATS`, en orden. TXT va al final porque no tiene firma: solo se acepta UTF-8 estricto sin bytes binarios. Se ignoran la extensión y el `Content-Type` del cliente. Si nada coincide → `rejected (type)`.
3. **Validación del formato** (§12.1, columna "Validación"): decodificación completa o parseo del contenedor, con límites contra bombas (píxeles, cuadros, entradas y tasa de compresión del ZIP). Si falla → `rejected (invalid)`.
4. **ClamAV** INSTREAM. Si encuentra algo → `rejected (malware)` y auditoría **critical**. Si no responde → **falla cerrado**: 503 y `clamav.unavailable`.
5. **Estegoanálisis por formato** (§12.3–12.8), fuera del event loop: `ProcessPoolExecutor` de `MEDIA_WORKERS` procesos, y ffmpeg/ffprobe como subprocesos. Timeout de 10 s; un timeout cuenta como sospechoso. **Excepción:** si el `sha256` del archivo coincide con el `clean_sha256` de un archivo ya publicado, se omite el análisis. Son bytes que generó el propio sistema; por ejemplo, un archivo descargado del chat y vuelto a subir. La sanitización de PNG y WAV aleatoriza el plano LSB, así que el análisis estadístico los marcaría como sospechosos. Cualquier modificación cambia el hash y fuerza el análisis completo.
6. **Política:**
   - Contenido activo (JavaScript, acciones automáticas o adjuntos en un PDF; macros, objetos OLE/ActiveX, paquetes incrustados o relaciones externas en un DOCX) → `rejected (active)`.
   - Sospechoso → se guarda en `/data/quarantine/<uuid>`, `status=quarantined`, auditoría warning `file.quarantined` con el veredicto. El usuario recibe "archivo retenido para revisión" y **el archivo no se publica**.
   - Rechazado (por cualquier motivo) → no se guarda el archivo; se registran `sha256`, `mime` y motivo en `files` y en auditoría.
   - Limpio → **sanitización** (§12.9; si falla o vence `SANITIZE_TIMEOUT_S` → `rejected (invalid)`) → **reanálisis estructural de la versión sanitizada** (§12.9; si encuentra algo → `rejected (recheck)`, no se guarda nada) → `/data/media/<uuid>`, `status=clean` → publicación (§9.7).
7. Archivos con permisos `0640`, dueño uid 10001. Solo `media` monta el volumen.

### 9.7 Publicación y descarga (riesgo 12)
- **Publicación:** `media` llama a `chat POST /internal/rooms/{room_id}/files {file_id, session_id, alias, mime, size}`. `chat` guarda un mensaje `kind='file'` cifrado y difunde a cada conexión `{"t":"file","id":file_id,"from":alias,"mime":…,"size":…,"url":…,"ts":…}`, con una **URL firmada por destinatario**:
  `url = /api/media/files/{file_id}?exp={exp}&sig={b64url(HMAC-SHA256(url_signing_key, "{file_id}|{session_id}|{exp}"))}`, con `exp = now + 60 s`.
  Si `chat` no responde, `media` devuelve 503. El archivo queda `clean` pero no aparece en ninguna sala, así que nadie puede obtener una URL firmada para él.
- **Descarga:** `GET /api/media/files/{id}?exp&sig`. El gateway valida la sesión; `media` exige firma válida contra `X-Session-Id` (`hmac.compare_digest`), `exp` no vencido, `files.room_id == X-Room-Id` y `status` ∈ {`clean`, `released`}. Si algo falla → `404` (no revela si el archivo existe) y auditoría `file.download.denied`.
- **Cabeceras de respuesta:** `Content-Type` de la lista blanca (TXT: `text/plain; charset=utf-8`), `X-Content-Type-Options: nosniff`, `Content-Disposition: attachment; filename="archivo.<ext>"` para **todos** los formatos (el nombre original no se guarda: puede filtrar información y es un vector de inyección), `Cache-Control: private, no-store`.
- **Presentación en la SPA:**
  | Categoría | Cómo se muestra |
  |---|---|
  | Imagen | `<img>` con la URL firmada |
  | Audio y video | Tras un clic: `fetch` del archivo completo → URL `blob:` → `<audio>` / `<video controls>`. El reproductor pide rangos durante minutos y la URL firmada vence en 60 s |
  | Documento y texto | Tras un clic: `fetch` → URL `blob:` → descarga con `<a download>`. Nunca se renderizan dentro de la página |
- **Renovación:** si la URL de un archivo vence antes de usarla, la SPA envía `{"t":"file_url","file_id":…}` por el WS.

### 9.8 Cuarentena (admin)
- `GET /api/admin/quarantine` → lista con `room_id`, `alias`, `mime`, `size`, `sha256` y `verdict`.
- **Liberar:** lee el original de `/data/quarantine`, lo **sanitiza**, **reanaliza la versión sanitizada** (§12.9), la guarda en `/data/media`, borra el original, `status=released`, auditoría `file.released` (obligatoria) y publicación (§9.7). Si la sanitización falla → `422 "no se pudo sanitizar el archivo"`; si la versión sanitizada no supera el reanálisis → `422 "la versión sanitizada no superó el reanálisis"` y `file.release.failed`. En ambos casos el archivo sigue en cuarentena (RS-19, RS-36).
- **Eliminar:** borra el archivo, `status=deleted`, auditoría `file.deleted`.

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

**Por qué se firma:** TLS termina en el gateway y el tramo gateway→chat es HTTP interno. La firma impide que alguien con presencia en la red interna reemplace las claves efímeras (MITM activo). Como la firma cubre la `client_pub` que recibió el servidor, también se detecta una sustitución de la clave del cliente.

### 10.2 Tramas
- **Cifrado:** AES-256-GCM, nonce aleatorio de 12 bytes por trama, tag de 16 bytes concatenado al ciphertext (formato por defecto de WebCrypto y de `AESGCM`).
- **AAD** = UTF-8 de `"v1|{room_id}|{session_id}|{seq}|{dir}"`, con `dir ∈ {c2s, s2c}`. En `s2c`, `session_id` es el del **destinatario**.
- **En el cable:** `{"seq": <int>, "n": "<b64url nonce>", "c": "<b64url ct||tag>"}`.
- `seq` empieza en 1 **por conexión y por dirección** y debe ser estrictamente creciente; el receptor rechaza `seq <= último`. El sufijo `dir` impide reflejar tramas hacia su emisor. Como cada conexión tiene su propia `K`, una trama de una conexión anterior no descifra en la nueva.
- **Payload en claro** (JSON UTF-8, serializado sin espacios):
  - `c2s`: `{"t":"msg","body":"…"}` · `{"t":"file_url","file_id":"…"}`
  - `s2c`: `{"t":"msg","id":123,"from":"alias","body":"…","ts":"ISO-8601"}` · `{"t":"file","id":"<uuid>","from":"alias","mime":"…","size":123,"url":"…","ts":"…"}` · `{"t":"file_url","file_id":"…","url":"…"}` · `{"t":"system","event":"join|leave","alias":"…"}` · `{"t":"history","items":[…eventos msg/file…]}`
- **Límite práctico:** 2^32 tramas por clave con nonces aleatorios. Una conexión nunca se acerca a ese número.

### 10.3 Códigos de cierre del WS
| Código | Motivo |
|---|---|
| 4400 | Trama malformada, tag GCM inválido, o handshake inválido o vencido |
| 4401 | Sesión terminada (expulsión, sala eliminada, reconciliación) |
| 4403 | Origin no permitido, tipo de contenido no permitido en la sala o archivo ajeno |
| 4408 | Replay (`seq` no creciente) |
| 4409 | Reemplazada por otra conexión de la misma sesión |
| 4410 | Expiración por inactividad |
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
| `svc_token_{gateway,auth,rooms,chat,media}` | 32 bytes b64url | Solo su dueño (el del gateway va dentro de `gateway_token.conf`) |
| `svc_hash_{gateway,auth,rooms,chat,media}` | SHA-256 hex del token | Los receptores según la allowlist (§4.3) |
| `gateway_token.conf` | `proxy_set_header X-Service-Token "<token>";` | gateway |
| `kek_auth_v1` | 32 bytes b64url | auth |
| `kek_chat_v1` | 32 bytes b64url | chat |
| `chat_sign_key` | ECDSA P-256 en PKCS#8 PEM | chat (además se genera `deploy/public/chat-key.json` con la pública, montado en el gateway) |
| `url_signing_key` | 32 bytes b64url | chat, media |
| `db_<svc>_owner`, `db_<svc>_app` | 32 bytes b64url | `<svc>-migrate` / `<svc>` y `db` |
| `postgres_password` | 32 bytes b64url | db |

- Cada servicio lee sus secretos desde `/run/secrets/*` al arrancar y **no arranca si falta alguno**. Ningún secreto va en el código, en variables de entorno ni en un `.env` versionado.
- Tokens de sesión (admin, usuario, sala) y cookie de dispositivo: aleatorios; en BD solo su SHA-256.
- Argon2id para las contraseñas (admins y usuarios) y las claves de sala, con un **tope de 4 cálculos concurrentes** por proceso (4 × 64 MiB) para que un ataque de registros, logins o ingresos masivos no agote la memoria.

### 11.2 Envelope encryption
- **auth:** el secreto TOTP se cifra con `kek_auth_v{n}` (AAD `totp|<admin_id>`) y se guarda junto con `kek_version`.
- **chat:** cada sala tiene una DEK de 32 bytes, creada con su primer mensaje y envuelta con `kek_chat_v{n}` (AAD `dek|<room_id>`). Los mensajes se cifran con la DEK (AAD `msg|<room_id>|<session_id>`).

### 11.3 Rotación
| Qué | Cómo |
|---|---|
| KEK de auth | Montar `kek_auth_v2`, `CURRENT_KEK_VERSION=2`, reiniciar `auth`, ejecutar `python -m auth_svc.rotate_kek` (re-envuelve los secretos TOTP) y luego retirar la v1 |
| KEK de chat | Igual con `kek_chat_v2` y `python -m chat_svc.rotate kek` (re-envuelve las DEK; los mensajes no se tocan) |
| DEK de una sala comprometida | `python -m chat_svc.rotate room <room_id>`: DEK nueva y re-cifrado de los mensajes de la sala en una transacción. La escritura de mensajes toma `FOR SHARE` sobre `room_keys`, así que espera a que termine la rotación |
| Token de servicio | `gen_secrets.py --rotate svc_token_<x>` (regenera token y hash) y reiniciar `<x>` y sus receptores |
| Clave de firma del chat | `gen_secrets.py --rotate chat_sign_key` (regenera `chat-key.json`), reiniciar `chat` y recargar el gateway |
| TLS | `mkcert` en local; Let's Encrypt en el VPS con hooks de renovación (`docs/despliegue-vps.md`) |

---

## 12. Análisis de archivos y estegoanálisis (riesgos 6 y 9) — servicio `media`

### 12.1 Formatos permitidos (lista blanca)
Todo lo que no está en esta tabla se rechaza (`rejected (type)`): ejecutables, comprimidos (ZIP, RAR, 7z), Office con macros (`.docm`) y cualquier otro formato binario. Un archivo de texto plano (HTML, SVG, código, CSV…) solo se acepta como TXT: se sirve como `text/plain` y como descarga, así que nunca se interpreta.

| Categoría | Formato | MIME servido | Ext. | Detección (firma) | Tope | Validación |
|---|---|---|---|---|---|---|
| Imagen | PNG | `image/png` | `png` | `89 50 4E 47 0D 0A 1A 0A` | 5 MB | Pillow: ≤ 20 MP, `verify()` y luego `load()` |
| Imagen | JPEG | `image/jpeg` | `jpg` | `FF D8 FF` | 5 MB | Pillow: ≤ 20 MP, `verify()` y luego `load()` |
| Imagen | GIF | `image/gif` | `gif` | `GIF87a` o `GIF89a` | 5 MB | Pillow: ≤ 20 MP por cuadro y ≤ 300 cuadros |
| Audio | MP3 | `audio/mpeg` | `mp3` | `ID3`, o cabecera de trama MPEG Layer III (`FF` + bits de sincronía, versión válida y capa `01`) | 10 MB | ffprobe (`-f mp3`): un flujo de audio `mp3` (la carátula, si hay, aparece como imagen adjunta) |
| Audio | WAV | `audio/wav` | `wav` | `RIFF` + 4 bytes + `WAVE` | 10 MB | `fmt `: PCM entero de 16 bits (o `EXTENSIBLE` con subformato PCM), 1–2 canales, 8–48 kHz; `data` coherente |
| Video | MP4 | `video/mp4` | `mp4` | Caja `ftyp` en el byte 4, marca `isom`, `iso2`–`iso6`, `mp41`, `mp42`, `avc1` o `M4V ` | 25 MB | ffprobe (`-f mp4`): al menos un video H.264; el audio, si hay, AAC |
| Documento | PDF | `application/pdf` | `pdf` | `%PDF-` | 10 MB | pikepdf abre el archivo; cifrado → inválido |
| Documento | DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `docx` | `PK\x03\x04` + `[Content_Types].xml` con la parte principal de Word | 10 MB | ZIP: ≤ 1000 entradas, ≤ 100 MB descomprimido, compresión ≤ 100:1 por entrada, sin cifrado, sin nombres duplicados ni rutas con `..` o absolutas; XML sin DTD |
| Texto | TXT | `text/plain; charset=utf-8` | `txt` | Sin firma (se prueba al final) | 1 MB | UTF-8 estricto, sin `NUL` ni controles salvo `\t`, `\n` y `\r` |

### 12.2 Registro `FORMATS` (punto de extensión)
```python
# media_svc/formats/base.py
@dataclass(frozen=True)
class Format:
    mime: str                                     # Content-Type con el que se sirve
    ext: str                                      # extensión del nombre de descarga
    category: str                                 # image | audio | video | document | text
    detect: Callable[[bytes], bool]               # firma; nunca la extensión ni el Content-Type del cliente
    validate: Callable[[bytes, dict], None]       # lanza Invalid
    analyze: Callable[[bytes, dict], dict]        # veredicto (§12.3–12.8)
    sanitize: Callable[[bytes, dict], bytes]      # §12.9

# media_svc/formats/__init__.py
IMAGES = (png.FORMAT, jpeg.FORMAT, gif.FORMAT)   # también analizan lo incrustado en MP3, MP4 y DOCX
FORMATS: dict[str, Format] = {
    f.mime: f for f in (*IMAGES, mp3.FORMAT, wav.FORMAT, mp4.FORMAT, pdf.FORMAT, docx.FORMAT, txt.FORMAT)
}
# el orden del dict es el orden de detección: TXT siempre al final
```
- Cada formato vive en su módulo (`formats/png.py`, `formats/mp3.py`, …) y expone `FORMAT`. `validate`, `analyze` y `sanitize` son funciones de módulo que reciben los bytes y la configuración (`Settings.format_config`: umbrales, límites y timeouts), porque las ejecuta el `ProcessPoolExecutor` en otro proceso.
- `format_config["statistical"]` (por defecto `True`): con `False`, los analizadores omiten los estadísticos del LSB (chi², RS y entropía en PNG; SPA y entropía en WAV; paleta en GIF) y aplican solo las reglas estructurales. Es el modo del reanálisis de §12.9.
- El tope de tamaño sale de la categoría: `Settings.max_bytes(category)` (§19).
- **Veredicto** (`files.verdict`): `{"format", "suspicious", "active", "reasons": [...], "metrics": {...}}`. `reasons` son textos cortos en español (por ejemplo, "datos después de IEND"). Las métricas que no se pueden calcular (por ejemplo, NaN) se guardan como `null`, porque el veredicto debe serializarse en `jsonb`.
- Agregar un formato = una entrada, su módulo, sus fixtures y sus tests (§12.11).

### 12.3 Reglas comunes a todos los formatos
Cada analizador recorre la estructura completa del archivo y, además de lo propio de su formato, aplica:
- **Datos anexados:** bytes después del final lógico del formato (`IEND`, `FFD9`, trailer `3B` del GIF, tamaño declarado del `RIFF`, última trama o etiqueta del MP3, última caja del MP4, último `%%EOF` del PDF, registro de fin del ZIP) → sospechoso. Tolerancia: 16 bytes en JPEG y 2 en PDF (relleno y salto de línea de algunos editores); 0 en el resto. Es la técnica más común (`copy /b archivo + secreto`).
- **Metadatos y comentarios** cuya suma supera el umbral del formato (1 KB en los chunks de texto de PNG; 64 KB en los demás) → sospechoso.
- **Segmentos desconocidos o no referenciados** (chunks privados de PNG, chunks RIFF fuera de la lista, cajas MP4 desconocidas, frames ID3 `GEOB`, objetos PDF huérfanos, partes DOCX sin relación) → sospechoso.
- **Relleno que no es relleno:** zonas declaradas como relleno (`free`/`skip` en MP4, `JUNK`/`PAD ` en WAV) con contenido, según el umbral de cada formato → sospechoso.
- **Imágenes incrustadas** (carátula `APIC` de un MP3, `covr` de un MP4, imágenes de `word/media/` en un DOCX): no cuentan como metadatos; pasan por el analizador de su formato y sus hallazgos se suman al veredicto del contenedor.
- **Contenido activo** (solo documentos): `active = true` → rechazo (§9.6, paso 6).

### 12.4 Imágenes
**PNG** (dominio de píxeles, canales RGB):
- **Chi² de Westfeld–Pfitzmann** por canal: para los pares `(2k, 2k+1)` se calcula `E = (h[2k] + h[2k+1]) / 2` y `χ² = Σ (h[2k] − E)² / E` (solo pares con `E > 4`), con `p = 1 − CDF_χ²(χ², gl = pares − 1)`. Se evalúa sobre los prefijos de 10 %, 25 %, 50 % y 100 % de los píxeles en orden de escaneo (prefijos de al menos 1000 píxeles), porque el embedding secuencial deja el prefijo con p ≈ 1. **Sospechoso si algún p ≥ `STEGO_CHI2_P`.**
- **Análisis RS** (Fridrich, Goljan, Du 2001): grupos de 2×2 píxeles en zigzag, función de variación `Σ|xᵢ₊₁ − xᵢ|`, máscara `[0,1,1,0]`, estimación de la tasa `p̂` por canal resolviendo `2(d₁+d₀)x² + (d₋₀−d₋₁−d₁−3d₀)x + d₀−d₋₀ = 0` (la raíz de menor módulo) con `p̂ = x/(x−½)`. **Sospechoso si `p̂ ≥ STEGO_RS_RATE`.**
- **Entropía del plano LSB** en bloques de 64×64: se reportan la media y la fracción de bloques con entropía ≥ 0.999 bits. Es una métrica de **apoyo**; solo se vuelve disparador si la calibración muestra que separa bien (`STEGO_ENTROPY_TRIGGER`, desactivado por defecto).
- **Estructura:** cualquier dato después de `IEND` es sospechoso; también lo son los chunks `tEXt/zTXt/iTXt` que sumen más de 1 KB y los chunks desconocidos o privados.

**JPEG:**
- Más de 16 bytes después del marcador `FFD9` final → sospechoso.
- Segmentos `APPn` + `COM` que sumen más de 64 KB → sospechoso.
- El recorrido salta los segmentos por su longitud; así una miniatura EXIF con su propio `FFD9` no confunde al análisis.
- *Stretch:* chi² sobre el histograma de coeficientes DCT (detector de JSteg) con `jpegio`, solo si instala sin problemas.

**GIF:**
- **Estructura:** se recorren los bloques hasta el trailer `3B`. Son sospechosos los datos posteriores, las extensiones de comentario que sumen más de 1 KB, las extensiones de aplicación distintas de `NETSCAPE2.0` y `ANIMEXTS1.0`, y las extensiones de texto plano.
- **Paleta:** herramientas como S-Tools y EzStego dejan paletas con grupos de colores casi idénticos. Se reporta la fracción de colores de la paleta con un vecino a distancia ≤ 2 por canal. Es una métrica de **apoyo**; solo se vuelve disparador si la calibración muestra que separa bien (`STEGO_GIF_PALETTE_TRIGGER`, desactivado por defecto). La sanitización recuantiza la paleta de todos modos (§12.9).

### 12.5 Audio
**WAV** (PCM de 16 bits):
- **Estructura RIFF:** el tamaño declarado debe coincidir con el del archivo. Chunks permitidos: `fmt `, `data`, `fact`, `LIST`, `id3 `, `bext`, `cue `, `smpl`, `JUNK` y `PAD `; cualquier otro → sospechoso. `LIST` + `id3 ` + `bext` que sumen más de 64 KB → sospechoso. `JUNK`/`PAD ` con bytes distintos de cero → sospechoso.
- **Sample Pair Analysis** (Dumitrescu, Wu y Wang, 2003, en el marco de conjuntos de traza de Ker) por canal, sobre pares de muestras consecutivas: estima la tasa de reemplazo de LSB `p̂`. Se evalúa sobre los prefijos de 1 %, 2.5 %, 5 %, 10 %, 25 %, 50 % y 100 % de las muestras, porque el embedding secuencial empieza al inicio. **Sospechoso si algún `p̂ ≥ STEGO_WAV_RATE`.** Es el análogo del análisis RS para señales de una dimensión.
- **Abstención de SPA:** el estimador solo es concluyente con suficientes pares en la traza 0 (≥ 20 000 y ≥ 10 % de los pares). Con audio fuerte o ruidoso se abstiene (`spa_rate = null`) y ese archivo queda cubierto solo por la sanitización, que aleatoriza el LSB; la calibración (§12.10) reporta qué fracción de grabaciones reales no es concluyente. Igual que RS, SPA degenera cerca del 100 % de embedding. Ambas son limitaciones declaradas. No se usa chi²: con 65 536 valores posibles por muestra, el histograma es demasiado suave y daría falsos positivos.
- **Entropía del plano LSB** por bloques: métrica de apoyo, igual que en PNG.

**MP3:**
- **Etiquetas** (`mutagen`): ID3v2 al inicio; ID3v1, APEv2 y Lyrics3 al final. Son sospechosos los frames `GEOB` (objeto encapsulado), los frames `PRIV` de más de 1 KB, los frames desconocidos y el texto de etiquetas (`COMM`, `TXXX`, `USLT`…) que sume más de 64 KB.
- **Flujo de tramas:** se recorre trama por trama desde el fin del ID3v2, con la longitud que da cada cabecera (bitrate, frecuencia y relleno). La primera trama puede ser una cabecera Xing/Info/VBRI. Los bytes que no pertenecen a ninguna trama ni a una etiqueta reconocida (entre tramas o al final) → sospechoso.
- **Bits de cabecera:** si los bits *private*, *copyright* u *original* cambian de una trama a otra → sospechoso. Un codificador los deja constantes; variarlos es un canal oculto conocido.
- *Stretch:* detector de **MP3Stego**, que oculta bits en la paridad de `part2_3_length` mientras codifica: un estadístico sobre ese campo de la información lateral, calibrado con `stego_lab`. Sin él, MP3Stego no se detecta, pero la recodificación (§12.9) destruye el payload.

### 12.6 Video (MP4)
- **Árbol de cajas** (ISO BMFF): tamaños coherentes y sin solapamientos. Datos después de la última caja → sospechoso. Cajas de nivel superior permitidas: `ftyp`, `moov`, `mdat`, `free`, `skip`, `wide`, `uuid`, `meta`, `udta`, `pdin` y, en MP4 fragmentado, `moof`, `mfra`, `sidx` y `styp`. Cualquier otra → sospechoso.
- **Metadatos:** `udta`, `meta` y `uuid` que sumen más de 64 KB → sospechoso. La carátula (`covr`) pasa por el analizador de imágenes.
- **Relleno:** `free`, `skip` o `wide` con más de 1 KB distinto de cero → sospechoso (algunos muxers escriben ahí una firma corta de texto).
- **Bytes del `mdat` no referenciados:** se cruzan la posición y el tamaño de todos los paquetes (`ffprobe -show_packets`) con el rango del `mdat`. Si quedan más de 4 KB sin referenciar → sospechoso. Es un escondite clásico porque no afecta la reproducción.
- **Flujos:** más de un video (sin contar la carátula), más de un audio, o flujos de datos, subtítulos o adjuntos → sospechoso.
- No se analiza el contenido del flujo de video (coeficientes, vectores de movimiento): limitación 5 (§3).

### 12.7 Documentos
**PDF** (pikepdf):
- Datos después del último `%%EOF` (más de 2 bytes) → sospechoso.
- Objetos no alcanzables desde el trailer (huérfanos) que sumen más de 1 KB → sospechoso. Las revisiones incrementales se reportan como métrica; la sanitización las elimina.
- Diccionario `Info` + metadatos XMP de más de 64 KB → sospechoso.
- **Contenido activo → rechazo:** `/JavaScript` o `/JS`; acciones automáticas (`/OpenAction`, `/AA`) que no sean un simple `/GoTo`; `/Launch`, `/SubmitForm`, `/ImportData`, `/GoToE`, `/GoToR`, `/RichMedia` y formularios XFA; y archivos incrustados (`/EmbeddedFiles`, anotaciones `/FileAttachment`), porque un adjunto saltaría la lista blanca.
- *Stretch:* extraer las imágenes del PDF y pasarlas por los analizadores de imagen.

**DOCX** (ZIP + OPC; XML con `lxml` sin DTD, entidades ni red):
- **ZIP:** bytes antes de la primera entrada o después del registro de fin (EOCD), comentario del ZIP no vacío o campos extra desconocidos o de más de 64 bytes en las entradas (se admiten los estándar: ZIP64, NTFS, marca de tiempo extendida y Unix) → sospechoso. Los nombres duplicados, las rutas peligrosas y el cifrado ya se rechazaron al validar.
- **Partes:** toda parte debe estar declarada en `[Content_Types].xml` y ser alcanzable por relaciones desde `_rels/.rels`. Partes sueltas → sospechoso; es el truco de "meter un archivo dentro del ZIP".
- **Texto oculto:** ejecuciones con `w:vanish` que contengan texto → sospechoso.
- `docProps/custom.xml`, `customXml/` y las variables de documento (`w:docVars` de `word/settings.xml`) que sumen más de 64 KB → sospechoso.
- **Imágenes** de `word/media/`: PNG, JPEG y GIF pasan por su analizador. Otros tipos (EMF, WMF, SVG, TIFF, BMP) → sospechoso, porque no se pueden analizar.
- **Contenido activo → rechazo:** `vbaProject.bin` (macros), `activeX/`, objetos OLE y paquetes incrustados en `word/embeddings/`, y relaciones `TargetMode="External"` que no sean hipervínculos (plantillas remotas, imágenes externas). Un DOCX con gráficos se rechaza, porque Word guarda sus datos como un Excel incrustado; el usuario puede exportarlo a PDF.

### 12.8 Texto (archivos TXT y mensajes del chat)
La detección y la limpieza viven en `shared.text`, porque las usan `media` (archivos TXT) y `chat` (mensajes):
- **Caracteres invisibles:** todo carácter de categoría Unicode `Cf`: ancho cero (U+200B–U+200D, U+2060–U+2064, U+FEFF), controles bidi (U+202A–U+202E, U+2066–U+2069), etiquetas (U+E0000–U+E007F) y guion suave (U+00AD). Se exceptúan U+200D dentro de una secuencia de emoji (entre dos caracteres `Extended_Pictographic`, con sus modificadores y selectores, como en 👨‍👩‍👧) y un BOM al inicio del archivo. Es el canal de herramientas como StegCloak. **TXT: sospechoso si hay al menos uno.**
- **Selectores de variación** (U+FE00–U+FE0F, U+E0100–U+E01EF): se admite uno después de un carácter base; dos o más seguidos → sospechoso (así se "pegan" bytes a un emoji).
- **Espacio en blanco al final de línea** (técnica SNOW): tabulaciones finales, o espacios finales que sumen más de `STEGO_TXT_TRAILING` bytes → sospechoso.
- **Homoglifos:** palabras que mezclan letras latinas con cirílicas o griegas → sospechoso.
- **Mensajes del chat:** solo se **limpian**, sin cuarentena. Se eliminan los caracteres invisibles y los selectores sobrantes, y se recortan los espacios finales de cada línea. Si se quitó algo, `chat` audita `msg.sanitized` (§9.5).

### 12.9 Sanitización (CDR) de todo archivo aceptado o liberado
| Formato | Sanitización | Qué destruye |
|---|---|---|
| PNG | Se decodifica (se conserva el canal alfa si existe), se **reemplaza el plano LSB por bits aleatorios** (imperceptible) y se recodifica sin chunks auxiliares. Recodificar sin tocar los píxeles **no** basta, porque PNG es sin pérdida | Payloads LSB aunque no se hayan detectado, chunks, datos anexados |
| JPEG | Se aplica la orientación EXIF y se recodifica a RGB con calidad 90, sin EXIF, ICC ni comentarios | Metadatos y datos anexados; además recuantiza los coeficientes DCT |
| GIF | Cada cuadro pasa a RGBA y se recuantiza con una paleta nueva; se conservan duraciones y bucle; sin comentarios ni más extensiones que `NETSCAPE2.0` | Paleta e índices (EzStego, Gifshuffle), comentarios, datos anexados |
| WAV | Se reescribe solo con `fmt ` y `data` y se **aleatoriza el LSB** de cada muestra (ruido a −96 dB, inaudible) | Payloads LSB, chunks extra, datos anexados |
| MP3 | Se **recodifica** con ffmpeg (LAME), con el mismo bitrate y un tope de 192 kbps, sin etiquetas | Etiquetas, tramas ajenas, bits de cabecera, payload de MP3Stego |
| MP4 | Se **remultiplexa** con ffmpeg (`-c copy`): un video y un audio, sin metadatos ni capítulos, con `-fflags +bitexact` y `-movflags +faststart` | Cajas extra, metadatos, bytes no referenciados, datos anexados. **No** destruye payloads dentro del flujo de video |
| PDF | Se reescribe completo con pikepdf, sin `Info` ni XMP | Datos anexados, objetos huérfanos, revisiones anteriores, metadatos |
| DOCX | Se reconstruye el ZIP solo con las partes alcanzables: `docProps/core.xml` mínimo, sin `custom.xml`, `customXml/`, variables de documento (`w:docVars`) ni miniatura; se eliminan las ejecuciones con `w:vanish`; las imágenes se sanitizan con su formato | Partes sueltas, metadatos, texto oculto, LSB de las imágenes, datos fuera del ZIP |
| TXT | UTF-8 sin BOM y saltos de línea `\n`, sin caracteres invisibles, selectores sobrantes ni espacios finales | Ancho cero, bidi, etiquetas, SNOW. Los homoglifos **no** se corrigen |

- Se guarda el `clean_sha256` de la salida. Una imagen o un WAV con el plano LSB aleatorio es estadísticamente idéntico a uno con LSB embebido al 100 %, así que el sistema reconoce sus propias salidas por hash (§9.6, paso 5) y no las vuelve a analizar. El prototipo del 2026-10-13 lo confirmó en PNG: también fallan las alternativas de poner el LSB en cero (lo marca RS), recodificar como JPEG o redimensionar (lo marca chi²).
- **Reanálisis de la versión sanitizada (RS-36):** antes de publicar, al subir y al liberar desde la cuarentena, la salida de la sanitización se vuelve a validar con su formato y se analiza con `statistical = False`. Los estadísticos se omiten porque la sanitización de PNG y WAV aleatoriza el LSB a propósito y la marcarían siempre. Si quedara cualquier hallazgo estructural (por ejemplo, un defecto del sanitizador que deje datos anexados), el archivo no se publica: `rejected (recheck)` al subir, o `422` y sigue en cuarentena al liberar.
- **ffmpeg y ffprobe** son parsers grandes que reciben entrada no confiable. Se ejecutan sin shell, con el demuxer forzado (`-f mp3` / `-f mp4`, nunca autodetección), `-protocol_whitelist file` (sin red ni listas de reproducción), `-nostdin`, límites de CPU y memoria (`prlimit` en Linux: 2 GiB de memoria virtual y 120 s de CPU por proceso) y timeout. Entrada y salida por archivos temporales en `/tmp`.

### 12.10 Calibración y fixtures
`services/media/tools/stego_lab.py`:
- `embed <in> <out> --rate 0.1 --mode seq|random`: LSB replacement con bits aleatorios en PNG o WAV.
- `append <in> <out> --bytes N`: agrega datos al final de cualquier formato.
- `hide-text <in.txt> <out.txt> --method zw|vs|snow`: ancho cero, selectores de variación o espacios finales.
- `calibrate <dir_limpios>`: genera variantes al 5, 10, 25, 50 y 100 % y reporta TPR/FPR por detector (PNG y WAV).

Se necesitan ≥ 30 imágenes limpias reales (fotos de celular y capturas de pantalla) y ≥ 20 grabaciones WAV reales (voz y música). El chi² tiende a dar falsos positivos con histogramas muy suaves; los umbrales finales se fijan con esta herramienta y se documentan en el informe con la tabla TPR/FPR. Las reglas estructurales son deterministas y no se calibran; sus fixtures (MP3, MP4, PDF, DOCX) se generan en las pruebas (§16.1).

Para el informe se prueban también herramientas reales: OpenStego (PNG), steghide (JPEG, WAV), MP3Stego, StegCloak (texto) y `copy /b` o `cat` para anexar datos. Se documenta el resultado de cada una: detectado, o solo destruido por la sanitización.

### 12.11 Agregar formatos en el futuro
- **WebP:** RIFF + Pillow. Sin pérdida → mismo análisis y sanitización que PNG; con pérdida → como JPEG.
- **XLSX y PPTX:** el mismo analizador OOXML del DOCX, con otra parte principal.
- **MOV y M4A:** el mismo parser ISO BMFF del MP4.
- **FLAC y OGG:** decodificar a PCM con ffmpeg y aplicar el análisis del WAV; sanitizar recodificando.
- **Video:** recodificar H.264 en segundo plano, para destruir también los payloads del flujo (§3, fuera de alcance).

---

## 13. Gateway (Nginx) — riesgos 7, 10 y 16

- **TLS:** `listen 443 ssl; http2 on; ssl_protocols TLSv1.3; ssl_session_tickets off;`. El puerto 80 solo responde `301` a https, así que **`ws://` nunca llega a ningún servicio**.
- **Cabeceras** (nivel `server`, con `always`; ninguna `location` declara `add_header`):
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; media-src blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'` (en CSP3, `'self'` cubre `wss:` del mismo host; `media-src blob:` obliga a reproducir audio y video desde el `blob:` ya descargado, §9.7)
  - `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`, `server_tokens off`
- **Rutas:**
  | Ruta | Upstream | `auth_request` | Límite |
  |---|---|---|---|
  | `= /api/auth/login`, `= /api/auth/totp` | auth | — | zona `login` 1 r/s, ráfaga 5 |
  | `/api/auth/` | auth | — | zona `api` 10 r/s, ráfaga 20 |
  | `= /api/users/register`, `= /api/users/login`, `= /api/users/verify`, `= /api/users/verify/resend` | auth | — | `login` |
  | `/api/users/` | auth | — | `api` |
  | `= /api/device` | rooms | — | `api` |
  | `= /api/rooms` | rooms | usuario | `api` |
  | `= /api/rooms/join` | rooms | usuario | `login` |
  | `~ ^/api/rooms/<uuid>/(enter\|membership)$` | rooms | usuario | `api` |
  | `= /api/rooms/leave` | rooms | sesión | `api` |
  | `/api/admin/rooms` | rooms | admin | `api` |
  | `/api/admin/quarantine` | media | admin | `api` |
  | `/api/admin/audit` | audit | admin | `api` |
  | `= /api/media/files` | media | sesión | `api`, `client_max_body_size 25m` |
  | `/api/media/` | media | sesión | `api` |
  | `= /ws` | chat | sesión | `limit_conn` 20 por IP, `proxy_read_timeout 75s` |
  | `~ ^/api/admin/metrics/(auth\|rooms\|chat\|media\|audit)$` | ese servicio (`/api/admin/metrics`) | admin | `api` |
  | `= /api/status` | chat (`/health`) | — | `api` |
  | `= /chat-key.json` | archivo estático montado | — | — |
  | `/` | SPA (`try_files $uri /index.html`) | — | — |
  | cualquier otra `/api/…` o `/internal/…` | — | — | `404` JSON |
- **`auth_request`:** usa ubicaciones `internal` (`/_auth/admin` → `auth /internal/verify-admin`, `/_auth/user` → `auth /internal/verify-user`, `/_auth/session` → `rooms /internal/verify-session`) con `proxy_pass_request_body off` y `X-Original-URI`. La identidad se toma con `auth_request_set $x $upstream_http_x_…`. **La subpetición comparte las variables de la petición original**: esas ubicaciones usan `$verifier` y nunca `$upstream`, o la petición terminaría en el servicio que verifica. Lo comprueba `gateway/tests/check_routes.py` con servicios falsos (también en la CI).
- **Correlación y registros (RNF-19):** `proxy-base.conf` envía `X-Request-ID $request_id` (sobrescribe el del cliente) y oculta el que devuelve el servicio; el `server` lo agrega una sola vez a cada respuesta. El registro de acceso es JSON con `ts`, `service`, `level`, `request_id`, `msg`, `status` y `ms`, sin query string (las URL firmadas no quedan registradas).
- **Snippets de proxy** (en cada `location` se incluye exactamente uno, porque `proxy_set_header` no se hereda cuando una `location` declara los suyos). Las cabeceras de identidad son 8: `X-Admin-Id`, `X-Admin-User`, `X-User-Id`, `X-User-Name`, `X-Session-Id`, `X-Room-Id`, `X-Alias` y `X-Room-Mode`.
  - `proxy-base.conf`: `Host`, `X-Real-IP $remote_addr`, `X-Forwarded-For $remote_addr` (sobrescribe, no concatena), `X-Forwarded-Proto https` y el token del gateway (`include /run/secrets/gateway_token_conf`). Nunca se incluye solo.
  - `public.conf`: base + **vacía** las 8 cabeceras de identidad.
  - `admin.conf`: `auth_request` de admin + base + `X-Admin-*`, y vacía las demás.
  - `user.conf`: `auth_request` de usuario + base + `X-User-Id` y `X-User-Name`, y vacía las demás.
  - `session.conf`: `auth_request` de sesión + base + `X-Session-Id`, `X-Room-Id`, `X-User-Id`, `X-Alias` y `X-Room-Mode`, y vacía las demás.
  - `subrequest.conf`: para las ubicaciones `/_auth/*`: sin cuerpo, con `X-Original-URI`, e incluye `public.conf`.
- **Errores en JSON:** `error_page 401 403 404 413 429 500 502 503 504` → `{"error":"…"}` con `default_type application/json`. Un servicio caído (502) llega al cliente como `503 {"error":"servicio no disponible"}` (RNF-05).
- `client_max_body_size` es 16k por defecto y 25m solo en la subida. `client_body_timeout 10s`.
- **Verificación manual** (evidencia para el informe): `curl --tlsv1.2 --tls-max 1.2 https://localhost/` debe fallar; `curl -I http://localhost/ws` → 301; `curl https://localhost/internal/verify-admin` → 404.

---

## 14. Auditoría — servicio `audit` (riesgo 3)

### 14.1 Escritura
- `POST /internal/events`: valida el token, deduce `service` del token y normaliza `ip` (si no es una IP válida → `null`).
- Toma `pg_advisory_xact_lock(42)`, lee el último `hash` e inserta. *Límite conocido: las escrituras quedan serializadas; a esta escala no importa.*
- `hash = SHA256(prev_hash || json canónico de {ts, service, severity, actor, action, target, ip, details})`, con claves ordenadas, sin espacios y `ensure_ascii=False`. El primer `prev_hash` son 32 bytes en cero.
- `audit_app` no puede `UPDATE`, `DELETE` ni `TRUNCATE`. `GET /api/admin/audit/verify` recorre la cadena; si se rompe, devuelve `{ok:false, broken_at:id}` y registra `audit.chain.broken` (critical).
- **Nunca** se registran contraseñas, claves de sala, tokens, cuerpos de mensajes ni secretos TOTP.

### 14.2 Eventos
| Servicio | info | warning | critical |
|---|---|---|---|
| auth | `admin.create`, `admin.login.ok`, `admin.logout`, `user.register`, `user.register.renewed`, `user.register.existing`, `user.verify.ok`, `user.login.ok`, `user.alias.set`, `user.logout`, `user.seed`, `key.rotate.auth` | `admin.login.fail`, `admin.login.locked`, `admin.totp.fail`, `gateway.reject.admin`, `user.register.ratelimited`, `user.verify.fail`, `user.login.fail`, `user.login.locked`, `user.login.unverified`, `user.login.device_conflict`, `user.logout.partial`, `mail.unavailable`, `gateway.reject.user` | — |
| rooms | `room.create`, `room.update`, `room.delete`, `room.member.join`, `room.member.leave`, `room.enter.ok`, `session.end` | `room.join.fail`, `room.join.ratelimited`, `room.enter.full`, `room.enter.device_conflict`, `gateway.reject.session` | — |
| chat | `key.rotate.chat` | `ws.reject.{origin,handshake,replay,rate,size,forbidden,malformed}`, `msg.sanitized` | `ws.tamper` |
| media | `file.accepted`, `file.released`, `file.deleted` | `file.quarantined`, `file.rejected.{type,invalid,size,forbidden,active,recheck}`, `file.release.failed`, `file.download.denied`, `clamav.unavailable` | `file.rejected.malware` |
| todos | — | `http.reject.origin`, `svc.reject.token` (token ausente o inválido, o llamador fuera de la allowlist), `resource.high` (CPU o memoria ≥ 80 % durante 5 min, §21.1) | — |
| audit | — | — | `audit.chain.broken` |

`audit` registra sus propios `svc.reject.token` escribiendo directamente en su BD. Cada evento lleva en `details.request_id` el id de correlación de la petición que lo causó (§21.1), dentro del hash de la cadena.

### 14.3 Consulta
El dashboard pide `GET /api/admin/audit?min_severity=warning&after_id=<último>` cada 10 s (alertas) y la vista completa con `min_severity=info`.

### 14.4 Si `audit` no responde
`AuditClient.emit(..., required=…)` usa un timeout de 2 s y un reintento:
- **`required=True`** (eventos que otorgan algo: `admin.login.ok`, `user.register`, `user.register.renewed`, `user.verify.ok`, `user.login.ok`, `user.alias.set`, `user.seed`, `room.member.join`, `room.enter.ok`, `room.create/update/delete`, `file.accepted`, `file.released`, `key.rotate.*`): se emite **dentro** de la transacción, antes del commit. Si falla, la operación se revierte y responde 503.
- **Resto** (rechazos y avisos): se escribe en stdout con la marca `AUDIT_FALLBACK` y el JSON del evento, y la operación continúa (un rechazo sigue siendo rechazo).

---

## 15. Manejo de errores
- El cliente siempre recibe mensajes **genéricos** en JSON `{"error": "…"}` ("credenciales inválidas", "sala o clave inválida", "código inválido o vencido", "archivo no permitido" para cualquier rechazo de archivo, "archivo retenido para revisión", 404 en descargas negadas o salas ajenas). El detalle va a auditoría. Los 403 de cuenta sin verificar y los 409 de dispositivo solo se muestran después de validar la contraseña o la clave, así que no revelan nada a quien no las tiene.
- Toda respuesta lleva `X-Request-ID`. En un 5xx la SPA muestra "(ref. …)" con ese id, que permite encontrar la petición en los registros de cada servicio y en la auditoría (RNF-19).
- Excepciones no controladas: handler global → `500 {"error":"error interno"}` + log en stdout sin datos sensibles. FastAPI sin docs ni OpenAPI públicos (`docs_url=None`, `openapi_url=None`).
- Errores de validación: `422 {"error":"datos inválidos"}`, sin repetir la entrada.
- **Fallar cerrado:** secreto ausente → el servicio no arranca; ClamAV, BD o `audit` (en otorgamientos) caídos → 503; el `auth_request` del gateway falla → 401.

---

## 16. Pruebas y trazabilidad

### 16.1 Por servicio
- pytest contra **PostgreSQL real** (`deploy/docker-compose.test.yml`, puerto 5433). Cada servicio crea su BD `<svc>_test` con roles reales y migraciones aplicadas; sin mocks de BD.
- Los servicios vecinos (audit, chat, rooms) se simulan con `httpx.MockTransport` inyectado en `ServiceClient`. Las pruebas verifican qué se llamó, con qué token y con qué cuerpo.
- Las peticiones del "gateway" en las pruebas se construyen con el token de prueba del gateway y las cabeceras de identidad.
- Los WebSocket se prueban con el `TestClient` de Starlette dentro de un bloque `with` (un solo event loop).
- `@pytest.mark.clamav` marca los tests que necesitan clamd (`docker compose -f deploy/docker-compose.test.yml --profile clamav up`); se omiten en CI.
- Los fixtures de audio, video y documentos se generan en las propias pruebas (ffmpeg con `lavfi`, pikepdf y un DOCX mínimo armado con `zipfile`), sin binarios versionados en el repo.
- **Frontend:** vitest para `lib/crypto.ts` contra `docs/crypto-vectors.json`.

### 16.2 End-to-end (`e2e/`)
pytest + httpx + `websockets` contra el stack completo vía `https://localhost`, verificando TLS con la CA de mkcert. Crea su admin con `create_admin --password-stdin` y registra sus usuarios por la API. Cubre lo que cruza servicios:
- Registro con el código leído de Mailpit, alias y login de varios usuarios; chat entre ellos con *hello* firmado verificado; canal general para todas las cuentas; volver a entrar a una sala sin la clave.
- Sin sesión de usuario, `/api/rooms` y `/api/rooms/join` → 401. La misma cuenta desde un segundo dispositivo → 409. Cerrar sesión cierra el WebSocket con 4401.
- `X-Request-ID` en cada respuesta y en la auditoría; métricas de los cinco servicios.
- Imagen limpia → publicada y descargable; imagen con LSB → cuarentena y alerta visible en `GET /api/admin/audit`. Un MP3 con datos anexados y un TXT con caracteres de ancho cero → cuarentena.
- Gateway: `/internal/*` → 404; `X-Admin-Id`/`X-User-Id`/`X-Session-Id` enviados por el cliente se ignoran; una cookie de sala o de usuario en `/api/admin/*` → 401; `http://` → 301.

Se ejecuta en local antes de cada hito.

### 16.3 Riesgos nuevos R16 y R17
- **R16 — "Suplantación entre microservicios":** un proceso con presencia en la red interna (o un servicio comprometido) invoca endpoints internos o inyecta cabeceras de identidad haciéndose pasar por el gateway u otro servicio. La vulnerabilidad que habría sin tratamiento es que los servicios confíen en cualquier petición de la red interna. Valoración propuesta: **P=3, I=5 → 15 (Alto)**; residual estimado 5 (Medio). Tratamiento: §4.3–4.5 y §13.
- **R17 — "Acceso no autorizado a cuentas de usuario mediante ataques automatizados de contraseñas"** (fuerza bruta o *credential stuffing*). Lo introduce la cuenta obligatoria. La vulnerabilidad que habría sin tratamiento es un login de usuarios con intentos ilimitados y contraseñas débiles. Valoración propuesta: **P=4, I=3 → 12 (Medio-alto)**; residual estimado 6 (Medio). Tratamiento: §9.2 (Argon2id, bloqueo por cuenta y por IP con retraso progresivo, política de contraseñas, error genérico y hash dummy, correo verificado con código de un solo uso, rate limit de registro, sesión única por cuenta).

**Estado en los documentos del curso:** la Actividad 3 ya incluye R16 y R17 en su matriz de trazabilidad y amplía R6 a "archivos". Falta, si el equipo lo decide, agregarlos a las Tablas 1–4 de la Tarea 2 (`Documentación/`, que no se edita sin acordarlo); la propuesta completa está en el plan E2E-3.

### 16.4 Tests mínimos por riesgo
| R | Servicio | Tests |
|---|---|---|
| 01 | rooms | `key_hash` empieza con `$argon2id$`; la clave en claro no aparece en ninguna columna |
| 02 | shared, auth, chat | El servicio no arranca sin secretos; `rotate_kek` (auth) y `rotate kek/room` (chat) mantienen todo legible; los mensajes en BD no contienen el texto en claro |
| 03 | audit | `audit_app` no puede `UPDATE/DELETE/TRUNCATE`; una alteración hecha con el owner la detecta `verify`; `service` sale del token aunque el payload diga otra cosa |
| 04 | auth | Bloqueo tras 5 fallos; sin TOTP no hay acceso; código TOTP reusado rechazado; el token cambia al pasar a `full` |
| 05 | rooms, media, audit (+e2e) | Rutas de admin sin `X-Admin-Id` del gateway → 401; e2e: una cookie de sala o de usuario en `/api/admin/*` → 401 |
| 06 | media, chat (+e2e) | PNG y WAV con LSB al 10 % → cuarentena; PNG limpio → aceptado; una versión sanitizada con un hallazgo estructural no se publica ni se libera (RS-36); datos anexados a cada uno de los 8 formatos binarios → cuarentena; GIF con comentario de más de 1 KB, MP3 con frame `GEOB`, MP4 con bytes no referenciados en el `mdat`, PDF con objetos huérfanos y DOCX con parte suelta o texto oculto → cuarentena; TXT con ancho cero, selectores de variación o SNOW → cuarentena; tras sanitizar, el plano LSB cambia y cada formato sanitizado ya no tiene hallazgos estructurales; mensaje de chat con caracteres invisibles → se entrega sin ellos y se audita `msg.sanitized` |
| 07 | chat (+e2e) | WS con `Origin` ajeno → 4403; trama alterada → 4400 + auditoría critical; *hello* firmado verificable; vectores; e2e: 301 en http |
| 08 | rooms | Rate limit al unirse por usuario, IP, dispositivo y sala; respuesta igual para clave mala, sala inexistente, cerrada o el general; clave débil rechazada al crear la sala |
| 09 | media | Firma que no coincide, archivo sobre el tope de su categoría, decompression bomb, GIF con más de 300 cuadros, zip bomb o ruta con `..` en un DOCX, TXT con bytes binarios → rechazo; PDF con JavaScript o adjuntos y DOCX con macros u OLE → `rejected (active)`; ClamAV caído → 503; EICAR → rechazo (`clamav`) |
| 10 | chat | Rate de mensajes → 4429; trama mayor a 16 KB → 4413; sin `hello` en 10 s → 4400 |
| 11 | todos | `<svc>_app` no puede `CREATE TABLE`/`DROP` ni conectarse a otra BD |
| 12 | media | Firma inválida, vencida, de otra sesión o de otra sala → 404; archivo en cuarentena no descargable |
| 13 | auth, rooms (+e2e) | Login de una cuenta con sesión activa en otro dispositivo → 409; el logout corta la sesión de sala y el WebSocket; desde el mismo dispositivo → reemplaza la anterior; dos logins concurrentes → solo uno gana (índice único); la sesión vencida por inactividad libera la cuenta; `verify-user` y `verify-session` con otra cookie de dispositivo → 401; ingreso a una sala con una sesión de sala activa en otro dispositivo → 409; el cupo queda libre tras `leave` |
| 14 | chat | El `from` del payload se ignora; AAD de otra sala → 4400; `seq` repetido → 4408 |
| 15 | rooms | 20 entradas concurrentes con cupo 5 → exactamente 5 aceptadas; el `CHECK` impide superar el máximo |
| 16 | shared y cada servicio (+e2e) | Sin token → 401; token de un llamador fuera de la allowlist → 403; cabeceras de identidad (incluidas `X-User-*`) sin el token del gateway → ignoradas (401); e2e: `/internal/*` → 404 y cabeceras falsificadas ignoradas |
| 17 | auth (+e2e) | `password_hash` empieza con `$argon2id$` y ni la contraseña ni el código aparecen en ninguna columna; bloqueo tras 5 fallos por cuenta y tras 20 por IP; mismo error para una cuenta inexistente; contraseña débil o igual al correo → 422; registro que no revela cuentas y que no permite secuestrar un correo; sin verificar no hay sesión; código con vencimiento, 5 intentos y límite por IP; alias único por forma canónica y sin homoglifos; rate limit de registro por dispositivo e IP; una cookie de usuario no sirve en `/api/admin/*` y una de admin no sirve para ingresar a una sala; e2e: sin cuenta no se ingresa |

`docs/trazabilidad-riesgos.md` tiene la tabla `Riesgo | Control | Servicio/Archivo(s) | Test(s) | Estado`. Se actualiza con cada cambio de seguridad (comando `/risk-check`) y se copia al informe final.

### 16.5 CI (`.github/workflows/ci.yml`)
- Job `services`, en matriz `[shared, auth, rooms, chat, media, audit]` con servicio `postgres:17`: `ruff check` (incluye complejidad ciclomática ≤ 10, `C90`), `ruff format --check`, `pytest -m "not clamav" --cov=<paquete> --cov-fail-under=80`, `bandit -q -ll -r <paquete>` y `pip-audit`. La entrada `media` instala antes ffmpeg (`apt-get install ffmpeg`).
- Job `secrets`: gitleaks sobre todo el historial con `.gitleaks.toml` (las pruebas usan valores fijos documentados).
- Job `frontend`: `npm ci`, `npx vitest run` (incluye el contraste de RNF-09), `npm run build`, `npm audit --audit-level=high`.
- Job `gateway`: `nginx -t` y `gateway/tests/run.sh` (enrutamiento con servicios falsos).
- La rama `main` exige *pull request* con una aprobación, la plantilla de verificación de seguridad (`.github/pull_request_template.md`) y los cuatro jobs en verde (RS-37).
- El e2e no corre en CI (ClamAV es demasiado pesado).

---

## 17. Contexto para Claude Code
| Archivo | Contenido |
|---|---|
| `CLAUDE.md` | (~120 líneas) qué es, la arquitectura en 10 líneas, comandos (compose, pruebas por servicio, e2e, migraciones, `create_admin`, `gen_secrets`), mapa del repo, invariantes de seguridad, enlaces al spec, al plan y a la trazabilidad, y una sección **"Estado actual"** que se actualiza al cerrar cada fase |
| `CLAUDE.local.md` | (gitignored) cada integrante anota su rol (A/B/C), sus servicios y sus preferencias |
| `.claude/settings.json` | Allow: pytest, ruff, alembic, `docker compose`, npm/npx, git (lectura). Deny: `Read(deploy/secrets/**)`, `Read(deploy/certs/**)`, `Read(**/.env)`. Registra el hook |
| `.claude/rules/security.md` | Invariantes globales: nunca `ws://` ni HTTP en claro hacia el cliente; nunca secretos en el código; identidad y sala salen de la sesión verificada; queries parametrizadas; errores genéricos y detalle a auditoría; auditar todo rechazo; Argon2id; no registrar datos sensibles; fallar cerrado |
| `.claude/rules/microservices.md` | Nunca leer cabeceras de identidad sin verificar el token del gateway (usar `shared.identity`); `/internal/*` siempre con `require_caller` y allowlist; cada servicio toca **solo su BD**; las llamadas entre servicios pasan por `ServiceClient`; un servicio nuevo necesita red, secretos, rol de BD y entrada en la allowlist |
| `.claude/rules/backend.md` | `paths: services/**`: FastAPI async, paquete `<svc>_svc`, `create_app(settings, …)` inyectable, migraciones con GRANT explícito, dependencias de `shared` |
| `.claude/rules/frontend.md` | `paths: frontend/**`: TS estricto, nunca `dangerouslySetInnerHTML`, toda la cripto en `lib/crypto.ts`, `CryptoKey` no extraíbles y solo en memoria, nada en `localStorage`/`sessionStorage`, sin estilos ni scripts inline, sin `StrictMode` (abre y cierra el WS dos veces) |
| `.claude/rules/testing.md` | `paths: **/tests/**, e2e/**`: Postgres real, `test_rNN_*` por riesgo, vecinos con `MockTransport`, actualizar la trazabilidad |
| `.claude/commands/risk-check.md` | `/risk-check`: contrasta el diff con R1–R17 y las reglas; señala controles rotos o sin test; actualiza la trazabilidad |
| `.claude/skills/stego-analysis/SKILL.md` | Lista blanca y algoritmos por formato (§12), umbrales, sanitización, calibración y cómo agregar un formato |
| `.claude/skills/crypto-protocol/SKILL.md` | Protocolo (§10–11): handshake firmado, tramas, AAD, códigos, vectores, rotación |
| `.claude/agents/security-auditor.md` | Subagente de solo lectura: revisa cambios contra la Tabla 3, R16, R17, OWASP Top 10 y el modelo de confianza (§4.3) |
| `.claude/hooks/guard.py` | `PreToolUse` sobre `Edit\|Write`: bloquea `ws://`, bloques `PRIVATE KEY` y secretos literales de ≥ 16 caracteres fuera de `tests/`, `docs/`, `.claude/` y `CLAUDE.md`. En Python, multiplataforma |

---

## 18. Fases y reparto
Roles: **A** = auth + rooms + gateway; **B** = librería compartida + audit + chat; **C** = frontend + media. El equipo asigna los nombres en `CLAUDE.local.md`.

| Semana | A | B | C | Hito verificable |
|---|---|---|---|---|
| **S1** 13–19 oct | *Días 1–2, todos:* `.claude/` + `CLAUDE.md`, librería compartida, `Dockerfile` único, Postgres con 5 BD + `gen_secrets` + mkcert, esqueleto del gateway, CI. Luego A: `auth` completo + `auth_request` de admin | Servicio `audit` + vectores cripto (con firma) | SPA + `crypto.ts` (vectores) + login de admin | El admin entra vía gateway con TOTP y el evento aparece en `audit` |
| **S2** 20–26 oct | Cuentas de usuario en `auth` (correo verificado, alias, login, `verify-user`) + GW-2 + `rooms` completo (CRUD, canal general, membresías, entrada con cupo, `verify-session`, barrido, `kick`) | FND-9 (correlación, métricas) + AUD-4 + `chat` completo (handshake firmado, tramas, limpieza de mensajes, historial en orden, inactividad, heartbeat) | FND-10 (CI y modelo de amenazas) + UI de registro, verificación, alias, salas y chat; dashboard (salas, auditoría, estado) | Dos usuarios con correo verificado chatean vía gateway desde dos navegadores, en el general y en una sala; e2e de chat en verde |
| **S3** 27 oct–2 nov | Hardening del gateway, test de roles por servicio (R11), rotación de claves, VPS + Let's Encrypt + reenvío de correo, respaldos y monitor de disponibilidad | Con C: publicación de archivos en `chat`, URLs firmadas; formatos de audio y video (MP3, WAV, MP4); prueba de carga | `media`: pipeline con reanálisis, imágenes, documentos y texto, sanitización y cuarentena + UI de archivos y cuarentena; tiempos por formato, pruebas con personas, Lighthouse y navegadores | Demo en el VPS; 17/17 riesgos con test; trazabilidad completa; `docs/evidencias-rnf.md` |

**Orden de recorte si hay atraso:** chi² DCT de JPEG y detector de MP3Stego (*stretch*) → GIF → análisis RS (quedan chi² + entropía + estructura) → WAV (el audio queda en MP3) → DOCX (los documentos quedan en PDF) → historial → `rotate room` → UI de verificación de la cadena → e2e reducido al camino feliz + reglas del gateway.
**No se recorta nunca:** MFA del admin, cuenta obligatoria con correo verificado y sesión única por dispositivo, reanálisis de la versión sanitizada, cobertura y complejidad en la CI, solo TLS 1.3, *hello* firmado, tokens de servicio, Argon2id, cuarentena, sanitización, auditoría encadenada, los tests por riesgo, ni al menos un formato por categoría (imagen, audio, video, documento y texto) con validación, análisis y sanitización.

---

## 19. Configuración (variables no secretas)
| Variable | Servicios | Valor por defecto |
|---|---|---|
| `ALLOWED_ORIGINS` | todos | `https://localhost` (en dev se agrega `https://localhost:5173`) |
| `DB_HOST` / `DB_PORT` | todos | `db` / `5432` |
| `AUDIT_URL` · `ROOMS_URL` · `CHAT_URL` | según §4.4 | `http://audit:8000` · `http://rooms:8000` · `http://chat:8000` |
| `CURRENT_KEK_VERSION` | auth, chat | `1` |
| `ADMIN_IDLE_MIN` / `ADMIN_ABS_HOURS` | auth | `30` / `8` |
| `LOGIN_MAX_FAILS` / `LOGIN_WINDOW_MIN` / `LOGIN_DELAY_BASE` | auth | `5` / `15` / `0.25` (la ventana y el retraso valen también para usuarios) |
| `USER_IDLE_MIN` / `USER_ABS_HOURS` | auth | `15` / `12` |
| `USER_LOGIN_MAX_FAILS` / `USER_LOGIN_MAX_FAILS_IP` | auth | `5` / `20` |
| `REGISTER_MAX_PER_DEVICE` / `REGISTER_MAX_PER_IP` / `REGISTER_WINDOW_MIN` | auth | `3` / `30` / `60` |
| `VERIFY_CODE_TTL_MIN` / `VERIFY_MAX_ATTEMPTS` / `VERIFY_MAX_FAILS_IP` | auth | `15` / `5` / `20` |
| `RESEND_MAX_PER_WINDOW` / `RESEND_WINDOW_MIN` | auth | `3` / `60` |
| `SMTP_HOST` / `SMTP_PORT` / `MAIL_FROM` / `ROOMS_URL` | auth | `mailer` / `1025` / `Chat seguro <no-responder@chat-seguro.local>` / `http://rooms:8000` |
| `JOIN_MAX_FAILS_USER` / `_IP` / `_DEVICE` / `_ROOM` / `JOIN_WINDOW_MIN` | rooms | `5` / `5` / `10` / `20` / `10` |
| `ROOM_SESSION_GRACE_S` / `SWEEP_INTERVAL_S` | rooms | `120` / `30` |
| `ROOM_SESSION_IDLE_MIN` / `HEARTBEAT_INTERVAL_S` / `HANDSHAKE_TIMEOUT_S` | chat | `15` / `30` / `10` |
| `WS_RATE_PER_S` / `WS_BURST` / `WS_MAX_FRAME` | chat | `5` / `10` / `16384` |
| `HISTORY_SIZE` / `SIGNED_URL_TTL_S` | chat | `50` / `60` |
| `UPLOAD_MAX_BYTES` / `UPLOAD_PER_MIN` / `MAX_IMAGE_PIXELS` / `GIF_MAX_FRAMES` | media | `26214400` / `5` / `20000000` / `300` |
| `MAX_BYTES_IMAGE` / `_AUDIO` / `_VIDEO` / `_DOCUMENT` / `_TEXT` | media | `5242880` / `10485760` / `26214400` / `10485760` / `1048576` (5, 10, 25, 10 y 1 MB) |
| `STEGO_CHI2_P` / `STEGO_RS_RATE` / `STEGO_WAV_RATE` / `STEGO_ENTROPY_TRIGGER` / `STEGO_GIF_PALETTE_TRIGGER` / `STEGO_TXT_TRAILING` | media | `0.95` / `0.08` / `0.08` / `off` / `off` / `64` |
| `STEGO_TIMEOUT_S` / `SANITIZE_TIMEOUT_S` / `MEDIA_WORKERS` | media | `10` / `30` / `2` |
| `CLAMAV_HOST` / `CLAMAV_PORT` / `MEDIA_DIR` | media | `clamav` / `3310` / `/data` |
| `LOG_FORMAT` | todos | `json` en la imagen Docker (sin definir en las pruebas) |
| `RESOURCE_ALERT_PCT` / `RESOURCE_ALERT_MIN` / `RESOURCE_SAMPLE_S` | todos | `80` / `5` / `30` |

**Desarrollo del frontend:** `npm run dev` (Vite en `https://localhost:5173` con los certificados de mkcert) con `server.proxy` de `/api`, `/ws` y `/chat-key.json` hacia `https://localhost` (el gateway). Las cookies `__Host-` exigen https también en desarrollo.

---

## 20. Riesgos del proyecto y preguntas abiertas
| Tema | Mitigación / decisión pendiente |
|---|---|
| Microservicios en 3 semanas | `Dockerfile` único, librería compartida, compose con anclas YAML, días 1–2 dedicados a infraestructura, lista de recorte |
| Fecha exacta de entrega desconocida | Hitos semanales demostrables por sí solos |
| El docente puede pedir más formatos | Registro `FORMATS` (§12.2) y guía de §12.11 |
| 9 formatos en la semana 3 | Un módulo por formato sobre reglas comunes (§12.3); B apoya a C con audio y video; orden de recorte por formato (§18) |
| ffmpeg y los parsers de documentos amplían la superficie de ataque | Demuxer forzado, `-protocol_whitelist file`, sin shell, límites de CPU y memoria y timeout (§12.9); XML sin DTD; contenedor no-root, `read_only` y sin salida a internet |
| Registro abierto: cuentas desechables para esquivar el bloqueo por cuenta | Rate limit de registro por dispositivo e IP; el ingreso a salas también se limita por IP, dispositivo y sala |
| ClamAV usa ~1.5–3 GB de RAM y tarda minutos en cargar firmas | VPS con ≥ 4 GB; healthcheck de clamd con `start_period`; en ARM usar `clamav/clamav-debian` (variable `CLAMAV_IMAGE`); `StreamMaxLength 30M` para el video |
| `jpegio` puede no tener wheels para Python 3.13 | Es *stretch*; JPEG queda cubierto por estructura + recodificación |
| Falsos positivos del estegoanálisis en fotos y grabaciones reales | Calibración con ≥ 30 imágenes y ≥ 20 WAV; la cuarentena (no el rechazo) permite que el admin libere |
| R16 y R17 no están en el documento SGSI de la Tarea 2 | La Actividad 3 ya los incluye; el equipo decide si actualiza la Tarea 2 (§16.3) |
| El correo no llega (proveedor, spam, cuota) | Mailpit reenvía con STARTTLS a un proveedor con dominio verificado; reenvío de código con límite; el registro responde igual y queda `mail.unavailable` |
| Mailpit como reenviador en el VPS | Su bandeja web no se publica; solo `mailer` sale a internet; alternativa: reemplazarlo por un relay Postfix sin cambiar `auth` |
| Pruebas de carga desde una sola máquina | El gateway admite 20 WebSocket por IP: cada cliente de carga corre en su propio contenedor (§21.2) |
| Proveedor del VPS sin definir | Oracle Cloud Free (ARM, 24 GB) o DigitalOcean/AWS; el Compose es idéntico |

---

## 21. Requisitos no funcionales y de desarrollo seguro (Actividad 3)

La Actividad 3 especifica 21 RF, 19 RNF y 39 RS. Los RF y la mayoría de los RS ya estaban cubiertos por el diseño; esta sección agrega lo que faltaba y deja el mapa completo de dónde se cumple y cómo se demuestra cada uno.

### 21.1 Monitoreo y correlación (RNF-18, RNF-19, RS-20)
- **Id de correlación:** el gateway genera `X-Request-ID` (`$request_id`) y sobrescribe el del cliente. Cada servicio lo toma (o crea uno si falta), lo pone en sus registros, lo reenvía a los servicios que llama (`ServiceClient`) y lo manda a audit, que lo guarda en `details.request_id` dentro del hash de la cadena. Vuelve una sola vez en la respuesta.
- **Registros:** con `LOG_FORMAT=json`, una línea JSON por registro con `ts`, `service`, `level`, `request_id`, `logger` y `msg`, y una línea por petición con `status` y `ms`, **sin query string**. uvicorn corre con `--no-access-log`. El gateway escribe el mismo formato.
- **Métricas:** cada servicio expone `GET /api/admin/metrics` (solo admin; el gateway la publica como `/api/admin/metrics/<svc>`): `uptime_s`, peticiones, respuestas por estado, rechazos (4xx), latencia p50/p95 de las últimas 1000 peticiones, CPU y memoria, y las propias (`chat`: conexiones abiertas; `rooms`: ocupación de cada sala). El panel las muestra en la pestaña *Estado* cada 10 s.
- **Alerta de consumo:** cada servicio lee CPU y memoria de cgroup v2 cada 30 s, contra sus límites del compose. Si alguna pasa el 80 % durante 5 minutos seguidos, emite una advertencia `resource.high`, que el panel muestra en ≤ 10 s; se rearma cuando baja.
- **Disponibilidad (RNF-04):** `GET /api/status` (chat y su BD) para un monitor externo cada 60 s.

### 21.2 Rendimiento y escala (RNF-01, RNF-02, RNF-03, RNF-06, RNF-07, RNF-14)
- `perf/carga.py`: N participantes por proceso (≤ 20 por la regla de R10) inician sesión, se unen, **entran en paralelo** (p95 ≤ 2 s, RNF-02) y conversan midiendo la latencia de extremo a extremo con cifrado incluido (p95 ≤ 500 ms, RNF-01). Para 500 conexiones se lanzan 25 contenedores, cada uno con su IP (RNF-06); las cuentas salen de `python -m auth_svc.seed_users`. Unirse con clave ocurre una vez por cuenta y queda fuera de la medición (el gateway lo limita a 1 por segundo por IP).
- `services/media/tools/bench_formats.py`: percentil 95 por formato con muestras del tamaño máximo; objetivo: análisis ≤ `STEGO_TIMEOUT_S` (10 s) y sanitización ≤ `SANITIZE_TIMEOUT_S` (30 s) (RNF-03).
- Pruebas dentro de los servicios: consulta de auditoría con 100 000 eventos ≤ 2 s (RNF-07) y tres participantes con 90 mensajes intercalados que llegan a todos sin pérdidas, sin duplicados y en el mismo orden que el historial (RNF-14; `chat` guarda y difunde bajo un candado por sala).

### 21.3 Calidad y control de cambios (RNF-10, RNF-11, RS-30, RS-32, RS-33, RS-34, RS-37)
- Cobertura de líneas ≥ 80 % por servicio y complejidad ciclomática ≤ 10 por función, exigidas por la CI (§16.5).
- gitleaks en todo el historial; bandit y pip-audit.
- `main` protegida: PR con una aprobación, plantilla con lista de verificación de seguridad y los jobs en verde.
- `docs/modelo-amenazas.md` (STRIDE por componente y límites de confianza), elaborado antes de implementar y revisado ante cambios.
- `docs/trazabilidad-riesgos.md` suma la columna *Control ISO/IEC 27001:2022*; cada control de aplicación (ISO/IEC 27034) remite a su prueba. Es referencia de diseño, no certificación.

### 21.4 Recuperación (RNF-15, RNF-16, RNF-17)
- Las salas, membresías e historial viven en PostgreSQL: sobreviven a reinicios (RNF-15).
- `deploy/backup.sh`: `pg_dumpall` + volumen de archivos, cifrados con `age` para claves públicas (la privada no vive en el servidor), diarios y con 14 días de retención; `deploy/restore.sh` los restaura en un entorno con los mismos secretos. Objetivo: pérdida ≤ 24 h y restauración ≤ 1 h; después, la cadena de auditoría verifica y el historial se descifra con la KEK (RNF-16). Los secretos se respaldan aparte y fuera de línea.
- `restart: unless-stopped`: un servicio que termina vuelve a `healthy` en ≤ 60 s; los cupos de las sesiones caídas se liberan con el barrido (RNF-17).

### 21.5 Mapa Actividad 3 → spec → prueba

| Requisitos | Dónde | Prueba o evidencia |
|---|---|---|
| RF-01, RF-02…RF-09 (admin y salas) | §8.1, §9.1, §9.4, §14.3 | `services/auth/tests/test_r04_*`, `services/rooms/tests/test_r01_*`, `test_r05_admin.py`, `services/audit/tests/test_r05_admin.py` |
| RF-10 (cuarentena) | §9.8, §12.9 | `services/media/tests/test_cuarentena.py` (incluye el reanálisis) |
| RF-11, RF-12, RF-13 (ingreso, salida, cierre automático) | §9.3, §9.4 | `services/rooms/tests/test_join.py`, `test_enter.py`, `test_ciclo_de_vida.py`; `services/chat/tests/test_ciclo.py` |
| RF-14…RF-16 (mensajería y tipo de sala) | §9.5, §8.1 | `services/chat/tests/test_r10_limites.py`, `test_historial.py`, `test_r06_mensajes.py`, `test_archivos.py` |
| RF-17…RF-19 (archivos) | §9.6, §9.7, §12 | `services/media/tests/test_r06_*`, `test_r09_*`, `test_r12_descarga.py` |
| RF-20, RF-21 (registro, login y logout) | §9.2 | `services/auth/tests/test_r17_cuentas.py`, `test_correo_y_alias.py`, `test_r13_sesion_unica.py`; `e2e/test_chat.py::test_rs07_*` |
| RNF-01, RNF-02, RNF-06 | §21.2 | `perf/carga.py` (E2E-4) |
| RNF-03 | §21.2 | `tools/bench_formats.py` (MED-10, E2E-4) |
| RNF-04, RNF-12, RNF-15, RNF-16, RNF-17 | §21.1, §21.4 | E2E-4 (monitor externo, despliegue cronometrado, reinicios, simulacro de restauración) |
| RNF-05 | §9.6, §13 | `test_r09_clamav_caido_responde_503`; el gateway responde 503 si `media` cae |
| RNF-07, RNF-14 | §21.2 | `services/audit/tests/test_rnf07_rnf19.py`, `services/chat/tests/test_rnf14_orden.py` |
| RNF-08, RNF-09, RNF-13 | §21.2, plan FE-2 | prueba con 5 personas, Lighthouse ≥ 90 y navegadores (E2E-4); `frontend/src/lib/contrast.test.ts` |
| RNF-10, RNF-11 | §16.5, §21.3 | CI (cobertura y `C90`) |
| RNF-18, RNF-19 | §21.1 | `services/shared/tests/test_observabilidad.py`, `test_rnf18_*` de rooms y chat, `gateway/tests/check_routes.py`, `e2e/test_gateway.py::test_rnf*` |
| RS-01…RS-29, RS-31, RS-35 | §4.3, §9–§15 (riesgos R1–R17) | `docs/trazabilidad-riesgos.md` |
| RS-07 (cierre de sesión revoca las conexiones) | §9.2, §9.4 | `test_logout_libera_la_cuenta_y_corta_la_sala`, `test_logout_de_la_cuenta_corta_la_sala`, `e2e/test_chat.py::test_rs07_*` |
| RS-12 (en reposo) | §3, §11.2 | mensajes cifrados (`test_r02_store.py`); los archivos no se cifran en reposo (fuera de alcance, §3) |
| RS-19, RS-36 (liberación y reanálisis) | §9.6, §9.8, §12.9 | `test_rs36_*` en `services/media/tests/` |
| RS-30, RS-32, RS-33, RS-34, RS-37 | §16.5, §21.3 | CI, `docs/modelo-amenazas.md`, trazabilidad con ISO 27001, reglas de la rama |
| RS-38, RS-39 (cuentas y autorización por cuenta) | §9.2, §9.3 | pruebas de R13 y R17; `test_solo_los_miembros_entran`, `test_el_alias_es_el_de_la_cuenta_aunque_el_cliente_mande_otro` |
