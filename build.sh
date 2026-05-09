#!/usr/bin/env bash
# Build script para Render — ejecuta en cada deploy
set -o errexit  # exit on error

echo "==> Instalando dependencias de producción..."
pip install -r requirements/prod.txt

echo "==> Recolectando archivos estáticos (WhiteNoise)..."
python manage.py collectstatic --noinput --settings=config.settings.prod

echo "==> Aplicando migraciones..."
python manage.py migrate --noinput --settings=config.settings.prod

echo "==> Creando datos iniciales (org CMCR + superadmin idempotente)..."
python manage.py setup_initial_data --settings=config.settings.prod || true

echo "==> Build completado ✓"
