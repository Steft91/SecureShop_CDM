# Cumplimiento normativo y enfoques de seguridad — Primer parcial

> En el primer parcial solo se entregan `auth`, `stego` y el gateway. El servicio `audit`, la auditoría encadenada y TOTP quedan fuera de alcance.

| | |
|---|---|
| **Qué demuestra** | Cómo ISO/IEC 27001, ISO/IEC 27034, Zero Trust, Secure by Design y Shift Left se aplican al primer parcial (gateway, `auth` y `stego`), y cómo se relacionan con sus riesgos y con los mecanismos implementados |
| **Riesgos del parcial** | R2, R4, R5, R6, R7, R9, R10, R11, R13 y R16. Los demás (R1, R3, R8, R12, R14, R15) son de salas, chat, archivos y auditoría, y entran cuando se construyan esas piezas |
| **Requisito** | `docs/requisitos.md` RS-30…RS-34 (Actividad 3) |
| **Fuentes del proyecto** | `docs/specs/2026-10-12-chat-seguro-design.md` · `docs/plans/` · `docs/trazabilidad-riesgos.md` · Tarea 2 (Tablas 1–4) |
| **Estado de la evidencia** | Los mecanismos están **planificados y con test especificado**. La columna *Evidencia* cita el test o la prueba manual; el estado real vive en `docs/trazabilidad-riesgos.md` |

---

## 1. ISO/IEC 27001:2022

### 1.1 Sistema de gestión (cláusulas 4–10)
| Cláusula | Qué pide | Dónde está en el proyecto |
|---|---|---|
| 4 Contexto | Alcance y partes interesadas | Tarea 2 §2.1 (alcance del SGSI y activos críticos); spec §1–§3 y su nota de alcance del primer parcial |
| 5 Liderazgo | Política y roles | Reparto por persona en `docs/tickets/parcial-1/`; reglas en `.claude/rules/` |
| 6 Planificación | Evaluación y tratamiento de riesgos, objetivos | Tarea 2 Tablas 2–4 (R1–R15), R16 (spec §16.3) y `docs/requisitos.md` |
| 7 Apoyo | Recursos y documentación controlada | `CLAUDE.md`, `docs/` y la versión de cada entregable en git |
| 8 Operación | Implementar y operar los tratamientos | Planes por servicio y tickets; despliegue con `deploy/docker-compose.yml` |
| 9 Evaluación | Seguimiento y auditoría interna | Tests por riesgo, `/risk-check`, subagente `security-auditor` y las evidencias de `docs/informe-parcial-1.md` |
| 10 Mejora | Acciones correctivas | La trazabilidad se actualiza con cada cambio; lo que se dejó fuera queda en `docs/requisitos.md` §5 |

### 1.2 Declaración de aplicabilidad (Anexo A) — controles que implementa el parcial
El proyecto es una aplicación, no una organización completa: los controles de personas (A.6) y físicos (A.7), y la gobernanza (A.5.1–A.5.14), quedan fuera del alcance de este entregable.

| Control | Aplica | Riesgos | Mecanismo en el proyecto | Evidencia |
|---|---|---|---|---|
| A.5.15 Control de acceso | Sí | R5, R13, R16 | `auth_request` a `auth` en cada petición; `require_perm` en cada servicio; allowlist de llamadores por servicio | `test_r05_*`, `test_r16_*` |
| A.5.16 Gestión de identidades | Sí | R4, R5, R13 | Registro abierto sin roles; admin global solo por CLI (sin credenciales por defecto); una sesión por cuenta; cookie de dispositivo | `test_registro_crea_cuenta_sin_roles`, `test_crea_admin_con_argon2id_y_rol_admin`, `test_r13_*` |
| A.5.17 Información de autenticación | Sí | R4 | Argon2id (RFC 9106); política de contraseñas; JWT RS256 que solo `auth` firma; cookie de dispositivo guardada como SHA-256 | `test_r04_*`, `test_politica_de_claves`, `test_jwt_alterado_401` |
| A.5.18 Derechos de acceso | Sí | R5, R11 | RBAC con roles dinámicos y permisos de un catálogo fijo; los cambios valen en la siguiente petición; el sistema nunca se queda sin admin; roles de BD separados | `test_r05_*`, `test_r11_*` |
| A.5.34 Privacidad de datos personales | Parcial | R2, R5 | Solo se guarda el nombre de usuario (sin correo ni otros datos personales); `stego` no guarda las imágenes | revisión con `security-auditor` |
| A.8.2 Derechos de acceso privilegiado | Sí | R5, R11 | Los permisos de admin los da solo otro admin; `auth_owner` solo en el job de migración | `test_r05_sin_roles_manage_403`, `test_r11_*` |
| A.8.5 Autenticación segura | Sí | R4, R13 | Bloqueo tras 5 fallos, error genérico, sesión ligada al dispositivo y verificada en cada petición | `test_r04_*`, `test_r13_*` |
| A.8.6 Gestión de la capacidad | Sí | R10 | Rate limit en Nginx, token bucket por usuario en `stego`, tope de Argon2id concurrentes y de registros por IP | `test_r10_*` |
| A.8.7 Protección contra malware | Parcial | R9 | Magic bytes, decodificación con Pillow y topes de tamaño y de píxeles en `stego`; el antivirus llega con la subida de archivos | `test_r09_*` |
| A.8.8 Gestión de vulnerabilidades técnicas | Sí | — | `pip-audit`, CodeQL y dependencias fijadas en `requirements.lock` | CI (FND-7) |
| A.8.9 Gestión de la configuración | Sí | R2, R11 | Compose declarativo, secretos generados por `gen_secrets.py`, contenedores endurecidos | `docker compose config`, revisión |
| A.8.12 Prevención de fuga de datos | Sí | R2 | `Cache-Control: no-store`, `nosniff`, CSP, errores genéricos y registros sin secretos ni query strings | `test_errores_genericos`, `test_una_linea_por_peticion_sin_query_string` |
| A.8.15 Registro de actividad | Parcial | R5, R6 | Eventos de seguridad como registros JSON en cada servicio, con id de correlación; la bitácora encadenada queda para después | `test_formato_json_de_los_registros`, `testing.events(...)` por evento |
| A.8.16 Actividades de seguimiento | Parcial | R6, R10 | Eventos `warning` ante imágenes sospechosas y límites superados, visibles en `docker compose logs` | demo de PAR-3 |
| A.8.20 Seguridad de redes | Sí | R7, R10 | TLS 1.3 únicamente, HSTS, http → https, rate limit | verificación manual de GW-1 |
| A.8.21 Seguridad de los servicios de red | Sí | R16 | Token del gateway con allowlist por hash; `/internal/*` nunca enrutado | `test_r16_*`, GW-1 |
| A.8.22 Segregación de redes | Sí | R11, R16 | Redes `public`, `apps` y `data`; ni el gateway ni `stego` llegan a la BD | `docker compose config` |
| A.8.24 Uso de criptografía | Sí | R2, R7 | TLS 1.3, Argon2id, JWT RS256, tokens aleatorios con hash SHA-256 | `docs/justificacion-criptografica.md` |
| A.8.25 Ciclo de vida de desarrollo seguro | Sí | todos | Plan por tareas con test primero, revisión por tarea y CI | §5 de este documento |
| A.8.26 Requisitos de seguridad de las aplicaciones | Sí | todos | `docs/requisitos.md` (RS-xx) | este repositorio |
| A.8.27 Arquitectura segura | Sí | R5, R11, R16 | Microservicios, gateway único, mínimo privilegio, fallo cerrado | spec §4 |
| A.8.28 Codificación segura | Sí | R9 | SQL parametrizado, validadores Pydantic, reglas `.claude/rules/*`, hook `guard.py`, ruff `S`, bandit | CI |
| A.8.29 Pruebas de seguridad | Sí | todos | Un `test_rNN_*` por riesgo, calibración del estegoanálisis y la colección de Postman | `docs/informe-parcial-1.md` |
| A.8.31 Separación de entornos | Sí | R11 | `docker-compose.test.yml` (BD de prueba en 5433) separado de `deploy/docker-compose.yml`; secretos distintos | revisión |
| A.8.33 Información de prueba | Sí | — | Imágenes y datos sintéticos; nunca datos reales | `stego_svc.synthetic`, `shared.testing` |
| A.8.13 Copias de respaldo | No | — | Fuera de alcance (entorno académico) | — |

---

## 2. ISO/IEC 27034 — Seguridad de aplicaciones

ISO/IEC 27034 organiza la seguridad de una aplicación en torno a un **marco normativo** (ONF a nivel organización, ANF a nivel aplicación), **controles de seguridad de la aplicación** (ASC) y un **proceso de gestión** (ASMP) que verifica el nivel de confianza.

| Concepto | Qué es | En este proyecto |
|---|---|---|
| **ONF** (marco normativo de la organización) | Reglas, roles y controles reutilizables para todas las aplicaciones del equipo | `.claude/rules/security.md`, `microservices.md`, `backend.md`, `testing.md`; *Global Constraints* de los planes; `ruff.toml`; hook `guard.py` |
| **ANF** (marco normativo de la aplicación) | La parte del ONF que aplica a esta aplicación, con sus requisitos y controles | Spec, planes, `docs/requisitos.md` y `docs/trazabilidad-riesgos.md` |
| **Contexto de la aplicación** | Actores, tecnología, datos y entorno | Actores: usuario y admin global. Stack: FastAPI, PostgreSQL y Nginx. Datos: cuentas, roles y sesiones. Entorno: Docker Compose local |
| **Nivel de confianza objetivo** | Qué tan fuertes deben ser los controles, según el riesgo | **Alto**: API expuesta que maneja cuentas y permisos. Cada ASC del parcial tiene su test; el riesgo residual objetivo es Bajo/Medio (Tabla 4) |
| **ASC** (control de seguridad de la aplicación) | Control con identificador, contexto, implementación y medida de verificación | Cada riesgo del parcial es un ASC. Su fila en `trazabilidad-riesgos.md` es la ficha: control, archivos, test y estado |
| **Nivel de confianza real** | Resultado de verificar los ASC | Proporción de filas del parcial con test en verde. Meta: 10/10 |

### 2.1 Proceso de gestión (ASMP)
| Paso del proceso | Actividad en el proyecto | Artefacto |
|---|---|---|
| 1. Especificar requisitos y entorno de la aplicación | Requisitos funcionales y de seguridad, alcance y decisiones de interpretación | `docs/requisitos.md`, spec §1–§3 |
| 2. Evaluar los riesgos de seguridad de la aplicación | Activos, amenazas, vulnerabilidades, valoración P×I y tratamiento | Tarea 2 (Tablas 1–4), R16 (spec §16.3), §5.3 de este documento |
| 3. Crear y mantener el marco normativo de la aplicación | Spec, planes, reglas y comandos de Claude Code | `docs/specs/`, `docs/plans/`, `.claude/`, `CLAUDE.md` |
| 4. Aprovisionar y operar la aplicación | Implementación por tareas y despliegue reproducible | Planes, `deploy/` |
| 5. Auditar la seguridad de la aplicación | Tests por riesgo, revisión automática, calibración y Postman | `docs/informe-parcial-1.md`, `/risk-check`, `security-auditor`, `docs/calibracion-estego.md` |

### 2.2 Ciclo de vida de seguridad
| Fase | Control de seguridad en la fase | Evidencia |
|---|---|---|
| Requisitos | Requisitos de seguridad con ID; riesgos de la Tarea 2 | `docs/requisitos.md` |
| Diseño | Modelo de confianza y estructura de datos con restricciones | spec §4, §7 |
| Implementación | Reglas de codificación, hook de secretos, linters de seguridad | `.claude/rules/`, `guard.py`, ruff `S`, bandit |
| Verificación | Pruebas por riesgo, calibración, revisión y la colección de Postman | tests, `docs/informe-parcial-1.md` |
| Despliegue y operación | Secretos fuera del código, contenedores endurecidos, eventos de seguridad en los registros | `deploy/`, spec §4.5 |

---

## 3. Zero Trust

Principio del documento: *ningún usuario, dispositivo, sesión o recurso es confiable por defecto; cada solicitud se autentica, autoriza y valida con mínimo privilegio.*

| Principio | Mecanismo | Dónde | Evidencia |
|---|---|---|---|
| Nada es confiable por estar "dentro" de la red | Los servicios no se creen las cabeceras de identidad: solo valen si el llamador presenta el token del gateway | `shared.identity`, `shared.service_auth` | `test_identidad_solo_vale_si_la_trae_el_gateway`, `test_r16_*` |
| Cada solicitud se autentica | `auth_request` a `auth` en cada petición: verifica el JWT **y** la sesión a la que apunta, así que un token se revoca al instante; los permisos se leen de la BD en ese momento | GW-1, ATH-2 | `test_jwt_de_sesion_terminada_401`; curl de GW-1 con cabeceras falsificadas |
| Cada solicitud se autoriza | Permiso del catálogo con `require_perm` en `auth` y en `stego` | `shared.identity` | `test_r05_*` |
| Cada entrada se valida | Esquemas Pydantic con `extra="forbid"`, límites de tamaño y firma real del archivo | §8.1, §12.1 | `test_r09_*`, `test_r10_*`, `test_r05_registro_con_campo_role_422` |
| El dispositivo y la sesión se verifican, no se suponen | La sesión queda ligada a la cookie de dispositivo y se comprueba en cada petición; una sola sesión por cuenta | ATH-2 | `test_r13_jwt_con_otra_cookie_de_dispositivo_401`, `test_r13_login_desde_otro_dispositivo_409` |
| Mínimo privilegio | La cuenta nace sin roles; `auth_app` sin DDL; `cap_drop: ALL`; FS de solo lectura | §4.5, §7.6, §9.1 | `test_r05_*`, `test_r11_*` |
| Comunicación protegida | TLS 1.3 entre el cliente y el gateway | §13 | verificación manual de GW-1 |
| Segmentación | Tres redes; ni el gateway ni `stego` llegan a la BD | §4.5 | `docker compose config` |
| Supervisión continua | Cada rechazo emite un evento con el id de correlación | §14 | `testing.events(...)` en los tests |
| Fallar cerrado | Sin un secreto el servicio no arranca; `auth` caído → 503 en el gateway; análisis que excede el tiempo → `revision_manual` | §15 | `test_secreto_ausente_detiene_el_servicio`, `test_timeout_del_analisis_es_revision_manual`, curl de GW-1 |

**Excepción declarada:** el tramo interno gateway→servicio es HTTP plano (spec §3, limitación 3). Lo mitigan el token del gateway y las redes internas. La mejora es mTLS.

---

## 4. Secure by Design

| Principio | Decisión de diseño | Dónde |
|---|---|---|
| Seguridad desde la arquitectura | El modelo de confianza (§4.3) y los riesgos se definieron antes de escribir código; los microservicios nacen de R5, R11 y R16 | spec §4, §16 |
| Valores seguros por defecto | Sin credenciales por defecto; la cuenta nace sin roles; los cuerpos rechazan campos de más; cookies `__Host-`, `HttpOnly`, `SameSite=Strict` | §8.1, §9.1 |
| Fallar cerrado | Ver §3 | §15 |
| Defensa en profundidad | Capas independientes: rate limit en Nginx **y** token bucket en `stego`; firma real **y** decodificación **y** tope de píxeles; una sesión por cuenta en el código **y** en un índice único de la BD | §7.1, §12.1, §13 |
| Mínima superficie de ataque | Solo PNG/JPEG; sin documentación OpenAPI pública; `/internal/*` sin ruta; un único puerto publicado; `stego` sin BD | §13, §15 |
| Separación de funciones | `auth_owner` (migraciones) frente a `auth_app` (ejecución); `jwt_signing_key` solo en `auth` | §4.3, §7.6, §11 |
| La seguridad no depende del secreto del diseño | Algoritmos estándar y públicos | `docs/justificacion-criptografica.md` |
| Simplicidad | Una librería compartida y un `Dockerfile` único; sin broker ni malla de servicios | §5 |
| Seguridad verificable | Cada control tiene un test `test_rNN_*` y una fila en la trazabilidad | §16.4 |

---

## 5. Shift Left Security

### 5.1 Actividades por fase
| Fase | Actividad de seguridad temprana | Cuándo |
|---|---|---|
| Análisis | Activos, amenazas, vulnerabilidades y riesgos (Tarea 2) | Antes del diseño |
| Diseño | Modelo de amenazas (§5.3) y modelo de confianza | Antes del plan |
| Plan | Cada tarea nace con su test de seguridad (TDD) y su fila de trazabilidad | Antes de cada commit |
| Escritura de código | El hook `guard.py` bloquea `ws://`, claves privadas y secretos literales **al escribir** | En el editor |
| Revisión | Revisión por tarea, `/risk-check` y el subagente `security-auditor` (OWASP Top 10 y los riesgos del parcial) | Antes de cerrar cada tarea |
| Integración continua | Ver §5.2 | En cada push |
| Antes de la entrega | Calibración con imágenes reales, verificación manual de TLS y el Runner de Postman desde un clon limpio | PAR-3 |

### 5.2 Controles automáticos en CI (`.github/workflows/ci.yml`)
| Job | Qué detecta | Categoría |
|---|---|---|
| `ruff check` (reglas `E,F,I,B,S,UP,C90`) | Errores, malas prácticas, patrones inseguros (`S` = flake8-bandit) y complejidad > 10 | Análisis estático |
| `bandit -ll` | Vulnerabilidades de Python de severidad media o mayor | SAST |
| **CodeQL** (Python) | Inyecciones, flujos de datos no confiables, uso inseguro de APIs | SAST |
| `pip-audit` | CVE en dependencias | SCA |
| **gitleaks** | Secretos o claves en el historial del repositorio | Detección de secretos |
| `pytest` por servicio con PostgreSQL real y cobertura ≥ 80 % | Regresión de cada control | Pruebas de seguridad |

### 5.3 Modelo de amenazas (STRIDE por componente)
| Componente | S: suplantación | T: manipulación | R: repudio | I: divulgación | D: denegación | E: elevación |
|---|---|---|---|---|---|---|
| Gateway | Cabeceras de identidad falsas (R16, R5) | Downgrade a http (R7) | — | Cabeceras y versión del servidor (A.8.12) | Flood de peticiones (R10) | Rutas `/internal/*` (R16) |
| auth | Fuerza bruta de cuentas (R4); token robado o usado desde otro dispositivo (R13) | JWT alterado (firma RS256) | Acceso sin rastro (eventos JSON) | Clave de firma del JWT en el código (R2) | Argon2id masivo; registros masivos (R10) | Asignarse `admin` por el registro o con un campo de más; dejar el sistema sin admin (R5) |
| stego | — | Imagen que explota el decodificador (R9) | — | — | Bomba de descompresión; análisis masivo (R9, R10) | Usar la API sin el permiso (R5) |
| BD y red interna | Servicio que se hace pasar por el gateway (R16) | — | — | Credenciales con privilegios excesivos (R11) | — | Escalar desde un servicio comprometido (R11) |

---

## 6. Índice de evidencia (para el informe y la demo)

| Qué se quiere demostrar | Dónde está la evidencia |
|---|---|
| Requisitos funcionales y de seguridad | `docs/requisitos.md` |
| Riesgo → control → test | `docs/trazabilidad-riesgos.md` |
| Controles ISO ↔ riesgos ↔ mecanismos | §1.2 de este documento y la columna ISO de la trazabilidad |
| Justificación criptográfica | `docs/justificacion-criptografica.md` |
| Pruebas ejecutadas y sus resultados | Sección de evidencias de `docs/informe-parcial-1.md` (PAR-2) |
| Calibración del estegoanálisis | `docs/calibracion-estego.md` (STG-4) |
| Colección y corrida de Postman | `docs/postman/parcial-1.postman_collection.json` y `docs/evidencias/parcial-1-runner.png` (PAR-1) |
| Guion de la demostración | `docs/demo-parcial-1.md` (PAR-3) |
