# syntax=docker/dockerfile:1
FROM python:3.12-slim AS api
WORKDIR /app
COPY requirements.lock.txt .
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir -r requirements.lock.txt; else pip install --no-cache-dir -r requirements.lock.txt; fi
COPY backend ./backend
ENV RELAYOPS_DB=/data/relayops.sqlite3 RELAYOPS_PUBLIC_DEMO=1
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --limit-concurrency 20 --timeout-keep-alive 5"]
