# Justificación criptográfica

| | |
|---|---|
| **Requisito** | `docs/requisitos.md` RS-09…RS-15, RP-06: *justificar los algoritmos, protocolos, mecanismos de gestión de claves y controles que protegen los mensajes durante su transmisión* |
| **Fuente de verdad del protocolo** | `docs/specs/2026-10-12-chat-seguro-design.md` §10–§11 · vectores en `docs/crypto-vectors.json` |
| **Implementación** | `services/shared/shared/crypto.py` (Python) y `frontend/src/lib/crypto.ts` (WebCrypto), verificadas con los mismos vectores |

---

## 1. Qué se protege y de quién

| Activo | Propiedad exigida | Adversario considerado |
|---|---|---|
| Mensajes de la sala | Confidencialidad, integridad y autenticidad en tránsito y en reposo | Observador o atacante activo en la red; un participante malicioso; copia de la BD |
| Archivos multimedia | Confidencialidad e integridad en tránsito y en reposo | Ídem; acceso al volumen del servidor |
| Credenciales (contraseñas de las cuentas, claves de sala) | No recuperables a partir de la BD | Fuga de la BD; fuerza bruta fuera de línea |
| Tokens de sesión (JWT) | No falsificables, revocables al instante y ligados al dispositivo | Fuga de la BD; robo de cookie; un servicio comprometido que intente fabricar tokens |
| Claves criptográficas | Fuera del código y aisladas por servicio | Fuga del repositorio; un servicio comprometido |

**Fuera del modelo** (declarado en el spec §3): el servidor `chat` ve el texto plano para validar, persistir y auditar, y `media` ve las imágenes para analizarlas. Por eso no se eligió cifrado extremo a extremo: impediría el estegoanálisis y la validación en el servidor.

---

## 2. Arquitectura por capas

| Capa | Qué protege | Mecanismo |
|---|---|---|
| 1. Transporte (cliente ↔ gateway) | Todo el tráfico HTTP y WebSocket | TLS 1.3 únicamente, HSTS, `ws://` inexistente |
| 2. Aplicación (navegador ↔ `chat`) | Cada mensaje, incluso en el tramo interno HTTP | Handshake ECDH efímero con *hello* firmado → HKDF → AES-256-GCM por trama |
| 3. Reposo | Mensajes y archivos en BD y volumen | Envelope encryption: DEK por sala (mensajes) y DEK por archivo, envueltas con una KEK |
| 4. Credenciales | Contraseñas y claves de sala | Argon2id con sal por hash |
| 5. Identidad | Quién hace cada petición y con qué permisos | JWT RS256 que solo `auth` firma, verificado por `auth` en cada request junto con la sesión a la que apunta |

**Por qué dos capas de cifrado en tránsito:** TLS termina en el gateway y el tramo gateway→servicio es HTTP plano dentro de una red Docker interna. La capa 2 mantiene la confidencialidad e integridad de los mensajes aunque ese tramo se observe, y el *hello* firmado impide que alguien en la red interna sustituya las claves efímeras (MITM activo).

---

## 3. Algoritmos y parámetros

| Propósito | Elección | Alternativas descartadas y por qué | Referencia |
|---|---|---|---|
| Cifrado autenticado de tramas, mensajes y archivos | **AES-256-GCM**, nonce aleatorio de 96 bits, tag de 128 bits, AAD con el contexto | ChaCha20-Poly1305: WebCrypto no lo ofrece. AES-CBC + HMAC: más piezas y errores posibles. | NIST SP 800-38D |
| Acuerdo de clave por conexión | **ECDH P-256 efímero** en cliente y servidor | X25519: no está disponible de forma uniforme en WebCrypto. RSA: sin secreto hacia adelante y claves mayores. | NIST SP 800-56A |
| Derivación de la clave de sesión | **HKDF-SHA256**; `salt` aleatorio de 32 bytes; `info` = protocolo + sala + sesión | Usar el secreto ECDH directo: no separa dominios ni mezcla sal. | RFC 5869 |
| Autenticación del servidor | **ECDSA P-256 + SHA-256** sobre la transcripción del *hello*; firma en formato P1363 (`r‖s`) | Sin firma: TLS no llega al servicio, habría MITM interno. HMAC con secreto compartido: el navegador no puede guardarlo. | FIPS 186-5 |
| Hash de contraseñas y claves de sala | **Argon2id**, `t=3`, `m=64 MiB`, `p=4`, sal por hash; ≤ 4 cálculos concurrentes por proceso | bcrypt/PBKDF2: no resisten tanto GPU/ASIC. Parámetros de 2 GiB: inviables en un VPS de 4 GB. | RFC 9106 (opción de baja memoria) |
| Segundo factor de los permisos de admin | **TOTP** (HMAC-SHA1 por compatibilidad con las apps), ventana ±1, anti-reuso por *step* | SMS: depende de la red telefónica. Sin MFA: una contraseña robada daría el control de la plataforma. | RFC 6238 |
| Token de sesión del usuario | **JWT RS256** con clave RSA de 3072 bits; claims `iss`, `aud`, `sub`, `sid`, `stage`, `exp`. Solo `auth` tiene la clave privada, y el gateway lo verifica con `auth` **junto con la sesión** `sid` en cada request | HS256: el mismo secreto firma y verifica, así que cualquier verificador podría fabricar tokens. JWT sin sesión en el servidor: no se puede revocar al instante. Token opaco: el docente pidió JWT. RSA de 2048 bits: válido hasta 2030 según NIST; 3072 da margen al mismo costo práctico. | RFC 7519, RFC 7518, NIST SP 800-57 |
| Tokens de servicio y cookie de dispositivo | **256 / 128 bits** aleatorios (`secrets`); en BD solo su SHA-256 | UUID: poca entropía y predecible. | — |
| URLs firmadas de descarga | **HMAC-SHA256** sobre `file_id|user_id|exp`, TTL 60 s, comparación en tiempo constante | URL pública: R12. Cookie sola: permitiría compartir el enlace sin caducidad. | RFC 2104 |
| Integridad de la bitácora | Cadena **SHA-256**: `hash = H(prev_hash ‖ evento canónico)` | Firmar cada evento: exige gestionar otra clave sin ganar mucho a esta escala. | FIPS 180-4 |
| Detección de manipulación de archivos | **SHA-256** del original y del archivo sanitizado | — | FIPS 180-4 |

---

## 4. Protocolo del chat

### 4.1 Handshake por conexión WebSocket
```
Cliente                                               chat
  | genera (c_priv, c_pub) ECDH P-256 efímero          |
  |---- {"t":"hello","pub":c_pub} -------------------->|
  |                      genera (s_priv, s_pub) y salt |
  |        shared = ECDH(s_priv, c_pub)                |
  |        K = HKDF-SHA256(shared, salt, "secure-chat/v1|sala|sesión")
  |        T = "secure-chat/v1/hello|sala|sesión|c_pub|s_pub|salt"
  |        sig = ECDSA-P256(chat_sign_key, T)          |
  |<--- {"t":"hello","pub":s_pub,"salt":salt,"sig":sig}|
  | verifica sig con la clave pública de /chat-key.json |
  | K = HKDF(ECDH(c_priv, s_pub), salt, …)             |
```

### 4.2 Propiedades y cómo se logran
| Propiedad | Mecanismo | Verificación |
|---|---|---|
| **Confidencialidad** | AES-256-GCM con `K` única por conexión | Mensajes en BD y en el cable sin texto plano (`test_r02_mensajes_cifrados_en_reposo_y_legibles`) |
| **Integridad** | Tag GCM de 128 bits; cualquier alteración → cierre 4400 y alerta crítica | `test_r07_trama_alterada_cierra_4400_con_alerta_critica` |
| **Autenticidad del servidor** | Firma ECDSA que cubre las dos claves públicas, la sala y la sesión | `test_vector_de_firma_del_hello`, `test_firma_no_valida_si_cambia_la_clave_del_cliente` |
| **Autenticidad del remitente** | El `from` sale de la cuenta verificada por el gateway y del alias que devuelve `rooms`, nunca del payload | `test_r14_el_remitente_sale_de_la_identidad_verificada` |
| **Anti-replay** | `seq` estrictamente creciente por conexión y dirección | `test_r14_replay_cierra_4408` |
| **Anti-reflexión** | El sufijo `c2s`/`s2c` va en el AAD | `test_tramas_ida_y_vuelta_y_alteraciones` |
| **Aislamiento entre salas y sesiones** | `room_id` y el id de la sesión de la cuenta van en el AAD y en el `info` de HKDF | `test_r14_trama_cifrada_para_otra_sala_se_rechaza` |
| **Secreto hacia adelante** | ECDH efímero por conexión: comprometer `chat_sign_key` no descifra tráfico pasado | Diseño (la clave de firma no participa en el acuerdo) |
| **Sin reutilización de nonce** | 96 bits aleatorios por trama; límite práctico 2³² tramas por clave, que una conexión nunca alcanza | Diseño |

### 4.3 Lo que este protocolo no hace
- No es E2E: el servidor descifra para validar y persistir (limitación 1 del spec).
- No autentica al cliente con una clave propia: el cliente se autentica por la sesión de su cuenta (el JWT), verificada por el gateway en cada request.
- La cookie de dispositivo no es un identificador de hardware (limitación 7 del spec).

---

## 5. Gestión de claves

### 5.1 Ciclo de vida
| Clave | Generación | Almacenamiento | Quién la usa | Rotación | Revocación / destrucción |
|---|---|---|---|---|---|
| `K` de conexión | ECDH + HKDF en cada WS | Solo en memoria (en el navegador, `CryptoKey` no extraíble) | Navegador y `chat` | Cada conexión | Se descarta al cerrar |
| `jwt_signing_key` | `gen_secrets.py` (RSA de 3072 bits, PKCS#8) | Docker secret, solo en `auth` | Firma los JWT; `auth` los verifica con la pública | `gen_secrets.py --rotate jwt_signing_key` y reiniciar `auth` | Rotarla invalida todos los JWT: todos vuelven a iniciar sesión |
| `kek_auth_v{n}` | `gen_secrets.py` (256 bits) | Docker secret, solo en `auth` | Envuelve el secreto TOTP de las cuentas | Montar v{n+1} y `python -m auth_svc.rotate_kek` | Retirar la versión anterior |
| `kek_chat_v{n}` | Ídem | Docker secret, solo en `chat` | Envuelve las DEK de sala | `python -m chat_svc.rotate kek` | Ídem |
| DEK de sala | `os.urandom(32)` con el primer mensaje | `room_keys.dek_wrapped` (envuelta con la KEK, AAD `dek|sala`) | Cifra los mensajes de la sala | `python -m chat_svc.rotate room <id>` (re-cifra los mensajes) | Se pierde al borrar la fila |
| `kek_media_v{n}` | `gen_secrets.py` (256 bits) | Docker secret, solo en `media` | Envuelve las DEK de archivo | `python -m media_svc.rotate_kek` | Retirar la versión anterior |
| DEK de archivo | `os.urandom(32)` por archivo | `files.dek_wrapped` (AAD `filedek|archivo`) | Cifra el archivo en el volumen (AAD `file|archivo`) | Con la KEK | Al eliminar un archivo en cuarentena se borra el archivo físico |
| `chat_sign_key` | `gen_secrets.py` (ECDSA P-256, PKCS#8) | Docker secret, solo en `chat`; la pública va a `deploy/public/chat-key.json` | Firma el *hello* | `gen_secrets.py --rotate chat_sign_key` y reiniciar `chat` y el gateway | Cambiar `kid` |
| `url_signing_key` | `gen_secrets.py` | Docker secret en `chat` (firma) y `media` (verifica) | URLs de descarga | `--rotate url_signing_key` | Las URLs duran 60 s |
| Token de servicio `svc_token_*` | `gen_secrets.py` | Solo su dueño; los receptores guardan el SHA-256 (`svc_hash_*`) | `X-Service-Token` | `--rotate svc_token_<x>` y reiniciar | Quitar el hash del receptor |
| Contraseñas de BD | `gen_secrets.py` | Docker secrets: `*_owner` solo en el job de migración; `*_app` solo en su servicio | Conexión a PostgreSQL | `--rotate` y reiniciar | — |
| Sesión de la cuenta (JWT) y cookie de dispositivo | JWT firmado por `auth`; cookie de 128 bits (`secrets`) | En la BD solo el id de la sesión y el SHA-256 de la cookie; en el navegador, cookies `__Host-` `HttpOnly` | Autenticación por request | Al pasar por TOTP se crea una sesión con `sid` nuevo | `ended_at`; expiran por inactividad (30 min) y por tiempo absoluto (8 h) |
| Certificado TLS | mkcert (local), Let's Encrypt (VPS) | `deploy/certs/` (ignorado por git) | Gateway | Renovación automática con hooks | Revocación de la CA |

### 5.2 Principios aplicados
- **Ningún secreto en el código, en variables de entorno ni en `.env` versionado:** se leen de `/run/secrets` y el servicio no arranca si falta alguno.
- **Separación:** cada KEK vive solo en el servicio que la necesita. Un servicio comprometido no puede descifrar los datos de otro.
- **Firma asimétrica de la identidad:** solo `auth` tiene la clave privada de los JWT; ningún otro servicio puede fabricar un token, aunque esté comprometido.
- **Envelope encryption:** la rotación de una KEK solo re-envuelve claves pequeñas; los datos no se tocan.
- **Versionado:** `kek_*_v{n}` permite tener dos versiones montadas durante la migración.
- **Sin claves derivadas de contraseñas del usuario** para cifrar datos: las contraseñas solo se usan para autenticar (Argon2id).

---

## 6. Evidencia

| Qué | Dónde |
|---|---|
| Mismos resultados en Python y en el navegador | `docs/crypto-vectors.json` verificado por `services/shared/tests/test_vectors.py` y `frontend/src/lib/crypto.test.ts` |
| Cada propiedad del §4.2 | Tests citados en la tabla |
| Rotación de claves | `test_r02_rotar_la_kek_mantiene_el_totp_legible`, `test_r02_rotar_la_kek_mantiene_el_historial`, `test_r02_rotar_la_dek_de_una_sala`, `test_r02_rotar_la_kek_de_media` |
| TLS 1.3 únicamente | Verificación manual en `docs/trazabilidad-riesgos.md` y e2e |
| JWT no falsificable y revocable | `test_jwt_alterado_401`, `test_jwt_de_sesion_terminada_401` |
