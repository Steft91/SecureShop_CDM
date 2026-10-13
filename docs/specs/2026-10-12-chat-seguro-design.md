# Spec: Salas de Chat Seguras — Diseño de arquitectura (microservicios)

| | |
|---|---|
| **Fecha** | 2026-10-12 · **Revisión 2:** 2026-10-13 (arquitectura de microservicios; reemplaza el monolito modular de la revisión 1) |
| **Autores** | Zaith Alejandro Manangón Vinueza, Stefany Maricela Díaz Antun, Andrés Isaias Cedeño Cuenca |
| **Asignatura** | Software Seguro — Proyecto Integrador |
| **Estado** | Aprobado (diseño). Siguiente paso: plan de implementación en `docs/plans/` |
| **Fuente de requisitos** | `Documentación/Tarea 2/Actividad2_SGSI_Proyecto_Integrador.md` (enunciado + Tablas 1–4 de riesgos) |
| **Plazo** | ~3 semanas: 13 oct – 2 nov 2026 |

---

## 1. Propósito y criterios de éxito

Construir la aplicación de **salas de chat seguras** del proyecto integrador con **arquitectura de microservicios**, igual que en SecureShop (Tarea 1): un punto de entrada común, un servicio por dominio y una base de datos por servicio. El sistema debe implementar y **demostrar con pruebas** los 15 tratamientos de riesgo de la Tarea 2 (Tabla 3), más el riesgo R16 que introduce la propia arquitectura (§16.3).

**Criterios de éxito (definición de "terminado"):**
1. Un admin con usuario + contraseña + TOTP crea salas con ID único, clave, cupo y tipo (texto / multimedia / ambos).
2. Dos o más navegadores intercambian mensajes cifrados en una sala. Un alias no puede estar activo desde dos dispositivos.
3. Una imagen con LSB embebido termina en **cuarentena**, genera una alerta y queda en auditoría. Una imagen limpia se entrega sanitizada.
4. **Microservicios:** un gateway como único punto de entrada y 5 servicios (`auth`, `rooms`, `chat`, `media`, `audit`). Cada servicio tiene su propia BD, su propia imagen y su propio job de migración, y se despliega por separado (`docker compose up -d --build <servicio>`).
5. Los **16 riesgos** (R1–R15 de la Tarea 2 + R16) tienen al menos un test automatizado en verde, mapeado en `docs/trazabilidad-riesgos.md`.
6. Todo el sistema corre con un comando en local y en un VPS con certificado válido.

---

## 2. Requisitos del enunciado → decisiones

| Requisito | Decisión |
|---|---|
| Admin autenticado con usuario/contraseña gestiona salas | Servicio `auth`: Argon2id + TOTP obligatorio; primer admin por CLI; sin credenciales por defecto. CRUD de salas en `rooms` |
| Sala: ID único, clave, cupo máximo, tipo | Tabla `rooms` (BD `rooms`): `code` UNIQUE (normalizado a minúsculas), `key_hash` Argon2id, `max_participants`, `mode` |
| Un usuario se conecta desde un único dispositivo | Usuarios **sin cuenta**: alias + ID de sala + clave. Alias único activo por sala (índice único parcial). La sesión queda atada a la cookie de dispositivo y se verifica en el gateway en **cada** request. **Política: se rechaza el nuevo ingreso** |
| Acceso condicionado a ID + clave | Argon2id, rate limit por IP/dispositivo/sala, error genérico |
| Confidencialidad, integridad y autenticidad; justificar algoritmos, protocolos y gestión de claves | TLS 1.3 hasta el gateway + **cifrado por conexión en capa de aplicación** entre navegador y `chat` (ECDH P-256 con *hello* firmado → HKDF-SHA256 → AES-256-GCM con AAD) + envelope encryption en reposo (DEK por sala, KEK propia de `chat`) |
| Análisis de archivos y estegoanálisis con alertas, auditoría y política | Servicio `media`: firma → validación → ClamAV → estegoanálisis → **cuarentena** / rechazo / sanitización. Alertas en el servicio `audit` |
| *(Docente)* Microservicios como en SecureShop | Gateway Nginx + 5 servicios por dominio + 5 BD (una por servicio, roles aislados) |

**Decisiones de contexto tomadas con el equipo:**
- Backend **Python 3.13 + FastAPI** en todos los servicios. Cliente **web SPA (React + TypeScript)**.
- Despliegue: **Docker Compose local** y el **mismo Compose en un VPS** (Let's Encrypt).
- Multimedia: **solo PNG y JPEG** por ahora, con un **punto de extensión** para agregar formatos (§12.1).
- Comunicación interna: **REST síncrono + un token por servicio** (sin broker).
- BD: **un contenedor PostgreSQL, una base de datos y un par de roles por servicio**.
- Gateway: **Nginx con `auth_request`**. Se descartaron: JWT verificado en cada servicio (no hay revocación inmediata), gateway propio en FastAPI (habría que reimplementar el proxy de WebSocket) y Traefik/Kong (otra herramienta que aprender).
- Modelo criptográfico **B** (cifrado en capa de aplicación sobre TLS). Se descartaron A (solo TLS) y C (E2E puro, que impide el estegoanálisis en el servidor).

---

## 3. Alcance, fuera de alcance y limitaciones conocidas

**Dentro:** todo lo de la sección 2, el panel de admin (salas, cuarentena, auditoría), las pruebas por servicio y e2e, CI, el despliegue local y en el VPS, y el contexto para Claude Code.

**Fuera (YAGNI, con el disparador que justificaría agregarlo):**
| Omitido | Agregar cuando |
|---|---|
| Broker de mensajes (RabbitMQ/NATS) | Haya consumidores asíncronos reales o más de una instancia por servicio |
| mTLS / service mesh entre servicios | El sistema salga de una sola máquina o lo exija el docente (ver limitación 3) |
| Varias réplicas por servicio | Haga falta escalar `chat` (requiere pub/sub y un almacén compartido de claves) |
| HashiCorp Vault | Haya más de un servidor o se requiera rotación automática |
| Cifrado en reposo de archivos | Lo pida el docente (los archivos están fuera del webroot y se sirven autenticados) |
| Formatos distintos de PNG/JPEG | El docente los especifique (§12.6) |
| Cuentas de usuario final | Cambie el enunciado |
| `.mcp.json` | Usen GitHub Issues/Projects u otra integración externa |

**Limitaciones conocidas (se declaran en el informe):**
1. `chat` ve el texto plano de los mensajes por diseño (para validar, persistir y auditar) y `media` ve los archivos (para analizarlos). La confianza en esos servicios es un supuesto explícito.
2. Identidad basada en alias: quien conoce la clave de la sala puede entrar con **otro** alias desde otro dispositivo; para el sistema eso es otro participante, limitado por el cupo.
3. **Tramo interno en HTTP plano.** TLS termina en el gateway; las llamadas gateway→servicio y servicio→servicio viajan en HTTP dentro de redes Docker internas.
   - Los **mensajes** siguen protegidos en ese tramo por el cifrado de aplicación, y el *hello* firmado impide un MITM activo (§10.1).
   - Los **tokens de servicio y los archivos subidos** viajan en claro dentro de la red interna.
   - Mitigaciones: 4 redes segmentadas, `cap_drop: ALL` (sin `NET_RAW` no hay ARP spoofing ni sniffing desde un contenedor comprometido) y tokens rotables. Mejora futura: mTLS.
4. Una instancia por servicio: las claves de conexión viven en memoria de `chat` y la difusión ocurre dentro de ese proceso.
5. El estegoanálisis es estadístico. Esquemas adaptativos o LSB-matching (±1) pueden evadir chi²; la **sanitización** (§12.5) destruye payloads LSB aunque no se detecten.
6. `audit` es un punto único de falla para las operaciones que otorgan acceso (fallan cerradas con 503 si `audit` no responde, §14.4). Es una decisión deliberada a favor de la trazabilidad.

---

## 4. Arquitectura

### 4.1 Vista general
```
Navegador (React SPA + WebCrypto)
   │  HTTPS / WSS — solo TLS 1.3
   ▼
┌─ gateway (Nginx) ── redes: public, apps ─────────────────────────────────────┐
│ TLS · HSTS · CSP · rate limit · SPA estática · /chat-key.json                 │
│ auth_request → auth /internal/verify-admin  |  rooms /internal/verify-session │
│ Sobrescribe X-Admin-* / X-Session-* · inyecta su X-Service-Token              │
└───┬───────────┬────────────┬─────────────┬──────────────┬────────────────────┘
    ▼           ▼            ▼             ▼              ▼
  auth        rooms ◄─────► chat ◄─────── media ─────► clamav (red scan)
    │           │            │             │
    └───────────┴─────┬──────┴─────────────┴──── POST /internal/events ──► audit
                      ▼  (red data)
          PostgreSQL 17: BD auth · rooms · chat · media · audit
```

### 4.2 Servicios
| Servicio | Responsabilidad | BD (tablas) | Riesgos |
|---|---|---|---|
| **gateway** | Único punto de entrada: TLS, cabeceras de seguridad, rate limit perimetral, enrutamiento, autenticación delegada (`auth_request`), SPA estática | — | 7, 10, 16 |
| **auth** | Login de admin, TOTP, sesiones de admin, bloqueo; `verify-admin`; CLI `create_admin`; rotación de su KEK | `auth`: `admins`, `admin_sessions`, `failed_attempts` | 4, 5 |
| **rooms** | CRUD de salas, cookie de dispositivo, ingreso, cupo atómico, alias único, ciclo de vida de sesiones (salida, barrido); `verify-session` | `rooms`: `rooms`, `room_sessions`, `failed_attempts` | 1, 5, 8, 13, 15 |
| **chat** | WebSocket, handshake ECDH firmado, cifrado de tramas, mensajes cifrados en reposo (DEK por sala), historial, eventos de archivo, inactividad, heartbeat de sesiones | `chat`: `room_keys`, `messages` | 2, 7, 10, 14 |
| **media** | Subida, firma, ClamAV, estegoanálisis, sanitización, cuarentena, descarga con URL firmada, panel de cuarentena | `media`: `files` + volumen de archivos | 6, 9, 12 |
| **audit** | Recepción de eventos de todos los servicios, cadena de hash, consulta y verificación para el admin | `audit`: `audit_log` | 3 |

Cada servicio es un proyecto Python independiente (`services/<svc>/`, paquete `<svc>_svc`) que comparte una librería común (`services/shared/`, paquete `shared`) y una única plantilla de `Dockerfile` (argumento `SERVICE`).

### 4.3 Modelo de confianza
1. **Autenticación centralizada en el gateway.** Antes de enrutar, Nginx hace un `auth_request` a `auth` (rutas de admin) o a `rooms` (rutas de sesión de sala). Si responde 2xx, el gateway copia la identidad que devolvió (`X-Admin-Id`, `X-Admin-User` o `X-Session-Id`, `X-Room-Id`, `X-Alias`, `X-Room-Mode`) a la petición hacia el servicio. **Toda cabecera de identidad que mande el cliente se sobrescribe o se vacía** en todas las rutas.
2. **Autorización en cada servicio.** El servicio decide si esa identidad puede hacer la operación: rol de admin, pertenencia a la sala, modo de la sala.
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
   | rooms | gateway, chat |
   | chat | gateway, rooms, media |
   | media | gateway |
   | audit | gateway, auth, rooms, chat, media |
5. **Red:** los servicios no publican puertos y el gateway nunca enruta `/internal/*`.
6. **Claves aisladas:** `kek_auth` (TOTP) solo en `auth`; `kek_chat` (DEK de salas) y `chat_sign_key` solo en `chat`; `url_signing_key` solo en `chat` (firma) y `media` (verifica).

### 4.4 Comunicación interna (REST síncrono, timeout 3 s)
| Llamador → receptor | Endpoint | Cuándo | Si el receptor no responde |
|---|---|---|---|
| gateway → auth | `GET /internal/verify-admin` | cada `/api/admin/*` | 401 al cliente |
| gateway → rooms | `GET /internal/verify-session` | cada `/api/rooms/leave`, `/api/media/*`, `/ws` | 401 al cliente |
| rooms → chat | `POST /internal/sessions/{id}/kick` | salida, barrido, sala eliminada | Se registra y se continúa: la sesión ya terminó en `rooms` y el heartbeat la reconcilia |
| chat → rooms | `POST /internal/sessions/{id}/end` | cierre limpio, violación, inactividad | Se registra; el barrido de `rooms` la termina tras el período de gracia |
| chat → rooms | `POST /internal/sessions/heartbeat` | cada 30 s con las sesiones conectadas | Se reintenta en el siguiente ciclo |
| media → chat | `POST /internal/rooms/{room_id}/files` | archivo aceptado o liberado | 503 al que subió el archivo; el archivo queda huérfano e inaccesible (§9.6) |
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

Servicios Python: usuario no-root (uid 10001), `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, `read_only: true` con `tmpfs: /tmp`. `media` monta además el volumen `media_data` en `/data`.

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
│   │       ├── identity.py          dependencias require_gateway / require_admin / require_session
│   │       ├── audit_client.py      emisión de eventos con fallback a stdout
│   │       ├── web.py               create_base_app: errores JSON, /health, Origin/CSRF
│   │       └── testing.py           utilidades de prueba (BD de prueba, migraciones, clientes)
│   ├── auth/    auth_svc/  migrations/  tests/  pyproject.toml  requirements.lock  alembic.ini
│   ├── rooms/   rooms_svc/ …
│   ├── chat/    chat_svc/  …
│   ├── media/   media_svc/ … (tools/stego_lab.py)
│   └── audit/   audit_svc/ …
├── gateway/
│   ├── Dockerfile                   build multi-stage de la SPA + nginx
│   ├── nginx.conf
│   └── snippets/                    proxy-base.conf, proxy-public.conf, proxy-admin.conf, proxy-session.conf
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
│   ├── specs/  plans/
│   ├── crypto-vectors.json          vectores compartidos Python ↔ TypeScript
│   ├── trazabilidad-riesgos.md      riesgo → control → servicio/archivo → test → estado
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
| Cripto | `cryptography` (ECDH y ECDSA P-256, HKDF, AESGCM) | Primitivas auditadas, interoperan con WebCrypto |
| MFA | `pyotp` + `qrcode` | TOTP RFC 6238 |
| Imágenes | Pillow, numpy, scipy (`chi2.sf`) | Decodificación y estadística (solo `media`) |
| Antimalware | ClamAV (`clamav/clamav`, o `clamav/clamav-debian` en ARM) vía INSTREAM | Riesgo 9 |
| Gateway | Nginx 1.27 (`auth_request`) | TLS 1.3, rate limit, autenticación delegada |
| Front | React 19, Vite, TypeScript estricto, react-router, CSS plano | Sin librería de UI: menos superficie |
| Cripto en el front | WebCrypto (`crypto.subtle`) | Nativo, claves no extraíbles |
| Pruebas | pytest, httpx, pytest-timeout; vitest; e2e con httpx + `websockets` | |
| CI | GitHub Actions: ruff, pytest (matriz por servicio), bandit, pip-audit, npm audit | |

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
CREATE TABLE failed_attempts (
  id         bigserial PRIMARY KEY,
  key        text NOT NULL,                     -- 'user:<u>' | 'ip:<ip>'
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON failed_attempts (key, created_at);
```

### 7.2 BD `rooms`
```sql
CREATE TABLE rooms (
  id                   uuid PRIMARY KEY,
  code                 text UNIQUE NOT NULL CHECK (code ~ '^[a-z0-9_-]{3,32}$'),  -- normalizado a minúsculas
  key_hash             text NOT NULL,           -- $argon2id$...
  mode                 text NOT NULL CHECK (mode IN ('text','media','both')),
  max_participants     int  NOT NULL CHECK (max_participants BETWEEN 2 AND 50),
  current_participants int  NOT NULL DEFAULT 0,
  active               boolean NOT NULL DEFAULT true,
  created_by           uuid NOT NULL,           -- id del admin (vive en la BD auth)
  created_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (current_participants BETWEEN 0 AND max_participants)   -- respaldo del riesgo 15
);
CREATE TABLE room_sessions (
  id          uuid PRIMARY KEY,
  room_id     uuid NOT NULL REFERENCES rooms(id),
  alias       text NOT NULL,                    -- NFKC, 2–24 caracteres
  device_hash bytea NOT NULL,                   -- SHA-256 de la cookie de dispositivo
  token_hash  bytea UNIQUE NOT NULL,
  last_seen   timestamptz NOT NULL DEFAULT now(),   -- creación o último heartbeat de chat
  created_at  timestamptz NOT NULL DEFAULT now(),
  ended_at    timestamptz,
  end_reason  text
);
CREATE UNIQUE INDEX one_active_alias_per_room
  ON room_sessions (room_id, lower(alias)) WHERE ended_at IS NULL;          -- riesgo 13
CREATE TABLE failed_attempts (
  id         bigserial PRIMARY KEY,
  key        text NOT NULL,                     -- 'ip:<ip>' | 'device:<hash>' | 'room:<id>'
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
Payload en claro antes de cifrar: `{"from","body","ts"}` (texto) o `{"from","file_id","ts"}` (archivo).

### 7.4 BD `media`
```sql
CREATE TABLE files (
  id           uuid PRIMARY KEY,
  room_id      uuid NOT NULL,
  session_id   uuid NOT NULL,
  alias        text NOT NULL,
  storage_name text UNIQUE,                     -- uuid4 hex sin extensión; NULL si fue rechazado
  mime         text NOT NULL,                   -- 'unknown' si la firma no coincidió
  size         int  NOT NULL,
  sha256       bytea NOT NULL,                  -- del archivo original
  clean_sha256 bytea,                           -- de los bytes sanitizados que se publican (§9.5, paso 5)
  status       text NOT NULL CHECK (status IN ('clean','quarantined','rejected','released','deleted')),
  verdict      jsonb NOT NULL,                  -- motivo y métricas del análisis
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
  actor     text NOT NULL,                      -- 'admin:<u>' | 'session:<id>' | 'ip:<ip>' | 'system'
  action    text NOT NULL,
  target    text,
  ip        inet,
  details   jsonb NOT NULL DEFAULT '{}',
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
| POST | `/api/auth/login` | auth | — | `{username, password}` → cookie `__Host-admin` (etapa `preauth`) |
| POST | `/api/auth/totp` | auth | cookie preauth | `{code}` → sesión `full`; el token se rota |
| POST | `/api/auth/logout` | auth | cookie admin | Cierra la sesión |
| GET | `/api/auth/me` | auth | cookie admin | `{username}` |
| GET | `/api/device` | rooms | — | Pone la cookie `__Host-device` si no existe (204) |
| POST | `/api/rooms/join` | rooms | cookie de dispositivo | `{code, key, alias}` → cookie `__Host-room` + `{session_id, room: {id, code, mode}}` |
| POST | `/api/rooms/leave` | rooms | sesión | Termina la sesión (204) |
| GET / POST | `/api/admin/rooms` | rooms | admin | Listar / crear `{code, key, max_participants, mode}` |
| PATCH | `/api/admin/rooms/{id}` | rooms | admin | Cambiar `key`, `max_participants` (≥ participantes actuales) o `mode` |
| DELETE | `/api/admin/rooms/{id}` | rooms | admin | `active=false`; termina y expulsa sus sesiones |
| POST | `/api/media/files` | media | sesión | multipart `file` → `{file_id, status}` |
| GET | `/api/media/files/{id}?exp=&sig=` | media | sesión | Descarga de un archivo `clean` o `released` |
| GET | `/api/admin/quarantine` | media | admin | Archivos en cuarentena con su `verdict` |
| POST | `/api/admin/quarantine/{id}/release` | media | admin | Sanitiza, publica en la sala y marca `released` |
| DELETE | `/api/admin/quarantine/{id}` | media | admin | Borra el archivo físico y marca `deleted` |
| GET | `/api/admin/audit?min_severity=&after_id=&limit=` | audit | admin | Eventos con `id > after_id`, del más nuevo al más viejo |
| GET | `/api/admin/audit/verify` | audit | admin | Recorre la cadena → `{ok, broken_at}` |
| WS | `/ws` | chat | sesión | Canal de chat (§9.4, §10) |
| GET | `/chat-key.json` | gateway (estático) | — | `{"kid": "v1", "pub": "<b64url 65 B>"}` clave pública ECDSA del chat |

**Cookies:** todas con prefijo `__Host-` (Secure, Path=/, sin Domain), `HttpOnly` y `SameSite=Strict`. Ningún token es accesible desde JavaScript.

**CSRF:** además de SameSite=Strict, la dependencia `require_gateway` de la librería compartida rechaza con 403 (y audita `http.reject.origin`) los `POST/PATCH/DELETE` públicos cuyo `Origin` no esté en `ALLOWED_ORIGINS`.

**Validaciones de entrada:**
- `code`: se normaliza a minúsculas; `^[a-z0-9_-]{3,32}$`.
- Clave de sala: ≥ 12 caracteres, al menos 3 de 4 clases (minúsculas, mayúsculas, dígitos, símbolos) y distinta del `code`.
- `alias`: NFKC y `strip`; 2–24 caracteres de letras, dígitos, espacio, `_` y `-`.
- Mensaje: 1–2000 caracteres y sin caracteres de control salvo `\n` y `\t`.
- `max_participants`: 2–50.
- `username`: se normaliza a minúsculas; `^[a-z0-9_.-]{3,32}$`. Contraseña de admin: misma política que la clave de sala.

### 8.2 API interna (nunca enrutada por el gateway)
| Servicio | Método y ruta | Llamadores | Contrato |
|---|---|---|---|
| auth | `GET /internal/verify-admin` | gateway | Lee la cookie `__Host-admin` (sesión `full` vigente; desliza `last_seen`) → `204` + `X-Admin-Id`, `X-Admin-User` · `401` |
| rooms | `GET /internal/verify-session` | gateway | Lee `__Host-room` + `__Host-device` → `204` + `X-Session-Id`, `X-Room-Id`, `X-Alias` (UTF-8 *percent-encoded*), `X-Room-Mode` · `401` |
| rooms | `POST /internal/sessions/{id}/end` | chat | `{reason}` → termina la sesión (idempotente) y libera cupo · `204` |
| rooms | `POST /internal/sessions/heartbeat` | chat | `{session_ids: [...]}` → `last_seen = now()` en las activas · `200 {ended: [...]}` con las de la lista que ya no están activas |
| chat | `POST /internal/sessions/{id}/kick` | rooms | `{code}` → cierra el WS si existe y avisa `leave` a la sala · `204` |
| chat | `POST /internal/rooms/{room_id}/files` | media | `{file_id, session_id, alias}` → guarda el evento cifrado y lo difunde · `204` |
| audit | `POST /internal/events` | auth, rooms, chat, media | `{severity, action, actor, target?, ip?, details?}` → `201 {id}`; `service` sale del token |

Todos los servicios exponen además `GET /health` sin token (`{"status": "ok"}` si su BD responde), usado solo por el healthcheck de Docker.

---

## 9. Flujos

### 9.1 Admin (riesgos 4 y 5)
1. `POST /api/auth/login`. Si hay ≥ 5 fallos en 15 min con clave `user:<u>` **o** `ip:<ip>` → `429` + `Retry-After` y auditoría `admin.login.locked`.
2. Argon2id verify. Si el usuario no existe se verifica contra un hash dummy, para no revelar por tiempo qué usuarios existen.
3. Si falla: se registra el fallo, retraso progresivo `min(0.25·2^(n−1), 4)` s y `401 "credenciales inválidas"`.
4. Si es correcto: `admin_sessions(stage='preauth', expires_at=now+5min)` y cookie `__Host-admin`.
5. `POST /api/auth/totp`: aplica el mismo bloqueo; descifra el secreto con `kek_auth` y verifica con `pyotp` (ventana ±1), rechazando si `step <= totp_last_step`.
   - Si falla → se registra el fallo.
   - Si es válido → `stage='full'`, **token nuevo** (contra la fijación de sesión), 30 min de inactividad y 8 h absolutas. Auditoría `admin.login.ok`.
6. En cada `/api/admin/*`, el gateway llama a `verify-admin`. El servicio de destino aplica `require_admin`, que exige que el llamador sea `gateway` y que venga `X-Admin-Id`.
7. Bootstrap: `docker compose exec auth python -m auth_svc.create_admin <usuario>` pide la contraseña (o la lee con `--password-stdin`) e imprime el QR de TOTP y el secreto.

### 9.2 Ingreso a sala (riesgos 1, 8, 13 y 15)
1. La SPA llama `GET /api/device` al cargar: cookie de dispositivo de 128 bits aleatorios, **sin fingerprinting**.
2. `POST /api/rooms/join {code, key, alias}` en `rooms`:
   1. Rate limit: ≥ 5 fallos en 10 min por `ip`, ≥ 10 por `device` o ≥ 20 por `room` → `429` y auditoría.
   2. Busca la sala activa por `code` y hace Argon2id verify (dummy si no existe). Si falla → registra el fallo en las tres claves y responde `401 "sala o clave inválida"`.
   3. **Transacción única:**
      ```sql
      UPDATE rooms SET current_participants = current_participants + 1
       WHERE id = :room AND active AND current_participants < max_participants
      RETURNING id;                      -- 0 filas → 409 "sala llena"
      INSERT INTO room_sessions (...);   -- violación del índice único → rollback → 409 "alias en uso"
      ```
      En la misma transacción se emite `room.join.ok` (obligatorio; si `audit` falla, el ingreso falla con 503).
   4. Responde con la cookie `__Host-room` (token de 256 bits; en BD solo su SHA-256) y `{session_id, room: {id, code, mode}}`.
3. `verify-session` busca la sesión activa por `token_hash` **y** comprueba que `device_hash` coincida con la cookie de dispositivo. Un token copiado a otro equipo no pasa el gateway.

### 9.3 Ciclo de vida de una sesión de sala
| Evento | Quién lo detecta | Qué ocurre |
|---|---|---|
| Botón "salir" | rooms (`/api/rooms/leave`) | `end_session(reason='leave')` → `chat kick(code=1000)` |
| Cierre limpio del WS (1000/1001: cerrar o recargar la pestaña) | chat | `rooms end(reason='closed')` + aviso `leave` a la sala |
| Violación de protocolo (4400/4403/4408/4413/4429) | chat | Cierra el WS, `rooms end(reason='violation')` y audita |
| Inactividad: 15 min sin mensajes del usuario | chat (en memoria) | Cierra con 4410 y `rooms end(reason='idle')` |
| Caída anormal del WS | — | `chat` deja de incluir la sesión en el heartbeat. Si no reconecta en 2 min, el barrido de `rooms` la termina (`reason='grace'`) |
| Sala eliminada por el admin | rooms | Termina todas sus sesiones (`reason='room_deleted'`) → `chat kick(code=4401)` por cada una |
| `chat` se reinicia | clientes | Reconectan y hacen un handshake nuevo; la sesión de `rooms` sigue viva si vuelven dentro del período de gracia |
| `rooms` se reinicia | — | Nada: las sesiones viven en su BD |

- `end_session` es idempotente: `UPDATE … SET ended_at = now() WHERE id = :s AND ended_at IS NULL RETURNING room_id`. Si devuelve una fila, decrementa `current_participants` en la misma transacción.
- **Reconciliación:** la respuesta del heartbeat (`ended`) le dice a `chat` qué conexiones cerrar con 4401, aunque se haya perdido un `kick`.
- Recargar la pestaña equivale a volver a entrar: la SPA no persiste la sesión.

### 9.4 Chat por WebSocket (riesgos 7, 10 y 14)
1. El gateway hace el `auth_request` de sesión. Si pasa, `chat` recibe las cabeceras de identidad y valida `Origin` contra `ALLOWED_ORIGINS` (si no coincide: acepta, cierra con 4403 y audita).
2. **Handshake** (§10.1): el cliente tiene 10 s para enviar `hello`. Si no lo hace o es inválido → 4400.
3. Si la misma sesión ya tenía un WS abierto, el anterior se cierra con **4409** (la nueva conexión gana; el gateway ya validó el dispositivo).
4. Tras el handshake, `chat` envía el historial (últimos 50 mensajes y eventos de archivo de la sala, re-cifrados para esta conexión) y difunde un evento `join`.
5. Por cada trama: tamaño ≤ `WS_MAX_FRAME` (16 KB; si no → 4413), token bucket de 5/s con ráfaga 10 (si no → 4429), `seq` mayor que el último recibido (si no → 4408), descifrado AES-GCM (si el tag falla → 4400 y auditoría **critical** `ws.tamper`).
6. Payload `msg`: el modo de la sala debe permitir texto (si no → 4403) y el cuerpo debe ser válido según §8.1 (si no → 4400). **El remitente sale de `X-Alias` / `X-Session-Id`, nunca del payload.**
7. Se persiste en `messages`, cifrado con la DEK de la sala (creada en la primera escritura), y se difunde a cada conexión de la sala cifrado con **su** clave y **su** contador `s2c`.
8. Payload `file_url`: si existe un mensaje `kind='file'` con ese `file_id` **en la sala de la sesión**, responde con una URL firmada nueva. Si no → 4403 y auditoría.
9. Cada 30 s una tarea de fondo envía el heartbeat a `rooms` y cierra por inactividad las conexiones con `last_activity` vencido.
10. uvicorn hace ping cada 30 s y cierra si no hay pong en otros 30 s (`--ws-ping-interval 30 --ws-ping-timeout 30`).

### 9.5 Subida de imágenes (riesgos 6 y 9)
`POST /api/media/files`. Requiere sesión, `X-Room-Mode` ∈ {`media`, `both`} (si no → 403 y `file.rejected.forbidden`) y como máximo 5 subidas por minuto por sesión (si no → 429).
1. Tope de 5 MB (Nginx `client_max_body_size 5m` solo en esta ruta, más el control de la app). Si se excede → `rejected (size)`.
2. **Firma (magic bytes)** contra `FORMATS`. Se ignoran la extensión y el `Content-Type` del cliente. Si no coincide → `rejected (type)`.
3. **Validación con Pillow:** como máximo `MAX_IMAGE_PIXELS` = 20 MP, el formato decodificado debe coincidir con la firma, `verify()` y luego `load()`. Si falla → `rejected (invalid)`.
4. **ClamAV** INSTREAM. Si encuentra algo → `rejected (malware)` y auditoría **critical**. Si no responde → **falla cerrado**: 503 y `clamav.unavailable`.
5. **Estegoanálisis** (§12) en un `ProcessPoolExecutor` con timeout de 10 s. Un timeout cuenta como sospechoso. **Excepción:** si el `sha256` del archivo coincide con el `clean_sha256` de un archivo ya publicado, se omite el análisis. Son bytes que generó el propio sistema; por ejemplo, una imagen descargada del chat y vuelta a subir. La sanitización aleatoriza el plano LSB, así que el chi² la marcaría como sospechosa. Cualquier modificación cambia el hash y fuerza el análisis completo.
6. **Política:**
   - Sospechoso → se guarda en `/data/quarantine/<uuid>`, `status=quarantined`, auditoría warning `file.quarantined` con el veredicto. El usuario recibe "archivo retenido para revisión" y **el archivo no se publica**.
   - Rechazado → no se guarda el archivo; se registran `sha256`, `mime` y motivo en `files` y en auditoría.
   - Limpio → **sanitización** (§12.5) → `/data/media/<uuid>`, `status=clean` → publicación (§9.6).
7. Archivos con permisos `0640`, dueño uid 10001. Solo `media` monta el volumen.

### 9.6 Publicación y descarga (riesgo 12)
- **Publicación:** `media` llama a `chat POST /internal/rooms/{room_id}/files {file_id, session_id, alias}`. `chat` guarda un mensaje `kind='file'` cifrado y difunde a cada conexión `{"t":"file","id":file_id,"from":alias,"url":…,"ts":…}`, con una **URL firmada por destinatario**:
  `url = /api/media/files/{file_id}?exp={exp}&sig={b64url(HMAC-SHA256(url_signing_key, "{file_id}|{session_id}|{exp}"))}`, con `exp = now + 60 s`.
  Si `chat` no responde, `media` devuelve 503. El archivo queda `clean` pero no aparece en ninguna sala, así que nadie puede obtener una URL firmada para él.
- **Descarga:** `GET /api/media/files/{id}?exp&sig`. El gateway valida la sesión; `media` exige firma válida contra `X-Session-Id` (`hmac.compare_digest`), `exp` no vencido, `files.room_id == X-Room-Id` y `status` ∈ {`clean`, `released`}. Si algo falla → `404` (no revela si el archivo existe) y auditoría `file.download.denied`.
- **Cabeceras de respuesta:** `Content-Type` del allowlist, `X-Content-Type-Options: nosniff`, `Content-Disposition: inline; filename="image.<ext>"`, `Cache-Control: private, no-store`.
- **Renovación:** cuando una imagen expira en pantalla, la SPA envía `{"t":"file_url","file_id":…}` por el WS.

### 9.7 Cuarentena (admin)
- `GET /api/admin/quarantine` → lista con `room_id`, `alias`, `mime`, `size`, `sha256` y `verdict`.
- **Liberar:** lee el original de `/data/quarantine`, lo **sanitiza**, lo guarda en `/data/media`, borra el original, `status=released`, auditoría `file.released` (obligatoria) y publicación (§9.6).
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
  - `s2c`: `{"t":"msg","id":123,"from":"alias","body":"…","ts":"ISO-8601"}` · `{"t":"file","id":"<uuid>","from":"alias","url":"…","ts":"…"}` · `{"t":"file_url","file_id":"…","url":"…"}` · `{"t":"system","event":"join|leave","alias":"…"}` · `{"t":"history","items":[…eventos msg/file…]}`
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
- Tokens de sesión (admin, sala) y cookie de dispositivo: aleatorios; en BD solo su SHA-256.
- Argon2id para la contraseña del admin y las claves de sala, con un **tope de 4 verificaciones concurrentes** por proceso (4 × 64 MiB) para que un ataque de ingresos masivos no agote la memoria.

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

### 12.1 Punto de extensión
```python
# media_svc/formats.py
FORMATS = {
    "image/png":  Format(mime="image/png",  ext="png", signature=b"\x89PNG\r\n\x1a\n", pil_format="PNG",
                         analyze=png.analyze,  sanitize=png.sanitize),
    "image/jpeg": Format(mime="image/jpeg", ext="jpg", signature=b"\xff\xd8\xff",      pil_format="JPEG",
                         analyze=jpeg.analyze, sanitize=jpeg.sanitize),
}
```
Para agregar un formato basta con una entrada nueva, su módulo y sus tests. `analyze` y `sanitize` son funciones de módulo (las ejecuta un `ProcessPoolExecutor`).

### 12.2 PNG (dominio de píxeles, canales RGB)
- **Chi² de Westfeld–Pfitzmann** por canal: para los pares `(2k, 2k+1)` se calcula `E = (h[2k] + h[2k+1]) / 2` y `χ² = Σ (h[2k] − E)² / E` (solo pares con `E > 4`), con `p = 1 − CDF_χ²(χ², gl = pares − 1)`. Se evalúa sobre los prefijos de 10 %, 25 %, 50 % y 100 % de los píxeles en orden de escaneo (prefijos de al menos 1000 píxeles), porque el embedding secuencial deja el prefijo con p ≈ 1. **Sospechoso si algún p ≥ `STEGO_CHI2_P`.**
- **Análisis RS** (Fridrich, Goljan, Du 2001): grupos de 2×2 píxeles en zigzag, función de variación `Σ|xᵢ₊₁ − xᵢ|`, máscara `[0,1,1,0]`, estimación de la tasa `p̂` por canal resolviendo `2(d₁+d₀)x² + (d₋₀−d₋₁−d₁−3d₀)x + d₀−d₋₀ = 0` (la raíz de menor módulo) con `p̂ = x/(x−½)`. **Sospechoso si `p̂ ≥ STEGO_RS_RATE`.**
- **Entropía del plano LSB** en bloques de 64×64: se reportan la media y la fracción de bloques con entropía ≥ 0.999 bits. Es una métrica de **apoyo**; solo se vuelve disparador si la calibración muestra que separa bien (`STEGO_ENTROPY_TRIGGER`, desactivado por defecto).
- **Estructura:** cualquier dato después de `IEND` es sospechoso; también lo son los chunks `tEXt/zTXt/iTXt` que sumen más de 1 KB y los chunks desconocidos o privados.
- Las métricas que no se pueden calcular (por ejemplo, NaN) se guardan como `null`: el veredicto debe poder serializarse en `jsonb`.

### 12.3 JPEG
- Más de 16 bytes después del marcador `FFD9` final → sospechoso.
- Segmentos `APPn` + `COM` que sumen más de 64 KB → sospechoso.
- El recorrido salta los segmentos por su longitud; así una miniatura EXIF con su propio `FFD9` no confunde al análisis.
- *Stretch:* chi² sobre el histograma de coeficientes DCT (detector de JSteg) con `jpegio`, solo si instala sin problemas.

### 12.4 Calibración
`services/media/tools/stego_lab.py`:
- `embed <in> <out> --rate 0.1 --mode seq|random`: LSB replacement con bits aleatorios.
- `calibrate <dir_limpias>`: genera variantes al 5, 10, 25, 50 y 100 % y reporta TPR/FPR por detector.

Se necesitan ≥ 30 imágenes limpias reales (fotos de celular y capturas de pantalla). El chi² tiende a dar falsos positivos con histogramas muy suaves; los umbrales finales se fijan con esta herramienta y se documentan en el informe con la tabla TPR/FPR.

### 12.5 Sanitización (CDR) de todo archivo aceptado o liberado
- **PNG:** se decodifica (se conserva el canal alfa si existe), se **reemplaza el plano LSB por bits aleatorios** (imperceptible; destruye payloads LSB-1 aunque no se detecten) y se recodifica sin chunks auxiliares. Recodificar sin tocar los píxeles **no** basta, porque PNG es sin pérdida.
- **JPEG:** se aplica la orientación EXIF y se recodifica a RGB con calidad 90, sin EXIF, ICC ni comentarios.
- Se guarda el `clean_sha256` de la salida. Una imagen con el plano LSB aleatorio es estadísticamente idéntica a una con LSB embebido al 100 %, así que el sistema reconoce sus propias salidas por hash (§9.5, paso 5) y no las vuelve a analizar. El prototipo del 2026-10-13 lo confirmó: también fallan las alternativas de poner el LSB en cero (lo marca RS), recodificar como JPEG o redimensionar (lo marca chi²).

### 12.6 Agregar formatos en el futuro
Audio WAV: LSB sobre las muestras PCM (chi² y RS se adaptan a 16 bits); sanitización aleatorizando el LSB de las muestras. PDF y video: firma + ClamAV + política de rechazo hasta definir un análisis específico.

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
  | `= /api/auth/login`, `= /api/auth/totp` | auth | — | zona `login` 1 r/s, ráfaga 5 |
  | `/api/auth/` | auth | — | zona `api` 10 r/s, ráfaga 20 |
  | `= /api/device` | rooms | — | `api` |
  | `= /api/rooms/join` | rooms | — | `login` |
  | `= /api/rooms/leave` | rooms | sesión | `api` |
  | `/api/admin/rooms` | rooms | admin | `api` |
  | `/api/admin/quarantine` | media | admin | `api` |
  | `/api/admin/audit` | audit | admin | `api` |
  | `= /api/media/files` | media | sesión | `api`, `client_max_body_size 5m` |
  | `/api/media/` | media | sesión | `api` |
  | `= /ws` | chat | sesión | `limit_conn` 20 por IP, `proxy_read_timeout 75s` |
  | `= /chat-key.json` | archivo estático montado | — | — |
  | `/` | SPA (`try_files $uri /index.html`) | — | — |
  | cualquier otra `/api/…` o `/internal/…` | — | — | `404` JSON |
- **`auth_request`:** usa ubicaciones `internal` (`/_auth/admin` → `auth /internal/verify-admin`, `/_auth/session` → `rooms /internal/verify-session`) con `proxy_pass_request_body off` y `X-Original-URI`. La identidad se toma con `auth_request_set $x $upstream_http_x_…`.
- **Snippets de proxy** (en cada `location` se incluye exactamente uno, porque `proxy_set_header` no se hereda cuando una `location` declara los suyos):
  - `proxy-base.conf`: `Host`, `X-Real-IP $remote_addr`, `X-Forwarded-For $remote_addr` (sobrescribe, no concatena), `X-Forwarded-Proto https` y el token del gateway (`include /run/secrets/gateway_token.conf`).
  - `proxy-public.conf`: base + **vacía** las 6 cabeceras de identidad.
  - `proxy-admin.conf`: base + `X-Admin-*` desde `auth_request`, y vacía `X-Session-*`.
  - `proxy-session.conf`: base + `X-Session-*` desde `auth_request`, y vacía `X-Admin-*`.
- **Errores en JSON:** `error_page 401 403 404 413 429 502 503` → `{"error":"…"}` con `default_type application/json`.
- `client_max_body_size` es 16k por defecto y 5m solo en la subida. `client_body_timeout 10s`.
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
| auth | `admin.create`, `admin.login.ok`, `admin.logout`, `key.rotate.auth` | `admin.login.fail`, `admin.login.locked`, `admin.totp.fail`, `gateway.reject.admin` | — |
| rooms | `room.create`, `room.update`, `room.delete`, `room.join.ok`, `session.end` | `room.join.fail`, `room.join.ratelimited`, `room.join.full`, `room.join.alias_taken`, `gateway.reject.session` | — |
| chat | `key.rotate.chat` | `ws.reject.{origin,handshake,replay,rate,size,forbidden,malformed}` | `ws.tamper` |
| media | `file.accepted`, `file.released`, `file.deleted` | `file.quarantined`, `file.rejected.{type,invalid,size,forbidden}`, `file.download.denied`, `clamav.unavailable` | `file.rejected.malware` |
| todos | — | `http.reject.origin`, `svc.reject.token` (token ausente o inválido, o llamador fuera de la allowlist) | — |
| audit | — | — | `audit.chain.broken` |

`audit` registra sus propios `svc.reject.token` escribiendo directamente en su BD.

### 14.3 Consulta
El dashboard pide `GET /api/admin/audit?min_severity=warning&after_id=<último>` cada 10 s (alertas) y la vista completa con `min_severity=info`.

### 14.4 Si `audit` no responde
`AuditClient.emit(..., required=…)` usa un timeout de 2 s y un reintento:
- **`required=True`** (eventos que otorgan algo: `admin.login.ok`, `room.join.ok`, `room.create/update/delete`, `file.accepted`, `file.released`, `key.rotate.*`): se emite **dentro** de la transacción, antes del commit. Si falla, la operación se revierte y responde 503.
- **Resto** (rechazos y avisos): se escribe en stdout con la marca `AUDIT_FALLBACK` y el JSON del evento, y la operación continúa (un rechazo sigue siendo rechazo).

---

## 15. Manejo de errores
- El cliente siempre recibe mensajes **genéricos** en JSON `{"error": "…"}` ("credenciales inválidas", "sala o clave inválida", "archivo no permitido", "archivo retenido para revisión", 404 en descargas negadas). El detalle va a auditoría.
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
- **Frontend:** vitest para `lib/crypto.ts` contra `docs/crypto-vectors.json`.

### 16.2 End-to-end (`e2e/`)
pytest + httpx + `websockets` contra el stack completo vía `https://localhost`, verificando TLS con la CA de mkcert. Crea su admin con `create_admin --password-stdin`. Cubre lo que cruza servicios:
- Chat entre dos clientes con *hello* firmado verificado.
- Imagen limpia → publicada y descargable; imagen con LSB → cuarentena y alerta visible en `GET /api/admin/audit`.
- Gateway: `/internal/*` → 404; `X-Admin-Id`/`X-Session-Id` enviados por el cliente se ignoran; una cookie de sala en `/api/admin/*` → 401; `http://` → 301.

Se ejecuta en local antes de cada hito.

### 16.3 Riesgo nuevo R16
"Suplantación entre microservicios": un proceso con presencia en la red interna (o un servicio comprometido) invoca endpoints internos o inyecta cabeceras de identidad haciéndose pasar por el gateway u otro servicio. La vulnerabilidad que habría sin tratamiento es que los servicios confíen en cualquier petición de la red interna. Valoración propuesta: **P=3, I=5 → 15 (Alto)**; residual estimado 5 (Medio). Tratamiento: §4.3–4.5 y §13. Recomendación: agregarlo al documento SGSI de la Tarea 2.

### 16.4 Tests mínimos por riesgo
| R | Servicio | Tests |
|---|---|---|
| 01 | rooms | `key_hash` empieza con `$argon2id$`; la clave en claro no aparece en ninguna columna |
| 02 | shared, auth, chat | El servicio no arranca sin secretos; `rotate_kek` (auth) y `rotate kek/room` (chat) mantienen todo legible; los mensajes en BD no contienen el texto en claro |
| 03 | audit | `audit_app` no puede `UPDATE/DELETE/TRUNCATE`; una alteración hecha con el owner la detecta `verify`; `service` sale del token aunque el payload diga otra cosa |
| 04 | auth | Bloqueo tras 5 fallos; sin TOTP no hay acceso; código TOTP reusado rechazado; el token cambia al pasar a `full` |
| 05 | rooms, media, audit (+e2e) | Rutas de admin sin `X-Admin-Id` del gateway → 401; e2e: una cookie de sala en `/api/admin/*` → 401 |
| 06 | media | PNG con LSB secuencial al 10 % → cuarentena; PNG limpio → aceptado; datos después de `IEND` → cuarentena; tras sanitizar, el plano LSB cambia |
| 07 | chat (+e2e) | WS con `Origin` ajeno → 4403; trama alterada → 4400 + auditoría critical; *hello* firmado verificable; vectores; e2e: 301 en http |
| 08 | rooms | Rate limit de ingreso por IP, dispositivo y sala; clave débil rechazada al crear la sala |
| 09 | media | Firma que no coincide, más de 5 MB o decompression bomb → rechazo; ClamAV caído → 503; EICAR → rechazo (`clamav`) |
| 10 | chat | Rate de mensajes → 4429; trama mayor a 16 KB → 4413; sin `hello` en 10 s → 4400 |
| 11 | todos | `<svc>_app` no puede `CREATE TABLE`/`DROP` ni conectarse a otra BD |
| 12 | media | Firma inválida, vencida, de otra sesión o de otra sala → 404; archivo en cuarentena no descargable |
| 13 | rooms (+e2e) | Mismo alias desde otro dispositivo → 409; `verify-session` con otra cookie de dispositivo → 401; el alias queda libre tras `leave` |
| 14 | chat | El `from` del payload se ignora; AAD de otra sala → 4400; `seq` repetido → 4408 |
| 15 | rooms | 20 ingresos concurrentes con cupo 5 → exactamente 5 aceptados; el `CHECK` impide superar el máximo |
| 16 | shared y cada servicio (+e2e) | Sin token → 401; token de un llamador fuera de la allowlist → 403; cabeceras de identidad sin el token del gateway → ignoradas (401); e2e: `/internal/*` → 404 y cabeceras falsificadas ignoradas |

`docs/trazabilidad-riesgos.md` tiene la tabla `Riesgo | Control | Servicio/Archivo(s) | Test(s) | Estado`. Se actualiza con cada cambio de seguridad (comando `/risk-check`) y se copia al informe final.

### 16.5 CI (`.github/workflows/ci.yml`)
- Job `services`, en matriz `[shared, auth, rooms, chat, media, audit]` con servicio `postgres:17`: `ruff check`, `ruff format --check`, `pytest -m "not clamav"`, `bandit -q -r <paquete>` y `pip-audit -r requirements.lock`.
- Job `frontend`: `npm ci`, `npx vitest run`, `npm run build`, `npm audit --audit-level=high`.
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
| `.claude/commands/risk-check.md` | `/risk-check`: contrasta el diff con R1–R16 y las reglas; señala controles rotos o sin test; actualiza la trazabilidad |
| `.claude/skills/stego-analysis/SKILL.md` | Algoritmos (§12), umbrales, calibración y cómo agregar un formato |
| `.claude/skills/crypto-protocol/SKILL.md` | Protocolo (§10–11): handshake firmado, tramas, AAD, códigos, vectores, rotación |
| `.claude/agents/security-auditor.md` | Subagente de solo lectura: revisa cambios contra la Tabla 3, R16, OWASP Top 10 y el modelo de confianza (§4.3) |
| `.claude/hooks/guard.py` | `PreToolUse` sobre `Edit\|Write`: bloquea `ws://`, bloques `PRIVATE KEY` y secretos literales de ≥ 16 caracteres fuera de `tests/`, `docs/`, `.claude/` y `CLAUDE.md`. En Python, multiplataforma |

---

## 18. Fases y reparto
Roles: **A** = auth + rooms + gateway; **B** = librería compartida + audit + chat; **C** = frontend + media. El equipo asigna los nombres en `CLAUDE.local.md`.

| Semana | A | B | C | Hito verificable |
|---|---|---|---|---|
| **S1** 13–19 oct | *Días 1–2, todos:* `.claude/` + `CLAUDE.md`, librería compartida, `Dockerfile` único, Postgres con 5 BD + `gen_secrets` + mkcert, esqueleto del gateway, CI. Luego A: `auth` completo + `auth_request` de admin | Servicio `audit` + vectores cripto (con firma) | SPA + `crypto.ts` (vectores) + login de admin | El admin entra vía gateway con TOTP y el evento aparece en `audit` |
| **S2** 20–26 oct | `rooms` completo (CRUD, ingreso, `verify-session`, barrido, `kick`) | `chat` completo (handshake firmado, tramas, historial, inactividad, heartbeat) | UI de ingreso y de chat, dashboard (salas, auditoría) | Dos navegadores chatean vía gateway; e2e de chat en verde |
| **S3** 27 oct–2 nov | Hardening del gateway, test de roles por servicio (R11), rotación de claves, VPS + Let's Encrypt | Con C: publicación de archivos en `chat`, URLs firmadas | `media` completo (pipeline, estego, cuarentena) + UI de imágenes y cuarentena | Demo en el VPS; 16/16 riesgos con test; trazabilidad completa |

**Orden de recorte si hay atraso:** chi² DCT de JPEG → análisis RS (quedan chi² + entropía + estructura) → historial → `rotate room` → UI de verificación de la cadena → e2e reducido al camino feliz + reglas del gateway.
**No se recorta nunca:** MFA, solo TLS 1.3, *hello* firmado, tokens de servicio, Argon2id, cuarentena, sanitización, auditoría encadenada ni los tests por riesgo.

---

## 19. Configuración (variables no secretas)
| Variable | Servicios | Valor por defecto |
|---|---|---|
| `ALLOWED_ORIGINS` | todos | `https://localhost` (en dev se agrega `https://localhost:5173`) |
| `DB_HOST` / `DB_PORT` | todos | `db` / `5432` |
| `AUDIT_URL` · `ROOMS_URL` · `CHAT_URL` | según §4.4 | `http://audit:8000` · `http://rooms:8000` · `http://chat:8000` |
| `CURRENT_KEK_VERSION` | auth, chat | `1` |
| `ADMIN_IDLE_MIN` / `ADMIN_ABS_HOURS` | auth | `30` / `8` |
| `LOGIN_MAX_FAILS` / `LOGIN_WINDOW_MIN` / `LOGIN_DELAY_BASE` | auth | `5` / `15` / `0.25` |
| `JOIN_MAX_FAILS_IP` / `_DEVICE` / `_ROOM` / `JOIN_WINDOW_MIN` | rooms | `5` / `10` / `20` / `10` |
| `ROOM_SESSION_GRACE_S` / `SWEEP_INTERVAL_S` | rooms | `120` / `30` |
| `ROOM_SESSION_IDLE_MIN` / `HEARTBEAT_INTERVAL_S` / `HANDSHAKE_TIMEOUT_S` | chat | `15` / `30` / `10` |
| `WS_RATE_PER_S` / `WS_BURST` / `WS_MAX_FRAME` | chat | `5` / `10` / `16384` |
| `HISTORY_SIZE` / `SIGNED_URL_TTL_S` | chat | `50` / `60` |
| `UPLOAD_MAX_BYTES` / `UPLOAD_PER_MIN` / `MAX_IMAGE_PIXELS` | media | `5242880` / `5` / `20000000` |
| `STEGO_CHI2_P` / `STEGO_RS_RATE` / `STEGO_ENTROPY_TRIGGER` / `STEGO_TIMEOUT_S` | media | `0.95` / `0.08` / `off` / `10` |
| `CLAMAV_HOST` / `CLAMAV_PORT` / `MEDIA_DIR` | media | `clamav` / `3310` / `/data` |

**Desarrollo del frontend:** `npm run dev` (Vite en `https://localhost:5173` con los certificados de mkcert) con `server.proxy` de `/api`, `/ws` y `/chat-key.json` hacia `https://localhost` (el gateway). Las cookies `__Host-` exigen https también en desarrollo.

---

## 20. Riesgos del proyecto y preguntas abiertas
| Tema | Mitigación / decisión pendiente |
|---|---|
| Microservicios en 3 semanas | `Dockerfile` único, librería compartida, compose con anclas YAML, días 1–2 dedicados a infraestructura, lista de recorte |
| Fecha exacta de entrega desconocida | Hitos semanales demostrables por sí solos |
| El docente puede pedir más formatos | Punto de extensión `FORMATS` (§12.1, §12.6) |
| ClamAV usa ~1.5–3 GB de RAM y tarda minutos en cargar firmas | VPS con ≥ 4 GB; healthcheck de clamd con `start_period`; en ARM usar `clamav/clamav-debian` (variable `CLAMAV_IMAGE`) |
| `jpegio` puede no tener wheels para Python 3.13 | Es *stretch*; JPEG queda cubierto por estructura + recodificación |
| Falsos positivos del estegoanálisis en fotos reales | Calibración con ≥ 30 imágenes; la cuarentena (no el rechazo) permite que el admin libere |
| R16 no está en el documento SGSI | El equipo lo agrega a las Tablas 1–4 de la Tarea 2 |
| Proveedor del VPS sin definir | Oracle Cloud Free (ARM, 24 GB) o DigitalOcean/AWS; el Compose es idéntico |
