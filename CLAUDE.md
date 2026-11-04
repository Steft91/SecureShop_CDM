# Salas de Chat Seguras — contexto del proyecto

Proyecto integrador de **Software Seguro** con **microservicios**. El primer parcial es el enunciado oficial del docente (`docs/enunciado/Proyecto_Integrador_Primer_Parcial.pdf`, entrega el **04/11/2026**; spec §23): dos microservicios sin interfaz gráfica detrás de un API Gateway, probados con Postman. `auth` maneja usuarios, roles ADMIN/ANALYST/USER y su relación N:M, y su login entrega un JWT; `stego` analiza una imagen, la clasifica en `sin_indicios`, `sospechoso`, `no_concluyente` o `error`, aplica una política y guarda el análisis, y solo se entra con el token de `auth`. Sin registro abierto, sin cookies y sin restricción de dispositivos. Las salas, el chat y la interfaz gráfica llegan por incrementos, cuando el docente los defina. Equipo: Manangón, Díaz, Cedeño.

- **Enunciado del primer parcial:** `docs/enunciado/` (PDF del docente y su texto en `.md`)
- **Spec (diseño de referencia):** `docs/specs/2026-10-12-chat-seguro-design.md` (rev. 5; **la §23 manda en el primer parcial**)
- **Plan:** `docs/plans/2026-10-13-00-indice.md` (+ un archivo por subsistema)
- **Tickets (por parcial y persona):** `docs/tickets/README.md`
- **Riesgos → controles → tests:** `docs/trazabilidad-riesgos.md`
- **Requisitos del docente (RF/RS):** `docs/requisitos.md` · **Normas y enfoques:** `docs/cumplimiento-normativo.md` · **Criptografía justificada:** `docs/justificacion-criptografica.md`
- **Documentos académicos:** `Documentación/` (no tocar sin que lo pidan)

## Arquitectura
| Pieza | Qué hace | BD |
|---|---|---|
| gateway (Nginx) | Único punto de entrada: TLS 1.3, rate limit, `auth_request` a `auth` en cada petición y enrutamiento a `auth` y `stego` | — |
| auth | Login (Argon2id, bloqueo progresivo), JWT RS256 + sesión revocable, usuarios, roles ADMIN/ANALYST/USER y la N:M `user_roles`; `POST /internal/authorization/check`; CLI `create_admin` | auth |
| stego | Firma, Pillow, chi²/RS/estructura, veredicto y política; guarda cada análisis; `POST /api/steganography/analyze` y `GET /api/steganography/results/{id}` | stego |

Confianza: el gateway pregunta a `auth` en cada request y sobrescribe `X-User-*` con la identidad y los permisos actuales. Cada servicio exige `X-Service-Token` (guarda solo hashes) y acepta esas cabeceras únicamente si el llamador es `gateway`. Detalle en `.claude/rules/microservices.md`.

Eventos de seguridad: cada servicio los escribe como registros JSON con `shared.audit.emit` (login, permiso denegado, rol creado, imagen analizada…).

## Mapa del repo
```
services/shared   librería común (secrets, crypto, passwords, ratelimit, service_auth, identity, audit, web, observability, testing)
services/<svc>    <svc>_svc/ (código) · migrations/ (solo auth) · tests/ · pyproject.toml · requirements.lock
services/Dockerfile   plantilla única (ARG SERVICE) · services/lock.sh
gateway/          nginx.conf · snippets/ · Dockerfile
deploy/           docker-compose.yml · docker-compose.test.yml · gen_secrets.py · postgres/init.sh
docs/             spec, planes, tickets, colección de Postman, trazabilidad, informe
```

## Comandos
Preparación (una vez): `py -3.13 -m venv .venv` (macOS/Linux: `python3.13 -m venv .venv`), activar e instalar:
```bash
pip install -e "services/shared[dev]" -e services/auth -e services/stego
```
| Tarea | Comando |
|---|---|
| BD de pruebas | `docker compose -f deploy/docker-compose.test.yml up -d` |
| Tests de un servicio | `pytest services/<svc>` |
| Lint | `ruff check services deploy` y `ruff format --check services deploy` |
| Secretos locales | `python deploy/gen_secrets.py` |
| Certificados locales | `mkcert -install` y `mkcert -cert-file deploy/certs/fullchain.pem -key-file deploy/certs/privkey.pem localhost 127.0.0.1 ::1` |
| Stack del parcial | `docker compose -f deploy/docker-compose.yml up -d --build` |
| Redesplegar un servicio | `docker compose -f deploy/docker-compose.yml up -d --build <svc>` |
| Crear admin | `docker compose -f deploy/docker-compose.yml exec auth python -m auth_svc.create_admin <usuario>` |
| Eventos de seguridad | `docker compose -f deploy/docker-compose.yml logs auth stego` |
| Fijar dependencias | PowerShell: `docker run --rm -v "${PWD}:/w" -w /w python:3.13-slim sh services/lock.sh <svc>` |

## Reglas que Claude debe respetar
- Siempre `.claude/rules/security.md` y `.claude/rules/microservices.md`; `backend.md` y `testing.md` según la ruta.
- Antes de cerrar una tarea: `/risk-check` y, si tocó seguridad, el subagente `security-auditor`.
- No leer `deploy/secrets/` ni `deploy/certs/` (denegados en `.claude/settings.json`).
- **Prohibido hacer `merge` a `main`** hasta que el equipo lo autorice; cada persona trabaja en su rama (`feat/<nombre>-<tema>`, creada desde `main`). No hagas `push` ni abras PR sin que te lo pidan.
- macOS/Linux: si el hook falla porque no encuentra `python`, activa el `.venv` antes de abrir Claude Code.

## Estado actual
Actualizar al cerrar cada ticket (`docs/tickets/README.md` tiene la ruta de cada persona).
- Primer parcial: [x] 01 Fundaciones (FND-1 ✓, FND-2 ✓, FND-3 ✓, FND-4 ✓, FND-5 ✓, FND-6 ✓) · [x] 03 Auth (ATH-1 ✓, ATH-2 ✓, ATH-3 ✓, ATH-4 ✓) · [ ] 10 Stego · [ ] 04 Gateway (GW-1) · [ ] Entrega (PAR-1…3)
