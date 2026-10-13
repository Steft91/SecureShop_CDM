# Spec: Salas de Chat Seguras — Diseño de arquitectura

| | |
|---|---|
| **Fecha** | 2026-10-12 |
| **Autores** | Zaith Alejandro Manangón Vinueza, Stefany Maricela Díaz Antun, Andrés Isaias Cedeño Cuenca |
| **Asignatura** | Software Seguro — Proyecto Integrador |
| **Estado** | Aprobado (diseño). Siguiente paso: plan de implementación en `docs/plans/` |
| **Fuente de requisitos** | `Documentación/Tarea 2/Actividad2_SGSI_Proyecto_Integrador.md` (enunciado + Tablas 1–4 de riesgos) |
| **Plazo** | ~3 semanas: 13 oct – 2 nov 2026 |

---

## 1. Propósito y criterios de éxito

Construir la aplicación de **salas de chat seguras** del proyecto integrador. Debe implementar y **demostrar con pruebas** los 15 tratamientos de riesgo comprometidos en la Tarea 2 (Tabla 3), porque el docente evaluará la coherencia entre el SGSI y el software.

**Criterios de éxito (definición de "terminado"):**
1. Un admin con usuario + contraseña + TOTP crea salas con ID único, clave, cupo y tipo (texto / multimedia / ambos).
2. Dos o más navegadores intercambian mensajes cifrados en una sala. Un alias no puede estar activo desde dos dispositivos.
3. Una imagen con LSB embebido termina en **cuarentena**, genera alerta y queda en auditoría. Una imagen limpia se entrega sanitizada.
4. Los **15 riesgos** tienen al menos un test automatizado en verde, mapeado en `docs/trazabilidad-riesgos.md`.
5. El sistema corre con un comando (`docker compose up`) en local y en un VPS con certificado válido.

---

## 2. Requisitos del enunciado → decisiones

| Requisito del enunciado | Decisión |
|---|---|
| Admin autenticado con usuario/contraseña gestiona salas | Cuenta de admin con Argon2id + TOTP obligatorio. Primer admin creado por CLI; no existen credenciales por defecto |
| Sala: ID único, clave, cupo máximo, tipo (texto/multimedia/ambos) | Tabla `rooms`: `code` UNIQUE, `key_hash` Argon2id, `max_participants`, `mode` |
| Usuario se conecta desde un único dispositivo | Usuarios **sin cuenta**: entran con alias + ID de sala + clave. Un alias solo puede estar activo una vez por sala (índice único parcial). La sesión queda atada a la cookie de dispositivo. **Política: se rechaza el nuevo ingreso** |
| Acceso condicionado a ID + clave | Verificación Argon2id, rate limit por IP/dispositivo/sala, error genérico |
| Confidencialidad, integridad y autenticidad; justificar algoritmos, protocolos y gestión de claves | TLS 1.3 + **cifrado por sesión en capa de aplicación** (ECDH P-256 → HKDF-SHA256 → AES-256-GCM con AAD) + envelope encryption en reposo (DEK por sala, KEK en Docker secrets) |
| Análisis de archivos y detección de esteganografía, con alertas, auditoría y política | Pipeline: firma → validación → ClamAV → estegoanálisis → **cuarentena** si es sospechoso / rechazo si es inválido o malware → sanitización si es limpio |

**Decisiones de contexto tomadas con el equipo:**
- Backend **Python + FastAPI**. Cliente **web SPA (React + TypeScript)**.
- Despliegue: **Docker Compose local** y el **mismo Compose en un VPS** (Let's Encrypt).
- Multimedia: **solo PNG y JPEG** por ahora, con un **punto de extensión** para agregar formatos cuando el docente los especifique.
- Modelo criptográfico **B** (sesión ECDH/AES-GCM sobre TLS). Se descartaron: A (solo TLS, no cumple el AES-GCM por mensaje que promete la Tarea 2) y C (E2E puro, que impide el estegoanálisis en el servidor que exige el enunciado).

---

## 3. Alcance, fuera de alcance y limitaciones conocidas

**Dentro:** todo lo de la sección 2, el panel de admin (salas, cuarentena, auditoría), las pruebas por riesgo, CI, el despliegue local y en el VPS, y el contexto para Claude Code.

**Fuera (YAGNI, con el disparador que justificaría agregarlo):**
| Omitido | Agregar cuando |
|---|---|
| Redis / pub-sub | Haga falta más de una instancia de la API |
| Celery / colas | El estegoanálisis supere el timeout de 10 s con imágenes reales |
| HashiCorp Vault | Haya más de un servidor o se requiera rotación automática |
| Cifrado en reposo de archivos | Lo pida el docente (los archivos ya están fuera del webroot y se sirven autenticados) |
| Formatos distintos de PNG/JPEG | El docente los especifique (ver §12.6) |
| Cuentas de usuario final | Cambie el enunciado |
| `.mcp.json` | Usen GitHub Issues/Projects u otra integración externa |

**Limitaciones conocidas (se declaran en el informe):**
1. El servidor ve el texto plano de los mensajes por diseño: es necesario para validar, auditar y analizar archivos. La confianza en el servidor es un supuesto explícito.
2. Identidad basada en alias: quien conoce la clave de la sala puede entrar con **otro** alias desde otro dispositivo. Para el sistema eso es otro participante y lo limita el cupo.
3. Un solo proceso: las claves de sesión viven en memoria y un reinicio obliga a volver a entrar.
4. El estegoanálisis es estadístico. Esquemas adaptativos o LSB-matching (±1) pueden evadir chi². Lo mitiga la **sanitización** (§12.5), que destruye payloads LSB aunque no se detecten.

---

## 4. Arquitectura

```
Navegador (React SPA + WebCrypto)
   │  HTTPS / WSS — solo TLS 1.3
   ▼
┌────────────────────────── red "edge" ──────────────────────────┐
│ Nginx: TLS, HSTS, CSP, limit_req/limit_conn, sirve la SPA,      │
│        proxy /api → api:8000 y /ws → api:8000 (Upgrade)         │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌──────────────── red "internal" (internal: true) ────────────────┐
│ api (FastAPI, 1 proceso uvicorn, usuario no-root)                │
│   ├─ ProcessPoolExecutor → estegoanálisis                        │
│   ├─ hub WebSocket en memoria                                    │
│   └─ tarea de fondo: barrido de sesiones                         │
│ db (PostgreSQL 17, sin puertos publicados)                       │
│ clamav (clamd :3310, sin puertos publicados)                     │
│ migrate (job one-shot: alembic upgrade head con chat_migrator)   │
└──────────────────────────────────────────────────────────────────┘
Volumen "media": /data/media (limpios) y /data/quarantine (sospechosos). Solo lo monta api.
Secrets: /run/secrets/* (Docker secrets).
```

**Monolito modular**: un solo servicio FastAPI con módulos de responsabilidad clara. Se descartaron los microservicios porque con 3 semanas y 3 personas suman despliegue y red sin aportar a los criterios de éxito.

**Límite de escala conocido:** la difusión por WebSocket ocurre en memoria de un solo proceso. Para escalar se agrega Redis pub/sub y se mueven las claves de sesión a un almacén compartido.

---

## 5. Estructura del repositorio

```
SecureShop_CDM/
├── CLAUDE.md                     contexto principal para Claude Code (§17)
├── .claude/                      reglas, comando, skills, agente, hook (§17)
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── migrations/               Alembic (incluye los GRANT por tabla)
│   ├── app/
│   │   ├── main.py               app, routers, middlewares (cabeceras, Origin/CSRF, cookie de dispositivo)
│   │   ├── config.py             settings + lectura de /run/secrets (falla si falta alguno)
│   │   ├── db.py                 engine async (SQLAlchemy 2 + asyncpg)
│   │   ├── models.py             tablas
│   │   ├── audit.py              audit.write(...) con cadena de hash
│   │   ├── security/
│   │   │   ├── passwords.py      Argon2id (hash/verify, verify dummy)
│   │   │   ├── crypto.py         ECDH, HKDF, AES-GCM, envelope, firma de URLs
│   │   │   ├── ratelimit.py      ventana deslizante sobre failed_attempts + token bucket en memoria
│   │   │   └── rotate.py         CLI rotate_kek / rotate_room_dek
│   │   ├── admin/                login, TOTP, CRUD de salas, cuarentena, auditoría, CLI create_admin
│   │   ├── rooms/                device, join, leave, barrido de sesiones
│   │   ├── chat/                 hub WebSocket
│   │   └── media/
│   │       ├── pipeline.py       orquestación de la subida
│   │       ├── formats.py        ANALYZERS (punto de extensión)
│   │       ├── png.py  jpeg.py   validación, estegoanálisis y sanitización por formato
│   │       ├── stego.py          chi², RS, entropía (numpy)
│   │       └── clamav.py         cliente INSTREAM (socket de la stdlib)
│   ├── tools/stego_lab.py        `embed` (genera imágenes con LSB) y `calibrate` (TPR/FPR)
│   └── tests/
│       ├── conftest.py
│       ├── security/test_rNN_*.py   un archivo o más por riesgo
│       └── fixtures/               imágenes limpias y estego generadas
├── frontend/
│   ├── package.json  vite.config.ts  tsconfig.json
│   └── src/
│       ├── pages/ Join.tsx  Chat.tsx  AdminLogin.tsx  AdminDashboard.tsx
│       └── lib/   crypto.ts  ws.ts  api.ts
├── deploy/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml   overrides del VPS (certificados Let's Encrypt)
│   ├── nginx/nginx.conf  nginx/Dockerfile (build multi-stage de la SPA)
│   ├── postgres/init.sh          crea roles, BD y esquemas leyendo /run/secrets
│   ├── gen_secrets.py            genera deploy/secrets/*
│   ├── certs/                    (gitignored) certificados mkcert locales
│   └── secrets/                  (gitignored)
├── docs/
│   ├── specs/                    este documento
│   ├── plans/                    plan de implementación
│   ├── crypto-vectors.json       vectores compartidos Python ↔ TypeScript
│   └── trazabilidad-riesgos.md   riesgo → control → archivo → test → estado
├── .github/workflows/ci.yml
└── Documentación/                entregables académicos (ya existe)
```

---

## 6. Stack

| Capa | Tecnología | Por qué |
|---|---|---|
| API | Python 3.13, FastAPI, uvicorn | WebSockets nativos; el estegoanálisis y la cripto se hacen en el mismo lenguaje |
| BD | PostgreSQL 17, SQLAlchemy 2 (async) + asyncpg, Alembic | Constraints, índices parciales y transacciones para la atomicidad del cupo |
| Contraseñas | `argon2-cffi` (Argon2id, parámetros por defecto RFC 9106: t=3, m=64 MiB, p=4) | Comprometido en la Tarea 2 (riesgo 1) |
| Cripto | `cryptography` (ECDH P-256, HKDF, AESGCM) | Primitivas auditadas; interopera con WebCrypto |
| MFA | `pyotp` + `qrcode` (QR en la terminal del CLI) | TOTP RFC 6238 |
| Imágenes | Pillow, numpy, scipy (solo `chi2.sf`) | Decodificación y estadística |
| Antimalware | ClamAV (`clamav/clamav`) vía clamd INSTREAM | Comprometido (riesgo 9) |
| Front | React 19, Vite, TypeScript estricto, react-router, CSS plano | Sin librería de UI: menos superficie |
| Cripto en el front | WebCrypto (`crypto.subtle`) | Nativo, claves no extraíbles |
| Proxy | Nginx | TLS 1.3, cabeceras, rate limit perimetral (riesgos 7 y 10) |
| Tests | pytest, pytest-asyncio, httpx; vitest | |
| CI | GitHub Actions: ruff, pytest, bandit, pip-audit, npm audit | |

Las versiones exactas se fijan en el plan de implementación.

---

## 7. Modelo de datos

```sql
-- esquema public
CREATE TABLE admins (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username      text UNIQUE NOT NULL,
  password_hash text NOT NULL,              -- $argon2id$...
  totp_secret   bytea NOT NULL,             -- nonce||ct, AES-GCM con KEK, AAD "totp|<id>"
  totp_last_step bigint NOT NULL DEFAULT 0, -- anti-reuso del código TOTP
  kek_version   int NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE admin_sessions (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id    uuid NOT NULL REFERENCES admins(id),
  token_hash  bytea UNIQUE NOT NULL,        -- SHA-256 del token (256 bits aleatorios)
  stage       text NOT NULL CHECK (stage IN ('preauth','full')),
  last_seen   timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz NOT NULL,         -- preauth: 5 min; full: 8 h absolutas
  ended_at    timestamptz
);

CREATE TABLE rooms (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code                 text UNIQUE NOT NULL CHECK (code ~ '^[A-Za-z0-9_-]{3,32}$'),
  key_hash             text NOT NULL,       -- $argon2id$...
  mode                 text NOT NULL CHECK (mode IN ('text','media','both')),
  max_participants     int  NOT NULL CHECK (max_participants BETWEEN 2 AND 50),
  current_participants int  NOT NULL DEFAULT 0,
  dek_wrapped          bytea NOT NULL,      -- nonce||ct, AES-GCM con KEK, AAD "dek|<room_id>"
  kek_version          int  NOT NULL,
  active               boolean NOT NULL DEFAULT true,
  created_by           uuid NOT NULL REFERENCES admins(id),
  created_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (current_participants BETWEEN 0 AND max_participants)   -- respaldo del riesgo 15
);

CREATE TABLE room_sessions (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id       uuid NOT NULL REFERENCES rooms(id),
  alias         text NOT NULL,              -- NFKC, 2–24 caracteres
  device_hash   bytea NOT NULL,             -- SHA-256 de la cookie de dispositivo
  token_hash    bytea UNIQUE NOT NULL,
  last_seen     timestamptz NOT NULL DEFAULT now(),   -- cualquier trama o pong
  last_activity timestamptz NOT NULL DEFAULT now(),   -- solo mensajes del usuario
  created_at    timestamptz NOT NULL DEFAULT now(),
  ended_at      timestamptz,
  end_reason    text
);
CREATE UNIQUE INDEX one_active_alias_per_room
  ON room_sessions (room_id, lower(alias)) WHERE ended_at IS NULL;   -- riesgo 13

CREATE TABLE messages (
  id          bigserial PRIMARY KEY,
  room_id     uuid NOT NULL REFERENCES rooms(id),
  session_id  uuid NOT NULL REFERENCES room_sessions(id),
  alias       text NOT NULL,
  payload     bytea NOT NULL,               -- nonce||ct, AES-GCM con DEK, AAD "msg|<room>|<session>"
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE files (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id      uuid NOT NULL REFERENCES rooms(id),
  session_id   uuid NOT NULL REFERENCES room_sessions(id),
  storage_name text UNIQUE,                 -- uuid4 sin extensión; NULL si fue rechazado
  mime         text NOT NULL,
  size         int  NOT NULL,
  sha256       bytea NOT NULL,
  status       text NOT NULL CHECK (status IN ('clean','quarantined','rejected','released','deleted')),
  verdict      jsonb NOT NULL,              -- métricas del análisis y motivo
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE failed_attempts (
  id         bigserial PRIMARY KEY,
  scope      text NOT NULL,                 -- 'admin_login' | 'room_join'
  key        text NOT NULL,                 -- 'ip:1.2.3.4' | 'user:alice' | 'device:<hash>' | 'room:<id>'
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON failed_attempts (scope, key, created_at);

-- esquema audit (separado, permisos de solo inserción para la app)
CREATE TABLE audit.log (
  id        bigserial PRIMARY KEY,
  ts        timestamptz NOT NULL DEFAULT now(),
  severity  text NOT NULL CHECK (severity IN ('info','warning','critical')),
  actor     text NOT NULL,                  -- 'admin:<username>' | 'session:<id>' | 'ip:<ip>' | 'system'
  action    text NOT NULL,                  -- ver §14
  target    text,
  ip        inet,
  details   jsonb NOT NULL DEFAULT '{}',
  prev_hash bytea NOT NULL,
  hash      bytea NOT NULL                  -- SHA-256(prev_hash || json canónico de los campos)
);
```

### 7.1 Roles de base de datos (riesgo 11)

| Rol | Permisos | Uso |
|---|---|---|
| `postgres` | Superusuario | Solo `init.sh` al crear el contenedor |
| `chat_migrator` | Dueño de la BD y de los esquemas; DDL | Job `migrate` (Alembic). `ALTER ROLE chat_migrator SET log_statement = 'all'` (registro de consultas privilegiadas) |
| `chat_app` | `SELECT, INSERT, UPDATE, DELETE` en las tablas de `public`; en `audit.log` solo `SELECT, INSERT`; `USAGE` en las secuencias. **Sin** DDL, sin `TRUNCATE`, sin `CREATE` en esquemas | La API |

Los `GRANT` van **explícitos en las migraciones de Alembic**, tabla por tabla. `init.sh` crea los roles leyendo las contraseñas desde `/run/secrets` y ejecuta `REVOKE ALL ON SCHEMA public FROM PUBLIC`.

---

## 8. API HTTP

Prefijo `/api`. Todas las respuestas son JSON salvo la descarga de archivos.

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | — | 200 si responde la BD |
| GET | `/device` | — | Pone la cookie `__Host-device` si no existe. 204 |
| POST | `/admin/login` | — | `{username, password}` → cookie `__Host-admin` en etapa `preauth` |
| POST | `/admin/totp` | preauth | `{code}` → la sesión pasa a `full` (se rota el token) |
| POST | `/admin/logout` | admin | Cierra la sesión |
| GET | `/admin/me` | admin | `{username}` |
| GET / POST | `/admin/rooms` | admin | Listar / crear `{code, key, max_participants, mode}` |
| PATCH | `/admin/rooms/{id}` | admin | Cambiar `key`, `max_participants` (≥ actuales) o `mode` |
| DELETE | `/admin/rooms/{id}` | admin | `active=false` y cierra sus sesiones |
| GET | `/admin/quarantine` | admin | Archivos en cuarentena con su `verdict` |
| POST | `/admin/quarantine/{id}/release` | admin | Sanitiza, mueve a media, `status=released` y lo difunde a la sala |
| DELETE | `/admin/quarantine/{id}` | admin | Borra el archivo físico, `status=deleted` |
| GET | `/admin/audit?severity=&after_id=` | admin | Paginado por id; el dashboard consulta cada 10 s |
| GET | `/admin/audit/verify` | admin | Recorre la cadena → `{ok, broken_at}` |
| POST | `/rooms/join` | device | `{code, key, alias, client_pubkey}` → cookie `__Host-room` + `{session_id, server_pubkey, salt, room: {code, mode}}` |
| POST | `/rooms/leave` | room | Termina la sesión |
| POST | `/rooms/files` | room | multipart `file` → `{file_id, status}` |
| GET | `/files/{id}?exp=&sig=` | room | Descarga de un archivo limpio o liberado |
| WS | `/ws` | room + device | Canal de chat (§10) |

**Cookies:** todas con prefijo `__Host-` (exige Secure, Path=/ y sin Domain), `HttpOnly` y `SameSite=Strict`. **Ningún token es accesible desde JavaScript.**

**CSRF:** además de SameSite=Strict, un middleware rechaza los `POST/PATCH/DELETE` cuyo encabezado `Origin` no esté en `ALLOWED_ORIGINS`.

**Validaciones de entrada:**
- `code`: `^[A-Za-z0-9_-]{3,32}$`.
- Clave de sala: ≥ 12 caracteres, al menos 3 de 4 clases (minúsculas, mayúsculas, dígitos, símbolos) y distinta del `code`.
- `alias`: normalizado NFKC, 2–24 caracteres, solo letras, dígitos, espacio, `_` y `-`.
- `max_participants`: entre 2 y 50.
- Texto de un mensaje: ≤ 2000 caracteres.

---

## 9. Flujos

### 9.1 Login del admin (riesgos 4 y 5)
1. `POST /admin/login`. Si hay ≥ 5 `failed_attempts` en 15 min con la clave `user:<u>` **o** `ip:<ip>` → `429` con `Retry-After`, auditado como `admin.login.locked` (warning).
2. Argon2id verify. Si el usuario no existe se verifica contra un hash dummy precalculado, para no revelar por tiempo qué usuarios existen.
3. Si falla: se inserta en `failed_attempts`, retraso progresivo de `min(0.25·2^(n-1), 4)` s y respuesta `401 "credenciales inválidas"`.
4. Si es correcto: se crea `admin_sessions(stage='preauth', expires_at=now+5min)`.
5. `POST /admin/totp`: se descifra el secreto con la KEK y se verifica con `pyotp` (ventana ±1). Se rechaza si `step <= totp_last_step` (reuso). Si es válido: `stage='full'`, **se emite un token nuevo** (contra la fijación de sesión) con 30 min de inactividad y 8 h absolutas.
6. La dependencia `require_admin` exige una sesión `full` vigente **en cada request** de `/admin/*`. Una cookie `__Host-room` no la satisface (otra cookie y otra tabla).
7. Bootstrap: `docker compose run --rm api python -m app.admin.create_admin <username>` pide la contraseña (getpass, ≥ 12 caracteres) e imprime el QR de TOTP.

### 9.2 Ingreso a sala (riesgos 1, 8, 13 y 15)
1. La SPA llama `GET /device` al cargar (cookie de dispositivo de 128 bits aleatorios; **sin fingerprinting**).
2. `POST /rooms/join {code, key, alias, client_pubkey}`:
   1. Rate limit: ≥ 5 fallos en 10 min por `ip`, ≥ 10 por `device` o ≥ 20 por `room` → `429` y auditoría (warning).
   2. Se busca la sala activa por `code` y se hace Argon2id verify de `key` (dummy si no existe). Si falla → `failed_attempts` (las tres claves) y `401 "sala o clave inválida"`.
   3. **Transacción única:**
      ```sql
      UPDATE rooms SET current_participants = current_participants + 1
       WHERE id = :room AND active AND current_participants < max_participants
      RETURNING id;                          -- 0 filas → 409 "sala llena"
      INSERT INTO room_sessions (...);       -- violación de one_active_alias_per_room → rollback → 409 "alias en uso"
      ```
   4. Se valida `client_pubkey` (punto P-256 sin comprimir, 65 bytes; `from_encoded_point` verifica que esté en la curva). El servidor genera su par efímero, calcula el secreto ECDH y deriva `K_s` (§10.1). `K_s` y los contadores se guardan **solo en memoria**: `sessions[session_id]`.
   5. Respuesta: cookie `__Host-room` (token de 256 bits; en BD solo su SHA-256) y `{session_id, server_pubkey, salt, room}`. Auditoría `room.join.ok`.
3. **Fin de sesión** (idempotente: `UPDATE ... SET ended_at = now() WHERE id = :s AND ended_at IS NULL RETURNING room_id`; si devuelve fila se decrementa `current_participants` en la misma transacción):
   - `POST /rooms/leave`, o cierre limpio del WS (1000/1001, que incluye cerrar o recargar la pestaña) → fin inmediato.
   - Caída anormal del WS → se espera `ROOM_SESSION_GRACE` (2 min) por si reconecta desde el mismo dispositivo con la misma `K_s` en memoria del navegador.
   - Conectado pero sin mensajes del usuario durante `ROOM_SESSION_IDLE` (15 min) → el servidor cierra con 4410.
   - Un barrido cada 30 s aplica las dos reglas anteriores.
   - Al arrancar la API: se terminan **todas** las sesiones activas (`end_reason='restart'`) y se pone `current_participants = 0`.
   - Recargar la pestaña equivale a volver a entrar: `K_s` no es extraíble y nunca se persiste en el navegador.

### 9.3 Mensajería (riesgos 7, 10 y 14)
1. Handshake WS: `Origin` en `ALLOWED_ORIGINS` (si no → cierre 4403). Cookie `__Host-room` → sesión activa cuyo `device_hash` coincide con `__Host-device` (si no → 4401). Una sola conexión WS por sesión: una nueva reemplaza a la anterior del mismo dispositivo.
2. Al conectar, el servidor envía los últimos 50 mensajes de la sala (descifrados con la DEK y re-cifrados con `K_s`) y un evento de sistema `join`.
3. Por cada trama del cliente: token bucket (5/s, ráfaga 10; si se excede → 4429). Tamaño ≤ 4 KB (si no → 4413). `seq > last_seq` (si no → 4408). Descifrado AES-GCM (si el tag falla → 4400 y auditoría **critical** `ws.tamper`). JSON válido y sala que permite texto (si no → 4403).
4. **El remitente sale de la sesión.** Cualquier campo `from`/`room` del payload se ignora.
5. Se persiste `messages.payload` cifrado con la DEK y se difunde: para cada sesión conectada de la sala, cifrado con su `K_r` y su contador `s2c`.
6. Keepalive: ping del servidor cada 30 s. Sin pong en 60 s se cierra (caída anormal → período de gracia).
7. Nginx: `limit_conn` de 20 por IP y `proxy_read_timeout` de 75 s.

### 9.4 Subida de imágenes (riesgos 6 y 9)
`POST /rooms/files`: requiere sesión de sala, que `room.mode` esté en (`media`, `both`) y un máximo de 5 subidas por minuto por sesión.
1. Lectura en streaming con tope de 5 MB (Nginx `client_max_body_size 5m` solo en esta ruta; 16k en el resto).
2. **Firma (magic bytes)** contra `ANALYZERS`. La extensión y el `Content-Type` del cliente se ignoran. Si no coincide → `rejected (type)`.
3. **Validación de formato** (por formato): Pillow con `Image.MAX_IMAGE_PIXELS = 20_000_000`, `verify()`, reapertura y `load()`. El formato decodificado tiene que coincidir con la firma. Si falla → `rejected (invalid)`.
4. **ClamAV** INSTREAM. Si encuentra algo → `rejected (malware)`, auditoría **critical**. Si clamd no responde → **falla cerrado**: `503`, auditoría warning y el archivo no se acepta.
5. **Estegoanálisis** (§12) en `ProcessPoolExecutor` con timeout de 10 s. Si se agota el tiempo → se trata como sospechoso.
6. **Política:**
   - Sospechoso → se guarda en `/data/quarantine/<uuid>` con `status=quarantined`, auditoría warning `file.quarantined` y el `verdict` completo. El usuario recibe "archivo retenido para revisión". **No se difunde.**
   - Rechazado → no se guarda; se registran el `sha256` y el motivo.
   - Limpio → **sanitización** (§12.5) → `/data/media/<uuid>`, `status=clean` y difusión de un evento `file` cifrado a la sala.
7. Archivos con permisos `0640` y dueño uid 10001 (usuario no-root de la API). Nginx no monta el volumen.

### 9.5 Descarga (riesgo 12)
- El evento `file` incluye una URL `/api/files/{id}?exp=<unix>&sig=<b64url>` generada **para cada destinatario**: `sig = HMAC-SHA256(url_signing_key, "{file_id}|{session_id}|{exp}")`, con `exp = now + 60 s`. El cliente pide una URL nueva con una trama `{"t":"file_url","file_id":…}` cuando la anterior expira.
- `GET /files/{id}` exige: firma válida (`hmac.compare_digest`), `exp` no vencido, cookie `__Host-room` cuya sesión sea la de la firma y pertenezca a la sala del archivo, y `status` en (`clean`, `released`). Si algo falla → `404` (no revela si el archivo existe) y auditoría `file.download.denied`.
- Cabeceras de respuesta: `Content-Type` del allowlist, `X-Content-Type-Options: nosniff`, `Content-Disposition: inline; filename="image.<ext>"` y `Cache-Control: private, no-store`.

---

## 10. Protocolo criptográfico (fuente de verdad para Python y TypeScript)

### 10.1 Establecimiento de la clave de sesión
| Paso | Valor |
|---|---|
| Curva | P-256 (`ECDH`/`SECP256R1`), pares efímeros por sesión en ambos lados |
| Codificación de la clave pública | Punto sin comprimir de 65 bytes, base64url sin padding |
| Secreto compartido | 32 bytes (`deriveBits(…, 256)` / `exchange(ECDH())`) |
| KDF | HKDF-SHA256, `salt` = 32 bytes aleatorios del servidor, `info` = UTF-8 de `"secure-chat/v1|{room_id}|{session_id}"`, longitud 32 bytes |
| Resultado | `K_s`: clave AES-256-GCM. En el navegador es un `CryptoKey` **no extraíble** y se guarda solo en memoria |

El intercambio ocurre dentro de TLS 1.3 (el servidor está autenticado por su certificado) y dentro de la solicitud que ya validó la clave de sala, así que no hay MITM posible sin romper TLS.

### 10.2 Tramas
- Cifrado: AES-256-GCM, nonce aleatorio de 12 bytes por trama, tag de 16 bytes concatenado al final del ciphertext (formato por defecto de WebCrypto y de `AESGCM`).
- **AAD** = UTF-8 de `"v1|{room_id}|{session_id}|{seq}|{dir}"`, con `dir ∈ {c2s, s2c}`. En `s2c`, `session_id` es el del **destinatario** y `seq` es el contador de servidor de esa sesión.
- Formato en el cable (JSON de texto): `{"seq": <int>, "n": "<b64url nonce>", "c": "<b64url ct||tag>"}`.
- `seq` empieza en 1 y es estrictamente creciente por dirección. El receptor rechaza `seq <= último` (anti-replay). El sufijo `dir` impide reflejar una trama hacia su emisor.
- Payload en claro (JSON UTF-8):
  - `c2s`: `{"t":"msg","body":"…"}` · `{"t":"file_url","file_id":"…"}`
  - `s2c`: `{"t":"msg","id":123,"from":"alias","body":"…","ts":"ISO-8601"}` · `{"t":"file","id":"…","from":"alias","url":"…","ts":"…"}` · `{"t":"file_url","file_id":"…","url":"…"}` · `{"t":"system","event":"join|leave","alias":"…"}` · `{"t":"history","items":[…]}`
- Límite práctico: 2^32 tramas por clave con nonces aleatorios. Las sesiones duran horas, así que no se re-negocia la clave.

### 10.3 Códigos de cierre del WS
| Código | Motivo |
|---|---|
| 4400 | Trama malformada o tag GCM inválido |
| 4401 | Sesión o dispositivo inválido |
| 4403 | Origin no permitido o tipo de contenido no permitido en la sala |
| 4408 | Replay (`seq` no creciente) |
| 4410 | Expiración por inactividad |
| 4413 | Trama demasiado grande |
| 4429 | Rate limit |

### 10.4 Vectores de prueba
`docs/crypto-vectors.json` contiene casos fijos (claves privadas de prueba, salt, info, nonce, AAD, texto en claro → `K_s` y ciphertext esperados). pytest **y** vitest los verifican. Si cambia el protocolo, cambian los vectores.

---

## 11. Gestión de claves y secretos (riesgo 2)

| Secreto | Generación | Uso |
|---|---|---|
| `kek_v{n}` | 32 bytes aleatorios | Envuelve las DEK de sala (AAD `dek|<room_id>`) y los secretos TOTP (AAD `totp|<admin_id>`) |
| `url_signing_key` | 32 bytes aleatorios | HMAC de las URLs de descarga |
| `db_app_password`, `db_migrator_password`, `postgres_password` | 32 bytes, base64url | Conexiones a la BD |

- Se generan con `python deploy/gen_secrets.py` en `deploy/secrets/` (gitignored) y se montan como **Docker secrets** en `/run/secrets/`. `config.py` falla al arrancar si falta alguno. **Nunca** se guardan en código, en `.env` versionado ni en variables de entorno en claro.
- **DEK por sala:** 32 bytes aleatorios al crear la sala; se guarda solo envuelta (`dek_wrapped`, `kek_version`). Mensajes en reposo: AES-GCM con la DEK, AAD `msg|<room_id>|<session_id>`.
- **Rotación de la KEK:** se agrega `kek_v2`, se configura `CURRENT_KEK_VERSION=2` y se ejecuta `python -m app.security.rotate kek`, que re-envuelve todas las DEK y secretos TOTP con la v2. Los mensajes no se tocan. Después se puede retirar `kek_v1`.
- **Revocación de la DEK de una sala:** `python -m app.security.rotate room <code>` genera una DEK nueva y re-cifra los mensajes de esa sala en una transacción.
- Tokens (admin, sala) y cookie de dispositivo: aleatorios (`secrets.token_bytes(32)`/`(16)`). En BD solo su SHA-256; con esa entropía un hash rápido es suficiente.
- Argon2id para la contraseña del admin y las claves de sala.
- TLS: `mkcert` en local (`deploy/certs/`) y Let's Encrypt en el VPS (certbot en el host; `/etc/letsencrypt` montado de solo lectura).

---

## 12. Análisis de archivos y estegoanálisis (riesgos 6 y 9)

### 12.1 Punto de extensión
```python
# media/formats.py
ANALYZERS = {
    "image/png":  Format(signature=b"\x89PNG\r\n\x1a\n", ext="png", validate=png.validate, analyze=png.analyze, sanitize=png.sanitize),
    "image/jpeg": Format(signature=b"\xff\xd8\xff",      ext="jpg", validate=jpeg.validate, analyze=jpeg.analyze, sanitize=jpeg.sanitize),
}
```
Para agregar un formato basta con una entrada nueva, su módulo y sus tests. El pipeline no cambia.

### 12.2 PNG (dominio de píxeles)
- **Chi² de Westfeld–Pfitzmann** por canal RGB: para los pares de valores `(2k, 2k+1)` se calcula `E = (h[2k] + h[2k+1]) / 2` y `χ² = Σ (h[2k] − E)² / E` (solo pares con `E > 4`), con `p = 1 − CDF_χ²(χ², gl = pares − 1)`. Se evalúa sobre los prefijos 10 %, 25 %, 50 % y 100 % de los píxeles en orden de escaneo, porque el embedding secuencial deja el prefijo con p ≈ 1. **Sospechoso si algún p ≥ `STEGO_CHI2_P` (0.95).**
- **Análisis RS** (Fridrich, Goljan, Du 2001): grupos de 2×2 píxeles, función de discriminación de variación, máscara `[0,1,1,0]`. Se estima la tasa de embedding `p̂` por canal. **Sospechoso si `p̂ ≥ STEGO_RS_RATE` (0.08, valor inicial).**
- **Entropía del plano LSB** por bloques de 64×64: se reporta la media y la fracción de bloques con entropía ≥ 0.999 bits. Es una métrica de **apoyo**: se guarda en el `verdict` y solo se vuelve disparador si la calibración muestra que separa bien (`STEGO_ENTROPY_TRIGGER`, desactivado por defecto).
- **Estructura:** bytes después del chunk `IEND` (> 0 → sospechoso), chunks `tEXt/zTXt/iTXt` con más de 1 KB en total → sospechoso, y chunks privados o desconocidos → sospechoso.

### 12.3 JPEG
- Bytes después del último marcador `FFD9`: más de 16 → sospechoso.
- Segmentos `APPn` + `COM` con más de 64 KB en total → sospechoso.
- *Stretch:* chi² sobre el histograma de coeficientes DCT (detector de JSteg) usando `jpegio`, solo si instala sin problemas en el contenedor.

### 12.4 Calibración
`backend/tools/stego_lab.py`:
- `embed <in> <out> --rate 0.1 --mode seq|random`: LSB replacement (sirve para tests y para la demo).
- `calibrate <dir_limpias>`: genera variantes con tasas de 5, 10, 25, 50 y 100 % y reporta TPR/FPR por umbral.

Se necesitan ≥ 30 imágenes limpias reales (fotos y capturas). Los umbrales finales se fijan en `config.py` y se documentan en el informe junto con la tabla TPR/FPR.

### 12.5 Sanitización (CDR) de todo archivo aceptado o liberado
- **PNG:** se decodifica, se **sobrescribe el plano LSB con bits aleatorios** (imperceptible y destruye cualquier payload LSB-1 aunque no se haya detectado) y se recodifica sin chunks auxiliares.
- **JPEG:** se decodifica y se recodifica con calidad 90 sin EXIF, ICC ni comentarios (destruye payloads en DCT).
- Ojo: recodificar un PNG sin alterar los píxeles **no** elimina el LSB, porque PNG es sin pérdida. Por eso existe el paso de aleatorización.

### 12.6 Agregar formatos en el futuro
Audio WAV: LSB sobre las muestras PCM (chi² y RS se adaptan a muestras de 16 bits). Sanitización: aleatorizar el LSB de las muestras. Otros formatos (PDF, video): firma, ClamAV y política de rechazo hasta definir un análisis específico.

---

## 13. Nginx y cabeceras (riesgos 7 y 10)

- `listen 443 ssl; http2 on; ssl_protocols TLSv1.3;`. El puerto 80 solo responde `301` a https, así que **`ws://` nunca llega a la app**.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self' wss://$host; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`
- `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `limit_req_zone`: `api` a 10 r/s (ráfaga 20) y `login` a 1 r/s (ráfaga 5) sobre `/api/admin/login`, `/api/admin/totp` y `/api/rooms/join`. `limit_conn` de 20 por IP.
- `client_max_body_size`: 16k por defecto y 5m en `/api/rooms/files`.
- `server_tokens off`. Timeouts: `client_body_timeout 10s` y `proxy_read_timeout 75s` en `/ws`.
- Envía `X-Forwarded-For` y `X-Real-IP`. uvicorn corre con `--proxy-headers --forwarded-allow-ips='*'` (la API solo es alcanzable desde la red interna).
- Verificación manual (evidencia para el informe): `testssl.sh` o `curl --tlsv1.2 --tls-max 1.2` debe fallar, y `curl http://…/ws` debe devolver 301.

---

## 14. Auditoría (riesgo 3)

- `audit.write(severity, actor, action, target, ip, details)` corre en la misma transacción que la operación auditada cuando existe una. Para encadenar sin carreras, toma `pg_advisory_xact_lock(42)`, lee el último `hash` y luego inserta. *Límite conocido: las escrituras de auditoría quedan serializadas; a esta escala no importa.*
- `hash = SHA256(prev_hash || json canónico (claves ordenadas, sin espacios) de {ts, severity, actor, action, target, ip, details})`. El primer `prev_hash` son 32 bytes en cero.
- `chat_app` no puede `UPDATE`, `DELETE` ni `TRUNCATE` en `audit.log`. La cadena detecta una modificación hecha con otro rol, y `/admin/audit/verify` la reporta y audita `audit.chain.broken` (critical).
- **Eventos:**
  | Severidad | Acciones |
  |---|---|
  | info | `admin.login.ok`, `admin.logout`, `room.create/update/delete`, `room.join.ok`, `session.end`, `file.accepted`, `file.released`, `file.deleted`, `key.rotate.*` |
  | warning | `admin.login.fail`, `admin.totp.fail`, `admin.login.locked`, `room.join.fail`, `room.join.ratelimited`, `room.join.full`, `room.join.alias_taken`, `ws.reject.{origin,auth,replay,rate,size,forbidden}`, `file.quarantined`, `file.rejected.{type,invalid,size}`, `file.download.denied`, `clamav.unavailable` |
  | critical | `ws.tamper`, `file.rejected.malware`, `audit.chain.broken` |
- **Nunca** se registran contraseñas, claves de sala, tokens, contenido de mensajes ni secretos TOTP.
- El dashboard muestra `severity ≥ warning` como alertas (polling cada 10 s).

---

## 15. Manejo de errores

- El cliente siempre recibe mensajes **genéricos** ("credenciales inválidas", "sala o clave inválida", "archivo no permitido", "archivo retenido para revisión", 404 en las descargas negadas). El detalle va a `audit.log`.
- Excepciones no controladas: handler global → `500 {"error":"error interno"}` + log en stdout sin datos sensibles. Sin trazas hacia el cliente (`debug=False`).
- Las dependencias de seguridad **fallan cerrado**: ClamAV caído → 503; secreto ausente → la API no arranca; BD caída → 503.

---

## 16. Pruebas y trazabilidad

- **Backend:** pytest + pytest-asyncio + `httpx.AsyncClient` (ASGI) y el cliente WS de Starlette, contra **PostgreSQL real** (servicio del Compose / servicio de CI) con migraciones aplicadas y roles reales. Sin mocks de BD.
- **Frontend:** vitest para `lib/crypto.ts` contra `docs/crypto-vectors.json`.
- Marcador `@pytest.mark.clamav` para los tests que necesitan clamd: corren en local con el Compose y se omiten en CI.
- **Tests mínimos por riesgo** (archivos `backend/tests/security/test_rNN_<tema>.py`):

| R | Tests |
|---|---|
| 01 | `key_hash` empieza con `$argon2id$`; la clave en claro no aparece en ninguna columna |
| 02 | `config` falla sin secretos; `rotate kek` re-envuelve y los mensajes siguen descifrando; escaneo del repo sin claves (también lo hace el hook) |
| 03 | `chat_app` no puede `UPDATE/DELETE/TRUNCATE` en `audit.log`; una alteración hecha con `chat_migrator` la detecta `verify` |
| 04 | Bloqueo tras 5 fallos; sin TOTP no hay acceso; un código TOTP reusado se rechaza; el token cambia al pasar a `full` |
| 05 | Sin cookie → 401 en `/admin/*`; una cookie de sala → 401 en `/admin/*` |
| 06 | PNG con LSB secuencial al 10 % → cuarentena; PNG limpio → aceptado; datos después de IEND → cuarentena; tras sanitizar, el plano LSB difiere del original |
| 07 | WS con `Origin` ajeno → 4403; trama con un bit alterado → 4400 + auditoría critical; vectores cripto Python |
| 08 | Rate limit de ingreso por IP/dispositivo/sala; clave débil rechazada al crear la sala |
| 09 | Firma que no coincide → rechazo; > 5 MB → rechazo; decompression bomb → rechazo; EICAR → rechazo (`clamav`) |
| 10 | Exceder el rate de mensajes → 4429; trama > 4 KB → 4413 |
| 11 | `chat_app` no puede `CREATE TABLE` ni `DROP`, ni leer `pg_authid` |
| 12 | Firma inválida, expirada, de otra sesión o de otra sala → 404; archivo en cuarentena → no descargable |
| 13 | Mismo alias desde otro dispositivo → 409; token usado con otra cookie de dispositivo → 4401; el alias queda libre después de `leave` |
| 14 | El `from` del payload se ignora (el remitente sale de la sesión); AAD de otra sala → rechazo; `seq` repetido → 4408 |
| 15 | 20 ingresos concurrentes (`asyncio.gather`) en una sala con cupo 5 → exactamente 5 aceptados; el `CHECK` impide un `UPDATE` directo que supere el máximo |

- **`docs/trazabilidad-riesgos.md`:** tabla `Riesgo | Control (Tabla 3) | Archivo(s) | Test(s) | Estado`. Se actualiza con cada cambio de seguridad (comando `/risk-check`) y se copia al informe final.
- **CI** (`.github/workflows/ci.yml`, un solo workflow en push/PR): `ruff check`, `ruff format --check`, `pytest -m "not clamav"` con el servicio `postgres:17`, `bandit -r backend/app`, `pip-audit`, `npm ci && npm run build && npx vitest run && npm audit --audit-level=high`.

---

## 17. Contexto para Claude Code

Objetivo: que cualquier sesión futura entienda el proyecto sin releer este spec completo y respete las invariantes de seguridad.

| Archivo | Contenido |
|---|---|
| `CLAUDE.md` | (~100 líneas) qué es el proyecto, stack, comandos (`docker compose up`, tests, migraciones, `create_admin`), mapa del repo, **invariantes de seguridad** resumidas, enlaces al spec, al plan y a la trazabilidad, y una sección **"Estado actual"** que se actualiza al cerrar cada fase |
| `CLAUDE.local.md` | (gitignored) cada integrante anota su rol (A/B/C), su área y sus preferencias |
| `.claude/settings.json` | `permissions.allow`: pytest, ruff, alembic, `docker compose`, npm/npx, git (lectura). `permissions.deny`: `Read(deploy/secrets/**)`, `Read(**/.env)`, `Read(deploy/certs/**)`. Registra el hook `PreToolUse` |
| `.claude/rules/security.md` | Global: nunca `ws://` ni HTTP en claro; nunca claves o secretos en código; el remitente y la sala salen de la sesión; queries siempre parametrizadas (ORM o `text()` con binds); errores genéricos al cliente y detalle a auditoría; auditar todo rechazo; Argon2id para secretos de usuario; no registrar datos sensibles; fallar cerrado |
| `.claude/rules/backend.md` | `paths: backend/**`: FastAPI async, un router por módulo, dependencias `require_admin`/`require_room_session`, migraciones con GRANT explícito, sin lógica en `main.py` |
| `.claude/rules/frontend.md` | `paths: frontend/**`: TS estricto, nunca `dangerouslySetInnerHTML`, toda la cripto pasa por `lib/crypto.ts`, claves `CryptoKey` no extraíbles solo en memoria, nada en `localStorage`/`sessionStorage`, sin scripts ni estilos inline (CSP) |
| `.claude/rules/testing.md` | `paths: **/tests/**`: Postgres real, `test_rNN_*` por riesgo, un test que falle antes de implementar el control, actualizar la trazabilidad |
| `.claude/commands/risk-check.md` | `/risk-check`: lee el diff, lo contrasta con los 15 riesgos de la Tarea 2 y con `rules/security.md`, señala controles rotos o sin test y actualiza `docs/trazabilidad-riesgos.md` |
| `.claude/skills/stego-analysis/SKILL.md` | Algoritmos (§12) con fórmulas, umbrales, cómo calibrar con `stego_lab.py`, cómo agregar un formato |
| `.claude/skills/crypto-protocol/SKILL.md` | Protocolo (§10–11) exacto, formatos de trama, AAD, códigos de cierre, vectores, rotación |
| `.claude/agents/security-auditor.md` | Subagente de solo lectura: revisa cambios contra la Tabla 3 de la Tarea 2, OWASP Top 10 y `rules/security.md`; reporta hallazgos con severidad |
| `.claude/hooks/guard.py` | `PreToolUse` sobre `Edit\|Write`: bloquea (exit 2 con motivo) contenido con `ws://`, bloques `-----BEGIN … PRIVATE KEY-----` y asignaciones de secretos literales (`password = "…"`, `key = b"…"` de ≥ 16 caracteres) fuera de `tests/` y `docs/`. En Python para que funcione en Windows, Mac y Linux |

---

## 18. Fases y reparto

Roles: **A** = backend core/admin, **B** = tiempo real/cripto, **C** = frontend/multimedia. El equipo asigna los nombres en `CLAUDE.local.md`.

| Semana | A | B | C | Hito verificable |
|---|---|---|---|---|
| **S1** 13–19 oct | *Día 1, todos:* Compose (nginx, api, db, clamav, migrate), mkcert, `init.sh` con roles, Alembic base, `.claude/` + `CLAUDE.md`, CI esqueleto. Luego: modelos y migraciones, Argon2id, login + TOTP + bloqueo, `require_admin`, `audit.write` con cadena, CLI `create_admin` | `crypto.py` (ECDH, HKDF, GCM, envelope, firma de URLs), `config.py` con secretos, KEK/DEK, `crypto-vectors.json` | SPA Vite/React/TS, router, `api.ts`, `crypto.ts` que pasa los vectores, pantallas de login admin y de ingreso | El admin entra con TOTP y crea una sala; los vectores pasan en Python y en TS |
| **S2** 20–26 oct | CRUD de salas (política de clave, DEK), `join` transaccional, rate limits, sesión única, barrido; tests r01, r04, r05, r08, r13, r15 | Hub WS: auth, Origin, tramas, anti-replay, re-cifrado en el fan-out, persistencia envelope, historial, keepalive; tests r07, r10, r14 | UI de chat (handshake, envío/recepción, eventos), dashboard (salas, auditoría) | Dos navegadores chatean cifrado; cupo y alias únicos verificados por tests |
| **S3** 27 oct–2 nov | Hardening de Nginx, test r11, `rotate kek/room`, r02/r03, despliegue en VPS + Let's Encrypt | Con C: ClamAV, URLs firmadas, descarga, r12 | Pipeline de imágenes completo, estegoanálisis, sanitización, calibración, UI de cuarentena; tests r06, r09 | Demo en el VPS; **15/15 riesgos con test en verde**; trazabilidad completa |

**Orden de recorte si hay atraso:** chi² DCT de JPEG → análisis RS (quedan chi² + entropía + estructura) → historial de mensajes → `rotate room` (`rotate kek` se queda) → UI de verificación de la cadena (el endpoint se queda).
**No se recorta nunca:** MFA, solo TLS 1.3, Argon2id, cuarentena, sanitización, auditoría encadenada ni los tests por riesgo.

---

## 19. Configuración (variables no secretas)

| Variable | Valor por defecto |
|---|---|
| `ALLOWED_ORIGINS` | `https://localhost` (en dev se agrega `https://localhost:5173`) |
| `CURRENT_KEK_VERSION` | `1` |
| `ADMIN_IDLE_MIN` / `ADMIN_ABS_HOURS` | `30` / `8` |
| `ROOM_SESSION_IDLE_MIN` / `ROOM_SESSION_GRACE_S` | `15` / `120` |
| `LOGIN_MAX_FAILS` / `LOGIN_WINDOW_MIN` | `5` / `15` |
| `JOIN_MAX_FAILS_IP` / `_DEVICE` / `_ROOM` / `JOIN_WINDOW_MIN` | `5` / `10` / `20` / `10` |
| `WS_RATE_PER_S` / `WS_BURST` / `WS_MAX_FRAME` | `5` / `10` / `4096` |
| `UPLOAD_MAX_BYTES` / `UPLOAD_PER_MIN` / `MAX_IMAGE_PIXELS` | `5242880` / `5` / `20000000` |
| `STEGO_CHI2_P` / `STEGO_RS_RATE` / `STEGO_ENTROPY_TRIGGER` / `STEGO_TIMEOUT_S` | `0.95` / `0.08` / `off` / `10` |
| `SIGNED_URL_TTL_S` | `60` |
| `CLAMAV_HOST` / `CLAMAV_PORT` | `clamav` / `3310` |

**Desarrollo del frontend:** `npm run dev` con Vite en `https://localhost:5173` usando los certificados de mkcert, y `server.proxy` de `/api` y `/ws` hacia `https://localhost` (Nginx del Compose). Las cookies `__Host-` exigen https también en desarrollo.

---

## 20. Riesgos del proyecto y preguntas abiertas

| Tema | Mitigación / decisión pendiente |
|---|---|
| Fecha exacta de entrega desconocida (~3 semanas) | El hito de cada semana es demostrable por sí solo; existe una lista de recorte |
| El docente puede pedir más formatos | Punto de extensión `ANALYZERS` (§12.1, §12.6) |
| ClamAV usa ~1.5–3 GB de RAM y tarda minutos en cargar firmas | VPS con ≥ 4 GB. `healthcheck` de clamd y `depends_on: condition: service_healthy`. Verificar que la imagen tenga soporte arm64 si el VPS es ARM (Oracle Free) |
| `jpegio` puede no tener wheels para Python 3.13 | Es *stretch*; JPEG queda cubierto por estructura + recodificación |
| Falsos positivos del estegoanálisis en fotos reales | Calibración con ≥ 30 imágenes; la cuarentena (no el rechazo) permite que el admin libere |
| Proveedor del VPS sin definir | Oracle Cloud Free (ARM, 24 GB) o DigitalOcean/AWS; el Compose es idéntico |
