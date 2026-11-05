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
