# ukaro-boilerplate

Base reutilizable para todos los proyectos de [Ukarasoft Technology](https://ukarasoft.com).
Incluye multi-tenant, autenticación por roles, sistema de diseño, CI/CD y Docker listo para producción.

## Stack

- **Backend:** Django 6.x (Python 3.13)
- **Base de datos:** PostgreSQL 16 (prod) / SQLite (dev)
- **CSS:** Tailwind CDN + `ukaro.css` (variables CSS propias, dark mode)
- **JS reactivo:** Alpine.js 3.14
- **Interactividad:** HTMX 2.0
- **Deploy:** Docker multi-stage + Nginx + DigitalOcean

## Inicio rápido

```bash
git clone git@github.com:ukarosoft/ukaro-boilerplate.git mi-proyecto
cd mi-proyecto

python3 -m venv env && source env/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env
python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```

## Estructura

```
apps/core/          → Organization, User, middleware, decoradores
apps/notifications/ → Notificaciones in-app
config/settings/    → base.py / dev.py / prod.py
templates/          → base.html + components/
static/css/         → ukaro.css v2.0 (~100 variables CSS)
scripts/backup.sh   → pg_dump con rotación de 7 días
docs/CLAUDE.md      → Contexto completo para Claude Code
```

## Tests

```bash
# Correr todos los tests
DJANGO_SETTINGS_MODULE=config.settings.dev python -m pytest apps/core/tests/ -v

# Con coverage
DJANGO_SETTINGS_MODULE=config.settings.dev python -m pytest --cov=apps --cov-report=term-missing
```

46 tests cubriendo modelos, middleware, decoradores y vistas del core.

## Deploy

```bash
cp .env.example .env  # Configurar variables de producción
docker compose up -d

# Con SSL (después de apuntar el dominio)
docker compose --profile certbot run certbot
```

## Crear un módulo nuevo

```bash
python manage.py startapp nombre_modulo apps/nombre_modulo
```

Heredar de `TenantModel` o `TenantSoftDeleteModel` y filtrar siempre con `.for_tenant(request.tenant)`.

Ver `docs/CLAUDE.md` para la guía completa.

---

*Ukarasoft Technology — Raíces firmes, soluciones ilimitadas.*
