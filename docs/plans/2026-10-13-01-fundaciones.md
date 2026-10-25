# 01 · Fundaciones — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar listo todo lo que comparten los servicios: el contexto de Claude Code, la librería `shared` (secretos, cripto, contraseñas, límites, autenticación entre servicios, identidad del usuario con sus permisos, auditoría, base web, utilidades de prueba), los vectores cripto, la plantilla Docker, la generación de secretos (incluida la clave de firma de los JWT), PostgreSQL con 5 BD y la CI.

**Architecture:** `services/shared` es un paquete Python instalable (`chat-shared` → `import shared`). Cada servicio lo instala junto al suyo. La infraestructura (Dockerfile único con `ARG SERVICE`, `gen_secrets.py`, `init.sh`) se escribe una vez y cada servicio solo agrega su bloque al compose.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2 + asyncpg, Alembic, cryptography, argon2-cffi, httpx, pytest · Docker Compose · GitHub Actions.

**Spec:** `docs/specs/2026-10-12-chat-seguro-design.md` (§4.3, §5, §7.6, §10, §11, §15, §16, §17).

## Global Constraints

Las de `docs/plans/2026-10-13-00-indice.md` § *Global Constraints*. Resumen operativo:
- Python 3.13.
- `text()` con parámetros nombrados.
- Todas las rutas exigen `X-Service-Token` salvo `/health`.
- Errores `{"error": "..."}` en español.
- Cookies `__Host-*` con `Secure`, `HttpOnly` y `SameSite=Strict`.
- Secretos solo desde `/run/secrets`.
- Nunca `ws://`.
- Un test `test_rNN_*` por riesgo.
- Commits en español, sin atribución.

## Review Focus

Ninguno de los 5 casos del índice cae en este archivo, pero las utilidades que se crean aquí los soportan:
- `TokenBucket` para los límites del WS y de la API de esteganografía.
- `natural_image`/`embed_lsb` para los tests de imágenes.
- `user_headers` arma la identidad que pasa el gateway, con los permisos separados por comas; `user_from_headers` tolera que `X-User-Perms` no venga (sin permisos).

---

### Task FND-1: Higiene del repo y contexto de Claude Code

**Files:**
- Create: `.gitignore`, `.gitattributes`, `.dockerignore`, `ruff.toml`
- Create: `.github/pull_request_template.md`
- Create: `CLAUDE.md`
- Create: `.claude/settings.json`
- Create: `.claude/rules/security.md`, `.claude/rules/microservices.md`, `.claude/rules/backend.md`, `.claude/rules/frontend.md`, `.claude/rules/testing.md`
- Create: `.claude/commands/risk-check.md`
- Create: `.claude/skills/stego-analysis/SKILL.md`, `.claude/skills/crypto-protocol/SKILL.md`
- Create: `.claude/agents/security-auditor.md`
- Create: `.claude/hooks/guard.py`
- Create: `docs/trazabilidad-riesgos.md`

**Interfaces:**
- Consumes: nada.
- Produces:
  - El hook `guard.py`, que corre antes de cada `Edit|Write|MultiEdit` de Claude Code.
  - La tabla de trazabilidad que actualizan todas las tareas.
  - `ruff.toml` en la raíz, que aplica a todo `services/`, `deploy/` y `e2e/`. Incluye la regla `C90` con complejidad ciclomática ≤ 10 por función (RNF-11): una función más compleja se parte en el mismo ticket, no se silencia.
  - `.github/pull_request_template.md` con la lista de verificación de seguridad (A3-RS-32).

- [ ] **Step 1: Escribir el hook con su autoprueba**

`.claude/hooks/guard.py`:
```python
#!/usr/bin/env python3
"""Hook PreToolUse (Edit/Write/MultiEdit): bloquea secretos y canales en claro antes de tocar el disco.

Exit 2 = bloquear; Claude Code muestra el motivo (stderr). Autoprueba:
    python .claude/hooks/guard.py --self-test
"""

import json
import os
import re
import sys

RULES = [
    (re.compile(r"\bws://"), "usa wss:// (riesgo 7): el gateway solo acepta TLS 1.3"),
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "clave privada en el código (riesgo 2): va en deploy/secrets/",
    ),
    (
        re.compile(
            r"""(?i)\b(password|passwd|secret|token|api_key|kek|dek|signing_key)\s*[:=]\s*b?["'][^"'\s]{16,}["']"""
        ),
        "secreto literal (riesgo 2): léelo con shared.secrets desde /run/secrets",
    ),
]
EXEMPT_PREFIXES = ("docs/", ".claude/", "Documentación/", "e2e/", "CLAUDE.md", "CLAUDE.local.md")


def is_exempt(relative: str) -> bool:
    return relative.startswith(EXEMPT_PREFIXES) or "/tests/" in f"/{relative}"


def new_text(tool_input: dict) -> str:
    if "content" in tool_input:
        return tool_input["content"]
    if "new_string" in tool_input:
        return tool_input["new_string"]
    return "\n".join(edit.get("new_string", "") for edit in tool_input.get("edits", []))


def check(path: str, text: str, project: str) -> str | None:
    try:
        relative = os.path.relpath(path, project).replace("\\", "/")
    except ValueError:  # otra unidad en Windows
        relative = path.replace("\\", "/")
    if is_exempt(relative):
        return None
    for pattern, reason in RULES:
        if pattern.search(text):
            return f"{relative}: {reason}"
    return None


def self_test() -> int:
    root = "/repo"
    assert check("/repo/services/chat/chat_svc/ws.py", "url = 'ws://x'", root)
    assert check("/repo/services/chat/chat_svc/ws.py", "url = 'wss://x'", root) is None
    assert check("/repo/services/auth/auth_svc/x.py", 'password = "SuperSecreta-12345678"', root)
    assert check("/repo/services/auth/tests/test_x.py", 'password = "SuperSecreta-12345678"', root) is None
    assert check("/repo/docs/specs/a.md", "nunca ws://", root) is None
    assert check("/repo/deploy/llave.txt", "-----BEGIN PRIVATE KEY-----", root)
    assert check("/repo/services/stego/stego_svc/formats.py", 'signature=b"\\x89PNG\\r\\n"', root) is None
    print("guard.py: autoprueba OK")
    return 0


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        return self_test()
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    problem = check(tool_input.get("file_path", ""), new_text(tool_input), project)
    if problem:
        print(f"Bloqueado por .claude/hooks/guard.py — {problem}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Ejecutar la autoprueba**

Run: `python .claude/hooks/guard.py --self-test`
Expected: `guard.py: autoprueba OK`

- [ ] **Step 3: Registrar el hook y los permisos**

`.claude/settings.json`:
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(pytest:*)",
      "Bash(python -m pytest:*)",
      "Bash(ruff:*)",
      "Bash(alembic:*)",
      "Bash(docker compose:*)",
      "Bash(npm run:*)",
      "Bash(npm ci)",
      "Bash(npx vitest:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(git log:*)"
    ],
    "deny": [
      "Read(./deploy/secrets/**)",
      "Read(./deploy/certs/**)",
      "Read(./**/.env)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard.py\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Higiene del repositorio**

`.gitignore`:
```gitignore
# Secretos, certificados y archivos generados por entorno (spec §11)
deploy/secrets/
deploy/certs/
deploy/public/
.env
*.pem
*.key

# Contexto local de cada integrante
CLAUDE.local.md
.claude/settings.local.json

# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.ruff_cache/
*.egg-info/
build/

# Node
node_modules/
frontend/dist/

# Calibración del estegoanálisis (imágenes personales)
services/stego/tools/calibracion/
```

`.gitattributes`:
```gitattributes
* text=auto
*.sh text eol=lf
*.conf text eol=lf
*.png binary
*.jpg binary
*.pdf binary
*.docx binary
```

`.dockerignore`:
```gitignore
.git
**/.venv
**/node_modules
**/__pycache__
**/.pytest_cache
**/.ruff_cache
**/tests
deploy/secrets
deploy/certs
deploy/public
Documentación
docs
e2e
frontend/dist
```

`ruff.toml`:
```toml
line-length = 100
target-version = "py313"

[lint]
select = ["E", "F", "I", "B", "S", "UP", "C90"]  # C90: complejidad ciclomática (RNF-11)
ignore = ["E501"]  # ruff format ajusta el código; SQL y comentarios largos no se parten a la fuerza

[lint.mccabe]
max-complexity = 10

[lint.isort]
known-first-party = ["shared", "auth_svc", "rooms_svc", "chat_svc", "media_svc", "stego_svc", "audit_svc"]

[lint.flake8-bugbear]
# FastAPI declara dependencias y parámetros con llamadas en los valores por defecto.
extend-immutable-calls = ["fastapi.Depends", "fastapi.Query", "fastapi.params.Depends", "fastapi.params.Query"]

[lint.per-file-ignores]
"**/tests/**" = ["S101", "S105", "S106", "S311"]
"e2e/**" = ["S101", "S105", "S106", "S113", "S311", "S603", "S607"]
"services/shared/shared/testing.py" = ["S101", "S105", "S106", "S311", "S603", "S608"]
"services/*/tools/**" = ["S311"]
"deploy/**" = ["S603", "S607"]
```

- [ ] **Step 5: Reglas de Claude Code**

`.claude/rules/security.md`:
```markdown
# Invariantes de seguridad (aplican a todo el repo)

Fuente: spec §2–§15 y Tabla 3 de la Tarea 2. Si un cambio rompe una de estas reglas, se detiene y se discute; no se "arregla después".

1. **Transporte:** el cliente solo habla TLS 1.3 con el gateway. Nunca `ws://` ni `http://` hacia el navegador. El WS va por `wss://${location.host}/ws`.
2. **Secretos:** solo se leen con `shared.secrets` desde `/run/secrets`. Nunca en el código, en variables de entorno ni en logs. Los valores de prueba viven en `tests/` o en `shared/testing.py` y lo dicen en un comentario.
3. **Identidad:** el usuario sale de la identidad que verificó el gateway (`require_user`, `require_perm`, `user_from_headers`), y el alias y la pertenencia a la sala, de `rooms`. Nunca del cuerpo de la petición ni de la trama.
4. **Autorización:** por permiso del catálogo (`require_perm`) o por dueño/miembro de la sala, siempre en el servidor. Nunca por el rol del JWT ni por un campo del cuerpo. Los modelos de entrada usan `extra="forbid"`.
5. **SQL:** siempre `text()` con parámetros nombrados. Prohibido interpolar datos con f-strings.
6. **Contraseñas y claves de sala:** Argon2id (`shared.passwords`), con verificación contra un hash dummy cuando el usuario o la sala no existen.
7. **Errores:** el cliente recibe `{"error": "..."}` genérico; el detalle va a auditoría. Todo rechazo de seguridad se audita (`audit.emit(...)`).
8. **Datos sensibles:** nunca se registran contraseñas, claves de sala, tokens (JWT incluidos), cuerpos de mensajes ni secretos TOTP.
9. **Fallar cerrado:** si falta un secreto, el servicio no arranca. Si ClamAV, `stego` o la BD no responden → 503. Si `audit` no responde en un evento que otorga algo → 503 con rollback. Lo que **quita** acceso (logout, suspensión, expulsión, cierre) nunca espera a la auditoría.
10. **Cripto:** solo con `shared.crypto` (AES-256-GCM con AAD, ECDH P-256, HKDF-SHA256, ECDSA P-256) y PyJWT con `algorithms=["RS256"]` fijo. Nada de primitivas propias ni modos sin autenticación.
11. **Archivos:** jamás se sirve un archivo sin firma HMAC válida y pertenencia a la sala. Todo archivo publicado pasó por la sanitización.
12. **Datos en reposo:** los mensajes (DEK por sala, `chat`) y los archivos (DEK por archivo, `media`) se guardan siempre cifrados con envelope encryption. Un archivo en el volumen nunca es una imagen legible.
13. **Documentos de cumplimiento:** un cambio de control, algoritmo, clave o ruta de datos actualiza `docs/trazabilidad-riesgos.md` y, si aplica, `docs/justificacion-criptografica.md` y `docs/cumplimiento-normativo.md`.
```

`.claude/rules/microservices.md`:
```markdown
# Modelo de confianza entre microservicios (R16, spec §4.3)

- Toda ruta de un servicio exige `X-Service-Token` válido (`ServiceTokenMiddleware`, que agrega `shared.web.create_base_app`). Solo `/health` está exento.
- Rutas públicas (enrutadas por el gateway): `Depends(require_gateway)`, `Depends(require_user)` o `Depends(require_perm("<permiso>"))`. Rutas internas: `/internal/...` con `Depends(allow("<llamador>", ...))`.
- Las cabeceras `X-User-Id`, `X-User-Name`, `X-Session-Id` y `X-User-Perms` **solo** se leen a través de `shared.identity`, que exige que el llamador sea `gateway`. Los permisos que traen son los actuales: el gateway los pide a `auth` en cada request.
- Cada servicio se conecta **solo a su BD** con su rol `<svc>_app`. Nunca se consulta la BD de otro servicio: se pide por su API interna (por ejemplo, la membresía de una sala se le pregunta a `rooms`).
- Las llamadas a otros servicios pasan por `ServiceClient` (`app.state.peers`), nunca por un `httpx` suelto.
- Allowlist vigente: auth ← gateway, chat · rooms ← gateway, chat, media · chat ← gateway, auth, rooms, media · media ← gateway, chat · stego ← gateway, media · audit ← gateway, auth, rooms, chat, media, stego.
- Agregar un servicio o un llamador requiere tocar:
  - la red en `deploy/docker-compose.yml`;
  - los secretos `svc_token_*`/`svc_hash_*` y `deploy/gen_secrets.py`;
  - el rol de BD en `deploy/postgres/init.sh` (si el servicio guarda datos);
  - la allowlist del receptor;
  - esta regla.
```

`.claude/rules/backend.md`:
```markdown
---
paths:
  - "services/**"
---
# Convenciones de los servicios Python

- Paquete `<svc>_svc` dentro de `services/<svc>/`. Fábrica `create_app(settings=None, *, engine=None, service_auth=None, transport=None)`; sin argumentos lee secretos y entorno.
- Configuración en `config.py`: `Settings` (dataclass congelada) + `load_settings()`. Las perillas no secretas salen de `shared.secrets.env(NOMBRE, default)`.
- Rutas en módulos con `router = APIRouter()`. Nada de lógica en `main.py`.
- Transacciones con `async with engine.begin()`; lecturas con `engine.connect()`.
  - Un evento de rechazo se audita **después** del bloque (si no, el rollback lo perdería).
  - Un evento que otorga algo se audita **dentro** con `required=True`.
- Migraciones a mano (`op.execute`) con `GRANT` explícitos a `<svc>_app`. `migrations/env.py` solo llama `shared.migrations.run("<svc>")`.
- Las dependencias del servicio van en su `pyproject.toml`. Después de cambiarlas se regenera `requirements.lock` con `services/lock.sh`.
```

`.claude/rules/frontend.md`:
```markdown
---
paths:
  - "frontend/**"
---
# Convenciones del frontend

- TypeScript `strict`. Prohibido `dangerouslySetInnerHTML`, `eval` y HTML construido con strings.
- Toda la criptografía pasa por `src/lib/crypto.ts` (WebCrypto). Las `CryptoKey` son no extraíbles y viven solo en memoria.
- Nada en `localStorage`/`sessionStorage`: los tokens (el JWT incluido) están en cookies `HttpOnly` que JS no ve. La SPA ignora el `access_token` del cuerpo del login.
- Los botones se muestran según `GET /api/auth/me` (permisos) y `is_owner` de la sala, pero ocultarlos no protege nada: la autorización es del servidor.
- Sin estilos ni scripts inline (la CSP los bloquea). Estilos en `src/styles.css`.
- Sin `React.StrictMode`: monta los efectos dos veces, abre y cierra el WebSocket, y eso termina la sesión.
- HTTP solo por `src/lib/api.ts`; WebSocket solo por `src/lib/ws.ts`.
```

`.claude/rules/testing.md`:
```markdown
---
paths:
  - "**/tests/**"
  - "e2e/**"
---
# Convenciones de pruebas

- PostgreSQL real (`deploy/docker-compose.test.yml`, puerto 5433). Nunca mocks de BD.
- Un archivo `test_rNN_<tema>.py` por riesgo; el nombre de cada test describe el comportamiento, en español.
- Los servicios vecinos se simulan con `shared.testing.Recorder`. Se verifica a quién se llamó, con qué token y con qué cuerpo.
- WebSocket: `TestClient` dentro de `with` (un solo event loop) y la clase `Participant` del `conftest.py` de chat.
- Escribe el test, míralo fallar y recién entonces implementa.
- Al cerrar una tarea, actualiza `docs/trazabilidad-riesgos.md`.
```

- [ ] **Step 6: Comando, skills y subagente**

`.claude/commands/risk-check.md`:
```markdown
---
description: Contrasta los cambios actuales con R1–R16 y actualiza la trazabilidad
---
Revisa los cambios de la rama actual contra los riesgos del proyecto.

1. Obtén el diff: `git diff main...HEAD` y `git diff` (lo que no está commiteado).
2. Lee `docs/trazabilidad-riesgos.md`, `docs/requisitos.md`, `.claude/rules/security.md` y `.claude/rules/microservices.md`.
3. Por cada archivo cambiado, identifica qué riesgo (R1–R16) toca. La tabla del spec §16.4 dice qué servicio cubre cada uno.
4. Señala:
   - controles que el cambio debilita (con `archivo:línea`);
   - controles nuevos sin test `test_rNN_*`;
   - violaciones de las reglas.
5. Actualiza en `docs/trazabilidad-riesgos.md` las columnas *Servicio / archivos*, *Tests* y *Estado* de las filas afectadas. No marques "Implementado" sin un test en verde que lo demuestre: antes ejecuta `pytest services/<svc> -k rNN`.
6. Termina con una lista corta: qué quedó cubierto, qué falta y qué riesgo empeoró (si alguno).
```

`.claude/skills/stego-analysis/SKILL.md`:
```markdown
---
name: stego-analysis
description: Referencia del estegoanálisis del servicio stego (chi² de Westfeld, análisis RS, entropía LSB, estructura PNG/JPEG, veredicto, sanitización por aleatorización del LSB y calibración). Úsala al tocar services/stego o services/media, ajustar umbrales o agregar un formato.
---
# Estegoanálisis en `stego` (spec §12)

`stego` no guarda nada: valida, analiza y sanitiza. `media` decide la política (cuarentena, rechazo o publicación) con el veredicto.

## Veredicto (spec §12.7)
| Veredicto | Cuándo | Política en las salas |
|---|---|---|
| `invalida` (422) | Firma, tamaño, píxeles o decodificación inválidos | Rechazo |
| `problema` | Anomalía estructural (datos al final, chunks de texto grandes o desconocidos, metadatos JPEG excesivos) | Cuarentena |
| `revision_manual` | chi², RS (o entropía, si se activa) sobre el umbral, o timeout del análisis | Cuarentena |
| `limpia` | Nada de lo anterior | Sanitización y publicación |

Si coinciden una anomalía estructural y una estadística, gana `problema`.

## Detectores (PNG, canales RGB)
| Detector | Cálculo | Dispara si |
|---|---|---|
| Chi² (Westfeld–Pfitzmann) | Por canal: pares `(2k, 2k+1)`, `E=(h2k+h2k+1)/2`, `χ²=Σ(h2k−E)²/E` (pares con `E>4`), `p = chi2.sf(χ², pares−1)`; prefijos 10/25/50/100 % (≥ 1000 píxeles) | `p ≥ STEGO_CHI2_P` (0.95) |
| RS (Fridrich 2001) | Grupos 2×2 en zigzag, variación `Σ|xᵢ₊₁−xᵢ|`, máscara `[0,1,1,0]`, raíz de menor módulo de `2(d1+d0)x² + (d−0−d−1−d1−3d0)x + d0−d−0`, `p̂ = x/(x−½)` | `p̂ ≥ STEGO_RS_RATE` (0.08) |
| Entropía LSB | Bloques 64×64; media y fracción de bloques con H ≥ 0.999 | Solo si `STEGO_ENTROPY_TRIGGER` está activo (por defecto, no) |
| Estructura PNG | Bytes tras `IEND`, chunks de texto > 1 KB, chunks desconocidos | Cualquiera |
| Estructura JPEG | Más de 16 bytes tras `FFD9`, APPn+COM > 64 KB | Cualquiera |

## Valores medidos en el prototipo (2026-10-13, imágenes sintéticas "fotográficas")
| Imagen | chi² p | RS p̂ |
|---|---|---|
| Limpia (3 semillas) | 0.33–0.38 | 0.002–0.013 |
| LSB secuencial 5 % | 0.993–0.999 | 0.04–0.05 |
| LSB secuencial 10 % | 0.9994–0.9999 | 0.094–0.098 |
| LSB aleatorio 10 % | 0.59–0.69 | 0.11–0.12 |
| LSB aleatorio 50 % | 0.994–0.998 | 0.51–0.54 |
| LSB aleatorio 100 % | 1.0 | 1.0 (¡0.0 en una semilla: RS degenera cerca del 100 %; lo cubre chi²!) |
| Captura con colores planos | 0.0 | 0.0 |

## Sanitización y por qué existe `clean_sha256`
- PNG: XOR del plano LSB con bits aleatorios (destruye LSB-1) y recodificación sin chunks auxiliares; conserva el alfa.
- JPEG: orientación EXIF aplicada y recodificación RGB q=90 sin metadatos.
- Una imagen con el LSB aleatorizado es estadísticamente igual a una con LSB embebido al 100 % (chi² = 1.0). Por eso `media` guarda `clean_sha256` y no vuelve a analizar sus propias salidas. También se probaron como alternativas poner el LSB en cero (lo marca RS = 0.19), recodificar como JPEG (chi² 0.89–0.96) y redimensionar (chi² 0.997).

## Calibración con fotos reales
1. Copia ≥ 30 imágenes limpias (fotos de celular, capturas) en `services/stego/tools/calibracion/` (gitignored). Para el primer parcial alcanzan 15.
2. `python services/stego/tools/stego_lab.py calibrate services/stego/tools/calibracion`
3. Elige umbrales con FPR ≤ 5 % y TPR máxima para "secuencial 10 %". Configúralos con `STEGO_CHI2_P` / `STEGO_RS_RATE` en `deploy/docker-compose.yml` y anota la tabla en `docs/calibracion-estego.md`.

## Agregar un formato
1. Firma + `pil_format` + `analyze` + `sanitize` en `stego_svc/formats.py` (`FORMATS`).
2. Módulo `stego_svc/<formato>.py` con funciones de módulo (las ejecuta un `ProcessPoolExecutor`).
3. Clasificar sus motivos en `stego_svc/verdict.py` (`STRUCTURAL` o `STATISTICAL`).
4. Tests: uno limpio, uno con payload y uno de sanitización. Actualizar R6/R9 en la trazabilidad.
```

`.claude/skills/crypto-protocol/SKILL.md`:
```markdown
---
name: crypto-protocol
description: Protocolo criptográfico del chat (hello ECDSA firmado, ECDH P-256, HKDF-SHA256, AES-256-GCM con AAD, tramas, códigos de cierre, vectores) y gestión de claves (KEK/DEK, rotación, tokens de servicio). Úsala al tocar shared/crypto.py, chat_svc, frontend/src/lib/crypto.ts o ws.ts.
---
# Protocolo del chat (spec §10–§11)

## Handshake (por conexión WS)
1. Cliente → `{"t":"hello","pub":"<b64url punto P-256 sin comprimir, 65 B>"}` (primera trama, ≤ 10 s).
2. chat: ECDH efímero, `salt` de 32 B, `K = HKDF-SHA256(shared, salt, info="secure-chat/v1|{room_id}|{session_id}", 32)`. `session_id` es el id de la sesión de la cuenta (`X-Session-Id`, claim `sid` del JWT).
3. chat firma `T = "secure-chat/v1/hello|{room}|{session}|{client_pub}|{server_pub}|{salt}"` con ECDSA P-256/SHA-256 (firma P1363 `r‖s`, 64 B) y responde `{"t":"hello","pub","salt","sig"}`.
4. El cliente verifica `sig` sobre `T` reconstruida con **su** `client_pub`, usando `/chat-key.json` (lo sirve el gateway). Si falla → cierra con 4400.

## Tramas
- `{"seq","n","c"}`: AES-256-GCM, nonce aleatorio de 12 B, tag de 16 B al final de `c`. AAD `v1|{room}|{session}|{seq}|{c2s|s2c}`; en `s2c`, la sesión es la del destinatario.
- `seq` empieza en 1 por conexión y dirección, y es estrictamente creciente.
- El payload es JSON compacto (`separators=(",", ":")`, `ensure_ascii=False`), igual que `JSON.stringify`.
- Códigos de cierre: 4400 malformada, tag o handshake · 4401 sesión o membresía terminada · 4403 origin, no miembro, modo, archivo ajeno o borrado no autorizado · 4408 replay · 4409 reemplazada · 4410 inactividad · 4411 expulsado · 4413 grande · 4429 rate.

## Vectores
`docs/crypto-vectors.json` se regenera con `python services/shared/tools/gen_crypto_vectors.py`. Lo verifican `services/shared/tests/test_vectors.py` y `frontend/src/lib/crypto.test.ts`. Si cambias el protocolo, regenera y deja ambos tests en verde.

## Claves y rotación
| Clave | Dónde | Rotación |
|---|---|---|
| `jwt_signing_key` | auth (RSA 3072, firma los JWT RS256) | `python deploy/gen_secrets.py --rotate jwt_signing_key` + reiniciar auth (todos vuelven a iniciar sesión) |
| `kek_auth_v{n}` | auth (TOTP) | montar v{n+1}, `CURRENT_KEK_VERSION`, `python -m auth_svc.rotate_kek` |
| `kek_chat_v{n}` | chat (DEK de salas) | igual + `python -m chat_svc.rotate kek` |
| DEK de una sala | `room_keys` (chat) | `python -m chat_svc.rotate room <room_id>` |
| `kek_media_v{n}` | media (DEK de cada archivo, `files.dek_wrapped`) | igual + `python -m media_svc.rotate_kek` |
| `chat_sign_key` | chat; pública en `deploy/public/chat-key.json` | `python deploy/gen_secrets.py --rotate chat_sign_key` + reiniciar chat y el gateway |
| `svc_token_<x>` | dueño; hash en los receptores | `--rotate svc_token_<x>` + reiniciar `<x>` y sus receptores |
```

`.claude/agents/security-auditor.md`:
```markdown
---
name: security-auditor
description: Revisor de seguridad de solo lectura. Úsalo antes de cerrar una tarea o un PR para contrastar los cambios con los riesgos R1–R16, OWASP Top 10 y el modelo de confianza entre microservicios.
tools: Read, Grep, Glob, Bash
---
Eres el auditor de seguridad del proyecto "Salas de Chat Seguras" (curso Software Seguro). Solo lees; nunca editas archivos.

Antes de opinar, lee:
- `docs/specs/2026-10-12-chat-seguro-design.md` §4.3 (modelo de confianza), §10–§14;
- `.claude/rules/security.md` y `.claude/rules/microservices.md`;
- `docs/trazabilidad-riesgos.md` y `docs/requisitos.md` (requisitos RS-xx).

Procedimiento:
1. `git diff main...HEAD --stat` y luego el diff de cada archivo de `services/`, `gateway/`, `frontend/src/` y `deploy/`.
2. Para cada cambio, pregúntate:
   - ¿Viola alguna invariante?
   - ¿Lee identidad sin `shared.identity`?
   - ¿Agrega una ruta sin token o sin allowlist?
   - ¿Interpola SQL?
   - ¿Filtra datos sensibles a logs o errores?
   - ¿Falla abierto?
   - ¿Rompe el protocolo de `shared/crypto.py`?
3. Verifica que cada control tocado siga teniendo su `test_rNN_*`; ejecuta `pytest services/<svc> -q` si hace falta.

Formato de salida: una lista ordenada por severidad (Crítica, Alta, Media, Baja). Cada ítem lleva `archivo:línea`, riesgo afectado (R1–R16 u OWASP A0x), qué falla y la corrección concreta. Si no hay hallazgos, dilo explícitamente e indica qué revisaste.
```

- [ ] **Step 7: Tabla de trazabilidad inicial**

`docs/trazabilidad-riesgos.md`:
```markdown
# Trazabilidad de riesgos → controles → pruebas

Fuente de riesgos: Tarea 2 (Tablas 1–4) + R16 (spec §16.3). Cada tarea del plan actualiza su fila. "Implementado" exige un test en verde.

La columna *ISO/IEC 27001:2022* relaciona cada control con el Anexo A; el detalle (mecanismo y evidencia) está en `docs/cumplimiento-normativo.md` §1.2. Los requisitos RF/RS del docente están en `docs/requisitos.md`.

| R | Riesgo | Control (Tabla 3 / spec) | ISO/IEC 27001:2022 | Servicio / archivos | Tests | Estado |
|---|---|---|---|---|---|---|
| R1 | Claves de sala en texto plano | Argon2id con sal única | A.5.17, A.8.24 | rooms | — | Pendiente |
| R2 | Claves criptográficas en el código fuente | Docker secrets, KEK/DEK (mensajes y archivos), rotación | A.8.24, A.8.9, A.8.12 | shared, auth, chat, media | — | Pendiente |
| R3 | Manipulación de registros de auditoría | Servicio audit, rol solo INSERT/SELECT, cadena SHA-256 | A.8.15, A.5.28, A.5.33 | audit | — | Pendiente |
| R4 | Fuerza bruta contra las cuentas | Bloqueo + retraso progresivo + TOTP para permisos de admin | A.8.5, A.5.17 | auth | — | Pendiente |
| R5 | Operaciones sin verificación de permisos | `auth_request` con permisos actuales + `require_perm` y dueño de sala en cada servicio; registro sin `admin`; nunca sin admin | A.5.15, A.8.2, A.5.18 | gateway, auth, rooms, media, stego, audit | — | Pendiente |
| R6 | Imágenes con esteganografía | chi²/RS/estructura (`stego`) + cuarentena + sanitización (`media`) | A.8.7, A.8.16 | stego, media | — | Pendiente |
| R7 | WebSocket sin cifrar | TLS 1.3, `wss://`, Origin, hello firmado + AES-GCM | A.8.20, A.8.24 | gateway, chat | — | Pendiente |
| R8 | Fuerza bruta de claves de sala | Rate limit IP/usuario/sala + política de clave | A.5.17, A.8.5, A.8.6 | rooms | — | Pendiente |
| R9 | Archivos maliciosos | Magic bytes, Pillow, tope de píxeles (`stego`), ClamAV (`media`) | A.8.7, A.8.28 | stego, media | — | Pendiente |
| R10 | Agotamiento de conexiones | Rate limit Nginx + token bucket + tamaño de trama | A.8.6, A.8.20 | gateway, chat | — | Pendiente |
| R11 | Credenciales de BD con privilegios excesivos | Rol `<svc>_app` sin DDL, una BD por servicio | A.8.2, A.5.18, A.8.22 | todos | — | Pendiente |
| R12 | Archivos accesibles sin autorización | URL firmada + pertenencia a la sala | A.8.3, A.8.12 | media | — | Pendiente |
| R13 | Sesiones simultáneas de una cuenta | Índice único parcial en `user_sessions` + sesión ligada a la cookie de dispositivo + vencimiento por inactividad | A.5.16, A.5.15, A.8.5 | auth | — | Pendiente |
| R14 | Mensajes inyectados en otra sala | Identidad desde la sesión, AAD, anti-replay | A.8.3, A.8.24 | chat | — | Pendiente |
| R15 | Cupo superado por concurrencia | `UPDATE … WHERE current < max` + `CHECK` | A.8.6, A.8.28 | rooms | — | Pendiente |
| R16 | Suplantación entre microservicios | Token por servicio con hash, allowlist, gateway sobrescribe identidad | A.5.15, A.8.21, A.8.22 | shared, todos | — | Pendiente |

## Verificación manual (evidencia para el informe)
| Prueba | Comando | Resultado esperado | Fecha / resultado |
|---|---|---|---|
| TLS 1.2 rechazado | `curl --tlsv1.2 --tls-max 1.2 https://localhost/` | error de handshake | — |
| http → https | `curl -I http://localhost/ws` | `301` | — |
| /internal no enrutado | `curl https://localhost/internal/verify` | `404` JSON | — |
| Cabeceras de identidad falsificadas | `curl -H "X-User-Id: x" -H "X-User-Perms: audit:read" https://localhost/api/admin/audit` | `401` JSON | — |
| Flujo del parcial (Postman) | Runner de `docs/postman/parcial-1.postman_collection.json` | todas las pruebas en verde | — |
```

- [ ] **Step 8: Escribir `CLAUDE.md`**

`CLAUDE.md`:
````markdown
# Salas de Chat Seguras — contexto del proyecto

Proyecto integrador de **Software Seguro**: salas de chat con **microservicios**, cuentas con roles (RBAC) y salas con dueño, como en Discord. El objetivo es demostrar con pruebas los tratamientos de riesgo del SGSI (Tarea 2) más R16 (suplantación entre microservicios). Equipo: Manangón, Díaz, Cedeño. Primer parcial: auth + stego + audit + gateway, probado con Postman; lo demás, por incrementos.

- **Spec (fuente de verdad):** `docs/specs/2026-10-12-chat-seguro-design.md` (rev. 4)
- **Plan:** `docs/plans/2026-10-13-00-indice.md` (+ un archivo por subsistema)
- **Tickets (cadena Andrés → Stefany → Zaith):** `docs/tickets/README.md`
- **Riesgos → controles → tests:** `docs/trazabilidad-riesgos.md`
- **Requisitos del docente (RF/RS):** `docs/requisitos.md` · **Normas y enfoques:** `docs/cumplimiento-normativo.md` · **Criptografía justificada:** `docs/justificacion-criptografica.md`
- **Documentos académicos:** `Documentación/` (no tocar sin que lo pidan)

## Arquitectura
| Pieza | Qué hace | BD |
|---|---|---|
| gateway (Nginx) | TLS 1.3, CSP/HSTS, rate limit, `auth_request` a `auth`, SPA, `/chat-key.json` | — |
| auth | Registro, login (Argon2id, TOTP para permisos de admin), JWT RS256 + sesión por dispositivo, roles y permisos; `GET /internal/verify` | auth |
| rooms | Salas con dueño (máx. 2), membresía con clave y alias, cupo atómico, expulsión, veto y silencio | rooms |
| chat | WebSocket: hello firmado (ECDSA) + ECDH → AES-256-GCM por conexión; mensajes cifrados en reposo; borrado | chat |
| media | Subida: ClamAV → `stego` → cuarentena o sanitización; archivos cifrados; URL firmadas | media |
| stego | Firma, Pillow, chi²/RS/estructura, veredicto y sanitización; `POST /api/stego/analyze` | — |
| audit | Log encadenado con SHA-256; su rol solo hace INSERT/SELECT | audit |

Confianza: el gateway pregunta a `auth` en cada request y sobrescribe `X-User-*` con la identidad y los permisos actuales. Cada servicio exige `X-Service-Token` (guarda solo hashes) y acepta esas cabeceras únicamente si el llamador es `gateway`. Detalle en `.claude/rules/microservices.md`.

## Mapa del repo
```
services/shared   librería común (secrets, crypto, passwords, ratelimit, service_auth, identity, audit_client, web, testing)
services/<svc>    <svc>_svc/ (código) · migrations/ · tests/ · pyproject.toml · requirements.lock
services/Dockerfile   plantilla única (ARG SERVICE) · services/lock.sh
gateway/          nginx.conf · snippets/ · Dockerfile (compila la SPA)
frontend/         React + Vite + TS (src/lib/crypto.ts, ws.ts, api.ts; src/pages/)
e2e/              pruebas contra el stack completo vía https://localhost
deploy/           docker-compose.yml · docker-compose.test.yml · gen_secrets.py · postgres/init.sh
docs/             spec, planes, tickets, colección de Postman, trazabilidad, vectores cripto, despliegue
```

## Comandos
Preparación (una vez): `py -3.13 -m venv .venv` (macOS/Linux: `python3.13 -m venv .venv`), activar e instalar:
```bash
pip install -e "services/shared[dev]" -e services/audit -e services/auth -e services/stego
```
(Con el incremento 2 se suman `-e services/rooms -e services/chat`, y con el 3, `-e services/media`.)
| Tarea | Comando |
|---|---|
| BD de pruebas | `docker compose -f deploy/docker-compose.test.yml up -d` |
| Tests de un servicio | `pytest services/<svc>` (ClamAV real: levantar el perfil `clamav` y `pytest services/media -m clamav`) |
| Lint | `ruff check services deploy e2e` y `ruff format --check services deploy e2e` |
| Secretos locales | `python deploy/gen_secrets.py` |
| Certificados locales | `mkcert -install` y `mkcert -cert-file deploy/certs/fullchain.pem -key-file deploy/certs/privkey.pem localhost 127.0.0.1 ::1` |
| Stack completo | `docker compose -f deploy/docker-compose.yml up -d --build` |
| Redesplegar un servicio | `docker compose -f deploy/docker-compose.yml up -d --build <svc>` |
| Crear admin | `docker compose -f deploy/docker-compose.yml exec auth python -m auth_svc.create_admin <usuario>` |
| e2e | `pytest e2e` (con el stack arriba) |
| Frontend | `cd frontend && npm ci && npm run dev` · `npm test` · `npm run build` |
| Fijar dependencias | PowerShell: `docker run --rm -v "${PWD}:/w" -w /w python:3.13-slim sh services/lock.sh <svc>` |

## Reglas que Claude debe respetar
- Siempre `.claude/rules/security.md` y `.claude/rules/microservices.md`; `backend.md`, `frontend.md` y `testing.md` según la ruta.
- Antes de cerrar una tarea: `/risk-check` y, si tocó seguridad, el subagente `security-auditor`.
- No leer `deploy/secrets/` ni `deploy/certs/` (denegados en `.claude/settings.json`).
- **Prohibido hacer `merge` a `main`** hasta que el equipo lo autorice; el trabajo va en `feat/arquitectura-chat-seguro` o ramas hijas. No hagas `push` ni abras PR sin que te lo pidan.
- macOS/Linux: si el hook falla porque no encuentra `python`, activa el `.venv` antes de abrir Claude Code.

## Estado actual
Actualizar al cerrar cada ticket (`docs/tickets/README.md` tiene la cadena completa).
- Primer parcial: [ ] 01 Fundaciones · [ ] 02 Audit · [ ] 03 Auth (ATH-1…4) · [ ] 10 Stego · [ ] 04 Gateway (GW-1) · [ ] Parcial (PAR-1…3)
- Incremento 2: [ ] 03 Auth (ATH-5…6) · [ ] 05 Rooms · [ ] 06 Chat · [ ] 04 Gateway (GW-2) · [ ] 08 Frontend (FE-1…3)
- Incremento 3: [ ] 07 Media · [ ] 08 Frontend (FE-4…5) · [ ] 09 E2E y cierre
````

- [ ] **Step 9: Plantilla de PR**

`.github/pull_request_template.md`:
```markdown
## Qué cambia
<!-- La tarea del plan (p. ej. ATH-2) y su ticket (T-12). -->

## Riesgos y requisitos
<!-- R# y RF/RS que toca. -->

## Lista de verificación de seguridad
- [ ] Sin secretos, tokens ni contraseñas en el código, los registros ni los tests (salvo valores de prueba marcados como tales)
- [ ] La autorización se decide en el servidor, por permiso o por pertenencia, nunca por un campo que mande el cliente
- [ ] Cuerpos con `extra="forbid"`, consultas parametrizadas y errores genéricos hacia el cliente
- [ ] Todo rechazo y todo otorgamiento de acceso se audita
- [ ] Hay un `test_rNN_*` por cada control tocado y `docs/trazabilidad-riesgos.md` está al día
- [ ] ruff, pytest (cobertura ≥ 80 %), bandit y pip-audit en verde
- [ ] Nadie hace `merge` a `main` sin que el equipo lo autorice
```

- [ ] **Step 10: Verificar formato y commit**

Run: `python .claude/hooks/guard.py --self-test && python -c "import json; json.load(open('.claude/settings.json', encoding='utf-8')); print('settings OK')"`
Expected: `guard.py: autoprueba OK` y `settings OK`

```bash
git add .gitignore .gitattributes .dockerignore ruff.toml .github/pull_request_template.md CLAUDE.md .claude docs/trazabilidad-riesgos.md
git commit -m "chore: contexto de Claude Code, reglas de seguridad y trazabilidad de riesgos"
```

---

### Task FND-2: Paquete `shared`: secretos, criptografía y vectores

**Files:**
- Create: `services/shared/pyproject.toml`
- Create: `services/shared/shared/__init__.py`, `services/shared/shared/crypto.py`, `services/shared/shared/secrets.py`
- Create: `services/shared/tools/gen_crypto_vectors.py`
- Create: `docs/crypto-vectors.json` (generado)
- Test: `services/shared/tests/test_crypto.py`, `services/shared/tests/test_r02_secretos.py`, `services/shared/tests/test_vectors.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `shared.crypto`:
    - codificación y hashes: `b64e(bytes)->str`, `b64d(str)->bytes`, `sha256(bytes)->bytes`;
    - tokens y claves: `new_token(nbytes=32)->str`, `token_hash(str)->bytes`, `new_key()->bytes`;
    - AES-GCM: `seal(key, plaintext, aad, nonce=None)->bytes` (nonce‖ct‖tag) y `unseal(key, blob, aad)->bytes` (lanza `InvalidTag`);
    - AAD: `dek_aad(room_id)`, `totp_aad(admin_id)`, `msg_aad(room_id, session_id)`, `frame_aad(room_id, session_id, seq, direction)`;
    - ECDH/ECDSA: `CURVE`, `public_bytes(private)->bytes`, `load_public_key(raw)->EllipticCurvePublicKey` (lanza `ValueError`), `derive_session_key(shared, salt, room_id, session_id)->bytes`, `hello_transcript(room_id, session_id, client_pub_b64, server_pub_b64, salt_b64)->bytes`, `load_signing_key(pem)`, `sign_p1363(private, data)->bytes` (64 B), `verify_p1363(public, sig, data)->bool`;
    - handshake: `Handshake(reply: dict, key: bytes)`, `server_hello(client_pub_b64, room_id, session_id, sign_key, server_private=None, salt=None)->Handshake`;
    - tramas: `encode_payload(dict)->bytes`, `encrypt_frame(key, room_id, session_id, seq, direction, payload, nonce=None)->dict`, `decrypt_frame(key, room_id, session_id, direction, frame)->tuple[int, dict]` (lanza `ValueError` o `InvalidTag`);
    - URLs firmadas: `sign_url(key, file_id, session_id, exp)->str`, `verify_url(key, file_id, session_id, exp, sig, now)->bool`.
  - `shared.secrets`: `secrets_dir()`, `read_secret(name)->str`, `read_key(name)->bytes`, `read_versioned_keys(prefix, current)->dict[int, bytes]`, `env(name, default)`, `origins()->frozenset[str]`, `db_url(service, role)->str`.

- [ ] **Step 1: Empaquetado**

`services/shared/pyproject.toml`:
```toml
[project]
name = "chat-shared"
version = "0.1.0"
description = "Librería común de los microservicios del chat seguro"
requires-python = ">=3.13"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "httpx>=0.28",
  "python-multipart>=0.0.18",
  "sqlalchemy[asyncio]>=2.0.36",
  "asyncpg>=0.30",
  "alembic>=1.14",
  "argon2-cffi>=23.1",
  "cryptography>=44",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3",
  "pytest-timeout>=2.3",
  "pytest-cov>=5.0",
  "ruff>=0.8",
  "bandit>=1.8",
  "pip-audit>=2.7",
  "websockets>=14",
  "numpy>=2.1",
  "pillow>=11.0",
]

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["shared*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
timeout = 60
```

`services/shared/shared/__init__.py`:
```python
"""Librería común de los microservicios del chat seguro (spec §5)."""
```

Run: `pip install -e "services/shared[dev]"`
Expected: `Successfully installed chat-shared-0.1.0 ...`

- [ ] **Step 2: Tests de criptografía (fallan)**

`services/shared/tests/test_crypto.py`:
```python
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from shared.crypto import (
    CURVE,
    InvalidTag,
    b64d,
    b64e,
    decrypt_frame,
    derive_session_key,
    encrypt_frame,
    hello_transcript,
    load_public_key,
    load_signing_key,
    public_bytes,
    seal,
    server_hello,
    sign_url,
    unseal,
    verify_p1363,
    verify_url,
)

ROOM, SESSION = "room-1", "sess-1"
SIGNER = ec.generate_private_key(CURVE)  # clave de firma efímera, solo para estas pruebas


def client_key(reply: dict, private: ec.EllipticCurvePrivateKey) -> bytes:
    shared = private.exchange(ec.ECDH(), load_public_key(b64d(reply["pub"])))
    return derive_session_key(shared, b64d(reply["salt"]), ROOM, SESSION)


def test_seal_y_unseal_con_aad():
    key = b"\x01" * 32
    blob = seal(key, b"hola", b"aad")
    assert unseal(key, blob, b"aad") == b"hola"
    assert len(blob) == 12 + 4 + 16


def test_unseal_rechaza_alteracion_aad_distinto_y_blob_corto():
    key = b"\x01" * 32
    blob = seal(key, b"hola", b"aad")
    with pytest.raises(InvalidTag):
        unseal(key, blob[:-1] + bytes([blob[-1] ^ 1]), b"aad")
    with pytest.raises(InvalidTag):
        unseal(key, blob, b"otro")
    with pytest.raises(InvalidTag):
        unseal(key, b"corto", b"aad")


def test_hello_firmado_y_clave_compartida():
    private = ec.generate_private_key(CURVE)
    client_pub = b64e(public_bytes(private))
    hs = server_hello(client_pub, ROOM, SESSION, SIGNER)
    reply = hs.reply
    assert reply["t"] == "hello"
    transcript = hello_transcript(ROOM, SESSION, client_pub, reply["pub"], reply["salt"])
    assert verify_p1363(SIGNER.public_key(), b64d(reply["sig"]), transcript)
    assert client_key(reply, private) == hs.key


def test_firma_no_valida_si_cambia_la_clave_del_cliente():
    hs = server_hello(b64e(public_bytes(ec.generate_private_key(CURVE))), ROOM, SESSION, SIGNER)
    impostor = b64e(public_bytes(ec.generate_private_key(CURVE)))
    transcript = hello_transcript(ROOM, SESSION, impostor, hs.reply["pub"], hs.reply["salt"])
    assert not verify_p1363(SIGNER.public_key(), b64d(hs.reply["sig"]), transcript)


@pytest.mark.parametrize("bad", ["AAAA", b64e(b"\x04" + b"\x01" * 64), "no-es-base64-é"])
def test_hello_rechaza_clave_publica_invalida(bad):
    with pytest.raises(ValueError):
        server_hello(bad, ROOM, SESSION, SIGNER)


def test_tramas_ida_y_vuelta_y_alteraciones():
    key = b"\x02" * 32
    payload = {"t": "msg", "body": "hola ñandú 🎉"}
    frame = encrypt_frame(key, ROOM, SESSION, 1, "c2s", payload)
    assert decrypt_frame(key, ROOM, SESSION, "c2s", frame) == (1, payload)
    tampered = dict(frame, c=("A" if frame["c"][0] != "A" else "B") + frame["c"][1:])
    with pytest.raises(InvalidTag):
        decrypt_frame(key, ROOM, SESSION, "c2s", tampered)
    with pytest.raises(InvalidTag):
        decrypt_frame(key, "otra-sala", SESSION, "c2s", frame)
    with pytest.raises(InvalidTag):
        decrypt_frame(key, ROOM, SESSION, "s2c", frame)


@pytest.mark.parametrize(
    "frame",
    [
        {"seq": True, "n": "x", "c": "y"},
        {"seq": 0, "n": "x", "c": "y"},
        {"seq": "1", "n": "x", "c": "y"},
        {"seq": 1, "n": "AAAA", "c": "y"},
        {"seq": 1, "n": "é", "c": "y"},
    ],
)
def test_trama_malformada(frame):
    with pytest.raises(ValueError):
        decrypt_frame(b"\x02" * 32, ROOM, SESSION, "c2s", frame)


def test_pem_sin_salto_final_carga():
    pem = SIGNER.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    assert load_signing_key(pem.strip()).curve.name == "secp256r1"


def test_url_firmada_valida_vencida_y_de_otra_sesion():
    key = b"\x03" * 32
    sig = sign_url(key, "f1", "s1", 1060)
    assert verify_url(key, "f1", "s1", 1060, sig, now=1000)
    assert not verify_url(key, "f1", "s1", 1060, sig, now=1061)
    assert not verify_url(key, "f1", "s2", 1060, sig, now=1000)
    assert not verify_url(key, "f2", "s1", 1060, sig, now=1000)
```

Run: `pytest services/shared/tests/test_crypto.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.crypto'`

- [ ] **Step 3: Implementar `shared/crypto.py`**

`services/shared/shared/crypto.py`:
```python
"""Primitivas criptográficas del protocolo (spec §10–§11). Sin E/S: solo cálculos."""

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

__all__ = ["InvalidTag"]

NONCE_LEN = 12
TAG_LEN = 16
KEY_LEN = 32
PROTOCOL = "secure-chat/v1"
CURVE = ec.SECP256R1()


# --- codificación y aleatorios -------------------------------------------------
def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64d(text: str) -> bytes:
    """Lanza ValueError si el texto no es base64url."""
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def token_hash(token: str) -> bytes:
    """Los tokens tienen ≥ 128 bits de entropía: un hash rápido basta para guardarlos (spec §11.1)."""
    return sha256(token.encode())


def new_key() -> bytes:
    return os.urandom(KEY_LEN)


# --- AES-256-GCM ------------------------------------------------------------------
def seal(key: bytes, plaintext: bytes, aad: bytes, nonce: bytes | None = None) -> bytes:
    """Devuelve nonce ‖ ciphertext ‖ tag. El nonce explícito solo existe para los vectores de prueba."""
    nonce = nonce or os.urandom(NONCE_LEN)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def unseal(key: bytes, blob: bytes, aad: bytes) -> bytes:
    """Lanza InvalidTag si el blob, la clave o el AAD no corresponden."""
    if len(blob) < NONCE_LEN + TAG_LEN:
        raise InvalidTag
    return AESGCM(key).decrypt(blob[:NONCE_LEN], blob[NONCE_LEN:], aad)


def dek_aad(room_id: str) -> bytes:
    return f"dek|{room_id}".encode()


def totp_aad(admin_id: str) -> bytes:
    return f"totp|{admin_id}".encode()


def msg_aad(room_id: str, session_id: str) -> bytes:
    return f"msg|{room_id}|{session_id}".encode()


def frame_aad(room_id: str, session_id: str, seq: int, direction: str) -> bytes:
    return f"v1|{room_id}|{session_id}|{seq}|{direction}".encode()


# --- ECDH / ECDSA P-256 (spec §10.1) --------------------------------------------
def public_bytes(private_key: ec.EllipticCurvePrivateKey) -> bytes:
    return private_key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )


def load_public_key(raw: bytes) -> ec.EllipticCurvePublicKey:
    """Valida longitud, formato sin comprimir y pertenencia a la curva (ValueError si no)."""
    if len(raw) != 65 or raw[0] != 4:
        raise ValueError("clave pública P-256 inválida")
    return ec.EllipticCurvePublicKey.from_encoded_point(CURVE, raw)


def derive_session_key(shared: bytes, salt: bytes, room_id: str, session_id: str) -> bytes:
    info = f"{PROTOCOL}|{room_id}|{session_id}".encode()
    return HKDF(algorithm=hashes.SHA256(), length=KEY_LEN, salt=salt, info=info).derive(shared)


def hello_transcript(
    room_id: str, session_id: str, client_pub: str, server_pub: str, salt: str
) -> bytes:
    return f"{PROTOCOL}/hello|{room_id}|{session_id}|{client_pub}|{server_pub}|{salt}".encode()


def load_signing_key(pem: str) -> ec.EllipticCurvePrivateKey:
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey) or key.curve.name != CURVE.name:
        raise ValueError("chat_sign_key debe ser una clave ECDSA P-256")
    return key


def sign_p1363(private_key: ec.EllipticCurvePrivateKey, data: bytes) -> bytes:
    """Firma ECDSA/SHA-256 en formato IEEE P1363 (r‖s, 64 bytes), el que usa WebCrypto."""
    r, s = decode_dss_signature(private_key.sign(data, ec.ECDSA(hashes.SHA256())))
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def verify_p1363(public_key: ec.EllipticCurvePublicKey, signature: bytes, data: bytes) -> bool:
    if len(signature) != 64:
        return False
    der = encode_dss_signature(
        int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big")
    )
    try:
        public_key.verify(der, data, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False
    return True


@dataclass(frozen=True)
class Handshake:
    reply: dict  # {"t": "hello", "pub", "salt", "sig"}
    key: bytes  # K de esta conexión


def server_hello(
    client_pub_b64: str,
    room_id: str,
    session_id: str,
    sign_key: ec.EllipticCurvePrivateKey,
    server_private: ec.EllipticCurvePrivateKey | None = None,
    salt: bytes | None = None,
) -> Handshake:
    """Lado servidor del handshake. Lanza ValueError si la clave del cliente no es válida.

    server_private y salt solo se pasan para reproducir los vectores de prueba.
    """
    client_pub = b64d(client_pub_b64)
    peer = load_public_key(client_pub)
    server_private = server_private or ec.generate_private_key(CURVE)
    salt = salt or os.urandom(32)
    key = derive_session_key(server_private.exchange(ec.ECDH(), peer), salt, room_id, session_id)
    server_pub, salt_b64 = b64e(public_bytes(server_private)), b64e(salt)
    transcript = hello_transcript(room_id, session_id, b64e(client_pub), server_pub, salt_b64)
    reply = {
        "t": "hello",
        "pub": server_pub,
        "salt": salt_b64,
        "sig": b64e(sign_p1363(sign_key, transcript)),
    }
    return Handshake(reply, key)


# --- tramas (spec §10.2) --------------------------------------------------------
def encode_payload(payload: dict) -> bytes:
    """JSON compacto y sin escapar no-ASCII: idéntico a JSON.stringify del navegador."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()


def encrypt_frame(
    key: bytes,
    room_id: str,
    session_id: str,
    seq: int,
    direction: str,
    payload: dict,
    nonce: bytes | None = None,
) -> dict:
    blob = seal(key, encode_payload(payload), frame_aad(room_id, session_id, seq, direction), nonce)
    return {"seq": seq, "n": b64e(blob[:NONCE_LEN]), "c": b64e(blob[NONCE_LEN:])}


def decrypt_frame(
    key: bytes, room_id: str, session_id: str, direction: str, frame: dict
) -> tuple[int, dict]:
    """Lanza ValueError si la trama está malformada e InvalidTag si fue alterada."""
    seq, nonce_b64, ciphertext_b64 = frame.get("seq"), frame.get("n"), frame.get("c")
    if type(seq) is not int or seq < 1:
        raise ValueError("trama malformada: seq")
    if not isinstance(nonce_b64, str) or not isinstance(ciphertext_b64, str):
        raise ValueError("trama malformada: campos")
    nonce = b64d(nonce_b64)
    if len(nonce) != NONCE_LEN:
        raise ValueError("trama malformada: nonce")
    plaintext = unseal(
        key, nonce + b64d(ciphertext_b64), frame_aad(room_id, session_id, seq, direction)
    )
    payload = json.loads(plaintext)
    if not isinstance(payload, dict):
        raise ValueError("trama malformada: payload")
    return seq, payload


# --- URLs firmadas (spec §9.6) --------------------------------------------------
def sign_url(key: bytes, file_id: str, session_id: str, exp: int) -> str:
    message = f"{file_id}|{session_id}|{exp}".encode()
    return b64e(hmac.new(key, message, hashlib.sha256).digest())


def verify_url(key: bytes, file_id: str, session_id: str, exp: int, sig: str, now: int) -> bool:
    return exp >= now and hmac.compare_digest(sign_url(key, file_id, session_id, exp), sig)
```

Run: `pytest services/shared/tests/test_crypto.py -q`
Expected: PASS (todos)

- [ ] **Step 4: Tests de secretos (fallan)**

`services/shared/tests/test_r02_secretos.py`:
```python
import pytest

from shared.crypto import b64e
from shared.secrets import db_url, env, origins, read_key, read_versioned_keys


@pytest.fixture
def secrets_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))
    return tmp_path


def write(directory, name, value):
    (directory / name).write_text(value, encoding="utf-8")


def test_secreto_ausente_detiene_el_servicio(secrets_dir):
    with pytest.raises(RuntimeError, match="secreto requerido ausente: kek_auth_v1"):
        read_versioned_keys("kek_auth", 1)


def test_clave_debe_tener_32_bytes(secrets_dir):
    write(secrets_dir, "url_signing_key", b64e(b"x" * 16))
    with pytest.raises(RuntimeError, match="32 bytes"):
        read_key("url_signing_key")


def test_lee_claves_versionadas_y_url_de_bd(secrets_dir, monkeypatch):
    write(secrets_dir, "kek_auth_v1", b64e(b"\x01" * 32) + "\n")
    write(secrets_dir, "kek_auth_v2", b64e(b"\x02" * 32))
    write(secrets_dir, "db_rooms_app", "p@ss/word")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5433")
    assert read_versioned_keys("kek_auth", 2) == {1: b"\x01" * 32, 2: b"\x02" * 32}
    assert db_url("rooms", "app") == (
        "postgresql+asyncpg://rooms_app:p%40ss%2Fword@localhost:5433/rooms"
    )


def test_env_convierte_tipos(monkeypatch):
    monkeypatch.setenv("WS_BURST", "3")
    monkeypatch.setenv("WS_RATE_PER_S", "0.5")
    monkeypatch.setenv("STEGO_ENTROPY_TRIGGER", "off")
    assert env("WS_BURST", 10) == 3
    assert env("WS_RATE_PER_S", 5.0) == 0.5
    assert env("STEGO_ENTROPY_TRIGGER", None) is None
    assert env("NO_EXISTE", 7) == 7


def test_origins_separa_por_comas(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a, https://b,")
    assert origins() == frozenset({"https://a", "https://b"})
```

Run: `pytest services/shared/tests/test_r02_secretos.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.secrets'`

- [ ] **Step 5: Implementar `shared/secrets.py`**

`services/shared/shared/secrets.py`:
```python
"""Lectura de Docker secrets (/run/secrets) y de perillas no secretas (spec §11, §19).

Si falta un secreto, el servicio no arranca: fallar cerrado.
"""

import os
from pathlib import Path
from urllib.parse import quote

from shared.crypto import b64d


def secrets_dir() -> Path:
    return Path(os.environ.get("SECRETS_DIR", "/run/secrets"))


def read_secret(name: str) -> str:
    try:
        value = (secrets_dir() / name).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise RuntimeError(f"secreto requerido ausente: {name}") from None
    if not value:
        raise RuntimeError(f"secreto vacío: {name}")
    return value


def read_key(name: str) -> bytes:
    key = b64d(read_secret(name))
    if len(key) != 32:
        raise RuntimeError(f"{name} debe contener 32 bytes en base64url")
    return key


def read_versioned_keys(prefix: str, current: int) -> dict[int, bytes]:
    """Lee <prefix>_v1, <prefix>_v2, ... y exige que exista la versión vigente."""
    keys = {
        int(path.name.rsplit("_v", 1)[1]): read_key(path.name)
        for path in secrets_dir().glob(f"{prefix}_v*")
    }
    if current not in keys:
        raise RuntimeError(f"secreto requerido ausente: {prefix}_v{current}")
    return keys


def env(name: str, default):
    """Perilla no secreta del entorno, convertida al tipo del valor por defecto.

    Un default None indica una perilla float opcional que se desactiva con "" u "off".
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    if default is None:
        return None if raw in ("", "off") else float(raw)
    return type(default)(raw)


def origins() -> frozenset[str]:
    raw = env("ALLOWED_ORIGINS", "https://localhost")
    return frozenset(origin.strip() for origin in raw.split(",") if origin.strip())


def db_url(service: str, role: str) -> str:
    """URL asyncpg del rol <service>_<role>; su contraseña sale del secreto db_<service>_<role>."""
    password = quote(read_secret(f"db_{service}_{role}"), safe="")
    host, port = env("DB_HOST", "db"), env("DB_PORT", 5432)
    return f"postgresql+asyncpg://{service}_{role}:{password}@{host}:{port}/{service}"
```

Run: `pytest services/shared/tests/test_r02_secretos.py -q`
Expected: PASS

- [ ] **Step 6: Generador de vectores**

`services/shared/tools/gen_crypto_vectors.py`:
```python
"""Genera docs/crypto-vectors.json para verificar que Python y TypeScript interoperan (spec §10.4).

Las claves son FIJAS y solo sirven para pruebas: nunca se usan en ningún despliegue.
Uso: python services/shared/tools/gen_crypto_vectors.py
"""

import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec

from shared.crypto import (
    CURVE,
    b64e,
    encrypt_frame,
    hello_transcript,
    public_bytes,
    server_hello,
    sign_p1363,
)

OUT = Path(__file__).resolve().parents[3] / "docs" / "crypto-vectors.json"
ROOM_ID = "00000000-0000-4000-8000-000000000001"
SESSION_ID = "00000000-0000-4000-8000-000000000002"


def jwk(key: ec.EllipticCurvePrivateKey) -> dict:
    numbers = key.private_numbers()

    def encode(value: int) -> str:
        return b64e(value.to_bytes(32, "big"))

    return {
        "kty": "EC",
        "crv": "P-256",
        "d": encode(numbers.private_value),
        "x": encode(numbers.public_numbers.x),
        "y": encode(numbers.public_numbers.y),
    }


def main() -> None:
    client = ec.derive_private_key(int("11" * 32, 16), CURVE)
    server = ec.derive_private_key(int("22" * 32, 16), CURVE)
    signer = ec.derive_private_key(int("33" * 32, 16), CURVE)
    client_pub = b64e(public_bytes(client))
    hs = server_hello(
        client_pub, ROOM_ID, SESSION_ID, signer, server_private=server, salt=bytes(range(32))
    )
    samples = [
        ("c2s", {"t": "msg", "body": "hola"}),
        (
            "s2c",
            {
                "t": "msg",
                "id": 1,
                "from": "ana",
                "body": "¿qué tal? ñandú 🎉",
                "ts": "2026-10-13T00:00:00+00:00",
            },
        ),
        ("c2s", {"t": "file_url", "file_id": "00000000-0000-4000-8000-000000000003"}),
    ]
    frames = []
    for seq, (direction, payload) in enumerate(samples, start=1):
        nonce = bytes([seq]) * 12
        frames.append(
            {
                "dir": direction,
                "seq": seq,
                "nonce": b64e(nonce),
                "plaintext": payload,
                "frame": encrypt_frame(hs.key, ROOM_ID, SESSION_ID, seq, direction, payload, nonce),
            }
        )
    transcript = hello_transcript(
        ROOM_ID, SESSION_ID, client_pub, hs.reply["pub"], hs.reply["salt"]
    )
    data = {
        "_aviso": "Claves fijas SOLO para pruebas de interoperabilidad; nunca usarlas en un despliegue.",
        "room_id": ROOM_ID,
        "session_id": SESSION_ID,
        "client_private_jwk": jwk(client),
        "client_public": client_pub,
        "server_private_jwk": jwk(server),
        "server_public": hs.reply["pub"],
        "salt": hs.reply["salt"],
        "frames": frames,
        "hello": {
            "sign_public": b64e(public_bytes(signer)),
            "transcript": transcript.decode(),
            "signature": b64e(sign_p1363(signer, transcript)),
        },
    }
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"escrito {OUT}")


if __name__ == "__main__":
    main()
```

Run: `python services/shared/tools/gen_crypto_vectors.py`
Expected: `escrito ...docs/crypto-vectors.json`

- [ ] **Step 7: Test de vectores**

`services/shared/tests/test_vectors.py`:
```python
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec

from shared.crypto import (
    CURVE,
    b64d,
    decrypt_frame,
    encrypt_frame,
    hello_transcript,
    load_public_key,
    server_hello,
    verify_p1363,
)

VECTORS = json.loads(
    (Path(__file__).resolve().parents[3] / "docs" / "crypto-vectors.json").read_text(
        encoding="utf-8"
    )
)


def private(jwk: dict) -> ec.EllipticCurvePrivateKey:
    return ec.derive_private_key(int.from_bytes(b64d(jwk["d"]), "big"), CURVE)


def test_vectores_reproducen_handshake_y_tramas():
    v = VECTORS
    hs = server_hello(
        v["client_public"],
        v["room_id"],
        v["session_id"],
        ec.generate_private_key(CURVE),  # la firma no forma parte de la clave
        server_private=private(v["server_private_jwk"]),
        salt=b64d(v["salt"]),
    )
    assert (hs.reply["pub"], hs.reply["salt"]) == (v["server_public"], v["salt"])
    for f in v["frames"]:
        frame = encrypt_frame(
            hs.key, v["room_id"], v["session_id"], f["seq"], f["dir"], f["plaintext"], b64d(f["nonce"])
        )
        assert frame == f["frame"]
        assert decrypt_frame(hs.key, v["room_id"], v["session_id"], f["dir"], f["frame"]) == (
            f["seq"],
            f["plaintext"],
        )


def test_vector_de_firma_del_hello():
    v, h = VECTORS, VECTORS["hello"]
    transcript = hello_transcript(
        v["room_id"], v["session_id"], v["client_public"], v["server_public"], v["salt"]
    )
    assert transcript.decode() == h["transcript"]
    assert verify_p1363(load_public_key(b64d(h["sign_public"])), b64d(h["signature"]), transcript)
```

Run: `pytest services/shared -q`
Expected: PASS (crypto, secretos, vectores)

- [ ] **Step 8: Commit**

```bash
git add services/shared docs/crypto-vectors.json
git commit -m "feat(shared): criptografía del protocolo, lectura de secretos y vectores Python↔TS"
```

---

### Task FND-3: Contraseñas Argon2id y límites de intentos

**Files:**
- Create: `services/shared/shared/passwords.py`, `services/shared/shared/ratelimit.py`
- Test: `services/shared/tests/test_passwords.py`, `services/shared/tests/test_token_bucket.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `shared.passwords`: `hash_secret(str)->str`, `verify_secret(str|None, str)->bool`, `hash_secret_async`, `verify_secret_async`, `strong_enough(secret, *, forbid="")->bool`.
  - `shared.ratelimit`: `failures(conn, key, window_min)->int`, `any_over(conn, limits: list[tuple[str, int]], window_min)->bool`, `record(conn, keys, window_min)->int` y `TokenBucket(rate, burst, clock=time.monotonic)` con `.allow()->bool`. Las funciones con `conn` operan sobre la tabla `failed_attempts(key, created_at)` que tienen las BD de auth y rooms; se prueban contra BD en ATH-2 y ROOM-3.

- [ ] **Step 1: Tests (fallan)**

`services/shared/tests/test_passwords.py`:
```python
import pytest

from shared.passwords import hash_secret, strong_enough, verify_secret


def test_hash_es_argon2id_con_parametros_rfc9106():
    stored = hash_secret("Clave-Segura-2026")
    assert stored.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert verify_secret(stored, "Clave-Segura-2026")
    assert not verify_secret(stored, "otra-clave")


def test_sin_hash_verifica_contra_dummy_y_siempre_falla():
    assert verify_secret(None, "dummy-password-timing-only") is False
    assert verify_secret(None, "cualquier-cosa") is False


def test_hash_malformado_no_explota():
    assert verify_secret("no-es-un-hash", "x") is False


@pytest.mark.parametrize(
    ("secret", "forbid", "ok"),
    [
        ("Clave-Segura-2026", "", True),
        ("clavesegura2026", "", False),  # 2 clases
        ("Corta-1", "", False),  # < 12
        ("Sala-Uno-2026", "sala-uno-2026", False),  # igual al código
        ("ÑANDÚ-feliz-99", "", True),
    ],
)
def test_politica_de_claves(secret, forbid, ok):
    assert strong_enough(secret, forbid=forbid) is ok
```

`services/shared/tests/test_token_bucket.py`:
```python
from shared.ratelimit import TokenBucket


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_rafaga_y_recarga():
    clock = FakeClock()
    bucket = TokenBucket(rate=5, burst=10, clock=clock)
    assert all(bucket.allow() for _ in range(10))
    assert not bucket.allow()
    clock.now += 0.2  # 0.2 s × 5/s = 1 token
    assert bucket.allow()
    assert not bucket.allow()


def test_no_acumula_mas_que_la_rafaga():
    clock = FakeClock()
    bucket = TokenBucket(rate=5, burst=3, clock=clock)
    clock.now += 100
    assert [bucket.allow() for _ in range(4)] == [True, True, True, False]
```

Run: `pytest services/shared/tests/test_passwords.py services/shared/tests/test_token_bucket.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 2: Implementar `shared/passwords.py`**

```python
"""Argon2id para contraseñas de admin y claves de sala (riesgos 1 y 4, spec §11.1).

Perfil RFC 9106 de baja memoria (t=3, m=64 MiB, p=4), el predeterminado de argon2-cffi.
"""

import threading

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from starlette.concurrency import run_in_threadpool

_hasher = PasswordHasher()
# ponytail: tope global de 4 cálculos simultáneos (4 × 64 MiB) para que un ataque de ingresos
# masivos no agote la RAM; súbelo si el host tiene memoria de sobra.
_SLOTS = threading.BoundedSemaphore(4)
_DUMMY_HASH = _hasher.hash("dummy-password-timing-only")


def hash_secret(secret: str) -> str:
    with _SLOTS:
        return _hasher.hash(secret)


def verify_secret(stored_hash: str | None, secret: str) -> bool:
    """Sin hash (usuario o sala inexistente) verifica contra un dummy: mismo tiempo, siempre False."""
    with _SLOTS:
        try:
            matched = _hasher.verify(stored_hash or _DUMMY_HASH, secret)
        except (VerificationError, InvalidHashError):
            return False
    return matched and stored_hash is not None


async def hash_secret_async(secret: str) -> str:
    return await run_in_threadpool(hash_secret, secret)


async def verify_secret_async(stored_hash: str | None, secret: str) -> bool:
    return await run_in_threadpool(verify_secret, stored_hash, secret)


def strong_enough(secret: str, *, forbid: str = "") -> bool:
    """≥ 12 caracteres, ≥ 3 de 4 clases (minúsculas, mayúsculas, dígitos, símbolos) y distinta de `forbid`."""
    classes = sum(
        (
            any(c.islower() for c in secret),
            any(c.isupper() for c in secret),
            any(c.isdigit() for c in secret),
            any(not c.isalnum() for c in secret),
        )
    )
    return len(secret) >= 12 and classes >= 3 and secret.casefold() != forbid.casefold()
```

- [ ] **Step 3: Implementar `shared/ratelimit.py`**

```python
"""Límites de intentos fallidos (spec §9.1–§9.2) y token bucket del WebSocket (spec §9.4)."""

import time
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def failures(conn: AsyncConnection, key: str, window_min: int) -> int:
    result = await conn.execute(
        text(
            "SELECT count(*) FROM failed_attempts "
            "WHERE key = :key AND created_at > now() - make_interval(mins => :window)"
        ),
        {"key": key, "window": window_min},
    )
    return result.scalar_one()


async def any_over(conn: AsyncConnection, limits: list[tuple[str, int]], window_min: int) -> bool:
    """True si alguna clave alcanzó su máximo de fallos dentro de la ventana."""
    for key, limit in limits:
        if await failures(conn, key, window_min) >= limit:
            return True
    return False


async def record(conn: AsyncConnection, keys: list[str], window_min: int) -> int:
    """Registra un fallo por clave y devuelve el mayor conteo resultante (para el retraso progresivo)."""
    for key in keys:
        await conn.execute(text("INSERT INTO failed_attempts (key) VALUES (:key)"), {"key": key})
    return max([await failures(conn, key, window_min) for key in keys], default=0)


class TokenBucket:
    """Token bucket en memoria; una instancia por conexión WebSocket."""

    def __init__(self, rate: float, burst: int, clock: Callable[[], float] = time.monotonic):
        self.rate, self.burst, self.clock = rate, burst, clock
        self.tokens, self.updated = float(burst), clock()

    def allow(self) -> bool:
        now = self.clock()
        self.tokens = min(self.burst, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

Run: `pytest services/shared -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add services/shared
git commit -m "feat(shared): Argon2id con tope de concurrencia, política de claves y límites de intentos"
```

---

### Task FND-4: Autenticación entre servicios, identidad, auditoría y base web (R16)

**Files:**
- Create: `services/shared/shared/service_auth.py`, `services/shared/shared/identity.py`, `services/shared/shared/audit_client.py`, `services/shared/shared/web.py`
- Create: `services/shared/shared/observability.py` (Step 6: correlación y registros JSON)
- Create: `services/shared/shared/testing.py` (cabeceras, `ServiceAuth` de prueba y `Recorder`; FND-5 agrega lo de BD)
- Modify: `services/Dockerfile` (lo crea FND-6; allí ya trae `LOG_FORMAT=json` y `--no-access-log`)
- Test: `services/shared/tests/test_r16_service_auth.py`, `services/shared/tests/test_observabilidad.py`

**Interfaces:**
- Consumes: `shared.crypto.sha256`, `shared.crypto.b64e` (FND-2).
- Produces:
  - `shared.service_auth`: `TOKEN_HEADER = "X-Service-Token"`; `ServiceAuth(name, token, callers)` con `from_secrets(name, *, needs_token)` e `identify(token)->str|None`; `ServiceTokenMiddleware`; `allow(*callers)` (dependencia que devuelve el llamador); `ServiceClient(auth, urls, transport=None)` con `post(service, path, *, json=None, content=None, headers=None, timeout=3.0)->httpx.Response` (`json` para JSON, `content` para bytes, como las imágenes que `media` manda a `stego`).
  - `shared.identity`: `UserIdentity(user_id, username, session_id, perms: frozenset[str])`, `client_ip(conn)`, `user_from_headers(conn)->UserIdentity|None`, `require_gateway`, `require_user`, `require_perm(*perms)` (403 `"permiso insuficiente"` y evento `perm.denied` si falta alguno).
  - `shared.audit_client`: `AuditUnavailable`, `AuditClient(ServiceClient).emit(severity, action, *, actor, target=None, ip=None, details=None, required=False)`.
  - `shared.web`: `SESSION_COOKIE`, `DEVICE_COOKIE`, `set_cookie(response, name, value, max_age=None)`, `clear_cookie(response, name)`, `create_base_app(*, title, settings, engine, service_auth, audit, lifespan=None)->FastAPI` (con `engine=None`, `/health` responde sin BD: lo usa `stego`). La app expone `app.state.settings/engine/service_auth/audit` y `request.state.caller`. Instala `RequestContextMiddleware` como el más externo y llama a `configure_logging(title)`.
  - `shared.observability` (RNF-18, RNF-19): `REQUEST_HEADER = "X-Request-ID"`, `REQUEST_ID: ContextVar[str | None]`, `JsonFormatter(service)`, `configure_logging(service)` (solo con `LOG_FORMAT=json`) y `RequestContextMiddleware`. El middleware toma el id que puso el gateway (si cumple `^[A-Za-z0-9-]{8,64}$`; si no, crea uno de 32 hex), lo deja en `REQUEST_ID` y registra **una línea por petición** con `method`, `path` (sin query string), `status` y `ms`. `ServiceClient.post` reenvía el id y `AuditClient.emit` lo manda como `request_id` (audit lo guarda en la cadena, AUD-2). Los servicios no devuelven el id al cliente: lo hace el gateway (GW-1).
  - `shared.testing`:
    - constantes `ORIGIN`, `TOKENS` (gateway, auth, rooms, chat, media, stego), `ROLE_PASSWORD`, `USER_ID`, `SESSION_ID`;
    - `service_auth(name, callers)`;
    - cabeceras: `service_headers(name)`, `gateway_headers()`, `user_headers(user_id=USER_ID, username="ana", session_id=SESSION_ID, perms=())`, `cookie_header(cookies)->dict`;
    - `Recorder(routes=None)` con `.transport`, `.calls`, `.events(action=None)` y `.to(prefix)`; un cuerpo que no es JSON (una imagen) queda en `Call.body` como `bytes`.

- [ ] **Step 1: Utilidades de prueba (parte 1)**

`services/shared/shared/testing.py`:
```python
"""Utilidades de prueba compartidas por los servicios y el e2e. No se usan en producción.

Todas las contraseñas y tokens de este módulo son FIJOS y existen solo para pruebas.
"""

import json
from dataclasses import dataclass
from typing import Any

import httpx

from shared.crypto import sha256
from shared.service_auth import TOKEN_HEADER, ServiceAuth

ORIGIN = "https://testserver"
ROLE_PASSWORD = "solo-pruebas"
TOKENS = {
    name: f"token-de-prueba-{name}" for name in ("gateway", "auth", "rooms", "chat", "media", "stego")
}
USER_ID = "00000000-0000-4000-8000-0000000000a1"
SESSION_ID = "00000000-0000-4000-8000-000000000051"


def service_auth(name: str, callers: tuple[str, ...]) -> ServiceAuth:
    """ServiceAuth de prueba: token propio de TOKENS y hashes de los llamadores permitidos."""
    return ServiceAuth(
        name, TOKENS.get(name), {caller: sha256(TOKENS[caller].encode()) for caller in callers}
    )


def service_headers(name: str) -> dict:
    return {TOKEN_HEADER: TOKENS[name]}


def gateway_headers() -> dict:
    return {TOKEN_HEADER: TOKENS["gateway"], "origin": ORIGIN}


def user_headers(
    user_id: str = USER_ID,
    username: str = "ana",
    session_id: str = SESSION_ID,
    perms: tuple[str, ...] = (),
) -> dict:
    """La identidad que pone el gateway después de verificar el JWT con auth (spec §4.3)."""
    headers = {
        **gateway_headers(),
        "X-User-Id": user_id,
        "X-User-Name": username,
        "X-Session-Id": session_id,
    }
    if perms:  # Nginx no envía una cabecera vacía: sin permisos, X-User-Perms no viene
        headers["X-User-Perms"] = ",".join(perms)
    return headers


def cookie_header(cookies: dict) -> dict:
    return {"cookie": "; ".join(f"{name}={value}" for name, value in cookies.items())}


@dataclass
class Call:
    host: str
    path: str
    body: Any
    token: str | None


class Recorder:
    """Transporte httpx falso para ServiceClient: registra cada llamada y responde según `routes`.

    routes: {"/ruta" o "/prefijo*": status | "down" | callable(request) -> httpx.Response}.
    Por defecto: /internal/events → 201; cualquier otra → 204.
    """

    def __init__(self, routes: dict | None = None):
        self.routes = dict(routes or {})
        self.calls: list[Call] = []

    def _route(self, path: str):
        for key, value in self.routes.items():
            if path == key or (key.endswith("*") and path.startswith(key[:-1])):
                return value
        return None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        try:
            body = json.loads(request.content) if request.content else None
        except (ValueError, UnicodeDecodeError):
            body = request.content  # binario: por ejemplo, una imagen hacia stego
        self.calls.append(Call(request.url.host, request.url.path, body, request.headers.get(TOKEN_HEADER)))
        route = self._route(request.url.path)
        if route == "down":
            raise httpx.ConnectError("servicio caído (simulado)", request=request)
        if callable(route):
            return route(request)
        if isinstance(route, int):
            return httpx.Response(route)
        return httpx.Response(201 if request.url.path == "/internal/events" else 204)

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def events(self, action: str | None = None) -> list[dict]:
        return [
            c.body
            for c in self.calls
            if c.path == "/internal/events" and (action is None or c.body["action"] == action)
        ]

    def to(self, prefix: str) -> list[Call]:
        return [c for c in self.calls if c.path.startswith(prefix)]
```

- [ ] **Step 2: Tests de R16 (fallan)**

`services/shared/tests/test_r16_service_auth.py`:
```python
import logging
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends, Request, WebSocket
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.websockets import WebSocketDisconnect

from shared import testing
from shared.audit_client import AuditClient
from shared.identity import UserIdentity, require_gateway, require_perm, require_user
from shared.service_auth import ServiceClient, allow
from shared.web import create_base_app


class Body(BaseModel):
    n: int


def build_app(recorder: testing.Recorder):
    auth = testing.service_auth("rooms", ("gateway", "chat"))
    peers = ServiceClient(auth, {"audit": "http://audit:8000"}, recorder.transport)
    app = create_base_app(
        title="prueba",
        settings=SimpleNamespace(allowed_origins=frozenset({testing.ORIGIN})),
        engine=create_async_engine("postgresql+asyncpg://nadie@127.0.0.1:1/nada"),  # no se usa
        service_auth=auth,
        audit=AuditClient(peers),
    )
    router = APIRouter()

    @router.post("/api/publico", dependencies=[Depends(require_gateway)])
    async def publico(body: Body) -> dict:
        return {"n": body.n}

    @router.get("/api/admin/x")
    async def admin(who: UserIdentity = Depends(require_perm("audit:read"))) -> dict:
        return {"user": who.username}

    @router.get("/api/yo")
    async def yo(who: UserIdentity = Depends(require_user)) -> dict:
        return {
            "user_id": who.user_id,
            "username": who.username,
            "session_id": who.session_id,
            "perms": sorted(who.perms),
        }

    @router.post("/internal/solo-chat", dependencies=[Depends(allow("chat"))])
    async def interno() -> dict:
        return {"ok": True}

    @router.get("/api/falla", dependencies=[Depends(require_gateway)])
    async def falla() -> dict:
        raise RuntimeError("boom")

    @router.get("/api/obligatorio", dependencies=[Depends(require_gateway)])
    async def obligatorio(request: Request) -> dict:
        await request.app.state.audit.emit("info", "prueba.ok", actor="system", required=True)
        return {"ok": True}

    @router.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.close()

    app.include_router(router)
    return app


@pytest.fixture
def recorder():
    return testing.Recorder()


@pytest.fixture
def client(recorder):
    return TestClient(build_app(recorder), base_url=testing.ORIGIN, raise_server_exceptions=False)


def test_sin_token_401_y_se_audita(client, recorder):
    r = client.post("/api/publico", json={"n": 1})
    assert r.status_code == 401
    assert r.json() == {"error": "no autorizado"}
    [event] = recorder.events("svc.reject.token")
    assert event["target"] == "/api/publico"
    assert recorder.calls[0].token == testing.TOKENS["rooms"]  # rooms se identifica ante audit


def test_token_desconocido_401(client):
    assert client.get("/api/admin/x", headers={"X-Service-Token": "inventado"}).status_code == 401


def test_ruta_publica_solo_desde_el_gateway(client, recorder):
    r = client.post("/api/publico", json={"n": 1}, headers=testing.service_headers("chat"))
    assert r.status_code == 403
    assert recorder.events("svc.reject.token")[0]["actor"] == "svc:chat"


def test_csrf_exige_origin_permitido(client, recorder):
    sin_origin = {"X-Service-Token": testing.TOKENS["gateway"]}
    assert client.post("/api/publico", json={"n": 1}, headers=sin_origin).status_code == 403
    assert recorder.events("http.reject.origin")
    ajeno = {**sin_origin, "origin": "https://evil.example"}
    assert client.post("/api/publico", json={"n": 1}, headers=ajeno).status_code == 403
    r = client.post("/api/publico", json={"n": 2}, headers=testing.gateway_headers())
    assert r.json() == {"n": 2}


def test_ruta_interna_respeta_la_allowlist(client):
    assert client.post("/internal/solo-chat", headers=testing.gateway_headers()).status_code == 403
    assert client.post("/internal/solo-chat", headers=testing.service_headers("chat")).status_code == 200


def test_identidad_solo_vale_si_la_trae_el_gateway(client):
    assert client.get("/api/admin/x", headers=testing.gateway_headers()).status_code == 401
    ok = client.get("/api/admin/x", headers=testing.user_headers(perms=("audit:read",)))
    assert ok.json() == {"user": "ana"}
    impostor = {
        **testing.service_headers("chat"),
        "X-User-Id": "x",
        "X-User-Name": "ana",
        "X-Session-Id": "s",
        "X-User-Perms": "audit:read",
    }
    assert client.get("/api/admin/x", headers=impostor).status_code == 403


def test_r05_sin_el_permiso_403_y_se_audita(client, recorder):
    r = client.get("/api/admin/x", headers=testing.user_headers(perms=("stego:analyze",)))
    assert (r.status_code, r.json()) == (403, {"error": "permiso insuficiente"})
    [event] = recorder.events("perm.denied")
    assert event["actor"] == "user:ana"
    assert event["details"] == {"required": ["audit:read"]}


def test_permisos_se_leen_de_la_cabecera(client):
    headers = testing.user_headers(perms=("stego:analyze", "rooms:create"))
    assert client.get("/api/yo", headers=headers).json() == {
        "user_id": testing.USER_ID,
        "username": "ana",
        "session_id": testing.SESSION_ID,
        "perms": ["rooms:create", "stego:analyze"],
    }
    assert client.get("/api/yo", headers=testing.user_headers()).json()["perms"] == []


def test_errores_genericos(client):
    assert client.get("/api/falla", headers=testing.gateway_headers()).json() == {"error": "error interno"}
    r = client.post("/api/publico", json={"n": "x"}, headers=testing.gateway_headers())
    assert (r.status_code, r.json()) == (422, {"error": "datos inválidos"})


def test_evento_obligatorio_sin_audit_da_503():
    client = TestClient(build_app(testing.Recorder({"/internal/events": "down"})), base_url=testing.ORIGIN)
    r = client.get("/api/obligatorio", headers=testing.gateway_headers())
    assert (r.status_code, r.json()) == (503, {"error": "servicio no disponible"})


def test_evento_no_obligatorio_cae_a_stdout(caplog):
    client = TestClient(build_app(testing.Recorder({"/internal/events": "down"})), base_url=testing.ORIGIN)
    with caplog.at_level(logging.WARNING, logger="audit"):
        assert client.get("/api/admin/x").status_code == 401  # sin token → evento de rechazo
    assert "AUDIT_FALLBACK" in caplog.text


def test_websocket_sin_token_se_cierra_con_4401(client):
    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect("/ws"):
            pass
    assert closed.value.code == 4401
```

Run: `pytest services/shared/tests/test_r16_service_auth.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.identity'`

- [ ] **Step 3: Implementar `shared/identity.py`**

```python
"""Identidad propagada por el gateway (spec §4.3). Solo se lee si el llamador verificado es 'gateway'."""

from dataclasses import dataclass

from fastapi import HTTPException, Request
from starlette.requests import HTTPConnection

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass(frozen=True)
class UserIdentity:
    user_id: str
    username: str
    session_id: str  # sesión de la cuenta (claim sid del JWT)
    perms: frozenset[str]  # los actuales: auth los lee de la BD en cada request


def client_ip(conn: HTTPConnection) -> str | None:
    """IP del cliente original: uvicorn la toma de X-Forwarded-For, que el gateway sobrescribe."""
    return conn.client.host if conn.client else None


async def require_gateway(request: Request) -> None:
    """Rutas públicas: solo el gateway puede llamarlas, y las que cambian estado exigen Origin permitido (CSRF)."""
    audit, ip = request.app.state.audit, client_ip(request)
    if request.state.caller != "gateway":
        await audit.emit(
            "warning", "svc.reject.token", actor=f"svc:{request.state.caller}", target=request.url.path, ip=ip
        )
        raise HTTPException(403, "no autorizado")
    origin = request.headers.get("origin")
    if request.method in UNSAFE_METHODS and origin not in request.app.state.settings.allowed_origins:
        await audit.emit(
            "warning", "http.reject.origin", actor=f"ip:{ip}", target=request.url.path, ip=ip,
            details={"origin": origin},
        )
        raise HTTPException(403, "origen no permitido")


def user_from_headers(conn: HTTPConnection) -> UserIdentity | None:
    """Identidad que puso el gateway. Sin permisos, X-User-Perms no viene (Nginx omite cabeceras vacías).

    Quien la use fuera de require_user (el WebSocket de chat) debe comprobar antes que el llamador es 'gateway'.
    """
    headers = conn.headers
    values = (headers.get("x-user-id"), headers.get("x-user-name"), headers.get("x-session-id"))
    if not all(values):
        return None
    perms = frozenset(perm for perm in headers.get("x-user-perms", "").split(",") if perm)
    return UserIdentity(*values, perms)


async def require_user(request: Request) -> UserIdentity:
    await require_gateway(request)
    who = user_from_headers(request)
    if who is None:
        raise HTTPException(401, "no autenticado")
    return who


def require_perm(*perms: str):
    """Dependencia de ruta: el usuario debe tener **todos** los permisos pedidos (spec §9.1)."""

    async def dependency(request: Request) -> UserIdentity:
        who = await require_user(request)
        if not set(perms) <= who.perms:
            ip = client_ip(request)
            await request.app.state.audit.emit(
                "warning", "perm.denied", actor=f"user:{who.username}", target=request.url.path, ip=ip,
                details={"required": list(perms)},
            )
            raise HTTPException(403, "permiso insuficiente")
        return who

    return dependency
```

- [ ] **Step 4: Implementar `shared/service_auth.py`**

```python
"""Autenticación servicio a servicio (R16, spec §4.3): X-Service-Token + allowlist por ruta."""

import hmac
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, Request
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocket

from shared.crypto import sha256
from shared.identity import client_ip
from shared.secrets import read_secret, secrets_dir

TOKEN_HEADER = "X-Service-Token"  # noqa: S105 — es el nombre de la cabecera, no un secreto


@dataclass(frozen=True)
class ServiceAuth:
    name: str  # servicio dueño
    token: str | None  # token propio, para llamar a otros (audit no llama a nadie)
    callers: dict[str, bytes]  # nombre → SHA-256 del token de cada llamador permitido

    @classmethod
    def from_secrets(cls, name: str, *, needs_token: bool) -> "ServiceAuth":
        callers = {
            path.name.removeprefix("svc_hash_"): bytes.fromhex(path.read_text(encoding="utf-8").strip())
            for path in secrets_dir().glob("svc_hash_*")
        }
        if not callers:
            raise RuntimeError("secreto requerido ausente: svc_hash_* (llamadores permitidos)")
        return cls(name, read_secret(f"svc_token_{name}") if needs_token else None, callers)

    def identify(self, presented: str | None) -> str | None:
        """Nombre del llamador cuyo hash coincide (comparación en tiempo constante) o None."""
        if not presented:
            return None
        digest = sha256(presented.encode())
        found = None
        for name, expected in self.callers.items():
            if hmac.compare_digest(digest, expected):
                found = name
        return found


class ServiceTokenMiddleware:
    """Exige X-Service-Token válido en toda petición HTTP y WebSocket salvo /health."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket") or scope["path"] == "/health":
            await self.app(scope, receive, send)
            return
        service_app = scope["app"]
        caller = service_app.state.service_auth.identify(Headers(scope=scope).get(TOKEN_HEADER))
        if caller is None:
            client = scope.get("client")
            await service_app.state.audit.emit(
                "warning", "svc.reject.token", actor="svc:desconocido", target=scope["path"],
                ip=client[0] if client else None,
            )
            if scope["type"] == "websocket":
                await WebSocket(scope, receive, send).close(4401)
            else:
                await JSONResponse({"error": "no autorizado"}, status_code=401)(scope, receive, send)
            return
        scope.setdefault("state", {})["caller"] = caller
        await self.app(scope, receive, send)


def allow(*callers: str):
    """Dependencia de ruta interna: el llamador verificado debe estar en la allowlist."""

    async def dependency(request: Request) -> str:
        caller = request.state.caller
        if caller not in callers:
            await request.app.state.audit.emit(
                "warning", "svc.reject.token", actor=f"svc:{caller}", target=request.url.path,
                ip=client_ip(request),
            )
            raise HTTPException(403, "no autorizado")
        return caller

    return dependency


class ServiceClient:
    """Cliente HTTP interno: agrega el token propio y resuelve el destino por nombre de servicio."""

    def __init__(
        self,
        auth: ServiceAuth,
        urls: dict[str, str],
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.auth, self.urls, self.transport = auth, urls, transport

    async def post(
        self,
        service: str,
        path: str,
        *,
        json: dict | None = None,
        content: bytes | None = None,
        headers: dict | None = None,
        timeout: float = 3.0,
    ) -> httpx.Response:
        """`json` para cuerpos JSON; `content` para bytes (las imágenes que media manda a stego)."""
        # ponytail: un AsyncClient por llamada (sin pool compartido); basta en una red interna a esta escala.
        async with httpx.AsyncClient(transport=self.transport, timeout=timeout) as client:
            return await client.post(
                self.urls[service] + path,
                json=json,
                content=content,
                headers={**(headers or {}), TOKEN_HEADER: self.auth.token or ""},
            )
```

- [ ] **Step 5: Implementar `shared/audit_client.py` y `shared/web.py`**

`services/shared/shared/audit_client.py`:
```python
"""Emisión de eventos al servicio audit con fallback a stdout (spec §14.4)."""

import json
import logging

import httpx

from shared.service_auth import ServiceClient

log = logging.getLogger("audit")


class AuditUnavailable(Exception):
    """audit no respondió a un evento obligatorio: la operación debe revertirse (→ 503)."""


class AuditClient:
    def __init__(self, client: ServiceClient) -> None:
        self.client = client

    async def emit(
        self,
        severity: str,
        action: str,
        *,
        actor: str,
        target: str | None = None,
        ip: str | None = None,
        details: dict | None = None,
        required: bool = False,
    ) -> None:
        event = {
            "severity": severity,
            "action": action,
            "actor": actor,
            "target": target,
            "ip": ip,
            "details": details or {},
        }
        for _ in range(2):  # dos intentos de 2 s
            try:
                response = await self.client.post("audit", "/internal/events", json=event, timeout=2.0)
            except httpx.HTTPError:
                continue
            if response.status_code == 201:
                return
        if required:
            raise AuditUnavailable(action)
        log.warning("AUDIT_FALLBACK %s", json.dumps(event, ensure_ascii=False, default=str))
```

`services/shared/shared/web.py`:
```python
"""Base común de los servicios (spec §4.3, §15): token de servicio, errores JSON genéricos y /health."""

import logging

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.audit_client import AuditUnavailable
from shared.service_auth import ServiceTokenMiddleware

log = logging.getLogger("web")

SESSION_COOKIE = "__Host-session"  # el JWT (spec §8.1)
DEVICE_COOKIE = "__Host-device"


def set_cookie(response: Response, name: str, value: str, max_age: int | None = None) -> None:
    response.set_cookie(
        name, value, max_age=max_age, path="/", secure=True, httponly=True, samesite="strict"
    )


def clear_cookie(response: Response, name: str) -> None:
    response.delete_cookie(name, path="/", secure=True, httponly=True, samesite="strict")


def create_base_app(*, title: str, settings, engine, service_auth, audit, lifespan=None) -> FastAPI:
    app = FastAPI(title=title, docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.service_auth = service_auth
    app.state.audit = audit
    app.add_middleware(ServiceTokenMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "error"
        return JSONResponse({"error": detail}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"error": "datos inválidos"}, status_code=422)

    @app.exception_handler(AuditUnavailable)
    async def audit_down(request: Request, exc: AuditUnavailable) -> JSONResponse:
        log.error("auditoría no disponible para el evento obligatorio %s", exc)
        return JSONResponse({"error": "servicio no disponible"}, status_code=503)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("error no controlado en %s", request.url.path)
        return JSONResponse({"error": "error interno"}, status_code=500)

    @app.get("/health")
    async def health() -> JSONResponse:
        if engine is None:  # servicio sin BD (stego)
            return JSONResponse({"status": "ok"})
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:  # la BD no responde: el healthcheck de Docker lo verá
            return JSONResponse({"error": "bd no disponible"}, status_code=503)
        return JSONResponse({"status": "ok"})

    return app
```

Run: `pytest services/shared -q`
Expected: PASS (incluye los 12 tests de `test_r16_service_auth.py`)

- [ ] **Step 6: Correlación de peticiones y registros JSON (RNF-18, RNF-19)**

Un mismo `X-Request-ID` recorre gateway → servicios → audit, así que una petición de la demo se reconstruye de punta a punta en la auditoría y en los registros.

`services/shared/tests/test_observabilidad.py`:
```python
import asyncio
import json
import logging
import re

import httpx
import pytest
from fastapi import Depends, Request
from fastapi.testclient import TestClient
from test_r16_service_auth import build_app

from shared import testing
from shared.identity import require_gateway
from shared.observability import REQUEST_HEADER, REQUEST_ID, JsonFormatter
from shared.service_auth import ServiceClient


@pytest.fixture
def recorder():
    return testing.Recorder()


def build_client(recorder) -> TestClient:
    app = build_app(recorder)

    @app.get("/api/eco", dependencies=[Depends(require_gateway)])
    async def eco(request: Request) -> dict:
        await request.app.state.audit.emit("info", "prueba.eco", actor="system")
        return {"id": REQUEST_ID.get()}

    return TestClient(app, base_url=testing.ORIGIN)


def test_el_id_del_gateway_llega_al_codigo_y_a_audit(recorder):
    headers = {**testing.gateway_headers(), REQUEST_HEADER: "0123456789abcdef"}
    r = build_client(recorder).get("/api/eco", headers=headers)
    assert r.json() == {"id": "0123456789abcdef"}
    assert recorder.events("prueba.eco")[0]["request_id"] == "0123456789abcdef"


@pytest.mark.parametrize("presented", [None, "corto", "con espacios y !!"])
def test_id_ausente_o_invalido_se_reemplaza(recorder, presented):
    headers = {**testing.gateway_headers(), **({REQUEST_HEADER: presented} if presented else {})}
    got = build_client(recorder).get("/api/eco", headers=headers).json()["id"]
    assert re.fullmatch(r"[0-9a-f]{32}", got)


def test_service_client_reenvia_el_id():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get(REQUEST_HEADER))
        return httpx.Response(204)

    client = ServiceClient(
        testing.service_auth("rooms", ("gateway",)), {"chat": "http://chat:8000"}, httpx.MockTransport(handler)
    )
    token = REQUEST_ID.set("0123456789abcdef")
    try:
        asyncio.run(client.post("chat", "/internal/x"))
    finally:
        REQUEST_ID.reset(token)
    assert seen == ["0123456789abcdef"]


def test_formato_json_de_los_registros():
    record = logging.LogRecord("http", logging.INFO, __file__, 1, "request", None, None)
    record.status, record.ms = 200, 3
    token = REQUEST_ID.set("0123456789abcdef")
    try:
        line = json.loads(JsonFormatter("rooms").format(record))
    finally:
        REQUEST_ID.reset(token)
    assert (line["service"], line["level"], line["request_id"], line["msg"]) == (
        "rooms", "info", "0123456789abcdef", "request",
    )
    assert (line["status"], line["ms"]) == (200, 3)


def test_una_linea_por_peticion_sin_query_string(recorder, caplog):
    with caplog.at_level(logging.INFO, logger="http"):
        build_client(recorder).get("/api/eco?sig=secreto", headers=testing.gateway_headers())
    [record] = [r for r in caplog.records if r.name == "http"]
    assert (record.method, record.path, record.status) == ("GET", "/api/eco", 200)
    assert "secreto" not in caplog.text
```

Run: `pytest services/shared/tests/test_observabilidad.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.observability'`

`services/shared/shared/observability.py`:
```python
"""Correlación de peticiones y registros JSON (spec §21.1; RNF-18, RNF-19)."""

import json
import logging
import re
import time
from contextvars import ContextVar
from uuid import uuid4

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from shared.secrets import env

REQUEST_HEADER = "X-Request-ID"
REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
VALID_ID = re.compile(r"[A-Za-z0-9-]{8,64}")
log = logging.getLogger("http")


class JsonFormatter(logging.Formatter):
    """Una línea JSON por registro: ts, service, level, request_id, logger, msg (y los campos de la petición)."""

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "service": self.service,
            "level": record.levelname.lower(),
            "request_id": REQUEST_ID.get(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        entry.update({k: getattr(record, k) for k in ("method", "path", "status", "ms") if hasattr(record, k)})
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging(service: str) -> None:
    """Solo con LOG_FORMAT=json (en los contenedores). Las líneas de arranque de uvicorn siguen en texto."""
    if env("LOG_FORMAT", "") != "json":
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)


class RequestContextMiddleware:
    """ASGI puro (no BaseHTTPMiddleware, para no romper los WebSocket). Va como el más externo."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        presented = Headers(scope=scope).get(REQUEST_HEADER, "")
        token = REQUEST_ID.set(presented if VALID_ID.fullmatch(presented) else uuid4().hex)
        started, status = time.perf_counter(), 500

        async def capture(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture)
        finally:
            if scope["type"] == "http" and scope["path"] != "/health":
                log.info(
                    "request",
                    extra={
                        "method": scope["method"],
                        "path": scope["path"],  # sin query string: las URL firmadas no se registran
                        "status": status,
                        "ms": round((time.perf_counter() - started) * 1000),
                    },
                )
            REQUEST_ID.reset(token)
```

Modificar:
- `shared/service_auth.py`: `from shared.observability import REQUEST_HEADER, REQUEST_ID` y, en `ServiceClient.post`, el diccionario de cabeceras queda `{**(headers or {}), TOKEN_HEADER: self.auth.token or "", **({REQUEST_HEADER: rid} if (rid := REQUEST_ID.get()) else {})}`.
- `shared/audit_client.py`: `from shared.observability import REQUEST_ID` y `"request_id": REQUEST_ID.get()` en el `event`.
- `shared/web.py`: `from shared.observability import RequestContextMiddleware, configure_logging`; en `create_base_app`, después de `app.add_middleware(ServiceTokenMiddleware)`, `app.add_middleware(RequestContextMiddleware)` (Starlette pone el último agregado como el más externo, así que también los rechazos por token llevan el id) y `configure_logging(title)` al principio.

Run: `pytest services/shared -q`
Expected: PASS (12 + 7 tests)

- [ ] **Step 7: Trazabilidad y commit**

En `docs/trazabilidad-riesgos.md`, fila **R16**:
- *Servicio / archivos:* `services/shared/shared/service_auth.py`, `identity.py`, `web.py`, `observability.py`
- *Tests:* `services/shared/tests/test_r16_service_auth.py`, `test_observabilidad.py`
- *Estado:* `En progreso (falta e2e del gateway)`

Fila **R3** (auditoría): agregar `observability.py` (correlación) en *Servicio / archivos*; su prueba llega con AUD-2.

```bash
git add services/shared docs/trazabilidad-riesgos.md
git commit -m "feat(shared): token por servicio, identidad del gateway, auditoría con fallback, base web y correlación de peticiones (R16)"
```

---

### Task FND-5: Utilidades de BD para pruebas, migraciones comunes e imágenes sintéticas

**Files:**
- Modify: `services/shared/shared/testing.py` (agregar lo de BD e imágenes)
- Create: `services/shared/shared/migrations.py`
- Create: `deploy/docker-compose.test.yml`
- Test: `services/shared/tests/test_testing.py`

**Interfaces:**
- Consumes: `shared.secrets.db_url` (FND-2).
- Produces:
  - `shared.migrations.run(service)`.
  - `shared.testing`:
    - BD: `PG_HOST`, `PG_PORT`, `FOREIGN_DB`, `dsn(user, password, database, driver="postgresql+asyncpg")`, `db_urls(service)->(owner_url, app_url)`, `prepare_database(service, service_dir)`, `run(coro)`, `sql(url, statement, **params)->list[dict]`, `with_conn(url, fn, *args)`, `truncate_all(owner_url)`, `assert_least_privilege(app_url, table)`;
    - imágenes: `natural_image(seed=0, size=256)`, `embed_lsb(pixels, rate, mode="seq", seed=1)`, `png_bytes(pixels, **kw)`, `jpeg_bytes(pixels, quality=90, **kw)`.

- [ ] **Step 1: Postgres de pruebas**

`deploy/docker-compose.test.yml`:
```yaml
# Solo para pruebas locales. La contraseña "postgres" es de prueba; no es un secreto.
name: chat-seguro-test
services:
  db-test:
    image: postgres:17
    environment:
      POSTGRES_PASSWORD: postgres
    ports: ["127.0.0.1:5433:5432"]
    tmpfs: [/var/lib/postgresql/data]
  clamav-test:
    image: ${CLAMAV_IMAGE:-clamav/clamav:1.4}
    ports: ["127.0.0.1:3310:3310"]
    profiles: [clamav]
```

Run: `docker compose -f deploy/docker-compose.test.yml up -d`
Expected: `Container chat-seguro-test-db-test-1  Started`

- [ ] **Step 2: Test (falla)**

`services/shared/tests/test_testing.py`:
```python
from shared import testing


def test_sql_contra_el_postgres_de_pruebas():
    url = testing.dsn("postgres", testing.PG_SUPERUSER_PASSWORD, "postgres")
    assert testing.sql(url, "SELECT 1 AS uno") == [{"uno": 1}]


def test_imagenes_sinteticas():
    pixels = testing.natural_image(0, size=64)
    assert pixels.shape == (64, 64, 3)
    assert pixels.dtype.name == "uint8"
    stego = testing.embed_lsb(pixels, 0.5, "random")
    assert ((stego >> 1) == (pixels >> 1)).all()  # solo cambia el LSB
    assert (stego != pixels).any()
    assert testing.png_bytes(pixels).startswith(b"\x89PNG")
    assert testing.jpeg_bytes(pixels).startswith(b"\xff\xd8\xff")
```

Run: `pytest services/shared/tests/test_testing.py -q`
Expected: FAIL — `AttributeError: module 'shared.testing' has no attribute 'dsn'`

- [ ] **Step 3: Agregar a `shared/testing.py`**

Al inicio, junto a los imports existentes, agregar:
```python
import asyncio
import io
import os
import subprocess
import sys
from pathlib import Path

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
```

Al final del archivo:
```python
# --- PostgreSQL de pruebas (deploy/docker-compose.test.yml) ------------------------
PG_HOST = os.environ.get("TEST_PG_HOST", "localhost")
PG_PORT = int(os.environ.get("TEST_PG_PORT", "5433"))
PG_SUPERUSER_PASSWORD = os.environ.get("TEST_PG_PASSWORD", "postgres")
FOREIGN_DB = "otra_bd_test"  # BD ajena: ningún rol <svc>_app debe poder conectarse


def dsn(user: str, password: str, database: str, driver: str = "postgresql+asyncpg") -> str:
    return f"{driver}://{user}:{password}@{PG_HOST}:{PG_PORT}/{database}"


def db_urls(service: str) -> tuple[str, str]:
    """(url del rol owner, url del rol app) de la BD <service>_test."""
    database = f"{service}_test"
    return (
        dsn(f"{service}_owner", ROLE_PASSWORD, database),
        dsn(f"{service}_app", ROLE_PASSWORD, database),
    )


async def _recreate(service: str) -> None:
    conn = await asyncpg.connect(dsn("postgres", PG_SUPERUSER_PASSWORD, "postgres", driver="postgresql"))
    try:
        database = f"{service}_test"
        await conn.execute(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
        for role in (f"{service}_owner", f"{service}_app"):
            if not await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = $1", role):
                await conn.execute(f"CREATE ROLE {role} LOGIN PASSWORD '{ROLE_PASSWORD}'")
        await conn.execute(f'CREATE DATABASE "{database}" OWNER {service}_owner')
        await conn.execute(f'REVOKE ALL ON DATABASE "{database}" FROM PUBLIC')
        await conn.execute(f'GRANT CONNECT ON DATABASE "{database}" TO {service}_app')
        if not await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", FOREIGN_DB):
            await conn.execute(f'CREATE DATABASE "{FOREIGN_DB}"')
            await conn.execute(f'REVOKE ALL ON DATABASE "{FOREIGN_DB}" FROM PUBLIC')
    finally:
        await conn.close()


def prepare_database(service: str, service_dir: Path) -> None:
    """Recrea <service>_test con los roles reales y aplica las migraciones como en producción."""
    asyncio.run(_recreate(service))
    owner_url, _ = db_urls(service)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=service_dir,
        check=True,
        env={**os.environ, "MIGRATOR_DATABASE_URL": owner_url},
    )


def run(coro):
    return asyncio.run(coro)


async def _with_engine(url: str, fn):
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        return await fn(engine)
    finally:
        await engine.dispose()


def sql(url: str, statement: str, **params) -> list[dict]:
    """Ejecuta SQL en una transacción propia y devuelve las filas como dicts."""

    async def go(engine):
        async with engine.begin() as conn:
            result = await conn.execute(text(statement), params)
            return [dict(row) for row in result.mappings()] if result.returns_rows else []

    return run(_with_engine(url, go))


def with_conn(url: str, fn, *args):
    """Ejecuta `await fn(conn, *args)` dentro de una transacción con el rol de la URL."""

    async def go(engine):
        async with engine.begin() as conn:
            return await fn(conn, *args)

    return run(_with_engine(url, go))


def truncate_all(owner_url: str) -> None:
    sql(
        owner_url,
        "DO $$ DECLARE t text; BEGIN "
        "FOR t IN SELECT tablename FROM pg_tables "
        "WHERE schemaname = 'public' AND tablename <> 'alembic_version' LOOP "
        "EXECUTE format('TRUNCATE %I RESTART IDENTITY CASCADE', t); END LOOP; END $$",
    )


def assert_least_privilege(app_url: str, table: str) -> None:
    """R11: el rol de la app no hace DDL, no lee catálogos privilegiados ni entra a otra BD."""
    for statement, expected in (
        ("CREATE TABLE intruso (id int)", "permission denied"),
        (f"DROP TABLE {table}", "must be owner"),
        ("SELECT * FROM pg_authid", "permission denied"),
    ):
        try:
            sql(app_url, statement)
        except Exception as exc:  # se busca el mensaje de Postgres
            assert expected in str(exc), f"{statement}: {exc}"
        else:
            raise AssertionError(f"el rol de la app pudo ejecutar: {statement}")
    foreign = app_url.rsplit("/", 1)[0] + f"/{FOREIGN_DB}"
    try:
        sql(foreign, "SELECT 1")
    except Exception as exc:
        assert "permission denied" in str(exc), str(exc)
    else:
        raise AssertionError("el rol de la app pudo conectarse a otra base de datos")


# --- Imágenes sintéticas (requieren numpy y Pillow, extra [dev]) --------------------
def natural_image(seed: int = 0, size: int = 256):
    """Imagen "fotográfica": textura suave + ruido, pasada por JPEG q=85 como una foto de celular.

    Valores del prototipo: chi² p ≈ 0.33–0.38 y RS p̂ ≤ 0.013 (limpia).
    """
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float64)
    base = 110 + 60 * np.sin(x / 23) * np.cos(y / 31) + 30 * np.sin((x + y) / 47)
    rgb = np.stack([base, base * 0.8 + 20, 255 - base * 0.9], axis=-1)
    rgb = rgb + rng.normal(0, 2.0, (size, size, 3))
    buffer = io.BytesIO()
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(buffer, format="JPEG", quality=85)
    return np.asarray(Image.open(io.BytesIO(buffer.getvalue())).convert("RGB")).copy()


def embed_lsb(pixels, rate: float, mode: str = "seq", seed: int = 1):
    """LSB replacement con bits aleatorios (simula un mensaje cifrado). mode: 'seq' | 'random'."""
    import numpy as np

    flat = pixels.reshape(-1).copy()
    count = int(len(flat) * rate)
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, count, dtype=np.uint8)
    index = np.arange(count) if mode == "seq" else rng.choice(len(flat), count, replace=False)
    flat[index] = (flat[index] & 0xFE) | bits
    return flat.reshape(pixels.shape)


def png_bytes(pixels, **save_kwargs) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG", **save_kwargs)
    return buffer.getvalue()


def jpeg_bytes(pixels, quality: int = 90, **save_kwargs) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="JPEG", quality=quality, **save_kwargs)
    return buffer.getvalue()
```

- [ ] **Step 4: Punto de entrada común de Alembic**

`services/shared/shared/migrations.py`:
```python
"""Punto de entrada común de Alembic: cada servicio migra solo su BD, con su rol owner (spec §7.6)."""

import asyncio
import os

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from shared.secrets import db_url


def _migrate(connection) -> None:
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


def run(service: str) -> None:
    """MIGRATOR_DATABASE_URL solo se usa en pruebas; en producción la URL sale de db_<svc>_owner."""

    async def main() -> None:
        engine = create_async_engine(os.environ.get("MIGRATOR_DATABASE_URL") or db_url(service, "owner"))
        try:
            async with engine.connect() as connection:
                await connection.run_sync(_migrate)
        finally:
            await engine.dispose()

    asyncio.run(main())
```

Run: `pytest services/shared -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/shared deploy/docker-compose.test.yml
git commit -m "feat(shared): utilidades de BD de prueba, migraciones comunes e imágenes sintéticas"
```

---

### Task FND-6: Plantilla Docker, generación de secretos y PostgreSQL con 5 BD

**Files:**
- Create: `services/Dockerfile`, `services/lock.sh`
- Create: `deploy/gen_secrets.py`, `deploy/postgres/init.sh`, `deploy/docker-compose.yml`
- Test: `services/shared/tests/test_gen_secrets.py`

**Interfaces:**
- Consumes: `shared.crypto` (para el test).
- Produces:
  - `deploy/secrets/*`: los 30 archivos de la spec §11.1, entre ellos `gateway_token.conf`, `kek_media_v1`, `jwt_signing_key` (RSA de 3072 bits) y el token y hash de `stego`.
  - `deploy/public/chat-key.json` con `{"kid", "pub"}`.
  - Imagen por servicio: `docker build --build-arg SERVICE=<svc> -f services/Dockerfile .`.
  - Compose con `db`, las redes y las anclas `x-python-service` / `x-migrate`, que las tareas de cada servicio reutilizan.

- [ ] **Step 1: Test del generador de secretos (falla)**

`services/shared/tests/test_gen_secrets.py`:
```python
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from shared.crypto import b64d, b64e, load_signing_key, public_bytes

SCRIPT = Path(__file__).resolve().parents[3] / "deploy" / "gen_secrets.py"


def gen(root: Path, *args: str) -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--dir", str(root), *args], check=True, capture_output=True)


def test_genera_todo_y_no_sobrescribe(tmp_path):
    gen(tmp_path)
    secrets = tmp_path / "secrets"
    # 21 aleatorios (3 KEK, url, postgres, 10 de BD, 6 tokens) + 6 hashes + conf + chat_sign_key + jwt_signing_key
    assert len(list(secrets.iterdir())) == 30
    jwt_key = serialization.load_pem_private_key((secrets / "jwt_signing_key").read_bytes(), password=None)
    assert isinstance(jwt_key, rsa.RSAPrivateKey) and jwt_key.key_size == 3072
    stego_token = (secrets / "svc_token_stego").read_text().strip()
    assert (secrets / "svc_hash_stego").read_text() == hashlib.sha256(stego_token.encode()).hexdigest()
    token = (secrets / "svc_token_gateway").read_text().strip()
    assert (secrets / "svc_hash_gateway").read_text() == hashlib.sha256(token.encode()).hexdigest()
    assert token in (secrets / "gateway_token.conf").read_text()
    assert len(b64d((secrets / "kek_chat_v1").read_text().strip())) == 32
    key = load_signing_key((secrets / "chat_sign_key").read_text())
    published = json.loads((tmp_path / "public" / "chat-key.json").read_text())
    assert published["pub"] == b64e(public_bytes(key))
    before = {p.name: p.read_text() for p in secrets.iterdir()}
    gen(tmp_path)
    assert {p.name: p.read_text() for p in secrets.iterdir()} == before


def test_rotar_token_del_gateway_regenera_hash_y_conf(tmp_path):
    gen(tmp_path)
    secrets = tmp_path / "secrets"
    old = (secrets / "svc_token_gateway").read_text().strip()
    gen(tmp_path, "--rotate", "svc_token_gateway")
    new = (secrets / "svc_token_gateway").read_text().strip()
    assert new != old
    assert (secrets / "svc_hash_gateway").read_text() == hashlib.sha256(new.encode()).hexdigest()
    assert new in (secrets / "gateway_token.conf").read_text()
```

Run: `pytest services/shared/tests/test_gen_secrets.py -q`
Expected: FAIL — `can't open file ... deploy/gen_secrets.py`

- [ ] **Step 2: Implementar `deploy/gen_secrets.py`**

```python
"""Genera los secretos de deploy/secrets/ y la clave pública del chat (spec §11.1).

Nunca sobrescribe un secreto existente; --rotate NOMBRE regenera uno (y lo que se deriva de él).
Uso:  python deploy/gen_secrets.py [--rotate NOMBRE] [--dir RUTA]
Requiere `cryptography` (incluido en el .venv del proyecto).
"""

import argparse
import base64
import hashlib
import json
import secrets
from collections.abc import Callable
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

SERVICES = ("auth", "rooms", "chat", "media", "audit")  # los que tienen BD (stego no)
CALLERS = ("gateway", "auth", "rooms", "chat", "media", "stego")
RANDOM = (
    "kek_auth_v1",
    "kek_chat_v1",
    "kek_media_v1",
    "url_signing_key",
    "postgres_password",
    *(f"db_{svc}_{role}" for svc in SERVICES for role in ("owner", "app")),
    *(f"svc_token_{caller}" for caller in CALLERS),
)


def pem(key) -> str:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def new_signing_key() -> str:
    """ECDSA P-256 del hello del chat (spec §10.1)."""
    return pem(ec.generate_private_key(ec.SECP256R1()))


def new_jwt_key() -> str:
    """RSA de 3072 bits para los JWT RS256 de auth (spec §11.1)."""
    return pem(rsa.generate_private_key(public_exponent=65537, key_size=3072))


def public_key_json(pem: str) -> str:
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    raw = key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    pub = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    return json.dumps({"kid": hashlib.sha256(raw).hexdigest()[:16], "pub": pub}) + "\n"


class Generator:
    def __init__(self, root: Path, rotate: str | None) -> None:
        self.secrets_dir = root / "secrets"
        self.public_dir = root / "public"
        self.rotate = rotate
        self.changed: set[str] = set()

    def path(self, name: str) -> Path:
        return self.secrets_dir / name

    def read(self, name: str) -> str:
        return self.path(name).read_text(encoding="utf-8").strip()

    def write(self, name: str, content: str) -> None:
        path = self.path(name)
        path.write_text(content, encoding="utf-8")
        path.chmod(0o644)  # legible por el uid 10001 del contenedor; el directorio es 0700 (spec §11.1)
        self.changed.add(name)
        print(f"generado: {name}")

    def ensure(self, name: str, make: Callable[[], str]) -> None:
        if self.rotate == name or not self.path(name).exists():
            self.write(name, make())

    def run(self) -> None:
        self.secrets_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.public_dir.mkdir(parents=True, exist_ok=True)
        for name in RANDOM:
            self.ensure(name, lambda: secrets.token_urlsafe(32))
        for caller in CALLERS:
            token_name, hash_name = f"svc_token_{caller}", f"svc_hash_{caller}"
            if token_name in self.changed or not self.path(hash_name).exists():
                self.write(hash_name, hashlib.sha256(self.read(token_name).encode()).hexdigest())
        if "svc_token_gateway" in self.changed or not self.path("gateway_token.conf").exists():
            token = self.read("svc_token_gateway")
            self.write("gateway_token.conf", f'proxy_set_header X-Service-Token "{token}";\n')
        self.ensure("chat_sign_key", new_signing_key)
        self.ensure("jwt_signing_key", new_jwt_key)
        public = self.public_dir / "chat-key.json"
        if "chat_sign_key" in self.changed or not public.exists():
            public.write_text(public_key_json(self.read("chat_sign_key")), encoding="utf-8")
            print("generado: public/chat-key.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rotate", help="nombre del secreto a regenerar")
    parser.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    Generator(args.dir, args.rotate).run()


if __name__ == "__main__":
    main()
```

Run: `pytest services/shared/tests/test_gen_secrets.py -q`
Expected: PASS

- [ ] **Step 3: Plantilla Docker y bloqueo de dependencias**

`services/Dockerfile`:
```dockerfile
# Plantilla única de los servicios Python (spec §4.2). Uso: --build-arg SERVICE=<svc>
FROM python:3.13-slim
ARG SERVICE
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SERVICE=${SERVICE} LOG_FORMAT=json
RUN useradd --uid 10001 --no-create-home app \
 && mkdir -p /data/media /data/quarantine \
 && chown -R app:app /data
WORKDIR /srv
COPY services/${SERVICE}/requirements.lock /srv/requirements.lock
RUN pip install --no-cache-dir -r /srv/requirements.lock
COPY services/shared /srv/shared
RUN pip install --no-cache-dir --no-deps /srv/shared
COPY services/${SERVICE} /srv/svc
RUN pip install --no-cache-dir --no-deps /srv/svc
WORKDIR /srv/svc
USER app
EXPOSE 8000
# --ws-max-size: uvicorn corta antes de leer tramas absurdas; chat aplica su propio tope de 16 KB (4413).
# --no-access-log: la línea por petición la escribe RequestContextMiddleware (JSON, sin query string).
CMD exec uvicorn --factory "${SERVICE}_svc.main:create_app" --host 0.0.0.0 --port 8000 \
    --proxy-headers --forwarded-allow-ips '*' --ws-ping-interval 30 --ws-ping-timeout 30 \
    --ws-max-size 65536 --no-server-header --no-access-log
```

`services/lock.sh`:
```sh
#!/bin/sh
# Fija las versiones exactas de un servicio (incluye las dependencias de shared).
# Uso (PowerShell, desde la raíz):  docker run --rm -v "${PWD}:/w" -w /w python:3.13-slim sh services/lock.sh <svc>
set -eu
svc="$1"
python -m venv /tmp/venv
/tmp/venv/bin/pip install --quiet ./services/shared "./services/$svc"
/tmp/venv/bin/pip freeze --exclude-editable \
  | grep -v -E "^(chat-shared|${svc}-svc)( @| ?==)" > "services/$svc/requirements.lock"
echo "services/$svc/requirements.lock actualizado"
```

- [ ] **Step 4: PostgreSQL con una BD y dos roles por servicio**

`deploy/postgres/init.sh`:
```sh
#!/bin/sh
# Se ejecuta una sola vez, al crear el volumen. Crea una BD y dos roles por servicio (spec §7.6).
set -eu
for svc in auth rooms chat media audit; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
    -v db="$svc" -v owner="${svc}_owner" -v app="${svc}_app" \
    -v owner_pw="$(cat "/run/secrets/db_${svc}_owner")" \
    -v app_pw="$(cat "/run/secrets/db_${svc}_app")" <<'SQL'
CREATE ROLE :"owner" LOGIN PASSWORD :'owner_pw';
CREATE ROLE :"app" LOGIN PASSWORD :'app_pw';
ALTER ROLE :"owner" SET log_statement = 'all';
CREATE DATABASE :"db" OWNER :"owner";
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db" TO :"app";
SQL
done
```

`deploy/docker-compose.yml`:
```yaml
# Stack completo (spec §4–§5). Cada servicio se agrega en su propia tarea del plan.
name: chat-seguro

x-python-service: &python-service
  restart: unless-stopped
  read_only: true
  tmpfs: [/tmp]
  cap_drop: [ALL]
  security_opt: ["no-new-privileges:true"]
  healthcheck:
    test: ["CMD", "python", "-c", "import sys, urllib.request; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status != 200)"]
    interval: 10s
    timeout: 5s
    retries: 6
    start_period: 10s

x-migrate: &migrate
  command: ["alembic", "upgrade", "head"]
  read_only: true
  cap_drop: [ALL]
  security_opt: ["no-new-privileges:true"]
  networks: [data]
  depends_on:
    db:
      condition: service_healthy

services:
  db:
    image: postgres:17
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets: [postgres_password, db_auth_owner, db_auth_app, db_rooms_owner, db_rooms_app,
              db_chat_owner, db_chat_app, db_media_owner, db_media_app, db_audit_owner, db_audit_app]
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./postgres/init.sh:/docker-entrypoint-initdb.d/init.sh:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -h 127.0.0.1"]
      interval: 5s
      timeout: 5s
      retries: 20
    networks: [data]
    restart: unless-stopped

networks:
  public: {}
  apps: {internal: true}
  data: {internal: true}
  scan: {internal: true}
  clamav-egress: {}

volumes:
  pgdata: {}
  media_data: {}

secrets:
  postgres_password: {file: ./secrets/postgres_password}
  db_auth_owner: {file: ./secrets/db_auth_owner}
  db_auth_app: {file: ./secrets/db_auth_app}
  db_rooms_owner: {file: ./secrets/db_rooms_owner}
  db_rooms_app: {file: ./secrets/db_rooms_app}
  db_chat_owner: {file: ./secrets/db_chat_owner}
  db_chat_app: {file: ./secrets/db_chat_app}
  db_media_owner: {file: ./secrets/db_media_owner}
  db_media_app: {file: ./secrets/db_media_app}
  db_audit_owner: {file: ./secrets/db_audit_owner}
  db_audit_app: {file: ./secrets/db_audit_app}
  kek_auth_v1: {file: ./secrets/kek_auth_v1}
  kek_chat_v1: {file: ./secrets/kek_chat_v1}
  kek_media_v1: {file: ./secrets/kek_media_v1}
  chat_sign_key: {file: ./secrets/chat_sign_key}
  jwt_signing_key: {file: ./secrets/jwt_signing_key}
  url_signing_key: {file: ./secrets/url_signing_key}
  gateway_token_conf: {file: ./secrets/gateway_token.conf}
  svc_token_auth: {file: ./secrets/svc_token_auth}
  svc_token_rooms: {file: ./secrets/svc_token_rooms}
  svc_token_chat: {file: ./secrets/svc_token_chat}
  svc_token_media: {file: ./secrets/svc_token_media}
  svc_token_stego: {file: ./secrets/svc_token_stego}
  svc_hash_gateway: {file: ./secrets/svc_hash_gateway}
  svc_hash_auth: {file: ./secrets/svc_hash_auth}
  svc_hash_rooms: {file: ./secrets/svc_hash_rooms}
  svc_hash_chat: {file: ./secrets/svc_hash_chat}
  svc_hash_media: {file: ./secrets/svc_hash_media}
  svc_hash_stego: {file: ./secrets/svc_hash_stego}
```

- [ ] **Step 5: Verificar la BD real**

Run:
```bash
python deploy/gen_secrets.py
docker compose -f deploy/docker-compose.yml up -d db
docker compose -f deploy/docker-compose.yml exec db psql -U postgres -tAc "SELECT datname || ':' || pg_get_userbyid(datdba) FROM pg_database WHERE datname IN ('auth','rooms','chat','media','audit') ORDER BY 1"
docker compose -f deploy/docker-compose.yml exec db psql -U postgres -tAc "SELECT has_database_privilege('rooms_app','auth','CONNECT')"
```
Expected:
```
audit:audit_owner
auth:auth_owner
chat:chat_owner
media:media_owner
rooms:rooms_owner
f
```

- [ ] **Step 6: Commit**

```bash
git add services/Dockerfile services/lock.sh deploy/gen_secrets.py deploy/postgres/init.sh deploy/docker-compose.yml services/shared/tests/test_gen_secrets.py
git commit -m "feat(deploy): plantilla Docker, generación de secretos y PostgreSQL con BD por servicio"
```

---

### Task FND-7: Integración continua

**Files:**
- Create: `.github/workflows/ci.yml`, `.coveragerc`

**Interfaces:**
- Consumes: `services/shared` (FND-2…FND-6), `pytest-cov` (dev de `shared`) y la regla `C90` de `ruff.toml` (FND-1).
- Produces: el job `services` con matriz `svc`. Cada tarea `*-1` de un servicio agrega su nombre a la matriz, y FE-1 agrega el job `frontend`. El job falla si un servicio baja del **80 % de cobertura de líneas** (RNF-10) o si una función supera la complejidad 10 (RNF-11). Si un servicio no llega al 80 %, se agregan pruebas: el umbral no se baja. Los jobs `codeql` (SAST) y `secrets` (gitleaks) cubren Shift Left desde el primer push.

- [ ] **Step 1: Workflow**

`.github/workflows/ci.yml`:
```yaml
name: ci
on:
  push:
  pull_request:

jobs:
  services:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        svc: [shared]
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_PASSWORD: postgres
        ports: ["5433:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s --health-timeout 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Instalar
        run: |
          python -m pip install --upgrade pip
          if [ "${{ matrix.svc }}" != "shared" ]; then pip install -r "services/${{ matrix.svc }}/requirements.lock"; fi
          pip install -e "services/shared[dev]"
          if [ "${{ matrix.svc }}" != "shared" ]; then pip install -e "services/${{ matrix.svc }}"; fi
      - name: Ruff
        run: ruff check "services/${{ matrix.svc }}" && ruff format --check "services/${{ matrix.svc }}"
      - name: Pruebas con cobertura ≥ 80 % (RNF-10)
        run: |
          pkg="${{ matrix.svc }}_svc"; [ "${{ matrix.svc }}" = shared ] && pkg=shared
          pytest "services/${{ matrix.svc }}" -m "not clamav" --cov="$pkg" --cov-report=term --cov-fail-under=80
      - name: Bandit
        # -ll: severidad media o mayor. Se excluyen las pruebas, las herramientas y el soporte de pruebas.
        run: bandit -q -ll -r "services/${{ matrix.svc }}" -x "services/${{ matrix.svc }}/tests,services/${{ matrix.svc }}/tools,services/shared/shared/testing.py"
      - name: pip-audit
        run: pip-audit --skip-editable

  codeql:
    # SAST (Shift Left). `upload: never` + artefacto SARIF funciona también en repositorios privados
    # sin GitHub Advanced Security; si el repositorio es público, se puede quitar `upload: never`.
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    strategy:
      fail-fast: false
      matrix:
        language: [python, javascript-typescript]
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/analyze@v3
        with:
          upload: never
          output: codeql-results
      - uses: actions/upload-artifact@v4
        with:
          name: codeql-${{ matrix.language }}
          path: codeql-results

  secrets:
    # Detección de secretos en todo el historial. Si marca falsos positivos en `tests/`,
    # agrega un `.gitleaks.toml` con una lista de permitidos para esas rutas.
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

`.coveragerc` (en la raíz; mide solo código de producción):
```ini
[run]
omit =
    */tests/*
    */migrations/*
    */tools/*
    */shared/testing.py

[report]
exclude_lines =
    pragma: no cover
    if __name__ == .__main__.:
```

- [ ] **Step 2: Formatear y verificar en local**

Run: `ruff format services/shared deploy && ruff check --fix services/shared deploy && pytest services/shared -q --cov=shared --cov-fail-under=80`
Expected: sin errores de ruff, todos los tests en verde y `Required test coverage of 80% reached`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml .coveragerc services/shared deploy
git commit -m "ci: lint, pruebas con cobertura, bandit, pip-audit, CodeQL y gitleaks"
```
El `push` (`git push -u origin feat/arquitectura-chat-seguro`) se hace solo cuando el equipo lo pida.
Expected: al hacer push, el workflow `ci` pasa en GitHub (jobs `services (shared)`, `codeql` y `secrets`).

- [ ] **Step 4: Proteger `main` (lo hace quien administra el repositorio, una sola vez)**

En GitHub: *Settings → Branches → Add branch ruleset* sobre `main`:
- exigir pull request con **1 aprobación**;
- exigir que pasen los jobs `services`, `codeql` y `secrets`;
- bloquear el *force push* y el borrado de la rama.

Esto respalda por configuración la regla del equipo de no hacer `merge` a `main` sin autorización. Anota la fecha en la *Verificación manual* de `docs/trazabilidad-riesgos.md`.

Al cerrar este archivo, marca `[x] 01 Fundaciones` en la sección *Estado actual* de `CLAUDE.md`.

---

## Execution Handoff

Ejecuta los archivos en el orden del índice (`2026-10-13-00-indice.md`). Para cada tarea: lee la tarea **y** las secciones del spec que cita, sigue los pasos en orden (test que falla → implementación → test en verde → commit) y no adelantes tareas de otros archivos sin que sus dependencias estén en verde.
