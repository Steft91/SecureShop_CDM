# 01 · Fundaciones — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar listo todo lo que comparten los servicios del primer parcial (auth y stego, detrás del gateway): el contexto de Claude Code, la librería `shared` (secretos, cripto, contraseñas, límites, autenticación entre servicios, identidad del usuario con sus permisos, eventos de seguridad en JSON, base web, utilidades de prueba), la plantilla Docker, la generación de secretos (incluida la clave de firma de los JWT), PostgreSQL con la BD de auth y la CI.

**Architecture:** `services/shared` es un paquete Python instalable (`chat-shared` → `import shared`). Cada servicio lo instala junto al suyo. La infraestructura (Dockerfile único con `ARG SERVICE`, `gen_secrets.py`, `init.sh`) se escribe una vez y cada servicio solo agrega su bloque al compose.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2 + asyncpg, Alembic, cryptography, argon2-cffi, httpx, pytest · Docker Compose · GitHub Actions.

**Spec:** `docs/specs/2026-10-12-chat-seguro-design.md` (§4.3, §5, §7.6, §11, §15, §16, §17).

## Global Constraints

Las de `docs/plans/2026-10-13-00-indice.md` § *Global Constraints*. Resumen operativo:
- Python 3.13.
- `text()` con parámetros nombrados.
- Todas las rutas exigen `X-Service-Token` salvo `/health`.
- Errores `{"error": "..."}` en español.
- Cookies `__Host-*` con `Secure`, `HttpOnly` y `SameSite=Strict`.
- Secretos solo desde `/run/secrets`.
- Un test `test_rNN_*` por riesgo.
- Commits en español, sin atribución.

## Review Focus

Ninguno de los casos del índice cae en este archivo, pero las utilidades que se crean aquí los soportan:
- `TokenBucket` para el límite de la API de esteganografía.
- `user_headers` arma la identidad que pasa el gateway, con los permisos separados por comas; `user_from_headers` tolera que `X-User-Perms` no venga (sin permisos).

---

### Task FND-1: Higiene del repo y contexto de Claude Code

**Files:**
- Create: `.gitignore`, `.gitattributes`, `.dockerignore`, `ruff.toml`
- Create: `.github/pull_request_template.md`
- Create: `CLAUDE.md`
- Create: `.claude/settings.json`
- Create: `.claude/rules/security.md`, `.claude/rules/microservices.md`, `.claude/rules/backend.md`, `.claude/rules/testing.md`
- Create: `.claude/commands/risk-check.md`
- Create: `.claude/skills/stego-analysis/SKILL.md`
- Create: `.claude/agents/security-auditor.md`
- Create: `.claude/hooks/guard.py`
- Create: `docs/trazabilidad-riesgos.md`

**Interfaces:**
- Consumes: nada.
- Produces:
  - El hook `guard.py`, que corre antes de cada `Edit|Write|MultiEdit` de Claude Code.
  - La tabla de trazabilidad que actualizan todas las tareas.
  - `ruff.toml` en la raíz, que aplica a todo `services/` y `deploy/`. Incluye la regla `C90` con complejidad ciclomática ≤ 10 por función (RNF-11): una función más compleja se parte en el mismo ticket, no se silencia.
  - `.github/pull_request_template.md` con la lista de verificación de seguridad (RS-37).

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
    assert check("/repo/services/stego/stego_svc/x.py", "url = 'ws://x'", root)
    assert check("/repo/services/stego/stego_svc/x.py", "url = 'wss://x'", root) is None
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
**/__pycache__
**/.pytest_cache
**/.ruff_cache
**/tests
deploy/secrets
deploy/certs
Documentación
docs
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
known-first-party = ["shared", "auth_svc", "stego_svc"]

[lint.flake8-bugbear]
# FastAPI declara dependencias y parámetros con llamadas en los valores por defecto.
extend-immutable-calls = ["fastapi.Depends", "fastapi.Query", "fastapi.params.Depends", "fastapi.params.Query"]

[lint.per-file-ignores]
"**/tests/**" = ["S101", "S105", "S106", "S311"]
"services/shared/shared/testing.py" = ["S101", "S105", "S106", "S311", "S603", "S608"]
"services/*/tools/**" = ["S311"]
"deploy/**" = ["S603", "S607"]
```

- [ ] **Step 5: Reglas de Claude Code**

`.claude/rules/security.md`:
```markdown
# Invariantes de seguridad (aplican a todo el repo)

Fuente: spec §2–§15 y Tabla 3 de la Tarea 2, recortados al primer parcial (gateway, auth y stego). Si un cambio rompe una de estas reglas, se detiene y se discute; no se "arregla después".

1. **Transporte:** el cliente solo habla TLS 1.3 con el gateway. Nunca `http://` hacia el cliente: el gateway redirige con 301.
2. **Secretos:** solo se leen con `shared.secrets` desde `/run/secrets`. Nunca en el código, en variables de entorno ni en logs. Los valores de prueba viven en `tests/` o en `shared/testing.py` y lo dicen en un comentario.
3. **Identidad:** el usuario sale de la identidad que verificó el gateway (`require_user`, `require_perm`, `user_from_headers`). Nunca del cuerpo de la petición.
4. **Autorización:** por permiso del catálogo (`require_perm`), siempre en el servidor. Nunca por el rol del JWT ni por un campo del cuerpo. Los modelos de entrada usan `extra="forbid"`.
5. **SQL:** siempre `text()` con parámetros nombrados. Prohibido interpolar datos con f-strings.
6. **Contraseñas:** Argon2id (`shared.passwords`), con verificación contra un hash dummy cuando el usuario no existe.
7. **Errores:** el cliente recibe `{"error": "..."}` genérico; el detalle va al registro de eventos. Todo rechazo de seguridad y todo acceso otorgado se registra con `shared.audit.emit(...)`.
8. **Datos sensibles:** nunca se registran contraseñas, tokens (JWT incluidos) ni secretos.
9. **Fallar cerrado:** si falta un secreto, el servicio no arranca. Si la BD no responde → 503. Si el análisis de una imagen falla o se pasa de tiempo, el veredicto es `revision_manual`, nunca `limpia`.
10. **Cripto:** solo con `shared.crypto` y PyJWT con `algorithms=["RS256"]` fijo. Nada de primitivas propias.
11. **Documentos de cumplimiento:** un cambio de control, algoritmo, clave o ruta de datos actualiza `docs/trazabilidad-riesgos.md` y, si aplica, `docs/justificacion-criptografica.md` y `docs/cumplimiento-normativo.md`.
```

`.claude/rules/microservices.md`:
```markdown
# Modelo de confianza entre microservicios (R16, spec §4.3)

- El gateway es el único punto de entrada y el único que habla con `auth` y `stego`. Los servicios no se llaman entre sí.
- Toda ruta de un servicio exige `X-Service-Token` válido (`ServiceTokenMiddleware`, que agrega `shared.web.create_base_app`). Solo `/health` está exento.
- Rutas públicas (enrutadas por el gateway): `Depends(require_gateway)`, `Depends(require_user)` o `Depends(require_perm("<permiso>"))`. Rutas internas: `/internal/...` con `Depends(allow("<llamador>", ...))`.
- Las cabeceras `X-User-Id`, `X-User-Name`, `X-Session-Id` y `X-User-Perms` **solo** se leen a través de `shared.identity`, que exige que el llamador sea `gateway`. Los permisos que traen son los actuales: el gateway los pide a `auth` en cada request.
- Un servicio con datos se conecta **solo a su BD** con su rol `<svc>_app`. En el primer parcial solo `auth` tiene BD; `stego` no guarda nada.
- Allowlist vigente: auth ← gateway · stego ← gateway.
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

- Paquete `<svc>_svc` dentro de `services/<svc>/`. Fábrica `create_app(settings=None, *, engine=None, service_auth=None)`; sin argumentos lee secretos y entorno.
- Configuración en `config.py`: `Settings` (dataclass congelada) + `load_settings()`. Las perillas no secretas salen de `shared.secrets.env(NOMBRE, default)`.
- Rutas en módulos con `router = APIRouter()`. Nada de lógica en `main.py`.
- Transacciones con `async with engine.begin()`; lecturas con `engine.connect()`.
- Los eventos de seguridad se registran con `shared.audit.emit(...)` (síncrono: escribe una línea JSON y no falla). Uno que otorga algo va después del commit, para no registrar algo que se revirtió; uno de rechazo, donde se decide el rechazo.
- Migraciones a mano (`op.execute`) con `GRANT` explícitos a `<svc>_app`. `migrations/env.py` solo llama `shared.migrations.run("<svc>")`.
- Las dependencias del servicio van en su `pyproject.toml`. Después de cambiarlas se regenera `requirements.lock` con `services/lock.sh`.
```

`.claude/rules/testing.md`:
```markdown
---
paths:
  - "**/tests/**"
---
# Convenciones de pruebas

- PostgreSQL real (`deploy/docker-compose.test.yml`, puerto 5433). Nunca mocks de BD.
- Un archivo `test_rNN_<tema>.py` por riesgo; el nombre de cada test describe el comportamiento, en español.
- Los eventos de seguridad se verifican con el fixture `caplog` de pytest: `testing.events(caplog, "<acción>")`.
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
description: Referencia del estegoanálisis del servicio stego (chi² de Westfeld, análisis RS, entropía LSB, estructura PNG/JPEG, veredicto y calibración). Úsala al tocar services/stego, ajustar umbrales o agregar un formato.
---
# Estegoanálisis en `stego` (spec §12)

`stego` no guarda nada: valida la imagen, la analiza y responde un veredicto.

## Veredicto (spec §12.7)
| Veredicto | Cuándo |
|---|---|
| `invalida` (422) | Firma, tamaño, píxeles o decodificación inválidos |
| `problema` | Anomalía estructural (datos al final, chunks de texto grandes o desconocidos, metadatos JPEG excesivos) |
| `revision_manual` | chi², RS (o entropía, si se activa) sobre el umbral, o timeout del análisis |
| `limpia` | Nada de lo anterior |

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

## Calibración con fotos reales
1. Copia ≥ 30 imágenes limpias (fotos de celular, capturas) en `services/stego/tools/calibracion/` (gitignored). Para el primer parcial alcanzan 15.
2. `python services/stego/tools/stego_lab.py calibrate services/stego/tools/calibracion`
3. Elige umbrales con FPR ≤ 5 % y TPR máxima para "secuencial 10 %". Configúralos con `STEGO_CHI2_P` / `STEGO_RS_RATE` en `deploy/docker-compose.yml` y anota la tabla en `docs/calibracion-estego.md`.

## Agregar un formato
1. Firma + `pil_format` + `analyze` en `stego_svc/formats.py` (`FORMATS`).
2. Módulo `stego_svc/<formato>.py` con funciones de módulo (las ejecuta un `ProcessPoolExecutor`).
3. Clasificar sus motivos en `stego_svc/verdict.py` (`STRUCTURAL` o `STATISTICAL`).
4. Tests: uno limpio y uno con payload. Actualizar R6/R9 en la trazabilidad.
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
- `docs/specs/2026-10-12-chat-seguro-design.md` §4.3 (modelo de confianza), §9.1, §12 y §14;
- `.claude/rules/security.md` y `.claude/rules/microservices.md`;
- `docs/trazabilidad-riesgos.md` y `docs/requisitos.md` (requisitos RS-xx).

Procedimiento:
1. `git diff main...HEAD --stat` y luego el diff de cada archivo de `services/`, `gateway/` y `deploy/`.
2. Para cada cambio, pregúntate:
   - ¿Viola alguna invariante?
   - ¿Lee identidad sin `shared.identity`?
   - ¿Agrega una ruta sin token o sin allowlist?
   - ¿Interpola SQL?
   - ¿Filtra datos sensibles a logs o errores?
   - ¿Falla abierto?
3. Verifica que cada control tocado siga teniendo su `test_rNN_*`; ejecuta `pytest services/<svc> -q` si hace falta.

Formato de salida: una lista ordenada por severidad (Crítica, Alta, Media, Baja). Cada ítem lleva `archivo:línea`, riesgo afectado (R1–R16 u OWASP A0x), qué falla y la corrección concreta. Si no hay hallazgos, dilo explícitamente e indica qué revisaste.
```

- [ ] **Step 7: Tabla de trazabilidad inicial**

`docs/trazabilidad-riesgos.md`:
```markdown
# Trazabilidad de riesgos → controles → pruebas

Fuente de riesgos: Tarea 2 (Tablas 1–4) + R16 (spec §16.3), recortada al primer parcial (gateway, auth y stego). Cada tarea del plan actualiza su fila. "Implementado" exige un test en verde.

La columna *ISO/IEC 27001:2022* relaciona cada control con el Anexo A; el detalle (mecanismo y evidencia) está en `docs/cumplimiento-normativo.md` §1.2. Los requisitos RF/RS del docente están en `docs/requisitos.md`.

| R | Riesgo | Control en el primer parcial | ISO/IEC 27001:2022 | Servicio / archivos | Tests | Estado |
|---|---|---|---|---|---|---|
| R2 | Claves criptográficas en el código fuente | Docker secrets (`/run/secrets`); la clave de firma del JWT nunca está en el código | A.8.24, A.8.9, A.8.12 | shared, auth | — | Pendiente |
| R4 | Fuerza bruta contra las cuentas | Bloqueo + retraso progresivo del login | A.8.5, A.5.17 | auth | — | Pendiente |
| R5 | Operaciones sin verificación de permisos | `auth_request` con permisos actuales + `require_perm` en cada servicio; el registro no asigna roles; nunca sin admin | A.5.15, A.8.2, A.5.18 | gateway, auth, stego | — | Pendiente |
| R6 | Imágenes con esteganografía | chi², RS y estructura (`stego`) con veredicto | A.8.7, A.8.16 | stego | — | Pendiente |
| R7 | Canal sin cifrar | TLS 1.3 en el gateway, http → https | A.8.20, A.8.24 | gateway | — | Pendiente |
| R9 | Archivos maliciosos | Magic bytes, Pillow, tope de tamaño y de píxeles (`stego`) | A.8.7, A.8.28 | stego | — | Pendiente |
| R10 | Agotamiento de recursos | Rate limit en Nginx + token bucket por usuario en `stego` + tope de registros por IP | A.8.6, A.8.20 | gateway, auth, stego | — | Pendiente |
| R11 | Credenciales de BD con privilegios excesivos | Rol `auth_app` sin DDL, BD propia de `auth` | A.8.2, A.5.18, A.8.22 | auth | — | Pendiente |
| R13 | Sesiones simultáneas de una cuenta | Índice único parcial en `user_sessions` + sesión ligada a la cookie de dispositivo + vencimiento por inactividad | A.5.16, A.5.15, A.8.5 | auth | — | Pendiente |
| R16 | Suplantación entre microservicios | Token por servicio con hash, allowlist, gateway sobrescribe identidad | A.5.15, A.8.21, A.8.22 | shared, gateway, auth, stego | — | Pendiente |

Quedan fuera del primer parcial, hasta que el docente defina los siguientes entregables: R1, R3 (por ahora los eventos de seguridad son registros JSON, sin cadena de hashes), R8, R12, R14 y R15.

## Verificación manual (evidencia para el informe)
| Prueba | Comando | Resultado esperado | Fecha / resultado |
|---|---|---|---|
| TLS 1.2 rechazado | `curl --tlsv1.2 --tls-max 1.2 https://localhost/` | error de handshake | — |
| http → https | `curl -I http://localhost/` | `301` | — |
| /internal no enrutado | `curl https://localhost/internal/verify` | `404` JSON | — |
| Cabeceras de identidad falsificadas | `curl -H "X-User-Id: x" -H "X-User-Perms: roles:manage" https://localhost/api/admin/roles` | `401` JSON | — |
| Flujo del parcial (Postman) | Runner de `docs/postman/parcial-1.postman_collection.json` | todas las pruebas en verde | — |
```

- [ ] **Step 8: Escribir `CLAUDE.md`**

`CLAUDE.md`:
````markdown
# Salas de Chat Seguras — contexto del proyecto

Proyecto integrador de **Software Seguro** con **microservicios**. El primer parcial es lo que pidió el docente el 22/10/2026: dos microservicios sin interfaz gráfica detrás de un API Gateway, probados con Postman. `auth` maneja usuarios, roles y RBAC, y su login entrega un JWT; `stego` recibe una imagen y responde si es inválida, limpia, con problema o para revisión manual, y solo se entra con el token de `auth`. Las salas, el chat y la interfaz gráfica llegan por incrementos, cuando el docente los defina. Equipo: Manangón, Díaz, Cedeño.

- **Spec (diseño de referencia):** `docs/specs/2026-10-12-chat-seguro-design.md` (rev. 4; la nota del inicio dice qué entra en el primer parcial)
- **Plan:** `docs/plans/2026-10-13-00-indice.md` (+ un archivo por subsistema)
- **Tickets (por parcial y persona):** `docs/tickets/README.md`
- **Riesgos → controles → tests:** `docs/trazabilidad-riesgos.md`
- **Requisitos del docente (RF/RS):** `docs/requisitos.md` · **Normas y enfoques:** `docs/cumplimiento-normativo.md` · **Criptografía justificada:** `docs/justificacion-criptografica.md`
- **Documentos académicos:** `Documentación/` (no tocar sin que lo pidan)

## Arquitectura
| Pieza | Qué hace | BD |
|---|---|---|
| gateway (Nginx) | Único punto de entrada: TLS 1.3, rate limit, `auth_request` a `auth` en cada petición y enrutamiento a `auth` y `stego` | — |
| auth | Registro, login (Argon2id, bloqueo progresivo), JWT RS256 + sesión por dispositivo, roles y permisos; `GET /internal/verify`; CLI `create_admin` | auth |
| stego | Firma, Pillow, chi²/RS/estructura y veredicto; `POST /api/stego/analyze` con el permiso `stego:analyze` | — |

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
- **Prohibido hacer `merge` a `main`** hasta que el equipo lo autorice; el trabajo va en `feat/arquitectura-chat-seguro` o ramas hijas. No hagas `push` ni abras PR sin que te lo pidan.
- macOS/Linux: si el hook falla porque no encuentra `python`, activa el `.venv` antes de abrir Claude Code.

## Estado actual
Actualizar al cerrar cada ticket (`docs/tickets/README.md` tiene la ruta de cada persona).
- Primer parcial: [ ] 01 Fundaciones · [ ] 03 Auth (ATH-1…4) · [ ] 10 Stego · [ ] 04 Gateway (GW-1) · [ ] Entrega (PAR-1…3)
````

- [ ] **Step 9: Plantilla de PR**

`.github/pull_request_template.md`:
```markdown
## Qué cambia
<!-- La tarea del plan (p. ej. ATH-2) y su ticket (p. ej. ATH-2). -->

## Riesgos y requisitos
<!-- R# y RF/RS que toca. -->

## Lista de verificación de seguridad
- [ ] Sin secretos, tokens ni contraseñas en el código, los registros ni los tests (salvo valores de prueba marcados como tales)
- [ ] La autorización se decide en el servidor, por permiso o por pertenencia, nunca por un campo que mande el cliente
- [ ] Cuerpos con `extra="forbid"`, consultas parametrizadas y errores genéricos hacia el cliente
- [ ] Todo rechazo y todo acceso otorgado queda como evento (`shared.audit.emit`)
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

### Task FND-2: Paquete `shared`: secretos y utilidades criptográficas

**Files:**
- Create: `services/shared/pyproject.toml`
- Create: `services/shared/shared/__init__.py`, `services/shared/shared/crypto.py`, `services/shared/shared/secrets.py`
- Test: `services/shared/tests/test_crypto.py`, `services/shared/tests/test_r02_secretos.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `shared.crypto`: `b64e(bytes)->str`, `b64d(str)->bytes`, `sha256(bytes)->bytes`, `new_token(nbytes=32)->str` y `token_hash(str)->bytes`.
  - `shared.secrets`: `secrets_dir()`, `read_secret(name)->str`, `env(name, default)`, `origins()->frozenset[str]`, `db_url(service, role)->str`.

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
from shared.crypto import b64d, b64e, new_token, sha256, token_hash


def test_base64url_ida_y_vuelta_sin_relleno():
    data = bytes(range(256))
    text = b64e(data)
    assert "=" not in text and "+" not in text and "/" not in text
    assert b64d(text) == data


def test_tokens_aleatorios_y_su_hash():
    a, b = new_token(), new_token()
    assert a != b
    assert len(b64d(a)) == 32
    assert token_hash(a) == sha256(a.encode())
    assert len(token_hash(a)) == 32
```

Run: `pytest services/shared/tests/test_crypto.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.crypto'`

- [ ] **Step 3: Implementar `shared/crypto.py`**

`services/shared/shared/crypto.py`:
```python
"""Utilidades criptográficas comunes (spec §11). Sin E/S: solo cálculos."""

import base64
import hashlib
import secrets


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
```

Run: `pytest services/shared/tests/test_crypto.py -q`
Expected: PASS

- [ ] **Step 4: Tests de secretos (fallan)**

`services/shared/tests/test_r02_secretos.py`:
```python
import pytest

from shared.secrets import db_url, env, origins, read_secret


@pytest.fixture
def secrets_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))
    return tmp_path


def write(directory, name, value):
    (directory / name).write_text(value, encoding="utf-8")


def test_secreto_ausente_detiene_el_servicio(secrets_dir):
    with pytest.raises(RuntimeError, match="secreto requerido ausente: jwt_signing_key"):
        read_secret("jwt_signing_key")


def test_secreto_vacio_tambien_lo_detiene(secrets_dir):
    write(secrets_dir, "jwt_signing_key", "  \n")
    with pytest.raises(RuntimeError, match="secreto vacío: jwt_signing_key"):
        read_secret("jwt_signing_key")


def test_lee_secreto_y_url_de_bd(secrets_dir, monkeypatch):
    write(secrets_dir, "svc_hash_gateway", "abc123\n")
    write(secrets_dir, "db_auth_app", "p@ss/word")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5433")
    assert read_secret("svc_hash_gateway") == "abc123"
    assert db_url("auth", "app") == "postgresql+asyncpg://auth_app:p%40ss%2Fword@localhost:5433/auth"


def test_env_convierte_tipos(monkeypatch):
    monkeypatch.setenv("UN_ENTERO", "3")
    monkeypatch.setenv("UN_REAL", "0.5")
    monkeypatch.setenv("STEGO_ENTROPY_TRIGGER", "off")
    assert env("UN_ENTERO", 10) == 3
    assert env("UN_REAL", 5.0) == 0.5
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

Run: `pytest services/shared -q`
Expected: PASS (crypto y secretos)

- [ ] **Step 6: Commit**

```bash
git add services/shared
git commit -m "feat(shared): utilidades criptográficas y lectura de secretos"
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
  - `shared.ratelimit`: `failures(conn, key, window_min)->int`, `any_over(conn, limits: list[tuple[str, int]], window_min)->bool`, `record(conn, keys, window_min)->int` y `TokenBucket(rate, burst, clock=time.monotonic)` con `.allow()->bool`. Las funciones con `conn` operan sobre la tabla `failed_attempts(key, created_at)` de la BD de auth; se prueban contra BD en ATH-2.

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
        ("Ana-Lopez-2026", "ana-lopez-2026", False),  # igual al usuario
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
"""Argon2id para las contraseñas de las cuentas (riesgo 4, spec §11.1).

Perfil RFC 9106 de baja memoria (t=3, m=64 MiB, p=4), el predeterminado de argon2-cffi.
"""

import threading

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from starlette.concurrency import run_in_threadpool

_hasher = PasswordHasher()
# ponytail: tope global de 4 cálculos simultáneos (4 × 64 MiB) para que un ataque de logins
# masivos no agote la RAM; súbelo si el host tiene memoria de sobra.
_SLOTS = threading.BoundedSemaphore(4)
_DUMMY_HASH = _hasher.hash("dummy-password-timing-only")


def hash_secret(secret: str) -> str:
    with _SLOTS:
        return _hasher.hash(secret)


def verify_secret(stored_hash: str | None, secret: str) -> bool:
    """Sin hash (usuario inexistente) verifica contra un dummy: mismo tiempo, siempre False."""
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
"""Límites de intentos fallidos (spec §9.1) y token bucket del análisis de imágenes (spec §9.9)."""

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
    """Token bucket en memoria; stego guarda una instancia por usuario."""

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

### Task FND-4: Autenticación entre servicios, identidad, eventos de seguridad y base web (R16)

**Files:**
- Create: `services/shared/shared/service_auth.py`, `services/shared/shared/identity.py`, `services/shared/shared/audit.py`, `services/shared/shared/web.py`
- Create: `services/shared/shared/observability.py` (Step 6: correlación y registros JSON)
- Create: `services/shared/shared/testing.py` (cabeceras, `ServiceAuth` de prueba y `events`; FND-5 agrega lo de BD)
- Modify: `services/Dockerfile` (lo crea FND-6; allí ya trae `LOG_FORMAT=json` y `--no-access-log`)
- Test: `services/shared/tests/test_r16_service_auth.py`, `services/shared/tests/test_observabilidad.py`

**Interfaces:**
- Consumes: `shared.crypto.sha256` (FND-2).
- Produces:
  - `shared.service_auth`: `TOKEN_HEADER = "X-Service-Token"`; `ServiceAuth(name, callers)` con `from_secrets(name)` e `identify(token)->str|None`; `ServiceTokenMiddleware`; `allow(*callers)` (dependencia que devuelve el llamador). En el primer parcial los servicios no se llaman entre sí: el único llamador es el gateway.
  - `shared.identity`: `UserIdentity(user_id, username, session_id, perms: frozenset[str])`, `client_ip(conn)`, `user_from_headers(conn)->UserIdentity|None`, `require_gateway`, `require_user`, `require_perm(*perms)` (403 `"permiso insuficiente"` y evento `perm.denied` si falta alguno).
  - `shared.audit`: `emit(severity, action, *, actor, target=None, ip=None, details=None)`. Escribe una línea en el logger `audit` con el nivel de `severity` (`info`, `warning` o `critical`), `msg = action` y el resto en el campo `event`. No hay servicio audit en el primer parcial: los eventos se leen con `docker compose logs`.
  - `shared.web`: `SESSION_COOKIE`, `DEVICE_COOKIE`, `set_cookie(response, name, value, max_age=None)`, `clear_cookie(response, name)`, `create_base_app(*, title, settings, engine, service_auth, lifespan=None)->FastAPI` (con `engine=None`, `/health` responde sin BD: lo usa `stego`). La app expone `app.state.settings/engine/service_auth` y `request.state.caller`. Instala `RequestContextMiddleware` como el más externo y llama a `configure_logging(title)`.
  - `shared.observability` (RNF-19): `REQUEST_HEADER = "X-Request-ID"`, `REQUEST_ID: ContextVar[str | None]`, `JsonFormatter(service)`, `configure_logging(service)` (solo con `LOG_FORMAT=json`) y `RequestContextMiddleware`. El middleware toma el id que puso el gateway (si cumple `^[A-Za-z0-9-]{8,64}$`; si no, crea uno de 32 hex), lo deja en `REQUEST_ID` y registra **una línea por petición** con `method`, `path` (sin query string), `status` y `ms`. `JsonFormatter` agrega el id a cada línea, también a los eventos de `shared.audit`. Los servicios no devuelven el id al cliente: lo hace el gateway (GW-1).
  - `shared.testing`:
    - constantes `ORIGIN`, `TOKENS` (gateway, auth, stego), `ROLE_PASSWORD`, `USER_ID`, `SESSION_ID`;
    - `service_auth(name, callers)`;
    - cabeceras: `service_headers(name)`, `gateway_headers()`, `user_headers(user_id=USER_ID, username="ana", session_id=SESSION_ID, perms=())`, `cookie_header(cookies)->dict`;
    - `events(caplog, action=None)->list[dict]`: los eventos de `shared.audit` que capturó el fixture `caplog` de pytest, cada uno con `action`, `severity`, `actor`, `target`, `ip` y `details`.

- [ ] **Step 1: Utilidades de prueba (parte 1)**

`services/shared/shared/testing.py`:
```python
"""Utilidades de prueba compartidas por los servicios. No se usan en producción.

Todas las contraseñas y tokens de este módulo son FIJOS y existen solo para pruebas.
"""

from shared.crypto import sha256
from shared.service_auth import TOKEN_HEADER, ServiceAuth

ORIGIN = "https://testserver"
ROLE_PASSWORD = "solo-pruebas"
TOKENS = {name: f"token-de-prueba-{name}" for name in ("gateway", "auth", "stego")}
USER_ID = "00000000-0000-4000-8000-0000000000a1"
SESSION_ID = "00000000-0000-4000-8000-000000000051"


def service_auth(name: str, callers: tuple[str, ...]) -> ServiceAuth:
    """ServiceAuth de prueba con los hashes de los llamadores permitidos."""
    return ServiceAuth(name, {caller: sha256(TOKENS[caller].encode()) for caller in callers})


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


def events(caplog, action: str | None = None) -> list[dict]:
    """Eventos de shared.audit que capturó el fixture caplog, en orden."""
    return [
        {"action": r.getMessage(), "severity": r.levelname.lower(), **r.event}
        for r in caplog.records
        if r.name == "audit" and (action is None or r.getMessage() == action)
    ]
```

- [ ] **Step 2: Tests de R16 (fallan)**

`services/shared/tests/test_r16_service_auth.py`:
```python
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine

from shared import testing
from shared.identity import UserIdentity, require_gateway, require_perm, require_user
from shared.service_auth import allow
from shared.web import create_base_app


class Body(BaseModel):
    n: int


def build_app():
    app = create_base_app(
        title="prueba",
        settings=SimpleNamespace(allowed_origins=frozenset({testing.ORIGIN})),
        engine=create_async_engine("postgresql+asyncpg://nadie@127.0.0.1:1/nada"),  # no se usa
        service_auth=testing.service_auth("auth", ("gateway", "stego")),
    )
    router = APIRouter()

    @router.post("/api/publico", dependencies=[Depends(require_gateway)])
    async def publico(body: Body) -> dict:
        return {"n": body.n}

    @router.get("/api/admin/x")
    async def admin(who: UserIdentity = Depends(require_perm("roles:manage"))) -> dict:
        return {"user": who.username}

    @router.get("/api/yo")
    async def yo(who: UserIdentity = Depends(require_user)) -> dict:
        return {
            "user_id": who.user_id,
            "username": who.username,
            "session_id": who.session_id,
            "perms": sorted(who.perms),
        }

    @router.post("/internal/solo-gateway", dependencies=[Depends(allow("gateway"))])
    async def interno() -> dict:
        return {"ok": True}

    @router.get("/api/falla", dependencies=[Depends(require_gateway)])
    async def falla() -> dict:
        raise RuntimeError("boom")

    app.include_router(router)
    return app


@pytest.fixture
def client():
    return TestClient(build_app(), base_url=testing.ORIGIN, raise_server_exceptions=False)


def test_sin_token_401_y_se_registra(client, caplog):
    r = client.post("/api/publico", json={"n": 1})
    assert r.status_code == 401
    assert r.json() == {"error": "no autorizado"}
    [event] = testing.events(caplog, "svc.reject.token")
    assert (event["target"], event["severity"]) == ("/api/publico", "warning")


def test_token_desconocido_401(client):
    assert client.get("/api/admin/x", headers={"X-Service-Token": "inventado"}).status_code == 401


def test_ruta_publica_solo_desde_el_gateway(client, caplog):
    r = client.post("/api/publico", json={"n": 1}, headers=testing.service_headers("stego"))
    assert r.status_code == 403
    assert testing.events(caplog, "svc.reject.token")[0]["actor"] == "svc:stego"


def test_csrf_exige_origin_permitido(client, caplog):
    sin_origin = {"X-Service-Token": testing.TOKENS["gateway"]}
    assert client.post("/api/publico", json={"n": 1}, headers=sin_origin).status_code == 403
    assert testing.events(caplog, "http.reject.origin")
    ajeno = {**sin_origin, "origin": "https://evil.example"}
    assert client.post("/api/publico", json={"n": 1}, headers=ajeno).status_code == 403
    r = client.post("/api/publico", json={"n": 2}, headers=testing.gateway_headers())
    assert r.json() == {"n": 2}


def test_ruta_interna_respeta_la_allowlist(client):
    otro = testing.service_headers("stego")
    assert client.post("/internal/solo-gateway", headers=otro).status_code == 403
    assert client.post("/internal/solo-gateway", headers=testing.gateway_headers()).status_code == 200


def test_identidad_solo_vale_si_la_trae_el_gateway(client):
    assert client.get("/api/admin/x", headers=testing.gateway_headers()).status_code == 401
    ok = client.get("/api/admin/x", headers=testing.user_headers(perms=("roles:manage",)))
    assert ok.json() == {"user": "ana"}
    impostor = {
        **testing.service_headers("stego"),
        "X-User-Id": "x",
        "X-User-Name": "ana",
        "X-Session-Id": "s",
        "X-User-Perms": "roles:manage",
    }
    assert client.get("/api/admin/x", headers=impostor).status_code == 403


def test_r05_sin_el_permiso_403_y_se_registra(client, caplog):
    r = client.get("/api/admin/x", headers=testing.user_headers(perms=("stego:analyze",)))
    assert (r.status_code, r.json()) == (403, {"error": "permiso insuficiente"})
    [event] = testing.events(caplog, "perm.denied")
    assert event["actor"] == "user:ana"
    assert event["details"] == {"required": ["roles:manage"]}


def test_permisos_se_leen_de_la_cabecera(client):
    headers = testing.user_headers(perms=("stego:analyze", "roles:manage"))
    assert client.get("/api/yo", headers=headers).json() == {
        "user_id": testing.USER_ID,
        "username": "ana",
        "session_id": testing.SESSION_ID,
        "perms": ["roles:manage", "stego:analyze"],
    }
    assert client.get("/api/yo", headers=testing.user_headers()).json()["perms"] == []


def test_errores_genericos(client):
    assert client.get("/api/falla", headers=testing.gateway_headers()).json() == {"error": "error interno"}
    r = client.post("/api/publico", json={"n": "x"}, headers=testing.gateway_headers())
    assert (r.status_code, r.json()) == (422, {"error": "datos inválidos"})
```

Run: `pytest services/shared/tests/test_r16_service_auth.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.identity'`

- [ ] **Step 3: Implementar `shared/identity.py`**

```python
"""Identidad propagada por el gateway (spec §4.3). Solo se lee si el llamador verificado es 'gateway'."""

from dataclasses import dataclass

from fastapi import HTTPException, Request
from starlette.requests import HTTPConnection

from shared import audit

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
    ip = client_ip(request)
    if request.state.caller != "gateway":
        audit.emit(
            "warning", "svc.reject.token", actor=f"svc:{request.state.caller}", target=request.url.path, ip=ip
        )
        raise HTTPException(403, "no autorizado")
    origin = request.headers.get("origin")
    if request.method in UNSAFE_METHODS and origin not in request.app.state.settings.allowed_origins:
        audit.emit(
            "warning", "http.reject.origin", actor=f"ip:{ip}", target=request.url.path, ip=ip,
            details={"origin": origin},
        )
        raise HTTPException(403, "origen no permitido")


def user_from_headers(conn: HTTPConnection) -> UserIdentity | None:
    """Identidad que puso el gateway. Sin permisos, X-User-Perms no viene (Nginx omite cabeceras vacías)."""
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
            audit.emit(
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

from fastapi import HTTPException, Request
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from shared import audit
from shared.crypto import sha256
from shared.identity import client_ip
from shared.secrets import secrets_dir

TOKEN_HEADER = "X-Service-Token"  # noqa: S105 — es el nombre de la cabecera, no un secreto


@dataclass(frozen=True)
class ServiceAuth:
    name: str  # servicio dueño
    callers: dict[str, bytes]  # nombre → SHA-256 del token de cada llamador permitido

    @classmethod
    def from_secrets(cls, name: str) -> "ServiceAuth":
        callers = {
            path.name.removeprefix("svc_hash_"): bytes.fromhex(path.read_text(encoding="utf-8").strip())
            for path in secrets_dir().glob("svc_hash_*")
        }
        if not callers:
            raise RuntimeError("secreto requerido ausente: svc_hash_* (llamadores permitidos)")
        return cls(name, callers)

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
    """Exige X-Service-Token válido en toda petición HTTP salvo /health."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] == "/health":
            await self.app(scope, receive, send)
            return
        caller = scope["app"].state.service_auth.identify(Headers(scope=scope).get(TOKEN_HEADER))
        if caller is None:
            client = scope.get("client")
            audit.emit(
                "warning", "svc.reject.token", actor="svc:desconocido", target=scope["path"],
                ip=client[0] if client else None,
            )
            await JSONResponse({"error": "no autorizado"}, status_code=401)(scope, receive, send)
            return
        scope.setdefault("state", {})["caller"] = caller
        await self.app(scope, receive, send)


def allow(*callers: str):
    """Dependencia de ruta interna: el llamador verificado debe estar en la allowlist."""

    async def dependency(request: Request) -> str:
        caller = request.state.caller
        if caller not in callers:
            audit.emit(
                "warning", "svc.reject.token", actor=f"svc:{caller}", target=request.url.path,
                ip=client_ip(request),
            )
            raise HTTPException(403, "no autorizado")
        return caller

    return dependency
```

- [ ] **Step 5: Implementar `shared/audit.py` y `shared/web.py`**

`services/shared/shared/audit.py`:
```python
"""Eventos de seguridad como registros JSON (spec §14).

En el primer parcial no hay servicio audit: cada servicio escribe sus eventos en su salida estándar
(una línea JSON por evento con LOG_FORMAT=json) y se leen con `docker compose logs`.
"""

import logging

log = logging.getLogger("audit")
log.setLevel(logging.INFO)  # los eventos de seguridad no dependen del nivel por defecto (WARNING)

LEVELS = {"info": logging.INFO, "warning": logging.WARNING, "critical": logging.CRITICAL}


def emit(
    severity: str,
    action: str,
    *,
    actor: str,
    target: str | None = None,
    ip: str | None = None,
    details: dict | None = None,
) -> None:
    log.log(
        LEVELS[severity],
        action,
        extra={"event": {"actor": actor, "target": target, "ip": ip, "details": details or {}}},
    )
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


def create_base_app(*, title: str, settings, engine, service_auth, lifespan=None) -> FastAPI:
    app = FastAPI(title=title, docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.service_auth = service_auth
    app.add_middleware(ServiceTokenMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "error"
        return JSONResponse({"error": detail}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"error": "datos inválidos"}, status_code=422)

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
Expected: PASS (incluye los 9 tests de `test_r16_service_auth.py`)

- [ ] **Step 6: Correlación de peticiones y registros JSON (RNF-19)**

Un mismo `X-Request-ID` recorre gateway → servicio y aparece en cada registro y en cada evento, así que una petición de la demo se reconstruye de punta a punta en los registros.

`services/shared/tests/test_observabilidad.py`:
```python
import io
import json
import logging
import re

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from test_r16_service_auth import build_app

from shared import audit, testing
from shared.identity import require_gateway
from shared.observability import REQUEST_HEADER, REQUEST_ID, JsonFormatter


def build_client() -> TestClient:
    app = build_app()

    @app.get("/api/eco", dependencies=[Depends(require_gateway)])
    async def eco() -> dict:
        audit.emit("info", "prueba.eco", actor="system")
        return {"id": REQUEST_ID.get()}

    return TestClient(app, base_url=testing.ORIGIN)


def test_el_id_del_gateway_llega_al_codigo_y_a_los_eventos():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter("auth"))  # formatea dentro de la petición, como en producción
    logging.getLogger("audit").addHandler(handler)
    try:
        headers = {**testing.gateway_headers(), REQUEST_HEADER: "0123456789abcdef"}
        assert build_client().get("/api/eco", headers=headers).json() == {"id": "0123456789abcdef"}
    finally:
        logging.getLogger("audit").removeHandler(handler)
    line = json.loads(stream.getvalue())
    assert (line["msg"], line["request_id"]) == ("prueba.eco", "0123456789abcdef")
    assert line["event"]["actor"] == "system"


@pytest.mark.parametrize("presented", [None, "corto", "con espacios y !!"])
def test_id_ausente_o_invalido_se_reemplaza(presented):
    headers = {**testing.gateway_headers(), **({REQUEST_HEADER: presented} if presented else {})}
    got = build_client().get("/api/eco", headers=headers).json()["id"]
    assert re.fullmatch(r"[0-9a-f]{32}", got)


def test_formato_json_de_los_registros():
    record = logging.LogRecord("http", logging.INFO, __file__, 1, "request", None, None)
    record.status, record.ms = 200, 3
    token = REQUEST_ID.set("0123456789abcdef")
    try:
        line = json.loads(JsonFormatter("auth").format(record))
    finally:
        REQUEST_ID.reset(token)
    assert (line["service"], line["level"], line["request_id"], line["msg"]) == (
        "auth", "info", "0123456789abcdef", "request",
    )
    assert (line["status"], line["ms"]) == (200, 3)


def test_una_linea_por_peticion_sin_query_string(caplog):
    with caplog.at_level(logging.INFO, logger="http"):
        build_client().get("/api/eco?token=secreto", headers=testing.gateway_headers())
    [record] = [r for r in caplog.records if r.name == "http"]
    assert (record.method, record.path, record.status) == ("GET", "/api/eco", 200)
    assert "secreto" not in caplog.text
```

Run: `pytest services/shared/tests/test_observabilidad.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.observability'`

`services/shared/shared/observability.py`:
```python
"""Correlación de peticiones y registros JSON (spec §21.1; RNF-19)."""

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
    """Una línea JSON por registro: ts, service, level, request_id, logger, msg y, si los hay,
    los campos de la petición (method, path, status, ms) o el evento de seguridad (event)."""

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
        fields = ("method", "path", "status", "ms", "event")
        entry.update({k: getattr(record, k) for k in fields if hasattr(record, k)})
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
    """ASGI puro (no BaseHTTPMiddleware). Va como el más externo."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
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
            if scope["path"] != "/health":
                log.info(
                    "request",
                    extra={
                        "method": scope["method"],
                        "path": scope["path"],  # sin query string: ahí podrían viajar datos sensibles
                        "status": status,
                        "ms": round((time.perf_counter() - started) * 1000),
                    },
                )
            REQUEST_ID.reset(token)
```

Modificar `shared/web.py`: `from shared.observability import RequestContextMiddleware, configure_logging`; en `create_base_app`, después de `app.add_middleware(ServiceTokenMiddleware)`, `app.add_middleware(RequestContextMiddleware)` (Starlette pone el último agregado como el más externo, así que también los rechazos por token llevan el id) y `configure_logging(title)` al principio.

Run: `pytest services/shared -q`
Expected: PASS (9 + 6 tests)

- [ ] **Step 7: Trazabilidad y commit**

En `docs/trazabilidad-riesgos.md`, fila **R16**:
- *Servicio / archivos:* `services/shared/shared/service_auth.py`, `identity.py`, `web.py`, `observability.py`
- *Tests:* `services/shared/tests/test_r16_service_auth.py`, `test_observabilidad.py`
- *Estado:* `En progreso (falta e2e del gateway)`

```bash
git add services/shared docs/trazabilidad-riesgos.md
git commit -m "feat(shared): token por servicio, identidad del gateway, eventos de seguridad en JSON, base web y correlación de peticiones (R16)"
```

---

### Task FND-5: Utilidades de BD para pruebas y migraciones comunes

**Files:**
- Modify: `services/shared/shared/testing.py` (agregar lo de BD)
- Create: `services/shared/shared/migrations.py`
- Create: `deploy/docker-compose.test.yml`
- Test: `services/shared/tests/test_testing.py`

**Interfaces:**
- Consumes: `shared.secrets.db_url` (FND-2).
- Produces:
  - `shared.migrations.run(service)`.
  - `shared.testing` (BD): `PG_HOST`, `PG_PORT`, `FOREIGN_DB`, `dsn(user, password, database, driver="postgresql+asyncpg")`, `db_urls(service)->(owner_url, app_url)`, `prepare_database(service, service_dir)`, `run(coro)`, `sql(url, statement, **params)->list[dict]`, `with_conn(url, fn, *args)`, `truncate_all(owner_url)`, `assert_least_privilege(app_url, table)`.

Las imágenes sintéticas para el estegoanálisis las escribe Stefany en STG-1 (`stego_svc/synthetic.py`): solo las usa `stego`.

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

```

Run: `pytest services/shared/tests/test_testing.py -q`
Expected: FAIL — `AttributeError: module 'shared.testing' has no attribute 'dsn'`

- [ ] **Step 3: Agregar a `shared/testing.py`**

Al inicio, junto a los imports existentes, agregar:
```python
import asyncio
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
git commit -m "feat(shared): utilidades de BD de prueba y migraciones comunes"
```

---

### Task FND-6: Plantilla Docker, generación de secretos y PostgreSQL de auth

**Files:**
- Create: `services/Dockerfile`, `services/lock.sh`
- Create: `deploy/gen_secrets.py`, `deploy/postgres/init.sh`, `deploy/docker-compose.yml`
- Test: `services/shared/tests/test_gen_secrets.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `deploy/secrets/*`: 7 archivos. Son `postgres_password`, `db_auth_owner`, `db_auth_app`, `svc_token_gateway` con su hash `svc_hash_gateway` y su `gateway_token.conf` (lo incluye Nginx), y `jwt_signing_key` (RSA de 3072 bits).
  - Imagen por servicio: `docker build --build-arg SERVICE=<svc> -f services/Dockerfile .`.
  - Compose con `db`, las redes y las anclas `x-python-service` / `x-migrate`, que las tareas de cada servicio reutilizan.

- [ ] **Step 1: Test del generador de secretos (falla)**

`services/shared/tests/test_gen_secrets.py`:
```python
import hashlib
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SCRIPT = Path(__file__).resolve().parents[3] / "deploy" / "gen_secrets.py"


def gen(root: Path, *args: str) -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--dir", str(root), *args], check=True, capture_output=True)


def test_genera_todo_y_no_sobrescribe(tmp_path):
    gen(tmp_path)
    secrets = tmp_path / "secrets"
    assert sorted(p.name for p in secrets.iterdir()) == [
        "db_auth_app",
        "db_auth_owner",
        "gateway_token.conf",
        "jwt_signing_key",
        "postgres_password",
        "svc_hash_gateway",
        "svc_token_gateway",
    ]
    jwt_key = serialization.load_pem_private_key((secrets / "jwt_signing_key").read_bytes(), password=None)
    assert isinstance(jwt_key, rsa.RSAPrivateKey) and jwt_key.key_size == 3072
    token = (secrets / "svc_token_gateway").read_text().strip()
    assert (secrets / "svc_hash_gateway").read_text() == hashlib.sha256(token.encode()).hexdigest()
    assert token in (secrets / "gateway_token.conf").read_text()
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
"""Genera los secretos de deploy/secrets/ (spec §11.1).

Nunca sobrescribe un secreto existente; --rotate NOMBRE regenera uno (y lo que se deriva de él).
Uso:  python deploy/gen_secrets.py [--rotate NOMBRE] [--dir RUTA]
Requiere `cryptography` (incluido en el .venv del proyecto).
"""

import argparse
import hashlib
import secrets
from collections.abc import Callable
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SERVICES = ("auth",)  # los que tienen BD (stego no)
CALLERS = ("gateway",)  # quienes llaman a los servicios; en el primer parcial, solo el gateway
RANDOM = (
    "postgres_password",
    *(f"db_{svc}_{role}" for svc in SERVICES for role in ("owner", "app")),
    *(f"svc_token_{caller}" for caller in CALLERS),
)


def new_jwt_key() -> str:
    """RSA de 3072 bits para los JWT RS256 de auth (spec §11.1)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


class Generator:
    def __init__(self, root: Path, rotate: str | None) -> None:
        self.secrets_dir = root / "secrets"
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
        for name in RANDOM:
            self.ensure(name, lambda: secrets.token_urlsafe(32))
        for caller in CALLERS:
            token_name, hash_name = f"svc_token_{caller}", f"svc_hash_{caller}"
            if token_name in self.changed or not self.path(hash_name).exists():
                self.write(hash_name, hashlib.sha256(self.read(token_name).encode()).hexdigest())
        if "svc_token_gateway" in self.changed or not self.path("gateway_token.conf").exists():
            token = self.read("svc_token_gateway")
            self.write("gateway_token.conf", f'proxy_set_header X-Service-Token "{token}";\n')
        self.ensure("jwt_signing_key", new_jwt_key)


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
RUN useradd --uid 10001 --no-create-home app
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
# --no-access-log: la línea por petición la escribe RequestContextMiddleware (JSON, sin query string).
CMD exec uvicorn --factory "${SERVICE}_svc.main:create_app" --host 0.0.0.0 --port 8000 \
    --proxy-headers --forwarded-allow-ips '*' --no-server-header --no-access-log
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
for svc in auth; do
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
# Stack del primer parcial (spec §4–§5): db, auth, stego y gateway. Cada servicio se agrega en su propia tarea del plan.
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
    secrets: [postgres_password, db_auth_owner, db_auth_app]
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

volumes:
  pgdata: {}

secrets:
  postgres_password: {file: ./secrets/postgres_password}
  db_auth_owner: {file: ./secrets/db_auth_owner}
  db_auth_app: {file: ./secrets/db_auth_app}
  jwt_signing_key: {file: ./secrets/jwt_signing_key}
  gateway_token_conf: {file: ./secrets/gateway_token.conf}
  svc_hash_gateway: {file: ./secrets/svc_hash_gateway}
```

- [ ] **Step 5: Verificar la BD real**

Run:
```bash
python deploy/gen_secrets.py
docker compose -f deploy/docker-compose.yml up -d db
docker compose -f deploy/docker-compose.yml exec db psql -U postgres -tAc "SELECT datname || ':' || pg_get_userbyid(datdba) FROM pg_database WHERE datname = 'auth'"
docker compose -f deploy/docker-compose.yml exec db psql -U postgres -tAc "SELECT rolname FROM pg_roles WHERE rolname LIKE 'auth\_%' ORDER BY 1"
```
Expected:
```
auth:auth_owner
auth_app
auth_owner
```

- [ ] **Step 6: Commit**

```bash
git add services/Dockerfile services/lock.sh deploy/gen_secrets.py deploy/postgres/init.sh deploy/docker-compose.yml services/shared/tests/test_gen_secrets.py
git commit -m "feat(deploy): plantilla Docker, generación de secretos y PostgreSQL de auth"
```

---

### Task FND-7: Integración continua

**Files:**
- Create: `.github/workflows/ci.yml`, `.coveragerc`

**Interfaces:**
- Consumes: `services/shared` (FND-2…FND-6), `pytest-cov` (dev de `shared`) y la regla `C90` de `ruff.toml` (FND-1).
- Produces: el job `services` con matriz `svc`. Cada tarea `*-1` de un servicio agrega su nombre a la matriz. El job falla si un servicio baja del **80 % de cobertura de líneas** (RNF-10) o si una función supera la complejidad 10 (RNF-11). Si un servicio no llega al 80 %, se agregan pruebas: el umbral no se baja. Los jobs `codeql` (SAST) y `secrets` (gitleaks) cubren Shift Left desde el primer push.

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
          pytest "services/${{ matrix.svc }}" --cov="$pkg" --cov-report=term --cov-fail-under=80
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
        language: [python]
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
