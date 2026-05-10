#!/usr/bin/env bash
# Build script para Render con diagnóstico verbose para detectar errores reales.
set -o errexit

export DJANGO_SETTINGS_MODULE=config.settings.prod

echo "==> Python: $(python --version)"
echo "==> Settings: $DJANGO_SETTINGS_MODULE"

echo "==> Instalando dependencias..."
pip install -r requirements/prod.txt

echo "==> [DIAG] Probando import de Django + settings..."
python << 'PYEOF'
import os, sys, traceback
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'
try:
    import django
    print(f'  django version: {django.get_version()}')
    django.setup()
    from django.conf import settings
    print(f'  INSTALLED_APPS count: {len(settings.INSTALLED_APPS)}')
    print(f'  staticfiles in apps: {"django.contrib.staticfiles" in settings.INSTALLED_APPS}')
    print(f'  DATABASES default engine: {settings.DATABASES["default"]["ENGINE"]}')
    print(f'  STATIC_ROOT: {settings.STATIC_ROOT}')
    print(f'  STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}')
    from django.core.management import get_commands
    cmds = get_commands()
    print(f'  total commands: {len(cmds)}')
    print(f'  collectstatic: {cmds.get("collectstatic", "MISSING!")}')
    print(f'  migrate: {cmds.get("migrate", "MISSING!")}')
except Exception as e:
    print(f'  IMPORT ERROR: {type(e).__name__}: {e}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
PYEOF

echo "==> collectstatic..."
python -m django collectstatic --noinput

echo "==> migrate..."
python -m django migrate --noinput

echo "==> setup_initial_data (idempotente)..."
python -m django setup_initial_data || echo "  (no crítico — continúa)"

echo "==> Build completado ✓"
