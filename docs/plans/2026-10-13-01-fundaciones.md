# 01 · Fundaciones — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar listo todo lo que comparten los servicios: el contexto de Claude Code, la librería `shared` (secretos, cripto, contraseñas, límites, autenticación entre servicios, identidad, auditoría, base web, caracteres invisibles, utilidades de prueba), los vectores cripto, la plantilla Docker, la generación de secretos, PostgreSQL con 5 BD y la CI.

**Architecture:** `services/shared` es un paquete Python instalable (`chat-shared` → `import shared`). Cada servicio lo instala junto al suyo. La infraestructura (Dockerfile único con `ARG SERVICE`, `gen_secrets.py`, `init.sh`) se escribe una vez y cada servicio solo agrega su bloque al compose.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2 + asyncpg, Alembic, cryptography, argon2-cffi, httpx, pytest · Docker Compose · GitHub Actions.

**Spec:** `docs/specs/2026-10-12-chat-seguro-design.md` (§4.3, §5, §7.6, §10, §11, §12.8, §15, §16, §17).

> **Revisión 3 (2026-10-19, spec rev. 3: cuenta obligatoria y archivos de cualquier tipo).** Cambian:
> - FND-1: reglas, skill de estegoanálisis, trazabilidad con R17, `CLAUDE.md` y `ruff.toml` (las pruebas pueden lanzar procesos);
> - FND-4: `UserIdentity`, `require_user`, cabeceras `X-User-*`, `USER_COOKIE` y `user_headers`;
> - FND-5: `embed_lsb` para muestras int16, más audio y MP3 sintéticos;
> - FND-6: paquetes del sistema por servicio en el `Dockerfile` y el conteo correcto de secretos (26);
> - FND-7: ffmpeg en la CI de `media`;
> - FND-8, nueva: `shared.text`.
>
> Si ya ejecutaste esas tareas, aplica solo las diferencias y vuelve a correr `pytest services/shared`.
>
> **Revisión 4 (2026-10-20, spec rev. 4).** FND-1…FND-8 no cambian. Se agregan dos tareas con los requisitos de la Actividad 3: **FND-9** (id de correlación, registros JSON, métricas por servicio, alerta de CPU y memoria, y el alias en `UserIdentity`) y **FND-10** (cobertura ≥ 80 % y complejidad ≤ 10 en la CI, gitleaks, plantilla de PR y rama protegida, modelo de amenazas y columna ISO/IEC 27001 en la trazabilidad).

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

Ninguno de los casos del índice cae en este archivo, pero las utilidades que se crean aquí los soportan:
- `TokenBucket` para los límites del WS.
- `natural_image`/`embed_lsb` para los tests de imágenes; `natural_audio`/`wav_bytes`/`mp3_bytes` para los de audio, sin ffmpeg.
- `session_headers` codifica alias con tildes y, como `user_headers`, lleva la cuenta (`X-User-Id`) que verificó el gateway.
- `shared.text.clean` no toca los emojis compuestos (👨‍👩‍👧, ❤️): lo prueba `test_texto_normal_sin_hallazgos` (FND-8).
- El middleware de correlación es el más externo: también un 401 por falta de token lleva `X-Request-ID` (`test_rnf19_id_ausente_o_raro_se_reemplaza`, FND-9).
- `configure_logging` no toca el logging fuera de Docker (`LOG_FORMAT` sin definir): así pytest conserva sus handlers.

---

### Task FND-1: Higiene del repo y contexto de Claude Code

**Files:**
- Create: `.gitignore`, `.gitattributes`, `.dockerignore`, `ruff.toml`
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
  - `ruff.toml` en la raíz, que aplica a todo `services/`, `deploy/` y `e2e/`.

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
    assert check("/repo/services/media/media_svc/formats/png.py", 'SIGNATURE = b"\\x89PNG\\r\\n"', root) is None
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

# Calibración del estegoanálisis (imágenes y grabaciones personales)
services/media/tools/calibracion/
```

`.gitattributes`:
```gitattributes
* text=auto
*.sh text eol=lf
*.conf text eol=lf
*.png binary
*.jpg binary
*.gif binary
*.mp3 binary
*.wav binary
*.mp4 binary
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
select = ["E", "F", "I", "B", "S", "UP"]
ignore = ["E501"]  # ruff format ajusta el código; SQL y comentarios largos no se parten a la fuerza

[lint.isort]
known-first-party = ["shared", "auth_svc", "rooms_svc", "chat_svc", "media_svc", "audit_svc"]

[lint.flake8-bugbear]
# FastAPI declara dependencias y parámetros con llamadas en los valores por defecto.
extend-immutable-calls = ["fastapi.Depends", "fastapi.Query", "fastapi.params.Depends", "fastapi.params.Query"]

[lint.per-file-ignores]
"**/tests/**" = ["S101", "S105", "S106", "S311", "S603", "S607"]  # las pruebas lanzan ffmpeg, mkcert y herramientas
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
3. **Identidad:** el remitente, la cuenta, la sala y el admin salen de la identidad verificada (`require_admin`, `require_user`, `require_session`, `session_from_headers`). Nunca del cuerpo de la petición ni de la trama: el alias en el chat es el de la cuenta (elegido en el primer ingreso).
4. **SQL:** siempre `text()` con parámetros nombrados. Prohibido interpolar datos con f-strings.
5. **Contraseñas y claves de sala:** Argon2id (`shared.passwords`), con verificación contra un hash dummy cuando el usuario, el admin o la sala no existen.
6. **Errores:** el cliente recibe `{"error": "..."}` genérico; el detalle va a auditoría. Todo rechazo de seguridad se audita (`audit.emit(...)`).
7. **Datos sensibles:** nunca se registran contraseñas, claves de sala, tokens, cuerpos de mensajes ni secretos TOTP.
8. **Fallar cerrado:** si falta un secreto, el servicio no arranca. Si ClamAV o la BD no responden → 503. Si `audit` no responde en un evento obligatorio → 503 con rollback.
9. **Cripto:** solo con `shared.crypto` (AES-256-GCM con AAD, ECDH P-256, HKDF-SHA256, ECDSA P-256). Nada de primitivas propias ni modos sin autenticación.
10. **Archivos:** solo los 9 formatos de la lista blanca (spec §12.1), detectados por firma. Jamás se sirve un archivo sin firma HMAC válida y pertenencia a la sala, y todo archivo publicado pasó por la sanitización. El contenido activo (macros, JavaScript, adjuntos, OLE) se rechaza. ffmpeg y ffprobe solo se llaman desde `media_svc.ffmpeg` (demuxer forzado, `-protocol_whitelist file`, sin shell y con timeout).
11. **Cuentas:** admins y usuarios nunca se mezclan (tablas, cookies y verificaciones distintas). Una sola sesión activa por cuenta y una sola sesión de sala por usuario, ambas atadas a la cookie de dispositivo (R13).
```

`.claude/rules/microservices.md`:
```markdown
# Modelo de confianza entre microservicios (R16, spec §4.3)

- Toda ruta de un servicio exige `X-Service-Token` válido (`ServiceTokenMiddleware`, que agrega `shared.web.create_base_app`). Solo `/health` está exento.
- Rutas públicas (enrutadas por el gateway): `Depends(require_gateway)`, `Depends(require_admin)`, `Depends(require_user)` o `Depends(require_session)`. Rutas internas: `/internal/...` con `Depends(allow("<llamador>", ...))`.
- Las cabeceras `X-Admin-*`, `X-User-*` y `X-Session-*` **solo** se leen a través de `shared.identity`, que exige que el llamador sea `gateway`.
- Cada servicio se conecta **solo a su BD** con su rol `<svc>_app`. Nunca se consulta la BD de otro servicio: se pide por su API interna.
- Las llamadas a otros servicios pasan por `ServiceClient` (`app.state.peers`), nunca por un `httpx` suelto.
- Allowlist vigente: auth ← gateway · rooms ← gateway, chat · chat ← gateway, rooms, media · media ← gateway · audit ← gateway, auth, rooms, chat, media.
- Agregar un servicio o un llamador requiere tocar:
  - la red en `deploy/docker-compose.yml`;
  - los secretos `svc_token_*`/`svc_hash_*` y `deploy/gen_secrets.py`;
  - el rol de BD en `deploy/postgres/init.sh`;
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
- Nada en `localStorage`/`sessionStorage`: los tokens están en cookies `HttpOnly` que JS no ve.
- Sin estilos ni scripts inline (la CSP los bloquea). Estilos en `src/styles.css`.
- Sin `React.StrictMode`: monta los efectos dos veces, abre y cierra el WebSocket, y eso termina la sesión.
- HTTP solo por `src/lib/api.ts`; WebSocket solo por `src/lib/ws.ts`.
- Archivos del chat (`src/pages/Attachment.tsx`): imágenes con `<img>`; audio y video desde una URL `blob:` tras un clic; documentos y texto solo como descarga. Nunca se renderiza un documento ni un TXT dentro de la página.
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
- `media` necesita ffmpeg/ffprobe en el PATH para MP3 y MP4 (Windows: `winget install Gyan.FFmpeg`; macOS: `brew install ffmpeg`). Sin ffmpeg, esas pruebas se saltan (`needs_ffmpeg`); en la CI siempre corren.
- Las muestras de cada formato se generan en las propias pruebas del formato (las que comparten varios archivos, en `services/media/tests/samples.py`): no se versionan binarios.
- Escribe el test, míralo fallar y recién entonces implementa.
- Al cerrar una tarea, actualiza `docs/trazabilidad-riesgos.md`.
```

- [ ] **Step 6: Comando, skills y subagente**

`.claude/commands/risk-check.md`:
```markdown
---
description: Contrasta los cambios actuales con R1–R17 y actualiza la trazabilidad
---
Revisa los cambios de la rama actual contra los riesgos del proyecto.

1. Obtén el diff: `git diff main...HEAD` y `git diff` (lo que no está commiteado).
2. Lee `docs/trazabilidad-riesgos.md`, `.claude/rules/security.md` y `.claude/rules/microservices.md`.
3. Por cada archivo cambiado, identifica qué riesgo (R1–R17) toca. La tabla del spec §16.4 dice qué servicio cubre cada uno.
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
description: Referencia del análisis de archivos de media (lista blanca de 9 formatos, estegoanálisis por formato —chi², RS y SPA para LSB; estructura de PNG, JPEG, GIF, WAV, MP3, MP4, PDF, DOCX y TXT—, contenido activo, sanitización CDR, ffmpeg endurecido y calibración). Úsala al tocar services/media, ajustar umbrales o agregar un formato.
---
# Análisis de archivos en `media` (spec §12)

## Lista blanca y contrato (`media_svc/formats/`)
PNG, JPEG, GIF (imagen, 5 MB) · MP3, WAV (audio, 10 MB) · MP4 H.264/AAC (video, 25 MB) · PDF, DOCX (documento, 10 MB) · TXT UTF-8 (texto, 1 MB). Cada módulo expone `FORMAT = Format(mime, ext, category, detect, validate, analyze, sanitize)`; `validate`, `analyze` y `sanitize` reciben `(data, cfg)` y corren en el `ProcessPoolExecutor` con timeout. El veredicto es `{"format", "suspicious", "active", "reasons", "metrics"}`: `active` → rechazo, `suspicious` → cuarentena.

## Detectores
| Formato | Estadística | Estructura (dispara si…) |
|---|---|---|
| PNG | Chi² Westfeld–Pfitzmann por canal en prefijos 10/25/50/100 % (`p ≥ STEGO_CHI2_P`, 0.95) · RS de Fridrich (`p̂ ≥ STEGO_RS_RATE`, 0.08) · entropía LSB de apoyo | bytes tras `IEND`, chunks de texto > 1 KB, chunks desconocidos |
| JPEG | — (*stretch*: chi² DCT) | > 16 bytes tras `FFD9`, APPn + COM > 64 KB |
| GIF | fracción de colores casi idénticos en la paleta (solo con `STEGO_GIF_PALETTE_TRIGGER`) | datos tras el trailer, comentarios > 1 KB, extensiones de aplicación ajenas a NETSCAPE2.0/ANIMEXTS1.0, texto plano |
| WAV | SPA (Dumitrescu–Wu–Wang en conjuntos de traza de Ker) por canal en prefijos 1 %…100 % (`p̂ ≥ STEGO_WAV_RATE`, 0.08); **se abstiene** si la traza 0 tiene < 20 000 pares o < 10 % | datos tras el RIFF, chunks fuera de la lista, LIST/id3/bext > 64 KB, JUNK/PAD con datos |
| MP3 | — (*stretch*: MP3Stego vía `part2_3_length`) | bytes fuera de las tramas (salvo última trama truncada), bits private/copyright/original que cambian entre tramas, GEOB, PRIV > 1 KB, frames desconocidos, etiquetas > 64 KB; carátula → su analizador |
| MP4 | — (el flujo de video no se analiza) | datos tras la última caja, cajas de nivel superior desconocidas, udta/meta/uuid > 64 KB, free/skip con > 1 KB distinto de cero, > 4 KB del `mdat` sin paquete (ffprobe), flujos extra |
| PDF | — | > 2 bytes tras `%%EOF`, objetos huérfanos > 1 KB, Info + XMP > 64 KB · **activo:** JavaScript, acciones Launch/Submit/ImportData/GoToE/GoToR, adjuntos, XFA, multimedia |
| DOCX | — | bytes fuera de las entradas del ZIP, comentario, campos extra desconocidos, partes sin relación, `w:vanish` con texto, metadatos personalizados (+ `w:docVars`) > 64 KB; imágenes → su analizador · **activo:** macros, OLE, ActiveX, `embeddings/`, relaciones externas que no son hipervínculos |
| TXT | — | caracteres invisibles (Cf, salvo ZWJ en emojis y BOM inicial), selectores de variación encadenados, tabulaciones finales o > `STEGO_TXT_TRAILING` espacios finales, palabras con alfabetos mezclados |

## Valores medidos en los prototipos
PNG (2026-10-13, imágenes sintéticas "fotográficas"):
| Imagen | chi² p | RS p̂ |
|---|---|---|
| Limpia (3 semillas) | 0.33–0.38 | 0.002–0.013 |
| LSB secuencial 5 % | 0.993–0.999 | 0.04–0.05 |
| LSB secuencial 10 % | 0.9994–0.9999 | 0.094–0.098 |
| LSB aleatorio 10 % | 0.59–0.69 | 0.11–0.12 |
| LSB aleatorio 50 % | 0.994–0.998 | 0.51–0.54 |
| LSB aleatorio 100 % | 1.0 | 1.0 (¡0.0 en una semilla: RS degenera cerca del 100 %; lo cubre chi²!) |
| Captura con colores planos | 0.0 | 0.0 |

WAV (2026-10-19, voz sintética de `shared.testing.natural_audio`, regla de abstención activa):
| Señal | SPA p̂ |
|---|---|
| Limpia (20 casos de 10 s, mono y estéreo) | ≤ 0.040 |
| LSB aleatorio 10 % | 0.081–0.140 |
| LSB secuencial 10 % | mediana 0.39 (el prefijo lo concentra); mínimo 0.065 en audios de 5 s |
| LSB 100 % | ~0.96, pero **degenera a 0.0** en algunos casos (como RS) |
| Ruido fuerte o música a volumen alto | `None` (no concluyente): lo cubre la sanitización |

Chi² no sirve en audio de 16 bits: con 65 536 valores el histograma es demasiado suave y da p ≈ 1 en audio limpio.

## Sanitización y por qué existe `clean_sha256`
- PNG: XOR del plano LSB con bits aleatorios y recodificación sin chunks auxiliares; conserva el alfa. WAV: lo mismo con el LSB de cada muestra (−96 dB).
- JPEG: orientación EXIF aplicada y recodificación RGB q=90; GIF: recuantización de cada cuadro. En ambos hay que vaciar `image.info` antes de guardar: `convert()` lo copia y Pillow volvería a escribir el comentario.
- MP3: recodificación con LAME sin etiquetas. MP4: remultiplexado (`-c copy`) sin metadatos; el flujo de video no se toca (limitación declarada).
- PDF: reescritura completa con pikepdf, sin Info ni XMP. DOCX: ZIP reconstruido con las partes alcanzables, sin texto oculto, `w:docVars` ni metadatos; sus imágenes se sanitizan con su formato. TXT: `shared.text.clean`.
- Un archivo con el LSB aleatorizado es estadísticamente igual a uno con LSB embebido al 100 % (chi² = 1.0). Por eso `media` guarda `clean_sha256` y no vuelve a analizar sus propias salidas. En PNG también se probaron como alternativas poner el LSB en cero (lo marca RS = 0.19), recodificar como JPEG (chi² 0.89–0.96) y redimensionar (chi² 0.997).

## ffmpeg
Solo a través de `media_svc/ffmpeg.py`: demuxer forzado (`-f mp3`/`-f mp4`), `-protocol_whitelist file`, sin shell, `prlimit` (2 GiB, 120 s de CPU) en Linux y timeout. Nunca autodetección de formato.

## Calibración con archivos reales
1. Copia ≥ 30 imágenes limpias (fotos de celular, capturas) y ≥ 20 grabaciones WAV (voz y música) en `services/media/tools/calibracion/` (gitignored).
2. `python services/media/tools/stego_lab.py calibrate services/media/tools/calibracion`
3. Elige umbrales con FPR ≤ 5 % y TPR máxima para "secuencial 10 %". Configúralos con `STEGO_CHI2_P` / `STEGO_RS_RATE` / `STEGO_WAV_RATE` en `deploy/docker-compose.yml` y anota la tabla en el informe.
4. Herramientas reales para el informe: OpenStego (PNG), steghide (JPEG, WAV), MP3Stego, StegCloak (texto) y `copy /b` o `cat`. `stego_lab.py append` y `hide-text` reproducen los casos estructurales.

## Agregar un formato
1. Módulo `media_svc/formats/<formato>.py` con `detect`, `validate`, `analyze` y `sanitize` como funciones de módulo, y `FORMAT = Format(...)`.
2. Su entrada en `FORMATS` (`media_svc/formats/__init__.py`), **antes de TXT**; si es una imagen, también en `IMAGES`.
3. El tope de su categoría en `Settings.max_bytes_<categoría>` y el MIME en `frontend/src/lib/files.ts`.
4. Tests: uno limpio, uno por cada hallazgo, uno inválido y uno de sanitización (la salida no debe tener hallazgos estructurales). Muestras generadas en el archivo de pruebas del formato (las compartidas, en `tests/samples.py`). Actualizar R6/R9 en la trazabilidad.
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
2. chat: ECDH efímero, `salt` de 32 B, `K = HKDF-SHA256(shared, salt, info="secure-chat/v1|{room_id}|{session_id}", 32)`.
3. chat firma `T = "secure-chat/v1/hello|{room}|{session}|{client_pub}|{server_pub}|{salt}"` con ECDSA P-256/SHA-256 (firma P1363 `r‖s`, 64 B) y responde `{"t":"hello","pub","salt","sig"}`.
4. El cliente verifica `sig` sobre `T` reconstruida con **su** `client_pub`, usando `/chat-key.json` (lo sirve el gateway). Si falla → cierra con 4400.

## Tramas
- `{"seq","n","c"}`: AES-256-GCM, nonce aleatorio de 12 B, tag de 16 B al final de `c`. AAD `v1|{room}|{session}|{seq}|{c2s|s2c}`; en `s2c`, la sesión es la del destinatario.
- `seq` empieza en 1 por conexión y dirección, y es estrictamente creciente.
- El payload es JSON compacto (`separators=(",", ":")`, `ensure_ascii=False`), igual que `JSON.stringify`.
- Códigos de cierre: 4400 malformada, tag o handshake · 4401 sesión terminada · 4403 origin, modo o archivo ajeno · 4408 replay · 4409 reemplazada · 4410 inactividad · 4413 grande · 4429 rate.

## Vectores
`docs/crypto-vectors.json` se regenera con `python services/shared/tools/gen_crypto_vectors.py`. Lo verifican `services/shared/tests/test_vectors.py` y `frontend/src/lib/crypto.test.ts`. Si cambias el protocolo, regenera y deja ambos tests en verde.

## Claves y rotación
| Clave | Dónde | Rotación |
|---|---|---|
| `kek_auth_v{n}` | auth (TOTP) | montar v{n+1}, `CURRENT_KEK_VERSION`, `python -m auth_svc.rotate_kek` |
| `kek_chat_v{n}` | chat (DEK de salas) | igual + `python -m chat_svc.rotate kek` |
| DEK de una sala | `room_keys` (chat) | `python -m chat_svc.rotate room <room_id>` |
| `chat_sign_key` | chat; pública en `deploy/public/chat-key.json` | `python deploy/gen_secrets.py --rotate chat_sign_key` + reiniciar chat y el gateway |
| `svc_token_<x>` | dueño; hash en los receptores | `--rotate svc_token_<x>` + reiniciar `<x>` y sus receptores |
```

`.claude/agents/security-auditor.md`:
```markdown
---
name: security-auditor
description: Revisor de seguridad de solo lectura. Úsalo antes de cerrar una tarea o un PR para contrastar los cambios con los riesgos R1–R17, OWASP Top 10 y el modelo de confianza entre microservicios.
tools: Read, Grep, Glob, Bash
---
Eres el auditor de seguridad del proyecto "Salas de Chat Seguras" (curso Software Seguro). Solo lees; nunca editas archivos.

Antes de opinar, lee:
- `docs/specs/2026-10-12-chat-seguro-design.md` §4.3 (modelo de confianza), §10–§14;
- `.claude/rules/security.md` y `.claude/rules/microservices.md`;
- `docs/trazabilidad-riesgos.md`.

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

Formato de salida: una lista ordenada por severidad (Crítica, Alta, Media, Baja). Cada ítem lleva `archivo:línea`, riesgo afectado (R1–R17 u OWASP A0x), qué falla y la corrección concreta. Si no hay hallazgos, dilo explícitamente e indica qué revisaste.
```

- [ ] **Step 7: Tabla de trazabilidad inicial**

`docs/trazabilidad-riesgos.md`:
```markdown
# Trazabilidad de riesgos → controles → pruebas

Fuente de riesgos: Tarea 2 (Tablas 1–4) + R16 y R17 (spec §16.3). Cada tarea del plan actualiza su fila. "Implementado" exige un test en verde.

| R | Riesgo | Control (Tabla 3 / spec) | Servicio / archivos | Tests | Estado |
|---|---|---|---|---|---|
| R1 | Claves de sala en texto plano | Argon2id con sal única | rooms | — | Pendiente |
| R2 | Claves criptográficas en el código fuente | Docker secrets, KEK/DEK, rotación | shared, auth, chat | — | Pendiente |
| R3 | Manipulación de registros de auditoría | Servicio audit, rol solo INSERT/SELECT, cadena SHA-256 | audit | — | Pendiente |
| R4 | Fuerza bruta contra el admin | Bloqueo + retraso progresivo + TOTP | auth | — | Pendiente |
| R5 | Endpoints admin sin verificación de rol | `auth_request` + `require_admin` en cada servicio | gateway, rooms, media, audit | — | Pendiente |
| R6 | Archivos con esteganografía (9 formatos) | chi²/RS (PNG), SPA (WAV), estructura por formato, caracteres invisibles + cuarentena + sanitización | media, shared, chat | — | Pendiente |
| R7 | WebSocket sin cifrar | TLS 1.3, `wss://`, Origin, hello firmado + AES-GCM | gateway, chat | — | Pendiente |
| R8 | Fuerza bruta de claves de sala | Rate limit usuario/IP/dispositivo/sala + política de clave | rooms | — | Pendiente |
| R9 | Archivos maliciosos | Lista blanca por firma, topes por categoría, validación por formato (bombas de píxeles y ZIP), rechazo de contenido activo, ClamAV | media | — | Pendiente |
| R10 | Agotamiento de conexiones | Rate limit Nginx + token bucket + tamaño de trama | gateway, chat | — | Pendiente |
| R11 | Credenciales de BD con privilegios excesivos | Rol `<svc>_app` sin DDL, una BD por servicio | todos | — | Pendiente |
| R12 | Archivos accesibles sin autorización | URL firmada + pertenencia a la sala | media | — | Pendiente |
| R13 | Sesiones simultáneas de una cuenta | Índices únicos parciales (sesión de usuario y de sala) + cookie de dispositivo + inactividad | auth, rooms | — | Pendiente |
| R14 | Mensajes inyectados en otra sala | Identidad desde la sesión, AAD, anti-replay | chat | — | Pendiente |
| R15 | Cupo superado por concurrencia | `UPDATE … WHERE current < max` + `CHECK` | rooms | — | Pendiente |
| R16 | Suplantación entre microservicios | Token por servicio con hash, allowlist, gateway sobrescribe identidad | shared, todos | — | Pendiente |
| R17 | Ataques automatizados a contraseñas de usuarios | Argon2id, bloqueo por cuenta e IP con retraso, política de contraseña, rate limit de registro, error genérico | auth | — | Pendiente |

## Verificación manual (evidencia para el informe)
| Prueba | Comando | Resultado esperado | Fecha / resultado |
|---|---|---|---|
| TLS 1.2 rechazado | `curl --tlsv1.2 --tls-max 1.2 https://localhost/` | error de handshake | — |
| http → https | `curl -I http://localhost/ws` | `301` | — |
| /internal no enrutado | `curl https://localhost/internal/verify-admin` | `404` JSON | — |
```

- [ ] **Step 8: Escribir `CLAUDE.md`**

`CLAUDE.md`:
````markdown
# Salas de Chat Seguras — contexto del proyecto

Proyecto integrador de **Software Seguro**: salas de chat con **microservicios**. El objetivo es demostrar con pruebas los tratamientos de riesgo del SGSI (Tarea 2) más R16 (suplantación entre microservicios) y R17 (ataques a contraseñas de usuarios). Equipo: Manangón, Díaz, Cedeño. Plazo: 13 oct – 2 nov 2026.

- **Spec (fuente de verdad):** `docs/specs/2026-10-12-chat-seguro-design.md`
- **Plan:** `docs/plans/2026-10-13-00-indice.md` (+ un archivo por subsistema)
- **Riesgos → controles → tests:** `docs/trazabilidad-riesgos.md`
- **Documentos académicos:** `Documentación/` (no tocar sin que lo pidan)

## Arquitectura
| Pieza | Qué hace | BD |
|---|---|---|
| gateway (Nginx) | TLS 1.3, CSP/HSTS, rate limit, `auth_request`, SPA, `/chat-key.json` | — |
| auth | Admin con Argon2id + TOTP; cuentas de usuario con sesión única por dispositivo; `verify-admin` y `verify-user` | auth |
| rooms | Salas, ingreso con cuenta, cupo atómico, una sesión de sala por usuario, sesiones; `GET /internal/verify-session` | rooms |
| chat | WebSocket: hello firmado (ECDSA) + ECDH → AES-256-GCM por conexión; limpia caracteres invisibles; mensajes cifrados en reposo | chat |
| media | 9 formatos (imagen, audio, video, documento, texto): firma → validación → ClamAV → estegoanálisis por formato → cuarentena, rechazo o sanitización; URL firmadas | media |
| audit | Log encadenado con SHA-256; su rol solo hace INSERT/SELECT | audit |

Confianza: el gateway sobrescribe `X-Admin-*`, `X-User-*` y `X-Session-*`. Cada servicio exige `X-Service-Token` (guarda solo hashes) y acepta esas cabeceras únicamente si el llamador es `gateway`. Detalle en `.claude/rules/microservices.md`.

## Mapa del repo
```
services/shared   librería común (secrets, crypto, passwords, ratelimit, service_auth, identity, audit_client, web, text, testing)
services/<svc>    <svc>_svc/ (código) · migrations/ · tests/ · pyproject.toml · requirements.lock
services/Dockerfile   plantilla única (ARG SERVICE) · services/lock.sh
gateway/          nginx.conf · snippets/ · Dockerfile (compila la SPA)
frontend/         React + Vite + TS (src/lib/crypto.ts, ws.ts, api.ts; src/pages/)
e2e/              pruebas contra el stack completo vía https://localhost
deploy/           docker-compose.yml · docker-compose.test.yml · gen_secrets.py · postgres/init.sh
docs/             spec, planes, trazabilidad, vectores cripto, despliegue
```

## Comandos
Preparación (una vez): `py -3.13 -m venv .venv` (macOS/Linux: `python3.13 -m venv .venv`), activar e instalar:
```bash
pip install -e "services/shared[dev]" -e services/audit -e services/auth -e services/rooms -e services/chat -e services/media
```
| Tarea | Comando |
|---|---|
| BD de pruebas | `docker compose -f deploy/docker-compose.test.yml up -d` |
| Tests de un servicio | `pytest services/<svc>` (MP3/MP4 de `media` necesitan ffmpeg en el PATH; ClamAV real: levantar el perfil `clamav` y `pytest services/media -m clamav`) |
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
- macOS/Linux: si el hook falla porque no encuentra `python`, activa el `.venv` antes de abrir Claude Code.

## Estado actual
Actualizar al cerrar cada archivo del plan.
- [ ] 01 Fundaciones · [ ] 02 Audit · [ ] 03 Auth · [ ] 04 Gateway · [ ] 05 Rooms · [ ] 06 Chat · [ ] 07 Media · [ ] 08 Frontend · [ ] 09 E2E y cierre
````

- [ ] **Step 9: Verificar formato y commit**

Run: `python .claude/hooks/guard.py --self-test && python -c "import json; json.load(open('.claude/settings.json', encoding='utf-8')); print('settings OK')"`
Expected: `guard.py: autoprueba OK` y `settings OK`

```bash
git add .gitignore .gitattributes .dockerignore ruff.toml CLAUDE.md .claude docs/trazabilidad-riesgos.md
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


# --- URLs firmadas (spec §9.7) --------------------------------------------------
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
"""Argon2id para contraseñas (admins y usuarios) y claves de sala (riesgos 1, 4 y 17, spec §11.1).

Perfil RFC 9106 de baja memoria (t=3, m=64 MiB, p=4), el predeterminado de argon2-cffi.
"""

import threading

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from starlette.concurrency import run_in_threadpool

_hasher = PasswordHasher()
# ponytail: tope global de 4 cálculos simultáneos (4 × 64 MiB) para que un ataque de registros,
# logins o ingresos masivos no agote la RAM; súbelo si el host tiene memoria de sobra.
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
"""Límites de intentos fallidos (spec §9.1–§9.3) y token bucket del WebSocket (spec §9.5)."""

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
- Create: `services/shared/shared/testing.py` (cabeceras, `ServiceAuth` de prueba y `Recorder`; FND-5 agrega lo de BD)
- Test: `services/shared/tests/test_r16_service_auth.py`

**Interfaces:**
- Consumes: `shared.crypto.sha256`, `shared.crypto.b64e` (FND-2).
- Produces:
  - `shared.service_auth`: `TOKEN_HEADER = "X-Service-Token"`; `ServiceAuth(name, token, callers)` con `from_secrets(name, *, needs_token)` e `identify(token)->str|None`; `ServiceTokenMiddleware`; `allow(*callers)` (dependencia que devuelve el llamador); `ServiceClient(auth, urls, transport=None)` con `post(service, path, *, json, timeout=3.0)->httpx.Response`.
  - `shared.identity`: `AdminIdentity(admin_id, username)`, `UserIdentity(user_id, username)`, `SessionIdentity(session_id, room_id, alias, mode, user_id)`, `client_ip(conn)`, `encode_alias(alias)`, `require_gateway`, `require_admin`, `require_user`, `require_session`, `session_from_headers(conn)`.
  - `shared.audit_client`: `AuditUnavailable`, `AuditClient(ServiceClient).emit(severity, action, *, actor, target=None, ip=None, details=None, required=False)`.
  - `shared.web`: `ADMIN_COOKIE`, `USER_COOKIE`, `ROOM_COOKIE`, `DEVICE_COOKIE`, `set_cookie(response, name, value, max_age=None)`, `clear_cookie(response, name)`, `create_base_app(*, title, settings, engine, service_auth, audit, lifespan=None)->FastAPI`. La app expone `app.state.settings/engine/service_auth/audit` y `request.state.caller`.
  - `shared.testing`:
    - constantes `ORIGIN`, `TOKENS`, `ROLE_PASSWORD`, `USER_ID`;
    - `service_auth(name, callers)`;
    - cabeceras: `service_headers(name)`, `gateway_headers()`, `admin_headers(admin_id=..., username="root")`, `user_headers(user_id=USER_ID, username="ana")`, `session_headers(session_id, room_id, alias, mode="both", *, user_id=USER_ID)`, `cookie_header(cookies)->dict`;
    - `Recorder(routes=None)` con `.transport`, `.calls`, `.events(action=None)` y `.to(prefix)`.

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
from shared.identity import encode_alias
from shared.service_auth import TOKEN_HEADER, ServiceAuth

ORIGIN = "https://testserver"
ROLE_PASSWORD = "solo-pruebas"
TOKENS = {name: f"token-de-prueba-{name}" for name in ("gateway", "auth", "rooms", "chat", "media")}
USER_ID = "00000000-0000-4000-8000-0000000000aa"  # cuenta de prueba por defecto


def service_auth(name: str, callers: tuple[str, ...]) -> ServiceAuth:
    """ServiceAuth de prueba: token propio de TOKENS y hashes de los llamadores permitidos."""
    return ServiceAuth(
        name, TOKENS.get(name), {caller: sha256(TOKENS[caller].encode()) for caller in callers}
    )


def service_headers(name: str) -> dict:
    return {TOKEN_HEADER: TOKENS[name]}


def gateway_headers() -> dict:
    return {TOKEN_HEADER: TOKENS["gateway"], "origin": ORIGIN}


def admin_headers(admin_id: str = "00000000-0000-4000-8000-0000000000ad", username: str = "root") -> dict:
    return {**gateway_headers(), "X-Admin-Id": admin_id, "X-Admin-User": username}


def user_headers(user_id: str = USER_ID, username: str = "ana") -> dict:
    """La cuenta que verify-user de auth le entrega al gateway (spec §9.2)."""
    return {**gateway_headers(), "X-User-Id": user_id, "X-User-Name": username}


def session_headers(
    session_id: str, room_id: str, alias: str, mode: str = "both", *, user_id: str = USER_ID
) -> dict:
    return {
        **gateway_headers(),
        "X-Session-Id": session_id,
        "X-Room-Id": room_id,
        "X-User-Id": user_id,
        "X-Alias": encode_alias(alias),
        "X-Room-Mode": mode,
    }


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
        body = json.loads(request.content) if request.content else None
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
from dataclasses import asdict
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends, Request, WebSocket
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.websockets import WebSocketDisconnect

from shared import testing
from shared.audit_client import AuditClient
from shared.identity import (
    AdminIdentity,
    SessionIdentity,
    UserIdentity,
    require_admin,
    require_gateway,
    require_session,
    require_user,
)
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
    async def admin(who: AdminIdentity = Depends(require_admin)) -> dict:
        return {"user": who.username}

    @router.get("/api/sesion")
    async def sesion(who: SessionIdentity = Depends(require_session)) -> dict:
        return asdict(who)

    @router.get("/api/usuario")
    async def usuario(who: UserIdentity = Depends(require_user)) -> dict:
        return asdict(who)

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
    assert client.get("/api/admin/x", headers=testing.admin_headers()).json() == {"user": "root"}
    impostor = {**testing.service_headers("chat"), "X-Admin-Id": "x", "X-Admin-User": "root"}
    assert client.get("/api/admin/x", headers=impostor).status_code == 403


def test_alias_con_tildes_viaja_codificado(client):
    headers = testing.session_headers("s1", "r1", "José Ñúñez", "text")
    assert client.get("/api/sesion", headers=headers).json() == {
        "session_id": "s1",
        "room_id": "r1",
        "alias": "José Ñúñez",
        "mode": "text",
        "user_id": testing.USER_ID,
    }


def test_identidad_de_usuario_solo_desde_el_gateway(client):
    assert client.get("/api/usuario", headers=testing.gateway_headers()).status_code == 401
    assert client.get("/api/usuario", headers=testing.user_headers()).json() == {
        "user_id": testing.USER_ID,
        "username": "ana",
    }
    impostor = {**testing.service_headers("chat"), "X-User-Id": "x", "X-User-Name": "ana"}
    assert client.get("/api/usuario", headers=impostor).status_code == 403
    sin_cuenta = {k: v for k, v in testing.session_headers("s1", "r1", "ana").items() if k != "X-User-Id"}
    assert client.get("/api/sesion", headers=sin_cuenta).status_code == 401


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
from urllib.parse import quote, unquote

from fastapi import HTTPException, Request
from starlette.requests import HTTPConnection

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass(frozen=True)
class AdminIdentity:
    admin_id: str
    username: str


@dataclass(frozen=True)
class UserIdentity:
    user_id: str
    username: str


@dataclass(frozen=True)
class SessionIdentity:
    session_id: str
    room_id: str
    alias: str  # el nombre de la cuenta (spec §9.3)
    mode: str
    user_id: str


def client_ip(conn: HTTPConnection) -> str | None:
    """IP del cliente original: uvicorn la toma de X-Forwarded-For, que el gateway sobrescribe."""
    return conn.client.host if conn.client else None


def encode_alias(alias: str) -> str:
    """Las cabeceras HTTP son latin-1: el alias (UTF-8) viaja percent-encoded."""
    return quote(alias, safe="")


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


async def require_admin(request: Request) -> AdminIdentity:
    await require_gateway(request)
    admin_id, username = request.headers.get("x-admin-id"), request.headers.get("x-admin-user")
    if not admin_id or not username:
        raise HTTPException(401, "no autenticado")
    return AdminIdentity(admin_id, username)


async def require_user(request: Request) -> UserIdentity:
    """Cuenta de usuario verificada por auth (verify-user) y propagada por el gateway (spec §9.2)."""
    await require_gateway(request)
    user_id, username = request.headers.get("x-user-id"), request.headers.get("x-user-name")
    if not user_id or not username:
        raise HTTPException(401, "no autenticado")
    return UserIdentity(user_id, username)


def session_from_headers(conn: HTTPConnection) -> SessionIdentity | None:
    headers = conn.headers
    values = (
        headers.get("x-session-id"),
        headers.get("x-room-id"),
        headers.get("x-alias"),
        headers.get("x-room-mode"),
        headers.get("x-user-id"),
    )
    if not all(values):
        return None
    session_id, room_id, alias, mode, user_id = values
    return SessionIdentity(session_id, room_id, unquote(alias), mode, user_id)


async def require_session(request: Request) -> SessionIdentity:
    await require_gateway(request)
    who = session_from_headers(request)
    if who is None:
        raise HTTPException(401, "no autenticado")
    return who
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

    async def post(self, service: str, path: str, *, json: dict, timeout: float = 3.0) -> httpx.Response:
        # ponytail: un AsyncClient por llamada (sin pool compartido); basta en una red interna a esta escala.
        async with httpx.AsyncClient(transport=self.transport, timeout=timeout) as client:
            return await client.post(
                self.urls[service] + path, json=json, headers={TOKEN_HEADER: self.auth.token or ""}
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

ADMIN_COOKIE = "__Host-admin"
USER_COOKIE = "__Host-user"
ROOM_COOKIE = "__Host-room"
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

- [ ] **Step 6: Trazabilidad y commit**

En `docs/trazabilidad-riesgos.md`, fila **R16**:
- *Servicio / archivos:* `services/shared/shared/service_auth.py`, `identity.py`, `web.py`
- *Tests:* `services/shared/tests/test_r16_service_auth.py`
- *Estado:* `En progreso (falta e2e del gateway)`

```bash
git add services/shared docs/trazabilidad-riesgos.md
git commit -m "feat(shared): token por servicio, identidad del gateway, auditoría con fallback y base web (R16)"
```

---

### Task FND-5: Utilidades de BD para pruebas, migraciones comunes e imágenes y audio sintéticos

**Files:**
- Modify: `services/shared/shared/testing.py` (agregar lo de BD, imágenes y audio)
- Create: `services/shared/shared/migrations.py`
- Create: `deploy/docker-compose.test.yml`
- Test: `services/shared/tests/test_testing.py`

**Interfaces:**
- Consumes: `shared.secrets.db_url` (FND-2).
- Produces:
  - `shared.migrations.run(service)`.
  - `shared.testing`:
    - BD: `PG_HOST`, `PG_PORT`, `FOREIGN_DB`, `dsn(user, password, database, driver="postgresql+asyncpg")`, `db_urls(service)->(owner_url, app_url)`, `prepare_database(service, service_dir)`, `run(coro)`, `sql(url, statement, **params)->list[dict]`, `with_conn(url, fn, *args)`, `truncate_all(owner_url)`, `assert_least_privilege(app_url, table)`;
    - imágenes: `natural_image(seed=0, size=256)`, `embed_lsb(values, rate, mode="seq", seed=1)` (píxeles uint8 o muestras int16), `png_bytes(pixels, **kw)`, `jpeg_bytes(pixels, quality=90, **kw)`;
    - audio (sin ffmpeg): `natural_audio(seed=0, seconds=10.0, rate=44100, channels=1)` (int16, forma `(n, canales)`), `wav_bytes(samples, rate=44100)`, `mp3_bytes(frames=40)` (silencio MPEG-1 Layer III armado a mano).

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


def test_audio_sintetico():
    samples = testing.natural_audio(0, seconds=1, channels=2)
    assert samples.shape == (44100, 2)
    assert samples.dtype.name == "int16"
    stego = testing.embed_lsb(samples, 0.5, "random")
    assert ((stego >> 1) == (samples >> 1)).all()  # en int16 tampoco se tocan los bits altos
    assert (stego != samples).any()
    wav = testing.wav_bytes(samples)
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    assert len(wav) == 44 + samples.size * 2
    assert len(testing.mp3_bytes(3)) == 3 * 417 and testing.mp3_bytes(1)[:4] == b"\xff\xfb\x90\xc0"
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


# --- Imágenes y audio sintéticos (requieren numpy y Pillow, extra [dev]) ------------
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


def embed_lsb(values, rate: float, mode: str = "seq", seed: int = 1):
    """LSB replacement con bits aleatorios (simula un mensaje cifrado) en píxeles uint8 o muestras
    int16. mode: 'seq' | 'random'."""
    import numpy as np

    flat = values.reshape(-1).copy()
    count = int(len(flat) * rate)
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, count, dtype=np.uint8).astype(flat.dtype)
    index = np.arange(count) if mode == "seq" else rng.choice(len(flat), count, replace=False)
    flat[index] = flat[index] - (flat[index] & 1) + bits  # sin máscara de 8 bits: vale para int16
    return flat.reshape(values.shape)


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


def natural_audio(seed: int = 0, seconds: float = 10.0, rate: int = 44100, channels: int = 1):
    """Voz sintética de 16 bits: tonos con sílabas y pausas + ruido de fondo, a nivel de grabación.

    Es suave a escala del LSB, así que SPA resulta concluyente. Prototipo 2026-10-19: limpio
    p̂ ≤ 0.04; LSB al 10 % (secuencial o aleatorio) p̂ ≥ 0.10 con 10 s de audio.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * rate)) / rate
    columns = []
    for channel in range(channels):
        signal = np.zeros_like(t)
        for frequency, amplitude in ((150, 0.5), (300, 0.3), (450, 0.15), (900, 0.05)):
            signal += amplitude * np.sin(
                2 * np.pi * (frequency + 3 * channel) * t + rng.uniform(0, 2 * np.pi)
            )
        syllables = np.clip(np.sin(2 * np.pi * 1.3 * t + rng.uniform(0, 6)), 0, None) ** 2
        columns.append(signal * syllables + rng.normal(0, 0.002, t.shape))
    return np.clip(np.stack(columns, axis=-1) * 1500, -32768, 32767).round().astype(np.int16)


def wav_bytes(samples, rate: int = 44100) -> bytes:
    """WAV PCM de 16 bits con solo los chunks fmt y data."""
    import wave

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(samples.shape[1] if samples.ndim == 2 else 1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(samples.astype("<i2").tobytes())
    return buffer.getvalue()


def mp3_bytes(frames: int = 40) -> bytes:
    """MP3 de silencio sin ffmpeg: tramas MPEG-1 Layer III mono de 128 kbps a 44.1 kHz.

    Cabecera FF FB 90 C0 (sin CRC ni relleno, mono) + información lateral en cero
    (part2_3_length = 0: ningún coeficiente) → tramas de 417 bytes que decodifican a silencio.
    """
    return (b"\xff\xfb\x90\xc0" + bytes(413)) * frames
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
git commit -m "feat(shared): utilidades de BD de prueba, migraciones comunes e imágenes y audio sintéticos"
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
  - `deploy/secrets/*`: los 26 archivos de la spec §11.1, entre ellos `gateway_token.conf`.
  - `deploy/public/chat-key.json` con `{"kid", "pub"}`.
  - Imagen por servicio: `docker build --build-arg SERVICE=<svc> -f services/Dockerfile .` (`media` suma `--build-arg APT_PACKAGES=ffmpeg`).
  - Compose con `db`, las redes y las anclas `x-python-service` / `x-migrate`, que las tareas de cada servicio reutilizan.

- [ ] **Step 1: Test del generador de secretos (falla)**

`services/shared/tests/test_gen_secrets.py`:
```python
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from shared.crypto import b64d, b64e, load_signing_key, public_bytes

SCRIPT = Path(__file__).resolve().parents[3] / "deploy" / "gen_secrets.py"


def gen(root: Path, *args: str) -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--dir", str(root), *args], check=True, capture_output=True)


def test_genera_todo_y_no_sobrescribe(tmp_path):
    gen(tmp_path)
    secrets = tmp_path / "secrets"
    assert len(list(secrets.iterdir())) == 26
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
from cryptography.hazmat.primitives.asymmetric import ec

SERVICES = ("auth", "rooms", "chat", "media", "audit")
CALLERS = ("gateway", "auth", "rooms", "chat", "media")
RANDOM = (
    "kek_auth_v1",
    "kek_chat_v1",
    "url_signing_key",
    "postgres_password",
    *(f"db_{svc}_{role}" for svc in SERVICES for role in ("owner", "app")),
    *(f"svc_token_{caller}" for caller in CALLERS),
)


def new_signing_key() -> str:
    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


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
# Paquetes del sistema que solo necesita un servicio (media: ffmpeg para MP3 y MP4, spec §12).
ARG APT_PACKAGES=""
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SERVICE=${SERVICE}
RUN if [ -n "$APT_PACKAGES" ]; then \
      apt-get update && apt-get install -y --no-install-recommends $APT_PACKAGES \
      && rm -rf /var/lib/apt/lists/*; \
    fi \
 && useradd --uid 10001 --no-create-home app \
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
CMD exec uvicorn --factory "${SERVICE}_svc.main:create_app" --host 0.0.0.0 --port 8000 \
    --proxy-headers --forwarded-allow-ips '*' --ws-ping-interval 30 --ws-ping-timeout 30 \
    --ws-max-size 65536 --no-server-header
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
  chat_sign_key: {file: ./secrets/chat_sign_key}
  url_signing_key: {file: ./secrets/url_signing_key}
  gateway_token_conf: {file: ./secrets/gateway_token.conf}
  svc_token_auth: {file: ./secrets/svc_token_auth}
  svc_token_rooms: {file: ./secrets/svc_token_rooms}
  svc_token_chat: {file: ./secrets/svc_token_chat}
  svc_token_media: {file: ./secrets/svc_token_media}
  svc_hash_gateway: {file: ./secrets/svc_hash_gateway}
  svc_hash_auth: {file: ./secrets/svc_hash_auth}
  svc_hash_rooms: {file: ./secrets/svc_hash_rooms}
  svc_hash_chat: {file: ./secrets/svc_hash_chat}
  svc_hash_media: {file: ./secrets/svc_hash_media}
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
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `services/shared` (FND-2…FND-6).
- Produces: el job `services` con matriz `svc`. Cada tarea `*-1` de un servicio agrega su nombre a la matriz, y FE-1 agrega el job `frontend`.

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
      - name: ffmpeg (solo media)
        if: matrix.svc == 'media'
        run: sudo apt-get update && sudo apt-get install -y ffmpeg
      - name: Instalar
        run: |
          python -m pip install --upgrade pip
          if [ "${{ matrix.svc }}" != "shared" ]; then pip install -r "services/${{ matrix.svc }}/requirements.lock"; fi
          pip install -e "services/shared[dev]"
          if [ "${{ matrix.svc }}" != "shared" ]; then pip install -e "services/${{ matrix.svc }}"; fi
      - name: Ruff
        run: ruff check "services/${{ matrix.svc }}" && ruff format --check "services/${{ matrix.svc }}"
      - name: Pruebas
        run: pytest "services/${{ matrix.svc }}" -m "not clamav"
      - name: Bandit
        # -ll: severidad media o mayor. Se excluyen las pruebas, las herramientas y el soporte de pruebas.
        run: bandit -q -ll -r "services/${{ matrix.svc }}" -x "services/${{ matrix.svc }}/tests,services/${{ matrix.svc }}/tools,services/shared/shared/testing.py"
      - name: pip-audit
        run: pip-audit --skip-editable
```

- [ ] **Step 2: Formatear y verificar en local**

Run: `ruff format services/shared deploy && ruff check --fix services/shared deploy && pytest services/shared -q`
Expected: sin errores de ruff y todos los tests en verde.

- [ ] **Step 3: Commit y push**

```bash
git add .github/workflows/ci.yml services/shared deploy
git commit -m "ci: lint, pruebas, bandit y pip-audit de los servicios"
git push -u origin feat/arquitectura-chat-seguro
```
Expected: el workflow `ci` pasa en GitHub (job `services (shared)`).

---

### Task FND-8: Caracteres invisibles y otros canales ocultos en texto (`shared.text`, R6)

**Files:**
- Create: `services/shared/shared/text.py`
- Test: `services/shared/tests/test_r06_texto.py`

**Interfaces:**
- Consumes: nada (solo `unicodedata` y `re` de la stdlib).
- Produces: `shared.text.scan(text) -> dict[str, int]` (`invisible`, `extra_selectors`, `trailing_tabs`, `trailing_spaces`, `mixed_script_words`) y `shared.text.clean(text) -> (texto_limpio, quitados)`. Lo usan `media` para los archivos TXT (MED-10) y `chat` para los mensajes (CHAT-3).

- [ ] **Step 1: Tests (fallan)**

`services/shared/tests/test_r06_texto.py`:
```python
import pytest

from shared.text import clean, scan

STEGCLOAK = "hola‌‍⁡⁢⁣⁤ mundo"  # los 6 caracteres que usa StegCloak


def test_texto_normal_sin_hallazgos():
    texto = "Hola, ¿qué tal? Ñandú, acentos y emojis 🎉 ❤️ 👍🏽 👨‍👩‍👧\n\tcon sangría\n"
    assert scan(texto) == {
        "invisible": 0,
        "extra_selectors": 0,
        "trailing_tabs": 0,
        "trailing_spaces": 0,
        "mixed_script_words": 0,
    }
    assert clean(texto) == (texto, 0)


def test_r06_caracteres_de_ancho_cero():
    assert scan(STEGCLOAK)["invisible"] == 6
    assert clean(STEGCLOAK) == ("hola mundo", 6)


@pytest.mark.parametrize(
    "oculto",
    [
        "a‮b",  # control bidi (Trojan Source)
        "a\U000e0041\U000e0042b",  # etiquetas Unicode (ASCII smuggling)
        "a­b",  # guion suave
        "a﻿b",  # BOM en medio del texto
        "aㅤb",  # relleno Hangul (no es Cf)
    ],
)
def test_r06_otros_invisibles(oculto):
    assert scan(oculto)["invisible"] >= 1
    assert clean(oculto)[0] == "ab"


def test_bom_inicial_no_cuenta_pero_se_quita():
    assert scan("﻿hola")["invisible"] == 0
    assert clean("﻿hola") == ("hola", 1)


def test_r06_selectores_de_variacion_encadenados():
    oculto = "😀" + "︁︂" + "\U000e0101" * 5
    assert scan(oculto)["extra_selectors"] == 6
    assert clean(oculto) == ("😀︁", 6)


def test_r06_espacios_al_final_de_linea():
    snow = "linea uno \t \nlinea dos  \t\r\nfin"
    found = scan(snow)
    assert (found["trailing_tabs"], found["trailing_spaces"]) == (2, 4)
    assert clean(snow) == ("linea uno\nlinea dos\nfin", 6)


def test_r06_homoglifos():
    assert scan("pаypal")["mixed_script_words"] == 1  # 'а' cirílica
    assert scan("Ελληνικά y español")["mixed_script_words"] == 0  # palabras de un solo alfabeto
```

Run: `pytest services/shared/tests/test_r06_texto.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.text'`

- [ ] **Step 2: Implementar `shared/text.py`**

`services/shared/shared/text.py`:
```python
"""Canales ocultos en texto (spec §12.8): caracteres invisibles, selectores de variación,
espacios al final de línea y homoglifos. Lo usan media (archivos TXT) y chat (mensajes)."""

import re
import unicodedata

BOM = "﻿"
ZWJ = "‍"
# Invisibles que no son de categoría Cf pero también sirven para esconder datos.
EXTRA_INVISIBLE = frozenset("͏ᅟᅠㅤﾠ")
SCRIPTS = ("LATIN", "CYRILLIC", "GREEK")
WORD = re.compile(r"[^\W\d_]+")


def is_variation_selector(char: str) -> bool:
    code = ord(char)
    return 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF


def is_invisible(char: str) -> bool:
    """Categoría Cf (ancho cero, bidi, etiquetas, guion suave, BOM) y rellenos invisibles."""
    return (
        unicodedata.category(char) == "Cf"
        or char in EXTRA_INVISIBLE
        or 0xE0000 <= ord(char) <= 0xE007F
    )


def is_pictographic(char: str) -> bool:
    """Aproximación de Extended_Pictographic por bloques: emoji, símbolos y modificadores de tono."""
    code = ord(char)
    return (
        0x1F000 <= code <= 0x1FAFF
        or 0x2600 <= code <= 0x27BF
        or 0x2300 <= code <= 0x23FF
        or 0x2B00 <= code <= 0x2BFF
        or code in (0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D, 0x3297, 0x3299)
    )


def _joins_emoji(kept: list[str], text: str, index: int) -> bool:
    """U+200D legítimo: une dos emojis (👨‍👩‍👧), aunque el primero lleve un selector de variación."""
    previous = next((char for char in reversed(kept) if not is_variation_selector(char)), "")
    following = text[index + 1] if index + 1 < len(text) else ""
    return is_pictographic(previous) and is_pictographic(following)


def _filter(text: str) -> tuple[str, int, int]:
    """(texto sin invisibles ni selectores sobrantes, invisibles quitados, selectores quitados)."""
    kept: list[str] = []
    invisible = selectors = 0
    for index, char in enumerate(text):
        if is_variation_selector(char):
            if kept and not is_variation_selector(kept[-1]) and not kept[-1].isspace():
                kept.append(char)  # uno tras un carácter base: uso normal (❤️)
            else:
                selectors += 1  # encadenados: bytes "pegados" a un emoji
        elif is_invisible(char):
            if char == ZWJ and _joins_emoji(kept, text, index):
                kept.append(char)
            else:
                invisible += 1
        else:
            kept.append(char)
    return "".join(kept), invisible, selectors


def _scripts(word: str) -> set[str]:
    found = set()
    for char in word:
        name = unicodedata.name(char, "")
        found.update(script for script in SCRIPTS if name.startswith(script))
    return found


def scan(text: str) -> dict[str, int]:
    """Conteos de cada canal. Un BOM al inicio del archivo es normal y no cuenta."""
    body = text.removeprefix(BOM)
    _, invisible, selectors = _filter(body)
    trailing_tabs = trailing_spaces = 0
    for line in body.split("\n"):
        line = line.removesuffix("\r")
        tail = line[len(line.rstrip(" \t")) :]
        trailing_tabs += tail.count("\t")
        trailing_spaces += tail.count(" ")
    return {
        "invisible": invisible,
        "extra_selectors": selectors,
        "trailing_tabs": trailing_tabs,
        "trailing_spaces": trailing_spaces,
        "mixed_script_words": sum(1 for word in WORD.findall(body) if len(_scripts(word)) > 1),
    }


def clean(text: str) -> tuple[str, int]:
    """Quita invisibles, selectores sobrantes y espacios finales; normaliza los saltos a \\n.

    Devuelve el texto limpio y cuántos caracteres se quitaron. Los homoglifos no se corrigen:
    no hay forma de saber qué letra quiso escribir el autor.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    filtered, invisible, selectors = _filter(normalized)
    lines = filtered.split("\n")
    stripped = [line.rstrip(" \t") for line in lines]
    trailing = sum(len(line) - len(kept) for line, kept in zip(lines, stripped, strict=True))
    return "\n".join(stripped), invisible + selectors + trailing
```

Run: `pytest services/shared -q`
Expected: PASS

- [ ] **Step 3: Trazabilidad y commit**

Fila R6: agregar `services/shared/shared/text.py` y `services/shared/tests/test_r06_texto.py`.

```bash
git add services/shared docs/trazabilidad-riesgos.md
git commit -m "feat(shared): detección y limpieza de caracteres invisibles en texto (R6)"
```

Al cerrar este archivo, marca `[x] 01 Fundaciones` en la sección *Estado actual* de `CLAUDE.md`.

---

### Task FND-9: Correlación, registros JSON, métricas y alerta de consumo (RNF-18, RNF-19)

> **Rev. 4.** Tarea nueva: implementa los requisitos no funcionales de monitoreo de la Actividad 3 (spec §21.1) y el alias en la identidad del usuario. Va antes de los servicios; si ya los tienes, después de esta tarea corre sus pruebas (las de auth y rooms se actualizan en ATH-5 y ROOM-1…ROOM-4).

**Files:**
- Create: `services/shared/shared/observability.py`
- Modify: `services/shared/shared/web.py`, `services/shared/shared/audit_client.py`, `services/shared/shared/service_auth.py`, `services/shared/shared/identity.py` (se reemplazan completos), `services/shared/shared/testing.py` (`user_headers`)
- Modify: `services/Dockerfile` (`LOG_FORMAT=json`, `--no-access-log`), `deploy/docker-compose.yml` (límites de CPU y memoria en `x-python-service`)
- Test: `services/shared/tests/test_observabilidad.py`, `services/shared/tests/test_r16_service_auth.py` (se reemplaza: el alias viaja codificado)

**Interfaces:**
- Consumes: `shared.secrets.env` (FND-2), `shared.identity.require_admin` (FND-4).
- Produces:
  - `shared.observability`: `REQUEST_HEADER = "X-Request-ID"`, `REQUEST_ID` (`ContextVar`), `JsonFormatter`, `configure_logging(service)` (solo con `LOG_FORMAT=json`), `Metrics`, `RequestContextMiddleware`, `CgroupReader` y `ResourceMonitor(audit, reader, *, threshold_pct=80, sustain_s=300)`;
  - `create_base_app` agrega el middleware de correlación (el más externo), `app.state.metrics`, `app.state.extra_metrics` (cada servicio puede registrar `async (app) -> dict`), `app.state.monitor` (corre en el ciclo de vida cada `RESOURCE_SAMPLE_S`, 30 s) y `GET /api/admin/metrics` (solo admin);
  - `ServiceClient.post` reenvía `X-Request-ID`; `AuditClient.emit` manda `request_id` y audit lo guarda en `details` (AUD-4);
  - `UserIdentity(user_id, alias)`: `X-User-Name` lleva el alias *percent-encoded*; `testing.user_headers(user_id=USER_ID, alias="ana")`;
  - variables: `LOG_FORMAT`, `RESOURCE_ALERT_PCT` (80), `RESOURCE_ALERT_MIN` (5), `RESOURCE_SAMPLE_S` (30).

- [ ] **Step 1: Tests (fallan)**

`services/shared/tests/test_observabilidad.py`:
```python
import json
import logging
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends, Request
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from shared import testing
from shared.audit_client import AuditClient
from shared.identity import require_gateway
from shared.observability import (
    REQUEST_HEADER,
    CgroupReader,
    JsonFormatter,
    ResourceMonitor,
)
from shared.service_auth import ServiceClient
from shared.web import create_base_app


def build_app(recorder: testing.Recorder):
    auth = testing.service_auth("rooms", ("gateway",))
    peers = ServiceClient(
        auth, {"audit": "http://audit:8000", "chat": "http://chat:8000"}, recorder.transport
    )
    app = create_base_app(
        title="rooms",
        settings=SimpleNamespace(allowed_origins=frozenset({testing.ORIGIN})),
        engine=create_async_engine("postgresql+asyncpg://nadie@127.0.0.1:1/nada"),  # no se usa
        service_auth=auth,
        audit=AuditClient(peers),
    )
    router = APIRouter()

    @router.get("/api/eco", dependencies=[Depends(require_gateway)])
    async def eco(request: Request) -> dict:
        await request.app.state.audit.emit("info", "prueba.eco", actor="system")
        await peers.post("chat", "/internal/algo", json={})
        return {"ok": True}

    app.include_router(router)
    return app


@pytest.fixture
def recorder():
    return testing.Recorder()


@pytest.fixture
def client(recorder):
    return TestClient(build_app(recorder), base_url=testing.ORIGIN)


def test_rnf19_id_de_correlacion_viaja_a_otros_servicios_y_a_la_auditoria(client, recorder):
    r = client.get(
        "/api/eco", headers={**testing.gateway_headers(), REQUEST_HEADER: "abcd1234-req"}
    )
    assert r.headers[REQUEST_HEADER] == "abcd1234-req"
    [event] = recorder.events("prueba.eco")
    assert event["request_id"] == "abcd1234-req"
    assert [c.path for c in recorder.calls] == ["/internal/events", "/internal/algo"]


def test_rnf19_id_ausente_o_raro_se_reemplaza(client):
    nuevo = client.get("/api/eco", headers=testing.gateway_headers()).headers[REQUEST_HEADER]
    raro = client.get(
        "/api/eco", headers={**testing.gateway_headers(), REQUEST_HEADER: "corto"}
    ).headers[REQUEST_HEADER]
    assert len(nuevo) == len(raro) == 32 and nuevo != raro
    assert client.get("/api/eco").headers[REQUEST_HEADER]  # también en un rechazo (sin token)


def test_rnf19_registro_json_con_campos_comunes():
    record = logging.LogRecord("http", logging.INFO, __file__, 1, "GET %s", ("/api/x",), None)
    line = json.loads(JsonFormatter("chat").format(record))
    assert {k: line[k] for k in ("service", "level", "msg")} == {
        "service": "chat",
        "level": "info",
        "msg": "GET /api/x",
    }
    assert line["ts"].endswith("+00:00") and "request_id" in line


def test_rnf19_la_linea_de_acceso_no_lleva_la_query(client, caplog):
    with caplog.at_level(logging.INFO, logger="http"):
        client.get("/api/eco?exp=1&sig=secreta", headers=testing.gateway_headers())
    assert "/api/eco" in caplog.text and "secreta" not in caplog.text


def test_rnf18_metricas_solo_para_el_admin(client):
    client.get("/api/eco", headers=testing.gateway_headers())
    client.get("/api/eco")  # 401 sin token
    assert client.get("/api/admin/metrics", headers=testing.gateway_headers()).status_code == 401
    body = client.get("/api/admin/metrics", headers=testing.admin_headers()).json()
    assert body["service"] == "rooms"
    assert body["statuses"]["200"] == 1 and body["rejections"] >= 2
    assert body["latency_ms"]["p95"] is not None
    assert set(body["resources"]) == {"cpu_pct", "memory_pct"}


def test_rnf18_metricas_propias_del_servicio(recorder):
    app = build_app(recorder)

    async def extra(app) -> dict:
        return {"connections": 3}

    app.state.extra_metrics = extra
    body = TestClient(app, base_url=testing.ORIGIN).get(
        "/api/admin/metrics", headers=testing.admin_headers()
    )
    assert body.json()["extra"] == {"connections": 3}


def test_rnf18_lectura_de_cgroup(tmp_path, monkeypatch):
    (tmp_path / "cpu.max").write_text("50000 100000\n")  # medio CPU
    (tmp_path / "memory.current").write_text("858993459\n")
    (tmp_path / "memory.max").write_text("1073741824\n")
    reader = CgroupReader(tmp_path)
    ticks = iter([100.0, 110.0])
    monkeypatch.setattr("shared.observability.time.monotonic", lambda: next(ticks))
    (tmp_path / "cpu.stat").write_text("usage_usec 1000000\nuser_usec 1\n")
    assert reader.sample() == {"cpu_pct": None, "memory_pct": 80.0}  # la CPU necesita dos lecturas
    (tmp_path / "cpu.stat").write_text("usage_usec 5000000\nuser_usec 1\n")
    assert reader.sample()["cpu_pct"] == 80.0  # 4 s de CPU en 10 s con medio CPU
    assert CgroupReader(tmp_path / "no-existe").sample() == {"cpu_pct": None, "memory_pct": None}


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict]] = []

    async def emit(self, severity, action, *, actor, details=None, **_) -> None:
        self.events.append((severity, action, details))


def test_rnf18_alerta_tras_5_minutos_seguidos_sobre_el_umbral():
    audit, now, usage = FakeAudit(), [0.0], {"cpu_pct": 95.0, "memory_pct": 40.0}
    monitor = ResourceMonitor(
        audit, lambda: dict(usage), threshold_pct=80, sustain_s=300, clock=lambda: now[0]
    )
    for t in (0, 120, 299):
        now[0] = t
        testing.run(monitor.check())
    assert audit.events == []
    for t in (300, 330):  # avisa una sola vez mientras siga alto
        now[0] = t
        testing.run(monitor.check())
    assert [(s, a) for s, a, _ in audit.events] == [("warning", "resource.high")]
    assert audit.events[0][2]["cpu_pct"] == 95.0
    usage["cpu_pct"] = 30.0
    now[0] = 360
    testing.run(monitor.check())  # baja: se rearma
    usage["memory_pct"] = 85.0
    for t in (400, 700):
        now[0] = t
        testing.run(monitor.check())
    assert len(audit.events) == 2
```

Reemplazar `services/shared/tests/test_r16_service_auth.py` por:
```python
import logging
from dataclasses import asdict
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends, Request, WebSocket
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.websockets import WebSocketDisconnect

from shared import testing
from shared.audit_client import AuditClient
from shared.identity import (
    AdminIdentity,
    SessionIdentity,
    UserIdentity,
    require_admin,
    require_gateway,
    require_session,
    require_user,
)
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
    async def admin(who: AdminIdentity = Depends(require_admin)) -> dict:
        return {"user": who.username}

    @router.get("/api/sesion")
    async def sesion(who: SessionIdentity = Depends(require_session)) -> dict:
        return asdict(who)

    @router.get("/api/usuario")
    async def usuario(who: UserIdentity = Depends(require_user)) -> dict:
        return asdict(who)

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
    assert (
        client.post("/internal/solo-chat", headers=testing.service_headers("chat")).status_code
        == 200
    )


def test_identidad_solo_vale_si_la_trae_el_gateway(client):
    assert client.get("/api/admin/x", headers=testing.gateway_headers()).status_code == 401
    assert client.get("/api/admin/x", headers=testing.admin_headers()).json() == {"user": "root"}
    impostor = {**testing.service_headers("chat"), "X-Admin-Id": "x", "X-Admin-User": "root"}
    assert client.get("/api/admin/x", headers=impostor).status_code == 403


def test_alias_con_tildes_viaja_codificado(client):
    headers = testing.session_headers("s1", "r1", "José Ñúñez", "text")
    assert client.get("/api/sesion", headers=headers).json() == {
        "session_id": "s1",
        "room_id": "r1",
        "alias": "José Ñúñez",
        "mode": "text",
        "user_id": testing.USER_ID,
    }


def test_identidad_de_usuario_solo_desde_el_gateway(client):
    assert client.get("/api/usuario", headers=testing.gateway_headers()).status_code == 401
    assert client.get("/api/usuario", headers=testing.user_headers()).json() == {
        "user_id": testing.USER_ID,
        "alias": "ana",
    }
    con_tildes = testing.user_headers(alias="José Ñúñez")
    assert client.get("/api/usuario", headers=con_tildes).json()["alias"] == "José Ñúñez"
    impostor = {**testing.service_headers("chat"), "X-User-Id": "x", "X-User-Name": "ana"}
    assert client.get("/api/usuario", headers=impostor).status_code == 403
    sin_cuenta = {
        k: v for k, v in testing.session_headers("s1", "r1", "ana").items() if k != "X-User-Id"
    }
    assert client.get("/api/sesion", headers=sin_cuenta).status_code == 401


def test_errores_genericos(client):
    assert client.get("/api/falla", headers=testing.gateway_headers()).json() == {
        "error": "error interno"
    }
    r = client.post("/api/publico", json={"n": "x"}, headers=testing.gateway_headers())
    assert (r.status_code, r.json()) == (422, {"error": "datos inválidos"})


def test_evento_obligatorio_sin_audit_da_503():
    client = TestClient(
        build_app(testing.Recorder({"/internal/events": "down"})), base_url=testing.ORIGIN
    )
    r = client.get("/api/obligatorio", headers=testing.gateway_headers())
    assert (r.status_code, r.json()) == (503, {"error": "servicio no disponible"})


def test_evento_no_obligatorio_cae_a_stdout(caplog):
    client = TestClient(
        build_app(testing.Recorder({"/internal/events": "down"})), base_url=testing.ORIGIN
    )
    with caplog.at_level(logging.WARNING, logger="audit"):
        assert client.get("/api/admin/x").status_code == 401  # sin token → evento de rechazo
    assert "AUDIT_FALLBACK" in caplog.text


def test_websocket_sin_token_se_cierra_con_4401(client):
    with pytest.raises(WebSocketDisconnect) as closed:
        with client.websocket_connect("/ws"):
            pass
    assert closed.value.code == 4401
```

Run: `pytest services/shared -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.observability'`

- [ ] **Step 2: `observability.py`**

Decisiones:
- El id de correlación lo genera el gateway (`$request_id`, GW-2). Un servicio acepta el que llega si tiene el formato esperado; si no, crea uno. Viaja en `X-Request-ID` a los demás servicios y queda en cada evento de auditoría.
- Una línea JSON por registro (`ts`, `service`, `level`, `request_id`, `logger`, `msg` y campos extra) y una línea por petición **sin la query**: las URL de descarga llevan su firma ahí.
- CPU y memoria se leen de cgroup v2 dentro del contenedor (sin socket de Docker). Si alguna pasa el 80 % durante 5 minutos seguidos, se emite **una** advertencia `resource.high`, que el panel muestra en ≤ 10 s; se rearma cuando el consumo baja.

`services/shared/shared/observability.py`:
```python
"""Correlación, registros estructurados, métricas y alerta de consumo (spec §21; RNF-18 y RNF-19)."""

import asyncio
import json
import logging
import os
import re
import sys
import time
from collections import Counter, deque
from collections.abc import Callable
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_HEADER = "X-Request-ID"
REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
VALID_ID = re.compile(r"[A-Za-z0-9-]{8,64}")
log = logging.getLogger("http")


def incoming_id(scope: Scope) -> str:
    """El id que puso el gateway ($request_id) o uno nuevo si falta o tiene un formato raro."""
    presented = Headers(scope=scope).get(REQUEST_HEADER)
    return presented if presented and VALID_ID.fullmatch(presented) else uuid4().hex


class JsonFormatter(logging.Formatter):
    """Una línea JSON por registro, con el mismo formato en todos los servicios (RNF-19)."""

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        line = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "service": self.service,
            "level": record.levelname.lower(),
            "request_id": REQUEST_ID.get(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        line.update(getattr(record, "fields", {}))
        if record.exc_info:
            line["exc"] = self.formatException(record.exc_info)
        return json.dumps(line, ensure_ascii=False, default=str)


def configure_logging(service: str) -> None:
    """Con LOG_FORMAT=json (lo pone el Dockerfile) todo sale por stdout como JSON. En las pruebas
    no se toca el logging, para no quitarle sus handlers a pytest."""
    if os.environ.get("LOG_FORMAT") != "json":
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True


class Metrics:
    """Contadores en memoria del proceso; se reinician con el servicio."""

    def __init__(self, window: int = 1000) -> None:
        self.started = time.time()
        self.requests = 0
        self.statuses: Counter[str] = Counter()
        self.latencies: deque[float] = deque(maxlen=window)

    def observe(self, status: int, seconds: float) -> None:
        self.requests += 1
        self.statuses[str(status)] += 1
        self.latencies.append(seconds)

    def snapshot(self) -> dict:
        ordered = sorted(self.latencies)

        def percentile(q: float) -> float | None:
            if not ordered:
                return None
            return round(ordered[min(len(ordered) - 1, int(q * len(ordered)))] * 1000, 2)

        rejected = sum(n for status, n in self.statuses.items() if status.startswith("4"))
        return {
            "uptime_s": int(time.time() - self.started),
            "requests": self.requests,
            "statuses": dict(self.statuses),
            "rejections": rejected,
            "latency_ms": {"p50": percentile(0.50), "p95": percentile(0.95)},
        }


class RequestContextMiddleware:
    """Fija el id de correlación, lo devuelve en la respuesta, mide la latencia y deja una línea de
    registro por petición (sin la query: las URLs firmadas no deben quedar en los logs)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        request_id = incoming_id(scope)
        token = REQUEST_ID.set(request_id)
        started, status = time.perf_counter(), 500

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message)[REQUEST_HEADER] = request_id
            elif message["type"] == "websocket.accept":
                status = 101
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            elapsed = time.perf_counter() - started
            if scope["path"] != "/health":
                if scope["type"] == "http":
                    scope["app"].state.metrics.observe(status, elapsed)
                log.info(
                    "%s %s %s",
                    scope.get("method", "WS"),
                    scope["path"],
                    status,
                    extra={"fields": {"status": status, "ms": round(elapsed * 1000, 2)}},
                )
            REQUEST_ID.reset(token)


class CgroupReader:
    """CPU y memoria del contenedor desde cgroup v2 (sin privilegios ni socket de Docker)."""

    def __init__(self, root: Path = Path("/sys/fs/cgroup")) -> None:
        self.root = root
        self.last: tuple[float, int] | None = None

    def read(self, name: str) -> str | None:
        try:
            return (self.root / name).read_text(encoding="utf-8").strip()
        except OSError:
            return None

    def cpus(self) -> float:
        quota = (self.read("cpu.max") or "max").split()
        if quota[0] == "max":
            return float(os.cpu_count() or 1)
        return int(quota[0]) / int(quota[1])

    def sample(self) -> dict:
        """{"cpu_pct", "memory_pct"}; None en lo que no se puede medir (por ejemplo, fuera de Docker)."""
        cpu_pct = memory_pct = None
        stat = self.read("cpu.stat")
        if stat:
            usage = int(dict(line.split() for line in stat.splitlines())["usage_usec"])
            now = time.monotonic()
            if self.last is not None and now > self.last[0]:
                used = (usage - self.last[1]) / 1e6
                cpu_pct = round(100 * used / ((now - self.last[0]) * self.cpus()), 1)
            self.last = (now, usage)
        current, limit = self.read("memory.current"), self.read("memory.max")
        if current and limit and limit != "max":
            memory_pct = round(100 * int(current) / int(limit), 1)
        return {"cpu_pct": cpu_pct, "memory_pct": memory_pct}


class ResourceMonitor:
    """Avisa una vez (warning `resource.high`) cuando la CPU o la memoria pasan el umbral durante
    `sustain_s` seguidos; vuelve a armarse cuando el consumo baja (RNF-18)."""

    def __init__(
        self,
        audit,
        reader: Callable[[], dict],
        *,
        threshold_pct: float = 80.0,
        sustain_s: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.audit, self.reader, self.clock = audit, reader, clock
        self.threshold_pct, self.sustain_s = threshold_pct, sustain_s
        self.high_since: float | None = None
        self.alerted = False
        self.latest: dict = {"cpu_pct": None, "memory_pct": None}

    async def check(self) -> None:
        self.latest = self.reader()
        high = [k for k, v in self.latest.items() if v is not None and v >= self.threshold_pct]
        if not high:
            self.high_since, self.alerted = None, False
            return
        now = self.clock()
        if self.high_since is None:
            self.high_since = now
        if not self.alerted and now - self.high_since >= self.sustain_s:
            self.alerted = True
            await self.audit.emit(
                "warning",
                "resource.high",
                actor="system",
                details={**self.latest, "threshold_pct": self.threshold_pct},
            )

    async def run(self, interval_s: float) -> None:
        while True:
            try:
                await self.check()
            except Exception:  # medir nunca debe tumbar el servicio
                logging.getLogger("resources").exception("falló la medición de recursos")
            await asyncio.sleep(interval_s)
```

- [ ] **Step 3: Base web, auditoría, cliente interno e identidad**

Reemplazar `services/shared/shared/web.py` por:
```python
"""Base común de los servicios (spec §4.3, §15, §21): token de servicio, errores JSON genéricos,
/health, correlación y métricas."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.audit_client import AuditUnavailable
from shared.identity import require_admin
from shared.observability import (
    CgroupReader,
    Metrics,
    RequestContextMiddleware,
    ResourceMonitor,
    configure_logging,
)
from shared.secrets import env
from shared.service_auth import ServiceTokenMiddleware

log = logging.getLogger("web")

ADMIN_COOKIE = "__Host-admin"
USER_COOKIE = "__Host-user"
ROOM_COOKIE = "__Host-room"
DEVICE_COOKIE = "__Host-device"


def set_cookie(response: Response, name: str, value: str, max_age: int | None = None) -> None:
    response.set_cookie(
        name, value, max_age=max_age, path="/", secure=True, httponly=True, samesite="strict"
    )


def clear_cookie(response: Response, name: str) -> None:
    response.delete_cookie(name, path="/", secure=True, httponly=True, samesite="strict")


def with_monitor(lifespan):
    """Agrega al ciclo de vida del servicio la medición periódica de CPU y memoria (RNF-18)."""

    @asynccontextmanager
    async def combined(app: FastAPI):
        task = asyncio.create_task(app.state.monitor.run(env("RESOURCE_SAMPLE_S", 30.0)))
        try:
            if lifespan is None:
                yield
            else:
                async with lifespan(app):
                    yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    return combined


def create_base_app(*, title: str, settings, engine, service_auth, audit, lifespan=None) -> FastAPI:
    configure_logging(title)
    app = FastAPI(
        title=title,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=with_monitor(lifespan),
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.service_auth = service_auth
    app.state.audit = audit
    app.state.metrics = Metrics()
    app.state.extra_metrics = None  # async (app) -> dict: lo propio de cada servicio
    app.state.monitor = ResourceMonitor(
        audit,
        CgroupReader().sample,
        threshold_pct=env("RESOURCE_ALERT_PCT", 80.0),
        sustain_s=env("RESOURCE_ALERT_MIN", 5) * 60,
    )
    app.add_middleware(ServiceTokenMiddleware)
    app.add_middleware(RequestContextMiddleware)  # la última agregada es la más externa

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
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:  # la BD no responde: el healthcheck de Docker lo verá
            return JSONResponse({"error": "bd no disponible"}, status_code=503)
        return JSONResponse({"status": "ok"})

    @app.get("/api/admin/metrics", dependencies=[Depends(require_admin)])
    async def metrics(request: Request) -> dict:
        own = request.app.state.extra_metrics  # métricas propias del servicio, si registró alguna
        return {
            "service": title,
            **request.app.state.metrics.snapshot(),
            "resources": request.app.state.monitor.latest,
            **({"extra": await own(request.app)} if own else {}),
        }

    return app
```

Reemplazar `services/shared/shared/audit_client.py` por:
```python
"""Emisión de eventos al servicio audit con fallback a stdout (spec §14.4)."""

import json
import logging

import httpx

from shared.observability import REQUEST_ID
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
            # audit lo guarda en details: el evento se sigue hasta los registros de cada servicio
            "request_id": REQUEST_ID.get(),
        }
        for _ in range(2):  # dos intentos de 2 s
            try:
                response = await self.client.post(
                    "audit", "/internal/events", json=event, timeout=2.0
                )
            except httpx.HTTPError:
                continue
            if response.status_code == 201:
                return
        if required:
            raise AuditUnavailable(action)
        log.warning("AUDIT_FALLBACK %s", json.dumps(event, ensure_ascii=False, default=str))
```

Reemplazar `services/shared/shared/service_auth.py` por:
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
from shared.observability import REQUEST_HEADER, REQUEST_ID
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
            path.name.removeprefix("svc_hash_"): bytes.fromhex(
                path.read_text(encoding="utf-8").strip()
            )
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
                "warning",
                "svc.reject.token",
                actor="svc:desconocido",
                target=scope["path"],
                ip=client[0] if client else None,
            )
            if scope["type"] == "websocket":
                await WebSocket(scope, receive, send).close(4401)
            else:
                await JSONResponse({"error": "no autorizado"}, status_code=401)(
                    scope, receive, send
                )
            return
        scope.setdefault("state", {})["caller"] = caller
        await self.app(scope, receive, send)


def allow(*callers: str):
    """Dependencia de ruta interna: el llamador verificado debe estar en la allowlist."""

    async def dependency(request: Request) -> str:
        caller = request.state.caller
        if caller not in callers:
            await request.app.state.audit.emit(
                "warning",
                "svc.reject.token",
                actor=f"svc:{caller}",
                target=request.url.path,
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
        self, service: str, path: str, *, json: dict, timeout: float = 3.0
    ) -> httpx.Response:
        headers = {TOKEN_HEADER: self.auth.token or ""}
        if REQUEST_ID.get():  # la misma petición se sigue de un servicio a otro (RNF-19)
            headers[REQUEST_HEADER] = REQUEST_ID.get()
        # ponytail: un AsyncClient por llamada (sin pool compartido); basta en una red interna a esta escala.
        async with httpx.AsyncClient(transport=self.transport, timeout=timeout) as client:
            return await client.post(self.urls[service] + path, json=json, headers=headers)
```

Reemplazar `services/shared/shared/identity.py` por:
```python
"""Identidad propagada por el gateway (spec §4.3). Solo se lee si el llamador verificado es 'gateway'."""

from dataclasses import dataclass
from urllib.parse import quote, unquote

from fastapi import HTTPException, Request
from starlette.requests import HTTPConnection

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass(frozen=True)
class AdminIdentity:
    admin_id: str
    username: str


@dataclass(frozen=True)
class UserIdentity:
    user_id: str
    alias: str  # nombre visible elegido en el primer ingreso (spec §9.2)


@dataclass(frozen=True)
class SessionIdentity:
    session_id: str
    room_id: str
    alias: str  # el alias de la cuenta (spec §9.3)
    mode: str
    user_id: str


def client_ip(conn: HTTPConnection) -> str | None:
    """IP del cliente original: uvicorn la toma de X-Forwarded-For, que el gateway sobrescribe."""
    return conn.client.host if conn.client else None


def encode_alias(alias: str) -> str:
    """Las cabeceras HTTP son latin-1: el alias (UTF-8) viaja percent-encoded."""
    return quote(alias, safe="")


async def require_gateway(request: Request) -> None:
    """Rutas públicas: solo el gateway puede llamarlas, y las que cambian estado exigen Origin permitido (CSRF)."""
    audit, ip = request.app.state.audit, client_ip(request)
    if request.state.caller != "gateway":
        await audit.emit(
            "warning",
            "svc.reject.token",
            actor=f"svc:{request.state.caller}",
            target=request.url.path,
            ip=ip,
        )
        raise HTTPException(403, "no autorizado")
    origin = request.headers.get("origin")
    if (
        request.method in UNSAFE_METHODS
        and origin not in request.app.state.settings.allowed_origins
    ):
        await audit.emit(
            "warning",
            "http.reject.origin",
            actor=f"ip:{ip}",
            target=request.url.path,
            ip=ip,
            details={"origin": origin},
        )
        raise HTTPException(403, "origen no permitido")


async def require_admin(request: Request) -> AdminIdentity:
    await require_gateway(request)
    admin_id, username = request.headers.get("x-admin-id"), request.headers.get("x-admin-user")
    if not admin_id or not username:
        raise HTTPException(401, "no autenticado")
    return AdminIdentity(admin_id, username)


async def require_user(request: Request) -> UserIdentity:
    """Cuenta de usuario verificada por auth (verify-user) y propagada por el gateway (spec §9.2)."""
    await require_gateway(request)
    user_id, alias = request.headers.get("x-user-id"), request.headers.get("x-user-name")
    if not user_id or not alias:
        raise HTTPException(401, "no autenticado")
    return UserIdentity(user_id, unquote(alias))


def session_from_headers(conn: HTTPConnection) -> SessionIdentity | None:
    headers = conn.headers
    values = (
        headers.get("x-session-id"),
        headers.get("x-room-id"),
        headers.get("x-alias"),
        headers.get("x-room-mode"),
        headers.get("x-user-id"),
    )
    if not all(values):
        return None
    session_id, room_id, alias, mode, user_id = values
    return SessionIdentity(session_id, room_id, unquote(alias), mode, user_id)


async def require_session(request: Request) -> SessionIdentity:
    await require_gateway(request)
    who = session_from_headers(request)
    if who is None:
        raise HTTPException(401, "no autenticado")
    return who
```

En `services/shared/shared/testing.py`, reemplaza `user_headers` por:
```python
def user_headers(user_id: str = USER_ID, alias: str = "ana") -> dict:
    """La cuenta que verify-user de auth le entrega al gateway (spec §9.2); el alias va codificado."""
    return {**gateway_headers(), "X-User-Id": user_id, "X-User-Name": encode_alias(alias)}
```

Run: `ruff format services/shared && ruff check --fix services/shared && pytest services/shared -q`
Expected: sin errores de ruff y PASS

- [ ] **Step 4: Imagen y límites de recursos**

Reemplazar `services/Dockerfile` por:
```dockerfile
# Plantilla única de los servicios Python (spec §4.2). Uso: --build-arg SERVICE=<svc>
FROM python:3.13-slim
ARG SERVICE
# Paquetes del sistema que solo necesita un servicio (media: ffmpeg para MP3 y MP4, spec §12).
ARG APT_PACKAGES=""
# LOG_FORMAT=json: una línea JSON por registro, con el mismo formato en todos los servicios (RNF-19).
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SERVICE=${SERVICE} LOG_FORMAT=json
RUN if [ -n "$APT_PACKAGES" ]; then \
      apt-get update && apt-get install -y --no-install-recommends $APT_PACKAGES \
      && rm -rf /var/lib/apt/lists/*; \
    fi \
 && useradd --uid 10001 --no-create-home app \
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
# --no-access-log: el registro de acceso lo escribe shared.observability (JSON, con request_id y sin
# la query, que en las descargas lleva la firma de la URL).
CMD exec uvicorn --factory "${SERVICE}_svc.main:create_app" --host 0.0.0.0 --port 8000 \
    --proxy-headers --forwarded-allow-ips '*' --ws-ping-interval 30 --ws-ping-timeout 30 \
    --ws-max-size 65536 --no-server-header --no-access-log
```

En `deploy/docker-compose.yml`, agrega al ancla `x-python-service` (el monitor mide contra estos límites; `media` puede subir los suyos):
```yaml
  mem_limit: 512m
  cpus: 1.0
```

Run: `docker compose -f deploy/docker-compose.yml config -q`
Expected: sin errores.

- [ ] **Step 5: Commit**

```bash
git add services/shared services/Dockerfile deploy/docker-compose.yml
git commit -m "feat(shared): id de correlación, registros JSON, métricas y alerta de consumo (RNF-18, RNF-19)"
```

---

### Task FND-10: Calidad, control de cambios y modelo de amenazas (RNF-10, RNF-11, RS-30, RS-32, RS-33, RS-34, RS-37)

> **Rev. 4.** Tarea nueva con los requisitos de desarrollo seguro de la Actividad 3 (spec §21.3).

**Files:**
- Modify: `ruff.toml` (complejidad ≤ 10), `services/shared/pyproject.toml` (`pytest-cov`), `.github/workflows/ci.yml` (cobertura y job `secrets`), `docs/trazabilidad-riesgos.md` (columna ISO/IEC 27001)
- Create: `.gitleaks.toml`, `.github/pull_request_template.md`, `docs/modelo-amenazas.md`

**Interfaces:**
- Produces: la CI falla si un servicio baja del 80 % de cobertura de líneas, si una función supera complejidad 10 o si aparece un secreto en el historial; la rama `main` exige PR revisado y CI en verde.

- [ ] **Step 1: Complejidad y cobertura**

Reemplazar `ruff.toml` por:
```toml
line-length = 100
target-version = "py313"

[lint]
select = ["E", "F", "I", "B", "S", "UP", "C90"]  # C90: complejidad ciclomática (RNF-11)
ignore = ["E501"]  # ruff format ajusta el código; SQL y comentarios largos no se parten a la fuerza

[lint.mccabe]
max-complexity = 10

[lint.isort]
known-first-party = ["shared", "auth_svc", "rooms_svc", "chat_svc", "media_svc", "audit_svc"]

[lint.flake8-bugbear]
# FastAPI declara dependencias y parámetros con llamadas en los valores por defecto.
extend-immutable-calls = ["fastapi.Depends", "fastapi.Query", "fastapi.params.Depends", "fastapi.params.Query"]

[lint.per-file-ignores]
"**/tests/**" = ["S101", "S105", "S106", "S311", "S603", "S607"]  # las pruebas lanzan ffmpeg, mkcert y herramientas
"e2e/**" = ["S101", "S105", "S106", "S113", "S311", "S603", "S607"]
"services/shared/shared/testing.py" = ["S101", "S105", "S106", "S311", "S603", "S608"]
"services/*/tools/**" = ["S311"]
"deploy/**" = ["S603", "S607"]
```

En `services/shared/pyproject.toml`, agrega `"pytest-cov>=5.0",` a `dev`, después de `pytest-timeout`.

En `.github/workflows/ci.yml`, reemplaza el paso `Pruebas` del job `services` por:
```yaml
      - name: Pruebas con cobertura ≥ 80 % (RNF-10)
        run: |
          pkg="${{ matrix.svc }}_svc"; [ "${{ matrix.svc }}" = shared ] && pkg=shared
          pytest "services/${{ matrix.svc }}" -m "not clamav" --cov="$pkg" --cov-report=term --cov-fail-under=80
```
y cambia el nombre del paso `Ruff` por `Ruff (incluye complejidad ≤ 10, RNF-11)`.

Run: `pip install -e "services/shared[dev]" && ruff check services && pytest services/shared --cov=shared --cov-fail-under=80 -q`
Expected: `All checks passed!` y `Required test coverage of 80% reached` (shared ≈ 85 %; con la rev. 4, cada servicio queda entre 85 % y 98 %).

- [ ] **Step 2: Secretos en el historial (RS-32)**

`.gitleaks.toml`:
```toml
# Detección de secretos en la CI (spec §16.5, RS-32). Las pruebas, el e2e y la documentación usan
# contraseñas y tokens FIJOS de prueba (shared.testing); los secretos reales viven en deploy/secrets/,
# que está en .gitignore.
[extend]
useDefault = true

[allowlist]
description = "Valores de prueba documentados"
paths = [
  '''services/[^/]+/tests/''',
  '''services/shared/shared/testing\.py''',
  '''e2e/''',
  '''perf/''',
  '''docs/''',
]
```

En `.github/workflows/ci.yml`, agrega el job:
```yaml
  secrets:
    # Detección de secretos en todo el historial (RS-32). Las excepciones están en .gitleaks.toml.
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: gitleaks
        run: >-
          docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/repo" ghcr.io/gitleaks/gitleaks:v8.21.2
          git /repo --config /repo/.gitleaks.toml --redact --no-banner
```

Run: `docker run --rm -v "${PWD}:/repo" ghcr.io/gitleaks/gitleaks:v8.21.2 git /repo --config /repo/.gitleaks.toml --redact --no-banner`
Expected: `no leaks found`.

- [ ] **Step 3: Control de cambios (RS-37)**

`.github/pull_request_template.md`:
```markdown
## Qué cambia y por qué

<!-- Tarea del plan (por ejemplo, ATH-5) y riesgos o requisitos que toca (R1–R17, RS-xx, RNF-xx). -->

## Lista de verificación de seguridad (RS-37)

- [ ] La identidad (admin, cuenta, sesión, sala) sale del gateway o de la sesión verificada, nunca del cuerpo de la petición.
- [ ] Las rutas `/internal/*` nuevas usan `allow(...)` con la allowlist mínima, y las públicas `require_gateway`.
- [ ] Consultas con `text()` y parámetros nombrados; nada del usuario entra al texto SQL.
- [ ] Errores genéricos al cliente; el detalle va a la auditoría. Ningún secreto, token, contraseña ni cuerpo de mensaje en los registros.
- [ ] Cada rechazo nuevo emite su evento de auditoría; los eventos que otorgan algo son `required=True`.
- [ ] Hay pruebas `test_rNN_*` del riesgo que toca el cambio y `docs/trazabilidad-riesgos.md` está al día.
- [ ] Sin secretos en el código: la CI (gitleaks) pasa.
- [ ] `ruff`, la cobertura (≥ 80 %), bandit, pip-audit y la prueba de enrutamiento del gateway pasan.
- [ ] Si cambia el modelo de confianza o un flujo de datos, se actualizó `docs/modelo-amenazas.md`.
```

En GitHub → *Settings* → *Branches* → *Add branch ruleset* para `main`: exigir *pull request* con 1 aprobación, descartar aprobaciones viejas al subir cambios, exigir que pasen los checks `services`, `secrets`, `frontend` y `gateway`, y bloquear *force push* y borrado. Anota la captura en la trazabilidad (evidencia de RS-37).

- [ ] **Step 4: Modelo de amenazas y trazabilidad normativa (RS-30, RS-33, RS-34)**

`docs/modelo-amenazas.md`:
```markdown
# Modelo de amenazas (STRIDE)

Evidencia de RS-30 (*Secure by Design*): se elabora **antes** de implementar los componentes críticos y se revisa cuando cambian el modelo de confianza, las cuentas, las salas o los formatos admitidos. Fuente: spec §3 (limitaciones), §4 (arquitectura y confianza) y §16.3 (R16, R17). Cada amenaza remite al riesgo del SGSI, a su control y a la prueba que lo demuestra (`docs/trazabilidad-riesgos.md`).

## Límites de confianza

| Límite | Del lado no confiable | Del lado confiable | Control en el cruce |
|---|---|---|---|
| Internet → gateway | navegador, cualquier cliente | gateway | TLS 1.3, HSTS, CSP, rate limit, `auth_request`, cabeceras de identidad sobrescritas |
| gateway → servicios | red `apps` | cada servicio | `X-Service-Token` (hash por llamador), allowlist por ruta, identidad solo si el llamador es `gateway` |
| servicio → servicio | red `apps` | receptor | token propio del llamador y allowlist (R16) |
| servicio → PostgreSQL | red `data` | BD del servicio | rol `<svc>_app` sin DDL, una BD por servicio (R11) |
| media → archivos subidos | bytes del usuario | procesos de análisis | firma, validación con límites, ClamAV, procesos aislados con timeout, ffmpeg endurecido (R9) |
| auth → mailer | — | correo saliente | red interna `mail`; solo `mailer` sale a internet en el VPS |

## Amenazas por componente

| Componente | S (suplantación) | T (manipulación) | R (repudio) | I (divulgación) | D (denegación) | E (elevación) |
|---|---|---|---|---|---|---|
| gateway | Cabeceras de identidad falsas → se sobrescriben (R16) | Downgrade a TLS 1.2 o `ws://` → solo TLS 1.3, 301 (R7) | — | `/internal/*` expuesto → 404 (R16) | Inundación de peticiones o WebSockets → `limit_req`, `limit_conn` (R10) | Rutas mal enrutadas → `check_routes.py` en la CI |
| auth (admin) | Fuerza bruta → bloqueo + TOTP (R4) | Fijación de sesión → token nuevo al pasar a `full` | Acciones sin autor → auditoría obligatoria | Secreto TOTP en BD → AES-GCM con KEK (R2) | Bloqueo del admin por fallos ajenos → contadores separados por cuenta e IP | Cuenta de usuario en `/api/admin/*` → cookies y verificaciones distintas (R5) |
| auth (cuentas) | *Credential stuffing* → Argon2id, bloqueo, retraso, política (R17) | Registro con correo ajeno → código por correo; la cuenta sin verificar se renueva | Alta sin rastro → `user.register` obligatorio | Enumeración de correos → registro siempre 202, login genérico | Registros masivos → tope por dispositivo e IP | Alias que imita a otro → alias único por forma canónica, solo latino |
| rooms | Sesión robada → atada a la cookie de dispositivo (R13) | Cupo superado por carrera → `UPDATE` condicional + `CHECK` (R15) | Ingreso sin rastro → `room.enter.ok` obligatorio | Enumeración de salas → mismo 401/404 (RS-35) | Fuerza bruta de claves → rate limit por usuario, IP, dispositivo y sala (R8) | Usuario que crea salas → `require_admin` (R5) |
| chat | MITM interno → *hello* firmado (R7) | Trama alterada o repetida → AES-GCM + AAD + `seq` (R14) | Remitente falso → `from` sale de la sesión (R14) | Mensajes en BD → DEK por sala con KEK (R2) | Ráfagas o tramas gigantes → token bucket, 16 KB (R10) | Mensaje en otra sala → sala desde la sesión, AAD |
| media | Subir como otro → sesión del gateway | Archivo con contenido oculto → análisis por formato + cuarentena + CDR + reanálisis (R6, RS-36) | Subida sin autor → `files.user_id` y auditoría | Descarga ajena → URL firmada por sesión y sala (R12) | Bombas, archivos enormes → topes y límites, procesos con timeout (R9) | Ejecutar el archivo → `attachment`, `nosniff`, sin ruta pública |
| audit | Servicio que se hace pasar por otro → `service` sale del token | Borrar o editar eventos → rol solo INSERT/SELECT + cadena SHA-256 (R3) | — | Datos sensibles en eventos → nunca contraseñas, tokens ni cuerpos | audit caído → los otorgamientos fallan cerrados (503) | — |
| BD / secretos | — | DDL desde la app → rol sin DDL (R11) | — | Copia de la BD → hashes Argon2id, KEK fuera de la BD, respaldos cifrados con age | — | Credenciales de otra BD → `CONNECT` solo a la propia (R11) |

## Supuestos y riesgos aceptados

- `chat` ve el texto de los mensajes y `media` los archivos (limitación 1 de la spec): la confianza en esos servicios es explícita.
- El tramo interno es HTTP: los tokens de servicio viajan en claro dentro de redes Docker internas (limitación 3); se mitiga con redes segmentadas y `cap_drop: ALL`.
- Quien conoce la clave de una sala y tiene otra cuenta puede unirse (limitación 2); lo limita el cupo y queda auditado.
- El estegoanálisis no detecta todo (limitación 5); la sanitización destruye la mayoría de los canales.

## Revisión

| Fecha | Cambio revisado | Revisores | Resultado |
|---|---|---|---|
| — | Diseño inicial (spec rev. 4) | — | — |
```

En `docs/trazabilidad-riesgos.md`, agrega la columna *Control ISO/IEC 27001:2022* después de *Control* con estos valores (referencia de diseño, no certificación):

| R | Control ISO/IEC 27001:2022 |
|---|---|
| R1, R4, R8, R17 | A.5.17 Información de autenticación · A.8.5 Autenticación segura |
| R2 | A.8.24 Uso de criptografía |
| R3 | A.8.15 Registro de eventos |
| R5, R12, R14 | A.5.15 Control de acceso · A.8.3 Restricción de acceso a la información |
| R6, R9 | A.8.7 Protección contra malware · A.8.12 Prevención de fuga de datos |
| R7 | A.8.20 Seguridad de redes · A.8.24 Uso de criptografía |
| R10 | A.8.6 Gestión de la capacidad · A.8.16 Actividades de seguimiento |
| R11 | A.8.2 Derechos de acceso privilegiado |
| R13, R15 | A.5.15 Control de acceso · A.8.5 Autenticación segura |
| R16 | A.8.22 Segregación de redes · A.8.5 Autenticación segura |

y una sección *Controles de seguridad de la aplicación (ISO/IEC 27034)* que remita, por cada control, a su criterio de verificación (la prueba de la columna *Tests*).

- [ ] **Step 5: Commit**

```bash
git add ruff.toml services/shared/pyproject.toml .github .gitleaks.toml docs/modelo-amenazas.md docs/trazabilidad-riesgos.md
git commit -m "ci: cobertura mínima, complejidad, detección de secretos, plantilla de PR y modelo de amenazas"
```

---

## Execution Handoff

Ejecuta los archivos en el orden del índice (`2026-10-13-00-indice.md`). Para cada tarea: lee la tarea **y** las secciones del spec que cita, sigue los pasos en orden (test que falla → implementación → test en verde → commit) y no adelantes tareas de otros archivos sin que sus dependencias estén en verde.
