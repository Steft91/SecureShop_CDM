# Cumplimiento normativo y enfoques de seguridad

| | |
|---|---|
| **Qué demuestra** | Cómo ISO/IEC 27001, ISO/IEC 27034, Zero Trust, Secure by Design y Shift Left se aplican al proyecto, y cómo se relacionan con los riesgos (R1–R16) y con los mecanismos implementados |
| **Requisito** | `docs/requisitos.md` RS-30…RS-34, RP-07, RP-08 |
| **Fuentes del proyecto** | `docs/specs/2026-10-12-chat-seguro-design.md` · `docs/plans/` · `docs/trazabilidad-riesgos.md` · Tarea 2 (Tablas 1–4) |
| **Estado de la evidencia** | Los mecanismos están **diseñados y con test especificado**. La columna *Evidencia* cita el test o la prueba manual; pasa a "en verde" cuando se ejecute el plan (el estado real vive en `docs/trazabilidad-riesgos.md`). |

---

## 1. ISO/IEC 27001:2022

### 1.1 Sistema de gestión (cláusulas 4–10)
| Cláusula | Qué pide | Dónde está en el proyecto |
|---|---|---|
| 4 Contexto | Alcance y partes interesadas | Tarea 2 §2.1 (alcance del SGSI y activos críticos); spec §1–§3 |
| 5 Liderazgo | Política y roles | Reparto por persona en `docs/tickets/` (spec §18); reglas en `.claude/rules/` |
| 6 Planificación | Evaluación y tratamiento de riesgos, objetivos | Tarea 2 Tablas 2–4 (R1–R15) + R16 (spec §16.3); `docs/requisitos.md` |
| 7 Apoyo | Recursos y documentación controlada | `CLAUDE.md`, `docs/`, versión de cada entregable en git |
| 8 Operación | Implementar y operar los tratamientos | Plan de implementación por subsistema y tickets; despliegue (`docs/despliegue-vps.md`) |
| 9 Evaluación | Seguimiento, auditoría interna | Tests por riesgo, e2e, `/risk-check`, subagente `security-auditor`, `docs/informe-pruebas.md` |
| 10 Mejora | Acciones correctivas | Tabla de brechas B-xx (`docs/requisitos.md` §5); la trazabilidad se actualiza con cada cambio |

### 1.2 Declaración de aplicabilidad (Anexo A) — controles que implementa la aplicación
El proyecto es una aplicación, no una organización completa: los controles de personas (A.6) y físicos (A.7), y la gobernanza (A.5.1–A.5.14), quedan fuera del alcance de este entregable.

| Control | Aplica | Riesgos | Mecanismo en el proyecto | Evidencia |
|---|---|---|---|---|
| A.5.15 Control de acceso | Sí | R5, R13, R16 | `auth_request` a `auth` en cada request; `require_perm` y dueño o miembro de la sala en cada servicio; allowlist por servicio | `test_r05_*`, `test_r16_*` |
| A.5.16 Gestión de identidades | Sí | R4, R5, R13 | Registro abierto que solo da el rol `user`; primer admin solo por CLI (sin credenciales por defecto); una sesión por cuenta; cookie de dispositivo; alias reservado por sala | `test_crea_admin_con_argon2id_y_totp_cifrado`, `test_registro_da_solo_el_rol_user`, `test_r13_*` |
| A.5.17 Información de autenticación | Sí | R1, R4, R8 | Argon2id (RFC 9106); política de contraseñas y claves; TOTP con anti-reuso; JWT RS256 que solo `auth` firma; cookie de dispositivo guardada como SHA-256 | `test_r01_*`, `test_r04_*`, `test_politica_de_claves`, `test_jwt_alterado_401` |
| A.5.18 Derechos de acceso | Sí | R5, R11 | RBAC con roles dinámicos y permisos de un catálogo fijo; los cambios valen en la siguiente petición; MFA para todo permiso de admin; el sistema nunca se queda sin admin; roles de BD por servicio | `test_r05_*`, `test_r11_*` |
| A.5.28 Recopilación de evidencia | Sí | R3 | Cadena de auditoría SHA-256 verificable desde el panel | `test_r03_alteracion_detectada_por_verify` |
| A.5.33 Protección de registros | Sí | R3 | `audit_app` solo `SELECT, INSERT`; `service` deducido del token | `test_r03_rol_app_no_puede_alterar_ni_borrar` |
| A.5.34 Privacidad de datos personales | Parcial | R2, R5 | Solo nombre de usuario y alias (sin correo ni otros datos personales); el admin global no accede a las conversaciones ni cambia la clave de salas ajenas; nunca se registran cuerpos de mensajes | `test_admin_lista_salas_sin_mensajes`, `test_r05_admin_no_cambia_la_clave_ajena`, revisión con `security-auditor` |
| A.8.2 Derechos de acceso privilegiado | Sí | R5, R11 | MFA obligatorio para todo permiso de admin (sin TOTP la sesión no los recibe); `*_owner` solo en el job de migración | `test_r04_permiso_de_admin_sin_totp_no_vale`, `test_r11_*` |
| A.8.3 Restricción de acceso a la información | Sí | R12, R14 | URL firmada ligada al usuario y membresía verificada en la descarga; AAD con la sala; 404 genérico | `test_r12_*`, `test_r14_*` |
| A.8.5 Autenticación segura | Sí | R4, R7, R13 | TOTP, bloqueo, retraso progresivo, `sid` nuevo al pasar a la sesión completa, sesión ligada al dispositivo, hello firmado | `test_r04_*`, `test_r07_*`, `test_r13_*` |
| A.8.6 Gestión de la capacidad | Sí | R10, R15 | Rate limit Nginx, token bucket, tope de Argon2id concurrentes, cupo atómico, tope de registros y de análisis por minuto, máximo 2 salas por dueño | `test_r10_*`, `test_r15_*` |
| A.8.7 Protección contra malware | Sí | R9 | Magic bytes + decodificación Pillow (`stego`) + ClamAV que falla cerrado (`media`) | `test_r09_*` |
| A.8.8 Gestión de vulnerabilidades técnicas | Sí | — | `pip-audit`, `npm audit`, CodeQL, dependencias fijadas en `requirements.lock` / `package-lock.json` | CI (FND-7) |
| A.8.9 Gestión de la configuración | Sí | R2, R11 | Compose declarativo, secretos generados por `gen_secrets.py`, endurecimiento de contenedores | `docker compose config`, revisión |
| A.8.10 Eliminación de información | Sí | R6 | Cuarentena: el admin elimina el archivo físico; borrar un mensaje destruye su contenido y su imagen; las sesiones terminadas invalidan el token | `test_eliminar_borra_el_archivo`, `test_borrar_mensaje_propio` |
| A.8.12 Prevención de fuga de datos | Sí | R12, R2 | `Cache-Control: no-store`, `nosniff`, CSP, errores genéricos, archivos y mensajes cifrados en reposo | `test_r12_*`, `test_r02_*` |
| A.8.15 Registro de actividad | Sí | R3 | Eventos por servicio hacia `audit` (spec §14.2) | un `peers.events(...)` por rechazo |
| A.8.16 Actividades de seguimiento | Sí | R6, R10 | Alertas `warning`/`critical` y aviso en el panel de admin | e2e, verificación manual FE-3 |
| A.8.20 Seguridad de redes | Sí | R7, R10 | TLS 1.3 únicamente, HSTS, `ws://` inexistente, rate limit | e2e (TLS 1.2 rechazado, http → 301) |
| A.8.21 Seguridad de los servicios de red | Sí | R16 | Token por servicio; `/internal/*` nunca enrutado | e2e, `test_r16_*` |
| A.8.22 Segregación de redes | Sí | R11, R16 | Redes `public`, `apps`, `data`, `scan`, `clamav-egress` (internas salvo las que publican); ni el gateway ni `stego` llegan a la BD | `docker compose config` |
| A.8.24 Uso de criptografía | Sí | R2, R7, R14 | TLS 1.3, ECDH P-256 + HKDF + AES-256-GCM, ECDSA, envelope encryption, Argon2id | vectores; `docs/justificacion-criptografica.md` |
| A.8.25 Ciclo de vida de desarrollo seguro | Sí | todos | Plan por tareas con test primero; revisión por tarea; CI | §5 de este documento |
| A.8.26 Requisitos de seguridad de las aplicaciones | Sí | todos | `docs/requisitos.md` (RS-xx) | este repositorio |
| A.8.27 Arquitectura segura | Sí | R5, R11, R16 | Microservicios, gateway único, mínimo privilegio, fallo cerrado | spec §4 |
| A.8.28 Codificación segura | Sí | R1, R9 | SQL parametrizado, validadores Pydantic, reglas `.claude/rules/*`, hook `guard.py`, ruff `S`, bandit | CI |
| A.8.29 Pruebas de seguridad | Sí | todos | Un `test_rNN_*` por riesgo, e2e, calibración de estegoanálisis | `docs/informe-pruebas.md` |
| A.8.31 Separación de entornos | Sí | R11 | `docker-compose.test.yml` (BD de prueba en 5433) separado de `deploy/docker-compose.yml`; secretos distintos | revisión |
| A.8.33 Información de prueba | Sí | — | Imágenes y datos sintéticos; nunca datos reales | `shared.testing` |
| A.5.24–A.5.27 Gestión de incidentes | Parcial | R3, R6 | Detección y registro sí; no hay procedimiento formal de respuesta (fuera de alcance) | `docs/demo.md` (alerta → cuarentena) |
| A.8.13 Copias de respaldo | No | — | Fuera de alcance (entorno académico) | — |

---

## 2. ISO/IEC 27034 — Seguridad de aplicaciones

ISO/IEC 27034 organiza la seguridad de una aplicación en torno a un **marco normativo** (ONF a nivel organización, ANF a nivel aplicación), **controles de seguridad de la aplicación** (ASC) y un **proceso de gestión** (ASMP) que verifica el nivel de confianza.

| Concepto | Qué es | En este proyecto |
|---|---|---|
| **ONF** (marco normativo de la organización) | Reglas, roles y controles reutilizables para todas las aplicaciones del equipo | `.claude/rules/security.md`, `microservices.md`, `backend.md`, `frontend.md`, `testing.md`; *Global Constraints* del plan; `ruff.toml`; hook `guard.py` |
| **ANF** (marco normativo de la aplicación) | La parte del ONF que aplica a esta aplicación, con sus requisitos y controles | Spec + plan + `docs/requisitos.md` + `docs/trazabilidad-riesgos.md` |
| **Contexto de la aplicación** | Actores, tecnología, datos y entorno | Spec §1–§4: actores (usuario, dueño de sala, admin global), stack, datos (cuentas, mensajes, imágenes, claves), entorno (Compose local + VPS) |
| **Nivel de confianza objetivo** | Qué tan fuertes deben ser los controles, según el riesgo | **Alto**: aplicación expuesta a Internet que maneja contenido privado. Se exigen los 16 ASC con test; el riesgo residual objetivo es Bajo/Medio (Tabla 4) |
| **ASC** (control de seguridad de la aplicación) | Control con identificador, contexto, implementación y medida de verificación | Cada R1–R16 es un ASC. La fila de `trazabilidad-riesgos.md` es su ficha: control, archivos, test (medida de verificación) y estado |
| **Nivel de confianza real** | Resultado de verificar los ASC | Proporción de filas con test en verde en la trazabilidad. Meta: 16/16 |

### 2.1 Proceso de gestión (ASMP)
| Paso del proceso | Actividad en el proyecto | Artefacto |
|---|---|---|
| 1. Especificar requisitos y entorno de la aplicación | Requisitos funcionales y de seguridad; alcance; decisiones de interpretación | `docs/requisitos.md`, spec §1–§3 |
| 2. Evaluar los riesgos de seguridad de la aplicación | Activos, amenazas, vulnerabilidades, valoración P×I y tratamiento | Tarea 2 (Tablas 1–4), R16 (spec §16.3), §5.3 de este documento |
| 3. Crear y mantener el marco normativo de la aplicación | Spec, plan, reglas y comandos de Claude Code | `docs/specs/`, `docs/plans/`, `.claude/`, `CLAUDE.md` |
| 4. Aprovisionar y operar la aplicación | Implementación por tareas; despliegue reproducible | Plan, `deploy/`, `docs/despliegue-vps.md` |
| 5. Auditar la seguridad de la aplicación | Tests por riesgo, e2e, revisión automática y calibración | `docs/informe-pruebas.md`, `/risk-check`, `security-auditor`, `docs/calibracion-estego.md` |

### 2.2 Ciclo de vida de seguridad
| Fase | Control de seguridad en la fase | Evidencia |
|---|---|---|
| Requisitos | Requisitos de seguridad con ID; riesgos de la Tarea 2 | `docs/requisitos.md` |
| Diseño | Modelo de confianza, protocolo criptográfico firmado, estructura de datos con restricciones | spec §4, §7, §10 |
| Implementación | Reglas de codificación, hook de secretos, linters de seguridad | `.claude/rules/`, `guard.py`, ruff `S`, bandit |
| Verificación | Pruebas por riesgo, e2e, calibración, revisión | tests, `docs/informe-pruebas.md` |
| Despliegue y operación | Secretos fuera del código, contenedores endurecidos, auditoría y alertas | `deploy/`, spec §4.5, §14 |

---

## 3. Zero Trust

Principio del documento: *ningún usuario, dispositivo, sesión o recurso es confiable por defecto; cada solicitud se autentica, autoriza y valida con mínimo privilegio.*

| Principio | Mecanismo | Dónde | Evidencia |
|---|---|---|---|
| Nada es confiable por estar "dentro" de la red | Los servicios no se creen las cabeceras de identidad: solo valen si el llamador presenta el token del gateway | `shared.identity`, `shared.service_auth` | `test_r16_*`, `test_identidad_solo_vale_si_la_trae_el_gateway` |
| Cada solicitud se autentica | `auth_request` a `auth` en cada request: verifica el JWT **y** la sesión a la que apunta, así que un token se revoca al instante; los permisos se leen de la BD en ese momento | Gateway §13, spec §9.1 | e2e: cabeceras falsificadas ignoradas; `test_jwt_de_sesion_terminada_401` |
| Cada solicitud se autoriza | Permiso del catálogo (`require_perm`), dueño o miembro de la sala, modo de la sala, silencio, URL firmada por destinatario | `shared.identity`, rooms, MED-3 | `test_r05_*`, `test_r12_*`, `test_texto_en_sala_solo_multimedia_4403` |
| Cada entrada se valida | Esquemas Pydantic con `extra="forbid"`, límites de tamaño, firma real del archivo, trama AEAD | §8.1, §9.5, §10.2 | `test_r09_*`, `test_r10_*`, `test_r05_registro_con_campo_role_422` |
| El dispositivo y la sesión se verifican, no se suponen | La sesión de la cuenta queda ligada a la cookie de dispositivo y se comprueba en cada request; una sola sesión por cuenta | ATH-2 | `test_r13_jwt_con_otra_cookie_de_dispositivo_401`, `test_r13_login_desde_otro_dispositivo_409` |
| Mínimo privilegio | El registro solo da `user`; los permisos de admin exigen TOTP; un rol de BD por servicio sin DDL; `audit_app` solo INSERT/SELECT; `chat`/`media` sin DELETE; `cap_drop: ALL`; FS de solo lectura | §4.5, §7.6, §9.1 | `test_r05_*`, `test_r11_*` |
| Comunicación protegida en cualquier ubicación | TLS 1.3 al cliente + cifrado de aplicación entre navegador y `chat`; *hello* firmado contra MITM interno | §10 | vectores, e2e |
| Segmentación | 5 redes; ni el gateway ni `stego` llegan a la BD; solo `media` llega a ClamAV | §4.5 | `docker compose config` |
| Supervisión continua | Cada rechazo se audita; alertas; cadena verificable | §14 | `test_r03_*` |
| Fallar cerrado | Sin secreto no arranca; sin ClamAV o sin audit (en otorgamientos) → 503 | §15 | `test_secreto_ausente_detiene_el_servicio`, `test_r09_clamav_caido_*` |

**Excepción declarada:** el tramo interno gateway→servicio es HTTP plano (spec §3, limitación 3). Lo mitigan los tokens, las redes internas y el cifrado de aplicación de los mensajes. La mejora es mTLS.

---

## 4. Secure by Design

| Principio | Decisión de diseño | Dónde |
|---|---|---|
| Seguridad desde la arquitectura | El modelo de confianza (§4.3) y los 16 riesgos se definieron antes de escribir código; la arquitectura de microservicios nace de R5, R11 y R16 | spec §4, §16 |
| Valores seguros por defecto | Sin credenciales por defecto; el registro solo da el rol `user`; los permisos de admin exigen TOTP; los cuerpos rechazan campos de más; cookies `__Host-`, `HttpOnly`, `SameSite=Strict`; modo `text`/`media` explícito; la sala nace con clave fuerte obligatoria | §8.1, §9.1 |
| Fallar cerrado | Ver §3 | §15 |
| Defensa en profundidad | Capas independientes por riesgo: p. ej. cupo = `UPDATE … WHERE` atómico **y** `CHECK` en BD; archivos = firma + Pillow + ClamAV + estego + sanitización + URL firmada + cifrado en reposo | §7.2, §9.5 |
| Mínima superficie de ataque | Solo PNG/JPEG; sin documentación OpenAPI pública; `/internal/*` sin ruta; un único puerto publicado | §13, §15 |
| Separación de funciones | `owner` (migraciones) frente a `app` (ejecución); claves aisladas por servicio (`jwt_signing_key` y `kek_auth` solo en auth, `kek_chat` solo en chat, `kek_media` solo en media); el dueño administra su sala y el admin global la plataforma, sin acceso a las conversaciones | §4.3 (6), §7.6, §9.3, §11 |
| Seguridad no depende del secreto del diseño | Algoritmos estándar y públicos; vectores de prueba publicados | §10.4 |
| Simplicidad | Una librería compartida y un `Dockerfile` único; sin broker ni malla de servicios (justificado en el spec §3) | §5 |
| Seguridad verificable | Cada control tiene un test con nombre `test_rNN_*` y una fila en la trazabilidad | §16.4 |

---

## 5. Shift Left Security

### 5.1 Actividades por fase
| Fase | Actividad de seguridad temprana | Cuándo |
|---|---|---|
| Análisis | Activos, amenazas, vulnerabilidades y riesgos (Tarea 2) | Antes del diseño |
| Diseño | Modelo de amenazas (§5.3), modelo de confianza, protocolo con vectores | Antes del plan |
| Plan | Cada tarea nace con su test de seguridad (TDD) y su fila de trazabilidad | Antes de cada commit |
| Escritura de código | Hook `guard.py` bloquea `ws://`, claves privadas y secretos literales **al escribir** | En el editor |
| Revisión | Revisor por tarea; `/risk-check`; subagente `security-auditor` (OWASP Top 10 + R1–R16) | Antes de cerrar cada tarea |
| Integración continua | Ver §5.2 | En cada push |
| Pre-despliegue | e2e contra el stack completo; calibración con imágenes reales; verificación manual de TLS | Antes de cada hito |

### 5.2 Controles automáticos en CI (`.github/workflows/ci.yml`)
| Job | Qué detecta | Categoría |
|---|---|---|
| `ruff check` (reglas `E,F,I,B,S,UP`) | Errores, malas prácticas y patrones inseguros (`S` = flake8-bandit) | Análisis estático |
| `bandit -ll` | Vulnerabilidades de Python de severidad media o mayor | SAST |
| **CodeQL** (Python y JavaScript/TypeScript) | Inyecciones, flujos de datos no confiables, uso inseguro de APIs | SAST |
| `pip-audit` / `npm audit --audit-level=high` | CVE en dependencias | SCA |
| **gitleaks** | Secretos o claves en el historial del repositorio | Detección de secretos |
| `pytest -m "not clamav"` por servicio con PostgreSQL real | Regresión de cada control (R1–R16) | Pruebas de seguridad |

### 5.3 Modelo de amenazas (STRIDE por componente)
| Componente | S: suplantación | T: manipulación | R: repudio | I: divulgación | D: denegación | E: elevación |
|---|---|---|---|---|---|---|
| Gateway | Cabeceras de identidad falsas (R16, R5) | Downgrade a `ws://` (R7) | — | Cabeceras y versión del servidor (A.8.12) | Flood de conexiones (R10) | Rutas `/internal/*` (R16) |
| auth | Fuerza bruta de cuentas (R4); token robado o usado desde otro dispositivo (R13) | Fijación de sesión (R4); JWT alterado (firma RS256) | Acceso sin rastro (R3) | Secreto TOTP en BD (R2) | Argon2id masivo; registros masivos (R10) | Asignarse `admin` por el registro o con un campo de más; dejar el sistema sin admin (R5) |
| rooms | Suplantar el alias de otro miembro (alias reservado por sala) | Carrera por el cupo o por el límite de salas (R15) | — | Claves de sala en claro (R1) | Fuerza bruta de claves de sala (R8) | Administrar una sala ajena; el admin global cambiando la clave para leer (R5) |
| chat | MITM en el tramo interno (hello firmado, R7) | Mensaje alterado o repetido (R14) | — | Mensajes en la BD (R2) | Inundación de tramas (R10) | Inyección en otra sala; borrar mensajes ajenos (R14) |
| media | — | Esteganografía y malware (R6, R9) | — | Descarga directa de archivos (R12) | — | Subir estando silenciado o sin ser miembro (R5) |
| stego | — | Imagen que explota el decodificador (R9) | — | — | Bomba de descompresión; análisis masivo (R9, R10) | Usar la API sin el permiso (R5) |
| audit | — | Alterar o borrar la bitácora (R3) | Negar un acceso (R3) | — | — | — |
| BD y red interna | Servicio que se hace pasar por otro (R16) | — | — | Credenciales con privilegios excesivos (R11) | — | Escalar desde un servicio comprometido (R11) |

---

## 6. Índice de evidencia (para el informe y la demo)

| Qué se quiere demostrar | Dónde está la evidencia |
|---|---|
| Requisitos funcionales y de seguridad | `docs/requisitos.md` |
| Riesgo → control → test | `docs/trazabilidad-riesgos.md` |
| Controles ISO ↔ riesgos ↔ mecanismos | §1.2 de este documento + columna ISO de la trazabilidad |
| Justificación criptográfica | `docs/justificacion-criptografica.md` |
| Pruebas ejecutadas y sus resultados | `docs/informe-pruebas.md` (E2E-3) |
| Calibración del estegoanálisis | `docs/calibracion-estego.md` (E2E-3) |
| Guion de la demostración | `docs/demo.md` (E2E-3) |
| Demostración del primer parcial | `docs/postman/parcial-1.postman_collection.json` y `docs/demo-parcial-1.md` |
| Despliegue reproducible | `docs/despliegue-vps.md` |
