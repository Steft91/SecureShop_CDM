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
