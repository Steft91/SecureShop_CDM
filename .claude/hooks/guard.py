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
    assert (
        check("/repo/services/auth/tests/test_x.py", 'password = "SuperSecreta-12345678"', root)
        is None
    )
    assert check("/repo/docs/specs/a.md", "nunca ws://", root) is None
    assert check("/repo/deploy/llave.txt", "-----BEGIN PRIVATE KEY-----", root)
    assert (
        check("/repo/services/stego/stego_svc/formats.py", 'signature=b"\\x89PNG\\r\\n"', root)
        is None
    )
    print("guard.py: autoprueba OK")
    return 0


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        return self_test()
    # ponytail: bytes + UTF-8 explícito; en Windows la tubería usa cp1252 y "Á"/"Í" rompen el hook.
    event = json.loads(sys.stdin.buffer.read())
    sys.stderr.reconfigure(encoding="utf-8")
    tool_input = event.get("tool_input", {})
    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    problem = check(tool_input.get("file_path", ""), new_text(tool_input), project)
    if problem:
        print(f"Bloqueado por .claude/hooks/guard.py — {problem}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
