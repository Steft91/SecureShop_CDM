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
