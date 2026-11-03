# Plantilla única de los servicios Python (spec §4.2). Uso: --build-arg SERVICE=<svc>
FROM python:3.13-slim
ARG SERVICE
# FORWARDED_ALLOW_IPS: uvicorn solo cree el X-Forwarded-For que llega desde la IP fija del gateway
# en la red apps (deploy/docker-compose.yml). Con '*', otro contenedor podría falsear su IP.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SERVICE=${SERVICE} LOG_FORMAT=json \
    FORWARDED_ALLOW_IPS=172.30.10.10
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
    --proxy-headers --no-server-header --no-access-log
