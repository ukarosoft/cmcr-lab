#!/usr/bin/env bash
# Build script para Render — usa django-admin para evitar manage.py setdefault.
set -o errexit

export DJANGO_SETTINGS_MODULE=config.settings.prod

echo "==> Python: $(python --version)"
echo "==> Settings: $DJANGO_SETTINGS_MODULE"

echo "==> Instalando dependencias..."
pip install -r requirements/prod.txt

echo "==> Verificando configuración..."
django-admin check --deploy --fail-level WARNING || true
django-admin check

echo "==> collectstatic (WhiteNoise)..."
django-admin collectstatic --noinput

echo "==> migrate..."
django-admin migrate --noinput

echo "==> setup_initial_data (idempotente)..."
django-admin setup_initial_data || echo "  (no crítico — continúa)"

echo "==> Build completado ✓"
