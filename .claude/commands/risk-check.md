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
