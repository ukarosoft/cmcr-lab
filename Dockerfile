# ==============================================================
# Stage 1: Builder — instala dependencias en venv aislado
# ==============================================================
FROM python:3.13.2-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/prod.txt ./requirements.txt
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r requirements.txt

# ==============================================================
# Stage 2: Runtime — imagen mínima con usuario no-root
# ==============================================================
FROM python:3.13.2-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# Solo runtime deps (sin gcc ni build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r ukaro && useradd -r -g ukaro -m -d /home/ukaro ukaro

COPY --from=builder /venv /venv

WORKDIR /app
COPY --chown=ukaro:ukaro . .

# collectstatic con dummy vars (no toca la DB)
RUN SECRET_KEY=build-time-dummy-key \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput --clear

USER ukaro

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz/ || exit 1

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
