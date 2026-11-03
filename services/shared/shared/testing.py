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
