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
