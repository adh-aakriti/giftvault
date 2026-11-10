# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PORT=8000 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app/ app/

ARG GIT_SHA=unknown
ENV GIT_SHA=$GIT_SHA

USER appuser
EXPOSE 8000
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} app.main:app"]
