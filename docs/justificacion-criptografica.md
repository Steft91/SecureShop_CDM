# Justificación criptográfica — Primer parcial

| | |
|---|---|
| **Requisito** | `docs/requisitos.md` RS-13…RS-15, RS-36, RP-06: *justificar los algoritmos, protocolos, mecanismos de gestión de claves y controles* |
| **Alcance** | El primer parcial: el gateway, `auth` y `stego`. El cifrado de mensajes y archivos (spec §10–§11) se justifica aquí cuando se construya |
| **Implementación** | `services/shared/shared/{crypto,passwords,secrets}.py`, `services/auth/auth_svc/tokens.py`, `deploy/gen_secrets.py` y `gateway/nginx.conf` |

---

## 1. Qué se protege y de quién

| Activo | Propiedad exigida | Adversario considerado |
|---|---|---|
| Tráfico entre el cliente y el sistema | Confidencialidad e integridad en tránsito | Observador o atacante activo en la red |
| Contraseñas de las cuentas | No recuperables a partir de la BD | Fuga de la BD; fuerza bruta fuera de línea |
| Tokens de sesión (JWT) | No falsificables, revocables al instante y ligados al dispositivo | Fuga de la BD; robo del token; un servicio comprometido que intente fabricar tokens |
| Identidad entre servicios | Solo el gateway puede presentar la identidad de un usuario | Un contenedor de la red interna que se haga pasar por el gateway (R16) |
| Claves y secretos | Fuera del código y aislados por servicio | Fuga del repositorio; un servicio comprometido |

---

## 2. Arquitectura por capas

| Capa | Qué protege | Mecanismo |
|---|---|---|
| 1. Transporte (cliente ↔ gateway) | Todo el tráfico HTTP | TLS 1.3 únicamente, HSTS, http → https |
| 2. Identidad del usuario | Quién hace cada petición y con qué permisos | JWT RS256 que solo `auth` firma, verificado por `auth` en cada petición junto con la sesión a la que apunta |
| 3. Identidad entre servicios | Que las cabeceras `X-User-*` vengan del gateway | Token del gateway de 256 bits; los servicios guardan solo su SHA-256 |
| 4. Credenciales | Contraseñas de las cuentas | Argon2id con sal por hash |

**Tramo interno:** TLS termina en el gateway, y el tramo gateway→servicio es HTTP plano dentro de una red Docker interna (spec §3, limitación 3). En el primer parcial ese tramo solo lleva peticiones de `auth` y `stego`; lo protegen el token del gateway y las redes internas. La mejora es mTLS.

---

## 3. Algoritmos y parámetros

| Propósito | Elección | Alternativas descartadas y por qué | Referencia |
|---|---|---|---|
| Canal cliente ↔ gateway | **TLS 1.3** únicamente, con HSTS | TLS 1.2: admite suites sin secreto hacia adelante y más configuración insegura posible. | RFC 8446 |
| Hash de contraseñas | **Argon2id**, `t=3`, `m=64 MiB`, `p=4`, sal por hash; ≤ 4 cálculos concurrentes por proceso | bcrypt/PBKDF2: resisten menos GPU/ASIC. Parámetros de 2 GiB: inviables en un equipo de 4 GB. | RFC 9106 (opción de baja memoria) |
| Token de sesión del usuario | **JWT RS256** con clave RSA de 3072 bits; claims `iss`, `aud`, `sub`, `sid`, `name`, `roles`, `iat`, `exp`. Solo `auth` tiene la clave privada, solo se acepta `RS256`, y el gateway lo verifica con `auth` **junto con la sesión** `sid` en cada petición | HS256: el mismo secreto firma y verifica, así que cualquier verificador podría fabricar tokens. JWT sin sesión en el servidor: no se puede revocar al instante. Token opaco: el docente pidió JWT. RSA de 2048 bits: válido hasta 2030 según NIST; 3072 da margen al mismo costo práctico. | RFC 7519, RFC 7518, NIST SP 800-57 |
| Token del gateway y cookie de dispositivo | **256 / 128 bits** aleatorios (`secrets`); en BD y en los servicios solo su SHA-256, comparado en tiempo constante | UUID: poca entropía y predecible. Guardar el valor en claro: una fuga de la BD o de un secreto montado daría el token. | — |
| Huella de la imagen analizada | **SHA-256** del archivo en el veredicto y en el evento `stego.analyzed` | — | FIPS 180-4 |

---

## 4. Gestión de claves

### 4.1 Ciclo de vida
| Clave | Generación | Almacenamiento | Quién la usa | Rotación | Revocación / destrucción |
|---|---|---|---|---|---|
| `jwt_signing_key` | `gen_secrets.py` (RSA de 3072 bits, PKCS#8) | Docker secret, solo en `auth` | Firma los JWT; `auth` los verifica con la pública | `gen_secrets.py --rotate jwt_signing_key` y reiniciar `auth` | Rotarla invalida todos los JWT: todos vuelven a iniciar sesión |
| `svc_token_gateway` | `gen_secrets.py` (256 bits) | Solo en el gateway (`gateway_token.conf`); `auth` y `stego` guardan el SHA-256 (`svc_hash_gateway`) | Cabecera `X-Service-Token` | `gen_secrets.py --rotate svc_token_gateway` (regenera el token, el hash y el `.conf`) y reiniciar | Quitar el hash de los receptores |
| Contraseñas de BD | `gen_secrets.py` | Docker secrets: `postgres_password` solo en `db`, `db_auth_owner` solo en el job de migración, `db_auth_app` solo en `auth` | Conexión a PostgreSQL | `--rotate` y reiniciar | — |
| Sesión de la cuenta (JWT) y cookie de dispositivo | JWT firmado por `auth`; cookie de 128 bits (`secrets`) | En la BD solo el id de la sesión y el SHA-256 de la cookie; en el cliente, la cookie `__Host-device` `HttpOnly` | Autenticación en cada petición | Cada login crea una sesión con `sid` nuevo | `ended_at` al cerrar la sesión; vencen por inactividad (30 min) y por tiempo absoluto (8 h) |
| Certificado TLS | mkcert (local) | `deploy/certs/` (ignorado por git) | Gateway | Volver a generarlo con mkcert | Desinstalar la CA local |

### 4.2 Principios aplicados
- **Ningún secreto en el código, en variables de entorno ni en `.env` versionado:** se leen de `/run/secrets` y el servicio no arranca si falta alguno.
- **Separación:** cada secreto vive solo en el servicio que lo necesita. `stego` no tiene ninguna clave, solo el hash del token del gateway.
- **Firma asimétrica de la identidad:** solo `auth` tiene la clave privada de los JWT; ningún otro servicio puede fabricar un token, aunque esté comprometido.
- **Hash en lugar del valor:** los tokens del gateway y las cookies de dispositivo se guardan como SHA-256, así que una fuga no los entrega.
- **Las contraseñas solo autentican:** no se derivan claves de ellas.

---

## 5. Evidencia

| Qué | Dónde |
|---|---|
| Lectura de secretos y fallo cerrado | `test_secreto_ausente_detiene_el_servicio`, `test_secreto_vacio_tambien_lo_detiene` |
| Tokens aleatorios y su hash | `test_tokens_aleatorios_y_su_hash` |
| Argon2id con los parámetros de RFC 9106 | `test_hash_es_argon2id_con_parametros_rfc9106` |
| Generación y rotación de secretos | `test_genera_todo_y_no_sobrescribe` (RSA de 3072 bits), `test_rotar_token_del_gateway_regenera_hash_y_conf` |
| JWT no falsificable | `test_alg_none_y_hs256_con_la_clave_publica_se_rechazan`, `test_vencido_alterado_o_de_otra_audiencia_es_none`, `test_jwt_alterado_401` |
| JWT revocable y ligado al dispositivo | `test_jwt_de_sesion_terminada_401`, `test_r13_jwt_con_otra_cookie_de_dispositivo_401` |
| TLS 1.3 únicamente | Verificación manual de GW-1 en `docs/trazabilidad-riesgos.md` |
